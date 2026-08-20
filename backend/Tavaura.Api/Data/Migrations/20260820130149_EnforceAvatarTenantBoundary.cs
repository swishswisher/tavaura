using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Tavaura.Api.Data.Migrations
{
    /// <inheritdoc />
    public partial class EnforceAvatarTenantBoundary : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_RenderJobs_Avatars_AvatarId",
                table: "RenderJobs");

            migrationBuilder.DropIndex(
                name: "IX_RenderJobs_AvatarId",
                table: "RenderJobs");

            migrationBuilder.Sql(
                """
                UPDATE "Avatars" AS a
                SET "TenantId" = u."TenantId"
                FROM "Users" AS u
                WHERE a."UserId" = u."Id"
                  AND a."TenantId" IS NULL
                  AND u."TenantId" IS NOT NULL;

                UPDATE "Avatars" AS a
                SET "TenantId" = (
                    SELECT rj."TenantId"
                    FROM "RenderJobs" AS rj
                    WHERE rj."AvatarId" = a."Id"
                    LIMIT 1
                )
                WHERE a."TenantId" IS NULL
                  AND (
                      SELECT count(DISTINCT rj."TenantId")
                      FROM "RenderJobs" AS rj
                      WHERE rj."AvatarId" = a."Id"
                  ) = 1;

                DO $$
                BEGIN
                    IF EXISTS (SELECT 1 FROM "Avatars" WHERE "TenantId" IS NULL) THEN
                        RAISE EXCEPTION 'Existing avatars must be assigned to a tenant before applying this migration.';
                    END IF;
                    IF EXISTS (
                        SELECT 1
                        FROM "RenderJobs" AS rj
                        JOIN "Avatars" AS a ON a."Id" = rj."AvatarId"
                        WHERE rj."TenantId" <> a."TenantId"
                    ) THEN
                        RAISE EXCEPTION 'Cross-tenant avatar/render-job links must be corrected before applying this migration.';
                    END IF;
                END $$;
                """);

            migrationBuilder.AlterColumn<Guid>(
                name: "TenantId",
                table: "Avatars",
                type: "uuid",
                nullable: false,
                oldClrType: typeof(Guid),
                oldType: "uuid",
                oldNullable: true);

            migrationBuilder.AddUniqueConstraint(
                name: "AK_Avatars_TenantId_Id",
                table: "Avatars",
                columns: new[] { "TenantId", "Id" });

            migrationBuilder.CreateIndex(
                name: "IX_RenderJobs_TenantId_AvatarId",
                table: "RenderJobs",
                columns: new[] { "TenantId", "AvatarId" });

            migrationBuilder.AddForeignKey(
                name: "FK_RenderJobs_Avatars_TenantId_AvatarId",
                table: "RenderJobs",
                columns: new[] { "TenantId", "AvatarId" },
                principalTable: "Avatars",
                principalColumns: new[] { "TenantId", "Id" },
                onDelete: ReferentialAction.Restrict);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_RenderJobs_Avatars_TenantId_AvatarId",
                table: "RenderJobs");

            migrationBuilder.DropIndex(
                name: "IX_RenderJobs_TenantId_AvatarId",
                table: "RenderJobs");

            migrationBuilder.DropUniqueConstraint(
                name: "AK_Avatars_TenantId_Id",
                table: "Avatars");

            migrationBuilder.AlterColumn<Guid>(
                name: "TenantId",
                table: "Avatars",
                type: "uuid",
                nullable: true,
                oldClrType: typeof(Guid),
                oldType: "uuid");

            migrationBuilder.CreateIndex(
                name: "IX_RenderJobs_AvatarId",
                table: "RenderJobs",
                column: "AvatarId");

            migrationBuilder.AddForeignKey(
                name: "FK_RenderJobs_Avatars_AvatarId",
                table: "RenderJobs",
                column: "AvatarId",
                principalTable: "Avatars",
                principalColumn: "Id",
                onDelete: ReferentialAction.Restrict);
        }
    }
}
