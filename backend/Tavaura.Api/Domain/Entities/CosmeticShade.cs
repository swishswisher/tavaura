using System;

namespace Tavaura.Api.Domain.Entities;

public class CosmeticShade
{
    public Guid Id { get; set; }

    public Guid CosmeticProductId { get; set; }

    public string Name { get; set; } = string.Empty;

    public string HexColor { get; set; } = string.Empty;

    public string Finish { get; set; } = string.Empty;

    public bool IsActive { get; set; }
}

