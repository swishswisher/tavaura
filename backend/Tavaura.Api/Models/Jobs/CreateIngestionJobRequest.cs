using System.ComponentModel.DataAnnotations;

namespace Tavaura.Api.Models.Jobs;

public class CreateIngestionJobRequest
{
    [Required]
    public Guid GarmentId { get; set; }
}

