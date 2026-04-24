using Microsoft.EntityFrameworkCore.Migrations;
using Microsoft.EntityFrameworkCore.Infrastructure;

#nullable disable

namespace Tavaura.Api.Data.Migrations
{
    /// <inheritdoc />
    [DbContext(typeof(TavauraDbContext))]
    [Migration("20260415114500_NormalizePipelineStatusConstraints")]
    public partial class NormalizePipelineStatusConstraints : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.Sql(
                """
                UPDATE "IngestionJobs"
                SET "Status" = 'needs_review'
                WHERE "Status" NOT IN ('pending', 'processing', 'completed', 'failed', 'needs_review');
                """);

            migrationBuilder.Sql(
                """
                UPDATE "RenderJobs"
                SET "Status" = 'needs_review'
                WHERE "Status" NOT IN ('pending', 'processing', 'completed', 'failed', 'needs_review');
                """);

            migrationBuilder.DropCheckConstraint(
                name: "CK_IngestionJobs_Status",
                table: "IngestionJobs");

            migrationBuilder.DropCheckConstraint(
                name: "CK_RenderJobs_Status",
                table: "RenderJobs");

            migrationBuilder.AddCheckConstraint(
                name: "CK_IngestionJobs_Status",
                table: "IngestionJobs",
                sql: "\"Status\" IN ('pending', 'processing', 'completed', 'failed', 'needs_review')");

            migrationBuilder.AddCheckConstraint(
                name: "CK_RenderJobs_Status",
                table: "RenderJobs",
                sql: "\"Status\" IN ('pending', 'processing', 'completed', 'failed', 'needs_review')");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropCheckConstraint(
                name: "CK_IngestionJobs_Status",
                table: "IngestionJobs");

            migrationBuilder.DropCheckConstraint(
                name: "CK_RenderJobs_Status",
                table: "RenderJobs");

            migrationBuilder.AddCheckConstraint(
                name: "CK_IngestionJobs_Status",
                table: "IngestionJobs",
                sql: "\"Status\" IN ('pending', 'processing', 'completed', 'failed', 'needs_review')");

            migrationBuilder.AddCheckConstraint(
                name: "CK_RenderJobs_Status",
                table: "RenderJobs",
                sql: "\"Status\" IN ('pending', 'processing', 'completed', 'failed', 'needs_review')");
        }
    }
}
