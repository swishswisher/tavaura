using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Tavaura.Api.Data.Migrations
{
    /// <inheritdoc />
    public partial class HardenPipelineSchema : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<Guid>(
                name: "AssetVersionId",
                table: "RenderJobs",
                type: "uuid",
                nullable: false,
                defaultValue: new Guid("00000000-0000-0000-0000-000000000000"));

            migrationBuilder.AddColumn<int>(
                name: "AttemptCount",
                table: "RenderJobs",
                type: "integer",
                nullable: false,
                defaultValue: 0);

            migrationBuilder.AddColumn<DateTime>(
                name: "CompletedAt",
                table: "RenderJobs",
                type: "timestamp with time zone",
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "ErrorMessage",
                table: "RenderJobs",
                type: "text",
                nullable: true);

            migrationBuilder.AddColumn<DateTime>(
                name: "StartedAt",
                table: "RenderJobs",
                type: "timestamp with time zone",
                nullable: true);

            migrationBuilder.AddColumn<int>(
                name: "AttemptCount",
                table: "IngestionJobs",
                type: "integer",
                nullable: false,
                defaultValue: 0);

            migrationBuilder.AddColumn<DateTime>(
                name: "CompletedAt",
                table: "IngestionJobs",
                type: "timestamp with time zone",
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "ErrorMessage",
                table: "IngestionJobs",
                type: "text",
                nullable: true);

            migrationBuilder.AddColumn<DateTime>(
                name: "StartedAt",
                table: "IngestionJobs",
                type: "timestamp with time zone",
                nullable: true);

            migrationBuilder.CreateIndex(
                name: "IX_RenderResults_RenderJobId",
                table: "RenderResults",
                column: "RenderJobId");

            migrationBuilder.CreateIndex(
                name: "IX_RenderJobs_AssetVersionId",
                table: "RenderJobs",
                column: "AssetVersionId");

            migrationBuilder.CreateIndex(
                name: "IX_RenderJobs_AvatarId",
                table: "RenderJobs",
                column: "AvatarId");

            migrationBuilder.CreateIndex(
                name: "IX_RenderJobs_GarmentAssetId",
                table: "RenderJobs",
                column: "GarmentAssetId");

            migrationBuilder.CreateIndex(
                name: "IX_RenderJobs_Status_CreatedAt",
                table: "RenderJobs",
                columns: new[] { "Status", "CreatedAt" });

            migrationBuilder.CreateIndex(
                name: "IX_RenderJobs_TenantId_CreatedAt",
                table: "RenderJobs",
                columns: new[] { "TenantId", "CreatedAt" });

            migrationBuilder.AddCheckConstraint(
                name: "CK_RenderJobs_Status",
                table: "RenderJobs",
                sql: "\"Status\" IN ('pending', 'processing', 'completed', 'failed')");

            migrationBuilder.CreateIndex(
                name: "IX_IngestionJobs_Status_CreatedAt",
                table: "IngestionJobs",
                columns: new[] { "Status", "CreatedAt" });

            migrationBuilder.CreateIndex(
                name: "IX_IngestionJobs_TenantId_CreatedAt",
                table: "IngestionJobs",
                columns: new[] { "TenantId", "CreatedAt" });

            migrationBuilder.AddCheckConstraint(
                name: "CK_IngestionJobs_Status",
                table: "IngestionJobs",
                sql: "\"Status\" IN ('pending', 'processing', 'review_required', 'completed', 'failed')");

            migrationBuilder.CreateIndex(
                name: "IX_Garments_TenantId_ExternalProductId",
                table: "Garments",
                columns: new[] { "TenantId", "ExternalProductId" },
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_GarmentAssets_GarmentId",
                table: "GarmentAssets",
                column: "GarmentId");

            migrationBuilder.CreateIndex(
                name: "IX_GarmentAssets_TenantId_GarmentId_AssetType",
                table: "GarmentAssets",
                columns: new[] { "TenantId", "GarmentId", "AssetType" });

            migrationBuilder.AddCheckConstraint(
                name: "CK_GarmentAssets_AssetType",
                table: "GarmentAssets",
                sql: "\"AssetType\" IN ('front', 'back', 'side', 'model-worn')");

            migrationBuilder.CreateIndex(
                name: "IX_AssetVersions_GarmentAssetId_VersionNumber",
                table: "AssetVersions",
                columns: new[] { "GarmentAssetId", "VersionNumber" },
                unique: true);

            migrationBuilder.AddForeignKey(
                name: "FK_AssetVersions_GarmentAssets_GarmentAssetId",
                table: "AssetVersions",
                column: "GarmentAssetId",
                principalTable: "GarmentAssets",
                principalColumn: "Id",
                onDelete: ReferentialAction.Restrict);

            migrationBuilder.AddForeignKey(
                name: "FK_GarmentAssets_Garments_GarmentId",
                table: "GarmentAssets",
                column: "GarmentId",
                principalTable: "Garments",
                principalColumn: "Id",
                onDelete: ReferentialAction.Restrict);

            migrationBuilder.AddForeignKey(
                name: "FK_RenderJobs_AssetVersions_AssetVersionId",
                table: "RenderJobs",
                column: "AssetVersionId",
                principalTable: "AssetVersions",
                principalColumn: "Id",
                onDelete: ReferentialAction.Restrict);

            migrationBuilder.AddForeignKey(
                name: "FK_RenderJobs_Avatars_AvatarId",
                table: "RenderJobs",
                column: "AvatarId",
                principalTable: "Avatars",
                principalColumn: "Id",
                onDelete: ReferentialAction.Restrict);

            migrationBuilder.AddForeignKey(
                name: "FK_RenderJobs_GarmentAssets_GarmentAssetId",
                table: "RenderJobs",
                column: "GarmentAssetId",
                principalTable: "GarmentAssets",
                principalColumn: "Id",
                onDelete: ReferentialAction.Restrict);

            migrationBuilder.AddForeignKey(
                name: "FK_RenderResults_RenderJobs_RenderJobId",
                table: "RenderResults",
                column: "RenderJobId",
                principalTable: "RenderJobs",
                principalColumn: "Id",
                onDelete: ReferentialAction.Restrict);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_AssetVersions_GarmentAssets_GarmentAssetId",
                table: "AssetVersions");

            migrationBuilder.DropForeignKey(
                name: "FK_GarmentAssets_Garments_GarmentId",
                table: "GarmentAssets");

            migrationBuilder.DropForeignKey(
                name: "FK_RenderJobs_AssetVersions_AssetVersionId",
                table: "RenderJobs");

            migrationBuilder.DropForeignKey(
                name: "FK_RenderJobs_Avatars_AvatarId",
                table: "RenderJobs");

            migrationBuilder.DropForeignKey(
                name: "FK_RenderJobs_GarmentAssets_GarmentAssetId",
                table: "RenderJobs");

            migrationBuilder.DropForeignKey(
                name: "FK_RenderResults_RenderJobs_RenderJobId",
                table: "RenderResults");

            migrationBuilder.DropIndex(
                name: "IX_RenderResults_RenderJobId",
                table: "RenderResults");

            migrationBuilder.DropIndex(
                name: "IX_RenderJobs_AssetVersionId",
                table: "RenderJobs");

            migrationBuilder.DropIndex(
                name: "IX_RenderJobs_AvatarId",
                table: "RenderJobs");

            migrationBuilder.DropIndex(
                name: "IX_RenderJobs_GarmentAssetId",
                table: "RenderJobs");

            migrationBuilder.DropIndex(
                name: "IX_RenderJobs_Status_CreatedAt",
                table: "RenderJobs");

            migrationBuilder.DropIndex(
                name: "IX_RenderJobs_TenantId_CreatedAt",
                table: "RenderJobs");

            migrationBuilder.DropCheckConstraint(
                name: "CK_RenderJobs_Status",
                table: "RenderJobs");

            migrationBuilder.DropIndex(
                name: "IX_IngestionJobs_Status_CreatedAt",
                table: "IngestionJobs");

            migrationBuilder.DropIndex(
                name: "IX_IngestionJobs_TenantId_CreatedAt",
                table: "IngestionJobs");

            migrationBuilder.DropCheckConstraint(
                name: "CK_IngestionJobs_Status",
                table: "IngestionJobs");

            migrationBuilder.DropIndex(
                name: "IX_Garments_TenantId_ExternalProductId",
                table: "Garments");

            migrationBuilder.DropIndex(
                name: "IX_GarmentAssets_GarmentId",
                table: "GarmentAssets");

            migrationBuilder.DropIndex(
                name: "IX_GarmentAssets_TenantId_GarmentId_AssetType",
                table: "GarmentAssets");

            migrationBuilder.DropCheckConstraint(
                name: "CK_GarmentAssets_AssetType",
                table: "GarmentAssets");

            migrationBuilder.DropIndex(
                name: "IX_AssetVersions_GarmentAssetId_VersionNumber",
                table: "AssetVersions");

            migrationBuilder.DropColumn(
                name: "AssetVersionId",
                table: "RenderJobs");

            migrationBuilder.DropColumn(
                name: "AttemptCount",
                table: "RenderJobs");

            migrationBuilder.DropColumn(
                name: "CompletedAt",
                table: "RenderJobs");

            migrationBuilder.DropColumn(
                name: "ErrorMessage",
                table: "RenderJobs");

            migrationBuilder.DropColumn(
                name: "StartedAt",
                table: "RenderJobs");

            migrationBuilder.DropColumn(
                name: "AttemptCount",
                table: "IngestionJobs");

            migrationBuilder.DropColumn(
                name: "CompletedAt",
                table: "IngestionJobs");

            migrationBuilder.DropColumn(
                name: "ErrorMessage",
                table: "IngestionJobs");

            migrationBuilder.DropColumn(
                name: "StartedAt",
                table: "IngestionJobs");
        }
    }
}
