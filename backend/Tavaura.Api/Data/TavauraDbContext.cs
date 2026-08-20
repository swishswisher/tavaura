using Microsoft.EntityFrameworkCore;
using Tavaura.Api.Domain.Entities;

namespace Tavaura.Api.Data;

public class TavauraDbContext : DbContext
{
    private readonly Tavaura.Api.Tenancy.ITenantContext _tenantContext;

    public TavauraDbContext(
        DbContextOptions<TavauraDbContext> options,
        Tavaura.Api.Tenancy.ITenantContext tenantContext)
        : base(options)
    {
        _tenantContext = tenantContext;
    }

    public DbSet<Tenant> Tenants { get; set; } = null!;
    public DbSet<Account> Accounts { get; set; } = null!;
    public DbSet<AccountUserMembership> AccountUserMemberships { get; set; } = null!;
    public DbSet<Store> Stores { get; set; } = null!;
    public DbSet<MerchantAdminSettings> MerchantAdminSettings { get; set; } = null!;
    public DbSet<User> Users { get; set; } = null!;
    public DbSet<UserInvitation> UserInvitations { get; set; } = null!;
    public DbSet<Avatar> Avatars { get; set; } = null!;
    public DbSet<AvatarHairStyle> AvatarHairStyles { get; set; } = null!;
    public DbSet<Garment> Garments { get; set; } = null!;
    public DbSet<GarmentAsset> GarmentAssets { get; set; } = null!;
    public DbSet<AssetVersion> AssetVersions { get; set; } = null!;
    public DbSet<IngestionJob> IngestionJobs { get; set; } = null!;
    public DbSet<RenderJob> RenderJobs { get; set; } = null!;
    public DbSet<RenderResult> RenderResults { get; set; } = null!;
    public DbSet<CosmeticProduct> CosmeticProducts { get; set; } = null!;
    public DbSet<CosmeticShade> CosmeticShades { get; set; } = null!;
    public DbSet<UserLook> UserLooks { get; set; } = null!;
    public DbSet<Challenge> Challenges { get; set; } = null!;
    public DbSet<ChallengeEntry> ChallengeEntries { get; set; } = null!;

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<Tenant>().HasKey(t => t.Id);
        modelBuilder.Entity<Account>().HasKey(a => a.Id);
        modelBuilder.Entity<AccountUserMembership>().HasKey(am => am.Id);
        modelBuilder.Entity<Store>().HasKey(s => s.Id);
        modelBuilder.Entity<MerchantAdminSettings>().HasKey(s => s.Id);
        modelBuilder.Entity<User>().HasKey(u => u.Id);
        modelBuilder.Entity<UserInvitation>().HasKey(i => i.Id);
        modelBuilder.Entity<Avatar>().HasKey(a => a.Id);
        modelBuilder.Entity<AvatarHairStyle>().HasKey(h => h.Id);
        modelBuilder.Entity<Garment>().HasKey(g => g.Id);
        modelBuilder.Entity<GarmentAsset>().HasKey(ga => ga.Id);
        modelBuilder.Entity<AssetVersion>().HasKey(av => av.Id);
        modelBuilder.Entity<IngestionJob>().HasKey(ij => ij.Id);
        modelBuilder.Entity<RenderJob>().HasKey(rj => rj.Id);
        modelBuilder.Entity<RenderResult>().HasKey(rr => rr.Id);
        modelBuilder.Entity<CosmeticProduct>().HasKey(cp => cp.Id);
        modelBuilder.Entity<CosmeticShade>().HasKey(cs => cs.Id);
        modelBuilder.Entity<UserLook>().HasKey(ul => ul.Id);
        modelBuilder.Entity<Challenge>().HasKey(c => c.Id);
        modelBuilder.Entity<ChallengeEntry>().HasKey(ce => ce.Id);

        modelBuilder.Entity<Garment>()
            .HasIndex(g => new { g.TenantId, g.ExternalProductId })
            .IsUnique();

        modelBuilder.Entity<Garment>()
            .HasAlternateKey(g => new { g.TenantId, g.Id });

        modelBuilder.Entity<GarmentAsset>()
            .HasAlternateKey(ga => new { ga.TenantId, ga.Id });

        modelBuilder.Entity<AssetVersion>()
            .HasAlternateKey(av => new { av.TenantId, av.Id });

        modelBuilder.Entity<Avatar>()
            .HasAlternateKey(a => new { a.TenantId, a.Id });

        modelBuilder.Entity<RenderJob>()
            .HasAlternateKey(rj => new { rj.TenantId, rj.Id });

        modelBuilder.Entity<User>()
            .HasIndex(u => u.NormalizedEmail)
            .IsUnique();

        modelBuilder.Entity<User>()
            .Property(u => u.Email)
            .HasMaxLength(320);

        modelBuilder.Entity<User>()
            .Property(u => u.NormalizedEmail)
            .HasMaxLength(320);

        modelBuilder.Entity<User>()
            .Property(u => u.Role)
            .HasMaxLength(64);

        modelBuilder.Entity<User>()
            .Property(u => u.PasswordHash)
            .HasMaxLength(1024);

        modelBuilder.Entity<UserInvitation>()
            .HasIndex(i => i.TokenHash)
            .IsUnique();

        modelBuilder.Entity<UserInvitation>()
            .Property(i => i.TokenHash)
            .HasMaxLength(64);

        modelBuilder.Entity<UserInvitation>()
            .Property(i => i.Email)
            .HasMaxLength(320);

        modelBuilder.Entity<UserInvitation>()
            .Property(i => i.NormalizedEmail)
            .HasMaxLength(320);

        modelBuilder.Entity<UserInvitation>()
            .Property(i => i.Role)
            .HasMaxLength(64);

        modelBuilder.Entity<UserInvitation>()
            .HasIndex(i => new { i.NormalizedEmail, i.AcceptedAt, i.ExpiresAt });

        modelBuilder.Entity<Garment>()
            .Property(g => g.IsDeleted)
            .HasDefaultValue(false);

        modelBuilder.Entity<RenderJob>()
            .Property(rj => rj.IsDeleted)
            .HasDefaultValue(false);

        modelBuilder.Entity<RenderResult>()
            .Property(rr => rr.IsDeleted)
            .HasDefaultValue(false);

        modelBuilder.Entity<AssetVersion>()
            .HasIndex(av => new { av.GarmentAssetId, av.VersionNumber })
            .IsDescending(false, true)
            .IsUnique();

        modelBuilder.Entity<Account>()
            .HasIndex(a => a.Slug)
            .IsUnique();

        modelBuilder.Entity<AccountUserMembership>()
            .HasIndex(am => new { am.AccountId, am.UserId })
            .IsUnique();

        modelBuilder.Entity<Store>()
            .HasIndex(s => s.AccountId);

        modelBuilder.Entity<Store>()
            .HasIndex(s => s.TenantId)
            .IsUnique();

        modelBuilder.Entity<Store>()
            .HasIndex(s => new { s.AccountId, s.Slug })
            .IsUnique();

        modelBuilder.Entity<MerchantAdminSettings>()
            .HasIndex(s => s.TenantId)
            .IsUnique();

        modelBuilder.Entity<MerchantAdminSettings>()
            .Property(s => s.ApiKeyHash)
            .HasMaxLength(64);

        modelBuilder.Entity<MerchantAdminSettings>()
            .Property(s => s.ApiKeyPrefix)
            .HasMaxLength(32);

        modelBuilder.Entity<MerchantAdminSettings>()
            .Property(s => s.ApiKeyLastFour)
            .HasMaxLength(4);

        modelBuilder.Entity<MerchantAdminSettings>()
            .Property(s => s.ApiKeyScopes)
            .HasMaxLength(256);

        modelBuilder.Entity<IngestionJob>()
            .HasIndex(ij => new { ij.Status, ij.CreatedAt });

        modelBuilder.Entity<IngestionJob>()
            .HasIndex(ij => new { ij.TenantId, ij.CreatedAt });

        modelBuilder.Entity<RenderJob>()
            .HasIndex(rj => new { rj.Status, rj.CreatedAt });

        modelBuilder.Entity<RenderJob>()
            .HasIndex(rj => new { rj.TenantId, rj.CreatedAt });

        modelBuilder.Entity<GarmentAsset>()
            .HasIndex(ga => new { ga.TenantId, ga.GarmentId });

        modelBuilder.Entity<GarmentAsset>()
            .HasIndex(ga => new { ga.TenantId, ga.GarmentId, ga.AssetType });

        modelBuilder.Entity<RenderResult>()
            .HasIndex(rr => rr.RenderJobId);

        modelBuilder.Entity<GarmentAsset>()
            .HasOne<Garment>()
            .WithMany()
            .HasForeignKey(ga => new { ga.TenantId, ga.GarmentId })
            .HasPrincipalKey(g => new { g.TenantId, g.Id })
            .OnDelete(DeleteBehavior.Restrict);

        modelBuilder.Entity<UserInvitation>()
            .HasOne<Tenant>()
            .WithMany()
            .HasForeignKey(i => i.TenantId)
            .OnDelete(DeleteBehavior.Restrict);

        modelBuilder.Entity<UserInvitation>()
            .HasOne<User>()
            .WithMany()
            .HasForeignKey(i => i.CreatedByUserId)
            .OnDelete(DeleteBehavior.Restrict);

        modelBuilder.Entity<AssetVersion>()
            .HasOne<GarmentAsset>()
            .WithMany()
            .HasForeignKey(av => new { av.TenantId, av.GarmentAssetId })
            .HasPrincipalKey(ga => new { ga.TenantId, ga.Id })
            .OnDelete(DeleteBehavior.Restrict);

        modelBuilder.Entity<RenderJob>()
            .HasOne<GarmentAsset>()
            .WithMany()
            .HasForeignKey(rj => new { rj.TenantId, rj.GarmentAssetId })
            .HasPrincipalKey(ga => new { ga.TenantId, ga.Id })
            .OnDelete(DeleteBehavior.Restrict);

        modelBuilder.Entity<RenderJob>()
            .HasOne<Avatar>()
            .WithMany()
            .HasForeignKey(rj => new { rj.TenantId, rj.AvatarId })
            .HasPrincipalKey(a => new { a.TenantId, a.Id })
            .OnDelete(DeleteBehavior.Restrict);

        modelBuilder.Entity<RenderJob>()
            .HasOne<AssetVersion>()
            .WithMany()
            .HasForeignKey(rj => new { rj.TenantId, rj.AssetVersionId })
            .HasPrincipalKey(av => new { av.TenantId, av.Id })
            .OnDelete(DeleteBehavior.Restrict);

        modelBuilder.Entity<RenderResult>()
            .HasOne<RenderJob>()
            .WithMany()
            .HasForeignKey(rr => new { rr.TenantId, rr.RenderJobId })
            .HasPrincipalKey(rj => new { rj.TenantId, rj.Id })
            .OnDelete(DeleteBehavior.Restrict);

        modelBuilder.Entity<AccountUserMembership>()
            .HasOne<Account>()
            .WithMany()
            .HasForeignKey(am => am.AccountId)
            .OnDelete(DeleteBehavior.Restrict);

        modelBuilder.Entity<AccountUserMembership>()
            .HasOne<User>()
            .WithMany()
            .HasForeignKey(am => am.UserId)
            .OnDelete(DeleteBehavior.Restrict);

        modelBuilder.Entity<Store>()
            .HasOne<Account>()
            .WithMany()
            .HasForeignKey(s => s.AccountId)
            .OnDelete(DeleteBehavior.Restrict);

        modelBuilder.Entity<Store>()
            .HasOne<Tenant>()
            .WithOne()
            .HasForeignKey<Store>(s => s.TenantId)
            .OnDelete(DeleteBehavior.Restrict);

        modelBuilder.Entity<MerchantAdminSettings>()
            .HasOne<Tenant>()
            .WithMany()
            .HasForeignKey(s => s.TenantId)
            .OnDelete(DeleteBehavior.Restrict);

        modelBuilder.Entity<GarmentAsset>()
            .ToTable(t => t.HasCheckConstraint(
                "CK_GarmentAssets_AssetType",
                "\"AssetType\" IN ('front', 'back', 'side', 'model-worn')"));

        modelBuilder.Entity<IngestionJob>()
            .ToTable(t => t.HasCheckConstraint(
                "CK_IngestionJobs_Status",
                "\"Status\" IN ('pending', 'processing', 'completed', 'failed', 'needs_review')"));

        modelBuilder.Entity<RenderJob>()
            .ToTable(t => t.HasCheckConstraint(
                "CK_RenderJobs_Status",
                "\"Status\" IN ('pending', 'processing', 'completed', 'failed', 'needs_review')"));

        modelBuilder.Entity<MerchantAdminSettings>()
            .HasQueryFilter(s => s.TenantId == _tenantContext.TenantId);
        modelBuilder.Entity<Garment>()
            .HasQueryFilter(g => g.TenantId == _tenantContext.TenantId);
        modelBuilder.Entity<GarmentAsset>()
            .HasQueryFilter(ga => ga.TenantId == _tenantContext.TenantId);
        modelBuilder.Entity<AssetVersion>()
            .HasQueryFilter(av => av.TenantId == _tenantContext.TenantId);
        modelBuilder.Entity<IngestionJob>()
            .HasQueryFilter(ij => ij.TenantId == _tenantContext.TenantId);
        modelBuilder.Entity<RenderJob>()
            .HasQueryFilter(rj => rj.TenantId == _tenantContext.TenantId);
        modelBuilder.Entity<RenderResult>()
            .HasQueryFilter(rr => rr.TenantId == _tenantContext.TenantId);
        modelBuilder.Entity<CosmeticProduct>()
            .HasQueryFilter(cp => cp.TenantId == _tenantContext.TenantId);
        modelBuilder.Entity<Challenge>()
            .HasQueryFilter(c => c.TenantId == _tenantContext.TenantId);
        modelBuilder.Entity<Avatar>()
            .HasQueryFilter(a => a.TenantId == _tenantContext.TenantId);
        modelBuilder.Entity<UserLook>()
            .HasQueryFilter(ul => ul.TenantId == _tenantContext.TenantId);

        base.OnModelCreating(modelBuilder);
    }
}

