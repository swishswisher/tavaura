using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Tavaura.Api.Data.Migrations
{
    /// <inheritdoc />
    public partial class RequireUserLookTenant : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql(
                """
                UPDATE "UserLooks" AS ul
                SET "TenantId" = a."TenantId"
                FROM "Avatars" AS a
                WHERE ul."AvatarId" = a."Id"
                  AND ul."TenantId" IS NULL;

                UPDATE "UserLooks" AS ul
                SET "TenantId" = u."TenantId"
                FROM "Users" AS u
                WHERE ul."UserId" = u."Id"
                  AND ul."TenantId" IS NULL
                  AND u."TenantId" IS NOT NULL;

                DO $$
                BEGIN
                    IF EXISTS (SELECT 1 FROM "UserLooks" WHERE "TenantId" IS NULL) THEN
                        RAISE EXCEPTION 'Existing user looks must be assigned to a tenant before applying this migration.';
                    END IF;
                    IF EXISTS (
                        SELECT 1
                        FROM "UserLooks" AS ul
                        JOIN "Avatars" AS a ON a."Id" = ul."AvatarId"
                        WHERE ul."TenantId" <> a."TenantId"
                    ) THEN
                        RAISE EXCEPTION 'Cross-tenant user-look/avatar links must be corrected before applying this migration.';
                    END IF;
                END $$;
                """);

            migrationBuilder.AlterColumn<Guid>(
                name: "TenantId",
                table: "UserLooks",
                type: "uuid",
                nullable: false,
                oldClrType: typeof(Guid),
                oldType: "uuid",
                oldNullable: true);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AlterColumn<Guid>(
                name: "TenantId",
                table: "UserLooks",
                type: "uuid",
                nullable: true,
                oldClrType: typeof(Guid),
                oldType: "uuid");
        }
    }
}
