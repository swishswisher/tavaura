using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace Tavaura.Api.Data.Migrations
{
    /// <inheritdoc />
    public partial class AddGarmentProcessedImageUrl : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<string>(
                name: "ProcessedImageUrl",
                table: "GarmentAssets",
                type: "text",
                nullable: true);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropColumn(
                name: "ProcessedImageUrl",
                table: "GarmentAssets");
        }
    }
}
