using System;
using System.Security.Claims;
using System.Text;
using System.Threading.RateLimiting;
using Microsoft.AspNetCore.Authentication.JwtBearer;
using Microsoft.AspNetCore.Authorization;
using Microsoft.EntityFrameworkCore;
using Microsoft.IdentityModel.Tokens;
using Tavaura.Api.Auth;
using Tavaura.Api.Configuration;
using Tavaura.Api.Data;
using Tavaura.Api.Tenancy;

var builder = WebApplication.CreateBuilder(args);

const string CorsPolicy = "ConfiguredOrigins";

builder.Services.AddHttpContextAccessor();
builder.Services.AddScoped<TenantRlsConnectionInterceptor>();
builder.Services.AddDbContext<TavauraDbContext>((serviceProvider, options) =>
    options
        .UseNpgsql(builder.Configuration.GetConnectionString("DefaultConnection"))
        .AddInterceptors(serviceProvider.GetRequiredService<TenantRlsConnectionInterceptor>()));
builder.Services.AddControllers();
builder.Services.AddScoped<ITenantContext, TenantContext>();
builder.Services.Configure<JwtOptions>(builder.Configuration.GetSection(JwtOptions.SectionName));
builder.Services.AddSingleton<PasswordHasher>();
builder.Services.AddScoped<JwtTokenService>();
var authPermitLimit = builder.Configuration.GetValue("RateLimiting:AuthPermitLimit", 5);
var authWindowSeconds = builder.Configuration.GetValue("RateLimiting:AuthWindowSeconds", 60);
var publicWritePermitLimit = builder.Configuration.GetValue("RateLimiting:PublicWritePermitLimit", 10);
var publicWriteWindowSeconds = builder.Configuration.GetValue("RateLimiting:PublicWriteWindowSeconds", 60);
if (authPermitLimit <= 0 || authWindowSeconds <= 0 ||
    publicWritePermitLimit <= 0 || publicWriteWindowSeconds <= 0)
{
    throw new InvalidOperationException("Rate-limiting permit limits and windows must be positive.");
}

builder.Services.AddRateLimiter(options =>
{
    options.RejectionStatusCode = StatusCodes.Status429TooManyRequests;
    options.AddPolicy("auth", context => RateLimitPartition.GetFixedWindowLimiter(
        partitionKey: context.Connection.RemoteIpAddress?.ToString() ?? "unknown",
        factory: _ => new FixedWindowRateLimiterOptions
        {
            PermitLimit = authPermitLimit,
            Window = TimeSpan.FromSeconds(authWindowSeconds),
            QueueLimit = 0,
            AutoReplenishment = true
        }));
    options.AddPolicy("public-write", context => RateLimitPartition.GetFixedWindowLimiter(
        partitionKey: context.Connection.RemoteIpAddress?.ToString() ?? "unknown",
        factory: _ => new FixedWindowRateLimiterOptions
        {
            PermitLimit = publicWritePermitLimit,
            Window = TimeSpan.FromSeconds(publicWriteWindowSeconds),
            QueueLimit = 0,
            AutoReplenishment = true
        }));
});
builder.Services.AddCors(options =>
{
    var configuredOrigins = builder.Configuration
        .GetSection("Cors:AllowedOrigins")
        .Get<string[]>() ?? [];
    if (!builder.Environment.IsDevelopment() && configuredOrigins.Length == 0)
    {
        throw new InvalidOperationException("Cors:AllowedOrigins is required outside development.");
    }

    options.AddPolicy(CorsPolicy, policy =>
    {
        if (builder.Environment.IsDevelopment())
        {
            policy.SetIsOriginAllowed(origin =>
            {
                if (string.IsNullOrWhiteSpace(origin))
                {
                    return false;
                }

                if (!Uri.TryCreate(origin, UriKind.Absolute, out var uri))
                {
                    return false;
                }

                return uri.Host.Equals("localhost", StringComparison.OrdinalIgnoreCase) ||
                       configuredOrigins.Contains(origin, StringComparer.OrdinalIgnoreCase);
            });
        }
        else
        {
            policy.WithOrigins(configuredOrigins);
        }

        policy.AllowAnyHeader().AllowAnyMethod();
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

if (jwtOptions.ExpiresMinutes is < 5 or > 60)
{
    throw new InvalidOperationException("JWT ExpiresMinutes must be between 5 and 60 minutes.");
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
builder.Services.AddAuthorization(options =>
{
    options.FallbackPolicy = new AuthorizationPolicyBuilder()
        .RequireAuthenticatedUser()
        .Build();
});

var app = builder.Build();

app.UseHttpsRedirection();
app.UseCors(CorsPolicy);
app.UseRateLimiter();
app.UseAuthentication();
app.UseMiddleware<TenantContextMiddleware>();
app.UseAuthorization();
app.MapControllers();

app.Run();

public partial class Program;
