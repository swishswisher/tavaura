using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Tavaura.Api.Data.Migrations
{
    /// <inheritdoc />
    public partial class AlignPipelineStatusAndIndexes : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropCheckConstraint(
                name: "CK_RenderJobs_Status",
                table: "RenderJobs");

            migrationBuilder.DropCheckConstraint(
                name: "CK_IngestionJobs_Status",
                table: "IngestionJobs");

            migrationBuilder.DropIndex(
                name: "IX_AssetVersions_GarmentAssetId_VersionNumber",
                table: "AssetVersions");

            migrationBuilder.Sql(
                "UPDATE \"IngestionJobs\" SET \"Status\" = 'needs_review' WHERE \"Status\" = 'review_required';");

            migrationBuilder.AddCheckConstraint(
                name: "CK_RenderJobs_Status",
                table: "RenderJobs",
                sql: "\"Status\" IN ('pending', 'processing', 'completed', 'failed', 'needs_review')");

            migrationBuilder.AddCheckConstraint(
                name: "CK_IngestionJobs_Status",
                table: "IngestionJobs",
                sql: "\"Status\" IN ('pending', 'processing', 'completed', 'failed', 'needs_review')");

            migrationBuilder.CreateIndex(
                name: "IX_GarmentAssets_TenantId_GarmentId",
                table: "GarmentAssets",
                columns: new[] { "TenantId", "GarmentId" });

            migrationBuilder.CreateIndex(
                name: "IX_AssetVersions_GarmentAssetId_VersionNumber",
                table: "AssetVersions",
                columns: new[] { "GarmentAssetId", "VersionNumber" },
                unique: true,
                descending: new[] { false, true });
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropCheckConstraint(
                name: "CK_RenderJobs_Status",
                table: "RenderJobs");

            migrationBuilder.DropCheckConstraint(
                name: "CK_IngestionJobs_Status",
                table: "IngestionJobs");

            migrationBuilder.DropIndex(
                name: "IX_GarmentAssets_TenantId_GarmentId",
                table: "GarmentAssets");

            migrationBuilder.DropIndex(
                name: "IX_AssetVersions_GarmentAssetId_VersionNumber",
                table: "AssetVersions");

            migrationBuilder.AddCheckConstraint(
                name: "CK_RenderJobs_Status",
                table: "RenderJobs",
                sql: "\"Status\" IN ('pending', 'processing', 'completed', 'failed')");

            migrationBuilder.AddCheckConstraint(
                name: "CK_IngestionJobs_Status",
                table: "IngestionJobs",
                sql: "\"Status\" IN ('pending', 'processing', 'review_required', 'completed', 'failed')");

            migrationBuilder.CreateIndex(
                name: "IX_AssetVersions_GarmentAssetId_VersionNumber",
                table: "AssetVersions",
                columns: new[] { "GarmentAssetId", "VersionNumber" },
                unique: true);
        }
    }
}
