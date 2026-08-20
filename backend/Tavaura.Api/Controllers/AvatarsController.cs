using System.Security.Claims;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Tavaura.Api.Auth;
using Tavaura.Api.Data;
using Tavaura.Api.Domain.Entities;
using Tavaura.Api.Models.Avatars;
using Tavaura.Api.Tenancy;

namespace Tavaura.Api.Controllers;

[ApiController]
[Route("api/avatars")]
[Authorize(Roles = AuthRoles.CustomerMerchantOrPlatform)]
public class AvatarsController : ControllerBase
{
    private readonly TavauraDbContext _dbContext;
    private readonly ITenantContext _tenantContext;

    public AvatarsController(TavauraDbContext dbContext, ITenantContext tenantContext)
    {
        _dbContext = dbContext;
        _tenantContext = tenantContext;
    }

    [HttpPost]
    public async Task<ActionResult<AvatarResponse>> CreateAsync(
        [FromBody] CreateAvatarRequest request,
        CancellationToken cancellationToken)
    {
        if (!_tenantContext.TenantId.HasValue)
        {
            return BadRequest(new { message = "Missing tenant context." });
        }

        var tenantId = _tenantContext.TenantId.Value;
        var tenantExists = await _dbContext.Tenants.AnyAsync(t => t.Id == tenantId, cancellationToken);
        if (!tenantExists)
        {
            return BadRequest(new { message = "Tenant does not exist." });
        }

        if (request.UserId == Guid.Empty)
        {
            return BadRequest(new { message = "UserId is required." });
        }

        if (string.IsNullOrWhiteSpace(request.Source))
        {
            return BadRequest(new { message = "Source is required." });
        }

        if (request.HeightCm <= 0)
        {
            return BadRequest(new { message = "HeightCm must be greater than zero." });
        }

        if (request.WeightKg <= 0)
        {
            return BadRequest(new { message = "WeightKg must be greater than zero." });
        }

        if (request.Age <= 0)
        {
            return BadRequest(new { message = "Age must be greater than zero." });
        }

        if (string.IsNullOrWhiteSpace(request.Gender))
        {
            return BadRequest(new { message = "Gender is required." });
        }

        if (string.IsNullOrWhiteSpace(request.SkinTone))
        {
            return BadRequest(new { message = "SkinTone is required." });
        }

        var user = await _dbContext.Users.FirstOrDefaultAsync(u => u.Id == request.UserId, cancellationToken);
        if (user is null || user.TenantId != tenantId)
        {
            return BadRequest(new { message = "User does not exist in the tenant." });
        }

        if (User.IsInRole(AuthRoles.CustomerUser) &&
            !string.Equals(
                User.FindFirstValue(ClaimTypes.NameIdentifier),
                request.UserId.ToString(),
                StringComparison.OrdinalIgnoreCase))
        {
            return Forbid();
        }

        var now = DateTime.UtcNow;
        var avatar = new Avatar
        {
            Id = Guid.NewGuid(),
            UserId = request.UserId,
            TenantId = tenantId,
            Source = request.Source.Trim(),
            HeightCm = request.HeightCm,
            WeightKg = request.WeightKg,
            Age = request.Age,
            Gender = request.Gender.Trim(),
            IsPregnant = request.IsPregnant,
            SkinTone = request.SkinTone.Trim(),
            FacePreset = string.IsNullOrWhiteSpace(request.FacePreset) ? null : request.FacePreset.Trim(),
            HairStyleId = string.IsNullOrWhiteSpace(request.HairStyleId) ? null : request.HairStyleId.Trim(),
            SmplParametersJson = string.IsNullOrWhiteSpace(request.SmplParametersJson) ? "{}" : request.SmplParametersJson.Trim(),
            CreatedAt = now,
            UpdatedAt = now
        };

        _dbContext.Avatars.Add(avatar);
        await _dbContext.SaveChangesAsync(cancellationToken);

        var response = ToAvatarResponse(avatar);
        return Created($"/api/avatars/{avatar.Id}", response);
    }

    private static AvatarResponse ToAvatarResponse(Avatar avatar)
    {
        return new AvatarResponse
        {
            Id = avatar.Id,
            UserId = avatar.UserId,
            TenantId = avatar.TenantId,
            Source = avatar.Source,
            HeightCm = avatar.HeightCm,
            WeightKg = avatar.WeightKg,
            Age = avatar.Age,
            Gender = avatar.Gender,
            IsPregnant = avatar.IsPregnant,
            SkinTone = avatar.SkinTone,
            FacePreset = avatar.FacePreset,
            HairStyleId = avatar.HairStyleId,
            SmplParametersJson = avatar.SmplParametersJson,
            CreatedAt = avatar.CreatedAt,
            UpdatedAt = avatar.UpdatedAt
        };
    }
}
