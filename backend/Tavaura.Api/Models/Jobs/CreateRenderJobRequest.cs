using System.ComponentModel.DataAnnotations;

namespace Tavaura.Api.Models.Jobs;

public class CreateRenderJobRequest
{
    public Guid AvatarId { get; set; }

    [Required]
    public Guid GarmentId { get; set; }

    public string? AvatarImageUrl { get; set; }
}
