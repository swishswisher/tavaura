using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Tavaura.Api.Data.Migrations
{
    /// <inheritdoc />
    public partial class StabilizeIdentityAndTenantBoundaries : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql(
                """
                DO $$
                BEGIN
                    IF EXISTS (SELECT 1 FROM "Users" WHERE length("Email") > 320) THEN
                        RAISE EXCEPTION 'Cannot harden Users.Email: values longer than 320 characters exist.';
                    END IF;
                    IF EXISTS (SELECT 1 FROM "Users" WHERE length("Role") > 64) THEN
                        RAISE EXCEPTION 'Cannot harden Users.Role: values longer than 64 characters exist.';
                    END IF;
                    IF EXISTS (SELECT 1 FROM "Users" WHERE length("PasswordHash") > 1024) THEN
                        RAISE EXCEPTION 'Cannot harden Users.PasswordHash: values longer than 1024 characters exist.';
                    END IF;
                END $$;
                """);

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
                name: "FK_RenderJobs_GarmentAssets_GarmentAssetId",
                table: "RenderJobs");

            migrationBuilder.DropForeignKey(
                name: "FK_RenderResults_RenderJobs_RenderJobId",
                table: "RenderResults");

            migrationBuilder.DropIndex(
                name: "IX_RenderJobs_AssetVersionId",
                table: "RenderJobs");

            migrationBuilder.DropIndex(
                name: "IX_RenderJobs_GarmentAssetId",
                table: "RenderJobs");

            migrationBuilder.DropIndex(
                name: "IX_GarmentAssets_GarmentId",
                table: "GarmentAssets");

            migrationBuilder.DropColumn(
                name: "ApiKey",
                table: "MerchantAdminSettings");

            migrationBuilder.AlterColumn<string>(
                name: "Role",
                table: "Users",
                type: "character varying(64)",
                maxLength: 64,
                nullable: false,
                oldClrType: typeof(string),
                oldType: "text");

            migrationBuilder.AlterColumn<string>(
                name: "PasswordHash",
                table: "Users",
                type: "character varying(1024)",
                maxLength: 1024,
                nullable: false,
                oldClrType: typeof(string),
                oldType: "text");

            migrationBuilder.AlterColumn<string>(
                name: "Email",
                table: "Users",
                type: "character varying(320)",
                maxLength: 320,
                nullable: false,
                oldClrType: typeof(string),
                oldType: "text");

            migrationBuilder.AddColumn<int>(
                name: "FailedLoginCount",
                table: "Users",
                type: "integer",
                nullable: false,
                defaultValue: 0);

            migrationBuilder.AddColumn<DateTime>(
                name: "LastLoginAt",
                table: "Users",
                type: "timestamp with time zone",
                nullable: true);

            migrationBuilder.AddColumn<DateTime>(
                name: "LockoutEnd",
                table: "Users",
                type: "timestamp with time zone",
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "NormalizedEmail",
                table: "Users",
                type: "character varying(320)",
                maxLength: 320,
                nullable: true);

            migrationBuilder.Sql(
                """
                UPDATE "Users"
                SET "NormalizedEmail" = upper(trim("Email"));

                DO $$
                BEGIN
                    IF EXISTS (
                        SELECT "NormalizedEmail"
                        FROM "Users"
                        GROUP BY "NormalizedEmail"
                        HAVING count(*) > 1
                    ) THEN
                        RAISE EXCEPTION 'Cannot enforce unique normalized email: duplicate user emails exist.';
                    END IF;
                END $$;
                """);

            migrationBuilder.AlterColumn<string>(
                name: "NormalizedEmail",
                table: "Users",
                type: "character varying(320)",
                maxLength: 320,
                nullable: false,
                oldClrType: typeof(string),
                oldType: "character varying(320)",
                oldMaxLength: 320,
                oldNullable: true);

            migrationBuilder.AddColumn<Guid>(
                name: "TenantId",
                table: "Stores",
                type: "uuid",
                nullable: true);

            migrationBuilder.Sql(
                """
                UPDATE "Stores" AS s
                SET "TenantId" = (
                    SELECT t."Id"
                    FROM "Tenants" AS t
                    WHERE s."Domain" IS NOT NULL
                      AND lower(t."Domain") = lower(s."Domain")
                    LIMIT 1
                )
                WHERE s."TenantId" IS NULL
                  AND s."Domain" IS NOT NULL
                  AND (
                      SELECT count(*) FROM "Tenants" AS t
                      WHERE lower(t."Domain") = lower(s."Domain")
                  ) = 1;

                UPDATE "Stores" AS s
                SET "TenantId" = (
                    SELECT t."Id"
                    FROM "Tenants" AS t
                    WHERE lower(t."Name") = lower(s."Name")
                      AND lower(t."Platform") = lower(s."Platform")
                    LIMIT 1
                )
                WHERE s."TenantId" IS NULL
                  AND (
                      SELECT count(*) FROM "Tenants" AS t
                      WHERE lower(t."Name") = lower(s."Name")
                        AND lower(t."Platform") = lower(s."Platform")
                  ) = 1;

                DO $$
                BEGIN
                    IF EXISTS (SELECT 1 FROM "Stores" WHERE "TenantId" IS NULL) THEN
                        RAISE EXCEPTION 'Store-to-tenant mapping is ambiguous; map existing Stores before applying this migration.';
                    END IF;
                    IF EXISTS (
                        SELECT "TenantId" FROM "Stores"
                        GROUP BY "TenantId" HAVING count(*) > 1
                    ) THEN
                        RAISE EXCEPTION 'A tenant is mapped to more than one Store.';
                    END IF;
                END $$;
                """);

            migrationBuilder.AlterColumn<Guid>(
                name: "TenantId",
                table: "Stores",
                type: "uuid",
                nullable: false,
                oldClrType: typeof(Guid),
                oldType: "uuid",
                oldNullable: true);

            migrationBuilder.AddColumn<Guid>(
                name: "TenantId",
                table: "RenderResults",
                type: "uuid",
                nullable: true);

            migrationBuilder.Sql(
                """
                UPDATE "RenderResults" AS rr
                SET "TenantId" = rj."TenantId"
                FROM "RenderJobs" AS rj
                WHERE rr."RenderJobId" = rj."Id";
                """);

            migrationBuilder.AlterColumn<Guid>(
                name: "TenantId",
                table: "RenderResults",
                type: "uuid",
                nullable: false,
                oldClrType: typeof(Guid),
                oldType: "uuid",
                oldNullable: true);

            migrationBuilder.AddColumn<DateTime>(
                name: "ApiKeyCreatedAt",
                table: "MerchantAdminSettings",
                type: "timestamp with time zone",
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "ApiKeyHash",
                table: "MerchantAdminSettings",
                type: "character varying(64)",
                maxLength: 64,
                nullable: false,
                defaultValue: "");

            migrationBuilder.AddColumn<string>(
                name: "ApiKeyLastFour",
                table: "MerchantAdminSettings",
                type: "character varying(4)",
                maxLength: 4,
                nullable: false,
                defaultValue: "");

            migrationBuilder.AddColumn<string>(
                name: "ApiKeyPrefix",
                table: "MerchantAdminSettings",
                type: "character varying(32)",
                maxLength: 32,
                nullable: false,
                defaultValue: "");

            migrationBuilder.AddColumn<string>(
                name: "ApiKeyScopes",
                table: "MerchantAdminSettings",
                type: "character varying(256)",
                maxLength: 256,
                nullable: false,
                defaultValue: "");

            migrationBuilder.AddColumn<Guid>(
                name: "TenantId",
                table: "AssetVersions",
                type: "uuid",
                nullable: true);

            migrationBuilder.Sql(
                """
                UPDATE "AssetVersions" AS av
                SET "TenantId" = ga."TenantId"
                FROM "GarmentAssets" AS ga
                WHERE av."GarmentAssetId" = ga."Id";
                """);

            migrationBuilder.AlterColumn<Guid>(
                name: "TenantId",
                table: "AssetVersions",
                type: "uuid",
                nullable: false,
                oldClrType: typeof(Guid),
                oldType: "uuid",
                oldNullable: true);

            migrationBuilder.Sql(
                """
                INSERT INTO "AccountUserMemberships"
                    ("Id", "AccountId", "UserId", "Role", "Status", "CreatedAt")
                SELECT gen_random_uuid(), s."AccountId", u."Id", 'merchant_admin', 'active', now()
                FROM "Users" AS u
                JOIN "Stores" AS s ON s."TenantId" = u."TenantId"
                WHERE u."Role" = 'merchant_admin'
                ON CONFLICT ("AccountId", "UserId") DO NOTHING;
                """);

            migrationBuilder.AddUniqueConstraint(
                name: "AK_RenderJobs_TenantId_Id",
                table: "RenderJobs",
                columns: new[] { "TenantId", "Id" });

            migrationBuilder.AddUniqueConstraint(
                name: "AK_Garments_TenantId_Id",
                table: "Garments",
                columns: new[] { "TenantId", "Id" });

            migrationBuilder.AddUniqueConstraint(
                name: "AK_GarmentAssets_TenantId_Id",
                table: "GarmentAssets",
                columns: new[] { "TenantId", "Id" });

            migrationBuilder.AddUniqueConstraint(
                name: "AK_AssetVersions_TenantId_Id",
                table: "AssetVersions",
                columns: new[] { "TenantId", "Id" });

            migrationBuilder.CreateTable(
                name: "UserInvitations",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    TokenHash = table.Column<string>(type: "character varying(64)", maxLength: 64, nullable: false),
                    Email = table.Column<string>(type: "character varying(320)", maxLength: 320, nullable: false),
                    NormalizedEmail = table.Column<string>(type: "character varying(320)", maxLength: 320, nullable: false),
                    Role = table.Column<string>(type: "character varying(64)", maxLength: 64, nullable: false),
                    TenantId = table.Column<Guid>(type: "uuid", nullable: false),
                    CreatedByUserId = table.Column<Guid>(type: "uuid", nullable: false),
                    ExpiresAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    AcceptedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_UserInvitations", x => x.Id);
                    table.ForeignKey(
                        name: "FK_UserInvitations_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_UserInvitations_Users_CreatedByUserId",
                        column: x => x.CreatedByUserId,
                        principalTable: "Users",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                });

            migrationBuilder.CreateIndex(
                name: "IX_Users_NormalizedEmail",
                table: "Users",
                column: "NormalizedEmail",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_Stores_TenantId",
                table: "Stores",
                column: "TenantId",
                unique: true);

            migrationBuilder.CreateIndex(
                name: "IX_RenderResults_TenantId_RenderJobId",
                table: "RenderResults",
                columns: new[] { "TenantId", "RenderJobId" });

            migrationBuilder.CreateIndex(
                name: "IX_RenderJobs_TenantId_AssetVersionId",
                table: "RenderJobs",
                columns: new[] { "TenantId", "AssetVersionId" });

            migrationBuilder.CreateIndex(
                name: "IX_RenderJobs_TenantId_GarmentAssetId",
                table: "RenderJobs",
                columns: new[] { "TenantId", "GarmentAssetId" });

            migrationBuilder.CreateIndex(
                name: "IX_AssetVersions_TenantId_GarmentAssetId",
                table: "AssetVersions",
                columns: new[] { "TenantId", "GarmentAssetId" });

            migrationBuilder.CreateIndex(
                name: "IX_UserInvitations_CreatedByUserId",
                table: "UserInvitations",
                column: "CreatedByUserId");

            migrationBuilder.CreateIndex(
                name: "IX_UserInvitations_NormalizedEmail_AcceptedAt_ExpiresAt",
                table: "UserInvitations",
                columns: new[] { "NormalizedEmail", "AcceptedAt", "ExpiresAt" });

            migrationBuilder.CreateIndex(
                name: "IX_UserInvitations_TenantId",
                table: "UserInvitations",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_UserInvitations_TokenHash",
                table: "UserInvitations",
                column: "TokenHash",
                unique: true);

            migrationBuilder.AddForeignKey(
                name: "FK_AssetVersions_GarmentAssets_TenantId_GarmentAssetId",
                table: "AssetVersions",
                columns: new[] { "TenantId", "GarmentAssetId" },
                principalTable: "GarmentAssets",
                principalColumns: new[] { "TenantId", "Id" },
                onDelete: ReferentialAction.Restrict);

            migrationBuilder.AddForeignKey(
                name: "FK_GarmentAssets_Garments_TenantId_GarmentId",
                table: "GarmentAssets",
                columns: new[] { "TenantId", "GarmentId" },
                principalTable: "Garments",
                principalColumns: new[] { "TenantId", "Id" },
                onDelete: ReferentialAction.Restrict);

            migrationBuilder.AddForeignKey(
                name: "FK_RenderJobs_AssetVersions_TenantId_AssetVersionId",
                table: "RenderJobs",
                columns: new[] { "TenantId", "AssetVersionId" },
                principalTable: "AssetVersions",
                principalColumns: new[] { "TenantId", "Id" },
                onDelete: ReferentialAction.Restrict);

            migrationBuilder.AddForeignKey(
                name: "FK_RenderJobs_GarmentAssets_TenantId_GarmentAssetId",
                table: "RenderJobs",
                columns: new[] { "TenantId", "GarmentAssetId" },
                principalTable: "GarmentAssets",
                principalColumns: new[] { "TenantId", "Id" },
                onDelete: ReferentialAction.Restrict);

            migrationBuilder.AddForeignKey(
                name: "FK_RenderResults_RenderJobs_TenantId_RenderJobId",
                table: "RenderResults",
                columns: new[] { "TenantId", "RenderJobId" },
                principalTable: "RenderJobs",
                principalColumns: new[] { "TenantId", "Id" },
                onDelete: ReferentialAction.Restrict);

            migrationBuilder.AddForeignKey(
                name: "FK_Stores_Tenants_TenantId",
                table: "Stores",
                column: "TenantId",
                principalTable: "Tenants",
                principalColumn: "Id",
                onDelete: ReferentialAction.Restrict);

            migrationBuilder.Sql(
                """
                DO $$
                DECLARE
                    table_name text;
                BEGIN
                    FOREACH table_name IN ARRAY ARRAY[
                        'MerchantAdminSettings', 'Garments', 'GarmentAssets', 'AssetVersions',
                        'IngestionJobs', 'RenderJobs', 'RenderResults', 'Avatars',
                        'CosmeticProducts', 'UserLooks', 'Challenges'
                    ]
                    LOOP
                        EXECUTE format('ALTER TABLE %I ENABLE ROW LEVEL SECURITY', table_name);
                        EXECUTE format('DROP POLICY IF EXISTS tenant_isolation ON %I', table_name);
                        EXECUTE format(
                            'CREATE POLICY tenant_isolation ON %I USING (' ||
                            'current_setting(''app.is_worker'', true) = ''true'' OR ' ||
                            'current_setting(''app.is_platform'', true) = ''true'' OR ' ||
                            '"TenantId"::text = nullif(current_setting(''app.tenant_id'', true), '''')' ||
                            ') WITH CHECK (' ||
                            'current_setting(''app.is_worker'', true) = ''true'' OR ' ||
                            'current_setting(''app.is_platform'', true) = ''true'' OR ' ||
                            '"TenantId"::text = nullif(current_setting(''app.tenant_id'', true), '''')' ||
                            ')',
                            table_name);
                    END LOOP;
                END $$;
                """);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql(
                """
                DO $$
                DECLARE
                    table_name text;
                BEGIN
                    FOREACH table_name IN ARRAY ARRAY[
                        'MerchantAdminSettings', 'Garments', 'GarmentAssets', 'AssetVersions',
                        'IngestionJobs', 'RenderJobs', 'RenderResults', 'Avatars',
                        'CosmeticProducts', 'UserLooks', 'Challenges'
                    ]
                    LOOP
                        EXECUTE format('DROP POLICY IF EXISTS tenant_isolation ON %I', table_name);
                        EXECUTE format('ALTER TABLE %I DISABLE ROW LEVEL SECURITY', table_name);
                    END LOOP;
                END $$;
                """);

            migrationBuilder.DropForeignKey(
                name: "FK_AssetVersions_GarmentAssets_TenantId_GarmentAssetId",
                table: "AssetVersions");

            migrationBuilder.DropForeignKey(
                name: "FK_GarmentAssets_Garments_TenantId_GarmentId",
                table: "GarmentAssets");

            migrationBuilder.DropForeignKey(
                name: "FK_RenderJobs_AssetVersions_TenantId_AssetVersionId",
                table: "RenderJobs");

            migrationBuilder.DropForeignKey(
                name: "FK_RenderJobs_GarmentAssets_TenantId_GarmentAssetId",
                table: "RenderJobs");

            migrationBuilder.DropForeignKey(
                name: "FK_RenderResults_RenderJobs_TenantId_RenderJobId",
                table: "RenderResults");

            migrationBuilder.DropForeignKey(
                name: "FK_Stores_Tenants_TenantId",
                table: "Stores");

            migrationBuilder.DropTable(
                name: "UserInvitations");

            migrationBuilder.DropIndex(
                name: "IX_Users_NormalizedEmail",
                table: "Users");

            migrationBuilder.DropIndex(
                name: "IX_Stores_TenantId",
                table: "Stores");

            migrationBuilder.DropIndex(
                name: "IX_RenderResults_TenantId_RenderJobId",
                table: "RenderResults");

            migrationBuilder.DropUniqueConstraint(
                name: "AK_RenderJobs_TenantId_Id",
                table: "RenderJobs");

            migrationBuilder.DropIndex(
                name: "IX_RenderJobs_TenantId_AssetVersionId",
                table: "RenderJobs");

            migrationBuilder.DropIndex(
                name: "IX_RenderJobs_TenantId_GarmentAssetId",
                table: "RenderJobs");

            migrationBuilder.DropUniqueConstraint(
                name: "AK_Garments_TenantId_Id",
                table: "Garments");

            migrationBuilder.DropUniqueConstraint(
                name: "AK_GarmentAssets_TenantId_Id",
                table: "GarmentAssets");

            migrationBuilder.DropUniqueConstraint(
                name: "AK_AssetVersions_TenantId_Id",
                table: "AssetVersions");

            migrationBuilder.DropIndex(
                name: "IX_AssetVersions_TenantId_GarmentAssetId",
                table: "AssetVersions");

            migrationBuilder.DropColumn(
                name: "FailedLoginCount",
                table: "Users");

            migrationBuilder.DropColumn(
                name: "LastLoginAt",
                table: "Users");

            migrationBuilder.DropColumn(
                name: "LockoutEnd",
                table: "Users");

            migrationBuilder.DropColumn(
                name: "NormalizedEmail",
                table: "Users");

            migrationBuilder.DropColumn(
                name: "TenantId",
                table: "Stores");

            migrationBuilder.DropColumn(
                name: "TenantId",
                table: "RenderResults");

            migrationBuilder.DropColumn(
                name: "ApiKeyCreatedAt",
                table: "MerchantAdminSettings");

            migrationBuilder.DropColumn(
                name: "ApiKeyHash",
                table: "MerchantAdminSettings");

            migrationBuilder.DropColumn(
                name: "ApiKeyLastFour",
                table: "MerchantAdminSettings");

            migrationBuilder.DropColumn(
                name: "ApiKeyPrefix",
                table: "MerchantAdminSettings");

            migrationBuilder.DropColumn(
                name: "ApiKeyScopes",
                table: "MerchantAdminSettings");

            migrationBuilder.DropColumn(
                name: "TenantId",
                table: "AssetVersions");

            migrationBuilder.AlterColumn<string>(
                name: "Role",
                table: "Users",
                type: "text",
                nullable: false,
                oldClrType: typeof(string),
                oldType: "character varying(64)",
                oldMaxLength: 64);

            migrationBuilder.AlterColumn<string>(
                name: "PasswordHash",
                table: "Users",
                type: "text",
                nullable: false,
                oldClrType: typeof(string),
                oldType: "character varying(1024)",
                oldMaxLength: 1024);

            migrationBuilder.AlterColumn<string>(
                name: "Email",
                table: "Users",
                type: "text",
                nullable: false,
                oldClrType: typeof(string),
                oldType: "character varying(320)",
                oldMaxLength: 320);

            migrationBuilder.AddColumn<string>(
                name: "ApiKey",
                table: "MerchantAdminSettings",
                type: "text",
                nullable: false,
                defaultValue: "");

            migrationBuilder.CreateIndex(
                name: "IX_RenderJobs_AssetVersionId",
                table: "RenderJobs",
                column: "AssetVersionId");

            migrationBuilder.CreateIndex(
                name: "IX_RenderJobs_GarmentAssetId",
                table: "RenderJobs",
                column: "GarmentAssetId");

            migrationBuilder.CreateIndex(
                name: "IX_GarmentAssets_GarmentId",
                table: "GarmentAssets",
                column: "GarmentId");

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
    }
}
