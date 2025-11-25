using Microsoft.EntityFrameworkCore;
using Tavaura.Api.Domain.Entities;

namespace Tavaura.Api.Data;

public class TavauraDbContext : DbContext
{
    public TavauraDbContext(DbContextOptions<TavauraDbContext> options)
        : base(options)
    {
    }

    public DbSet<Tenant> Tenants { get; set; } = null!;
    public DbSet<User> Users { get; set; } = null!;
    public DbSet<Avatar> Avatars { get; set; } = null!;
    public DbSet<AvatarHairStyle> AvatarHairStyles { get; set; } = null!;
    public DbSet<Garment> Garments { get; set; } = null!;
    public DbSet<CosmeticProduct> CosmeticProducts { get; set; } = null!;
    public DbSet<CosmeticShade> CosmeticShades { get; set; } = null!;
    public DbSet<UserLook> UserLooks { get; set; } = null!;
    public DbSet<Challenge> Challenges { get; set; } = null!;
    public DbSet<ChallengeEntry> ChallengeEntries { get; set; } = null!;

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Tenant>().HasKey(t => t.Id);
        modelBuilder.Entity<User>().HasKey(u => u.Id);
        modelBuilder.Entity<Avatar>().HasKey(a => a.Id);
        modelBuilder.Entity<AvatarHairStyle>().HasKey(h => h.Id);
        modelBuilder.Entity<Garment>().HasKey(g => g.Id);
        modelBuilder.Entity<CosmeticProduct>().HasKey(cp => cp.Id);
        modelBuilder.Entity<CosmeticShade>().HasKey(cs => cs.Id);
        modelBuilder.Entity<UserLook>().HasKey(ul => ul.Id);
        modelBuilder.Entity<Challenge>().HasKey(c => c.Id);
        modelBuilder.Entity<ChallengeEntry>().HasKey(ce => ce.Id);

        base.OnModelCreating(modelBuilder);
    }
}

