using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace FutureCV.Infrastructure.Persistence.Migrations
{
    /// <inheritdoc />
    public partial class AddCvEvaluationsAndStructuredData : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "CVEvaluations",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    CvId = table.Column<Guid>(type: "uuid", nullable: false),
                    CvScore = table.Column<int>(type: "integer", nullable: true),
                    StrengthsJson = table.Column<string>(type: "jsonb", nullable: true),
                    WeaknessesJson = table.Column<string>(type: "jsonb", nullable: true),
                    ImprovementsJson = table.Column<string>(type: "jsonb", nullable: true),
                    MissingSkillsJson = table.Column<string>(type: "jsonb", nullable: true),
                    ModelVersion = table.Column<string>(type: "character varying(50)", maxLength: 50, nullable: false),
                    GeneratedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_CVEvaluations", x => x.Id);
                    table.ForeignKey(
                        name: "FK_CVEvaluations_CVs_CvId",
                        column: x => x.CvId,
                        principalTable: "CVs",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateIndex(
                name: "IX_CVEvaluations_CvId",
                table: "CVEvaluations",
                column: "CvId",
                unique: true);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "CVEvaluations");
        }
    }
}
