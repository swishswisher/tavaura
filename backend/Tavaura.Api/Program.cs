using System;
using Microsoft.EntityFrameworkCore;
using Tavaura.Api.Data;
using Tavaura.Api.Tenancy;

var builder = WebApplication.CreateBuilder(args);

const string LocalCorsPolicy = "LocalDevelopment";

builder.Services.AddDbContext<TavauraDbContext>(options =>
    options.UseNpgsql(builder.Configuration.GetConnectionString("DefaultConnection")));
builder.Services.AddControllers();
builder.Services.AddScoped<ITenantContext, TenantContext>();
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

var app = builder.Build();

app.UseHttpsRedirection();
app.UseCors(LocalCorsPolicy);
app.UseMiddleware<TenantContextMiddleware>();
app.MapControllers();

app.Run();

