using System;
using System.Security.Claims;
using System.Text;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Options;
using Microsoft.IdentityModel.Tokens;
using Tavaura.Api.Auth;
using Tavaura.Api.Configuration;
using Tavaura.Api.Data;
using Tavaura.Api.Tenancy;
using Tavaura.Api.Worker;

var builder = WebApplication.CreateBuilder(args);

const string LocalCorsPolicy = "LocalDevelopment";

builder.Services.AddDbContext<TavauraDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("DefaultConnection")));
builder.Services.AddControllers();
builder.Services.AddScoped<ITenantContext, TenantContext>();
builder.Services.Configure<JwtOptions>(builder.Configuration.GetSection(JwtOptions.SectionName));
builder.Services.AddSingleton<PasswordHasher>();
builder.Services.AddScoped<JwtTokenService>();
builder.Services.Configure<WorkerOptions>(builder.Configuration.GetSection(WorkerOptions.SectionName));
builder.Services.AddHttpClient<IWorkerIngestionClient, WorkerIngestionClient>((serviceProvider, client) =>
{
    var options = serviceProvider.GetRequiredService<IOptions<WorkerOptions>>().Value;
    client.BaseAddress = new Uri(options.BaseUrl);
});
builder.Services.AddHttpClient<IWorkerRenderClient, WorkerRenderClient>((serviceProvider, client) =>
{
    var options = serviceProvider.GetRequiredService<IOptions<WorkerOptions>>().Value;
    client.BaseAddress = new Uri(options.BaseUrl);
});
builder.Services.AddCors(options =>
{
    options.AddPolicy(LocalCorsPolicy, policy =>
    {
        policy
            .SetIsOriginAllowed(origin =>
            {
                if (string.IsNullOrWhiteSpace(origin))
                {
                    return false;
                }

                if (!Uri.TryCreate(origin, UriKind.Absolute, out var uri))
                {
                    return false;
                }

                return uri.Host.Equals("localhost", StringComparison.OrdinalIgnoreCase);
            })
            .AllowAnyHeader()
            .AllowAnyMethod();
    });
});

var jwtOptions = builder.Configuration.GetSection(JwtOptions.SectionName).Get<JwtOptions>() ?? new JwtOptions();
if (string.IsNullOrWhiteSpace(jwtOptions.Issuer) ||
    string.IsNullOrWhiteSpace(jwtOptions.Audience) ||
    string.IsNullOrWhiteSpace(jwtOptions.SigningKey))
{
    throw new InvalidOperationException("JWT configuration requires Issuer, Audience, and SigningKey.");
}

if (Encoding.UTF8.GetByteCount(jwtOptions.SigningKey) < 32)
{
    throw new InvalidOperationException("JWT SigningKey must be at least 32 bytes.");
}

builder.Services
    .AddAuthentication(JwtBearerDefaults.AuthenticationScheme)
    .AddJwtBearer(options =>
    {
        options.RequireHttpsMetadata = !builder.Environment.IsDevelopment();
        options.TokenValidationParameters = new TokenValidationParameters
        {
            ValidateIssuer = true,
            ValidIssuer = jwtOptions.Issuer,
            ValidateAudience = true,
            ValidAudience = jwtOptions.Audience,
            ValidateIssuerSigningKey = true,
            IssuerSigningKey = new SymmetricSecurityKey(Encoding.UTF8.GetBytes(jwtOptions.SigningKey)),
            ValidateLifetime = true,
            ClockSkew = TimeSpan.FromMinutes(2),
            NameClaimType = ClaimTypes.NameIdentifier,
            RoleClaimType = ClaimTypes.Role
        };
        options.Events = new JwtBearerEvents
        {
            OnTokenValidated = async context =>
            {
                var userIdValue = context.Principal?.FindFirstValue(ClaimTypes.NameIdentifier);
                if (!Guid.TryParse(userIdValue, out var userId))
                {
                    context.Fail("Authenticated token is missing a valid user id.");
                    return;
                }

                var dbContext = context.HttpContext.RequestServices.GetRequiredService<TavauraDbContext>();
                var tokenVersion = await dbContext.Users
                    .AsNoTracking()
                    .Where(u => u.Id == userId)
                    .Select(u => (int?)u.TokenVersion)
                    .FirstOrDefaultAsync();

                if (!tokenVersion.HasValue)
                {
                    context.Fail("Authenticated user was not found.");
                    return;
                }

                var tokenVersionClaim = context.Principal?.FindFirstValue(AuthClaimTypes.TokenVersion);
                if (tokenVersion.Value == 0 && string.IsNullOrWhiteSpace(tokenVersionClaim))
                {
                    return;
                }

                if (!int.TryParse(tokenVersionClaim, out var claimVersion) ||
                    claimVersion != tokenVersion.Value)
                {
                    context.Fail("Authenticated token has been revoked.");
                }
            }
        };
    });
builder.Services.AddAuthorization();

var app = builder.Build();

app.UseHttpsRedirection();
app.UseCors(LocalCorsPolicy);
app.UseAuthentication();
app.UseMiddleware<TenantContextMiddleware>();
app.UseAuthorization();
app.MapControllers();

app.Run();
