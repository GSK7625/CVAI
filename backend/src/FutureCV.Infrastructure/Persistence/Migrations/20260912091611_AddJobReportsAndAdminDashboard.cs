using System;
using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace FutureCV.Infrastructure.Persistence.Migrations
{
    /// <inheritdoc />
    public partial class AddJobReportsAndAdminDashboard : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.AddColumn<DateTimeOffset>(
                name: "BannedAt",
                table: "Jobs",
                type: "timestamp with time zone",
                nullable: true);

            migrationBuilder.AddColumn<Guid>(
                name: "BannedByAdminId",
                table: "Jobs",
                type: "uuid",
                nullable: true);

            migrationBuilder.AddColumn<string>(
                name: "BannedReason",
                table: "Jobs",
                type: "text",
                nullable: true);

            migrationBuilder.AddColumn<bool>(
                name: "IsBanned",
                table: "Jobs",
                type: "boolean",
                nullable: false,
                defaultValue: false);

            migrationBuilder.AddColumn<bool>(
                name: "IsDeleted",
                table: "Employers",
                type: "boolean",
                nullable: false,
                defaultValue: false);

            migrationBuilder.AddColumn<bool>(
                name: "IsDeleted",
                table: "Companies",
                type: "boolean",
                nullable: false,
                defaultValue: false);

            migrationBuilder.CreateTable(
                name: "JobReports",
                columns: table => new
                {
                    Id = table.Column<Guid>(type: "uuid", nullable: false),
                    JobId = table.Column<Guid>(type: "uuid", nullable: false),
                    ReporterUserId = table.Column<Guid>(type: "uuid", nullable: false),
                    Reason = table.Column<string>(type: "character varying(100)", maxLength: 100, nullable: false),
                    Details = table.Column<string>(type: "character varying(2000)", maxLength: 2000, nullable: true),
                    Status = table.Column<string>(type: "character varying(20)", maxLength: 20, nullable: false, defaultValue: "Pending"),
                    ResolvedByAdminId = table.Column<Guid>(type: "uuid", nullable: true),
                    ResolvedAt = table.Column<DateTimeOffset>(type: "timestamp with time zone", nullable: true),
                    AdminNote = table.Column<string>(type: "character varying(2000)", maxLength: 2000, nullable: true),
                    IsDeleted = table.Column<bool>(type: "boolean", nullable: false, defaultValue: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    UpdatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_JobReports", x => x.Id);
                    table.ForeignKey(
                        name: "FK_JobReports_AspNetUsers_ReporterUserId",
                        column: x => x.ReporterUserId,
                        principalTable: "AspNetUsers",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Restrict);
                    table.ForeignKey(
                        name: "FK_JobReports_AspNetUsers_ResolvedByAdminId",
                        column: x => x.ResolvedByAdminId,
                        principalTable: "AspNetUsers",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.SetNull);
                    table.ForeignKey(
                        name: "FK_JobReports_Jobs_JobId",
                        column: x => x.JobId,
                        principalTable: "Jobs",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateIndex(
                name: "IX_Jobs_BannedByAdminId",
                table: "Jobs",
                column: "BannedByAdminId");

            migrationBuilder.CreateIndex(
                name: "IX_JobReports_JobId",
                table: "JobReports",
                column: "JobId");

            migrationBuilder.CreateIndex(
                name: "IX_JobReports_ReporterUserId",
                table: "JobReports",
                column: "ReporterUserId");

            migrationBuilder.CreateIndex(
                name: "IX_JobReports_ResolvedByAdminId",
                table: "JobReports",
                column: "ResolvedByAdminId");

            migrationBuilder.CreateIndex(
                name: "IX_JobReports_Status",
                table: "JobReports",
                column: "Status");

            migrationBuilder.AddForeignKey(
                name: "FK_Jobs_AspNetUsers_BannedByAdminId",
                table: "Jobs",
                column: "BannedByAdminId",
                principalTable: "AspNetUsers",
                principalColumn: "Id",
                onDelete: ReferentialAction.SetNull);
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropForeignKey(
                name: "FK_Jobs_AspNetUsers_BannedByAdminId",
                table: "Jobs");

            migrationBuilder.DropTable(
                name: "JobReports");

            migrationBuilder.DropIndex(
                name: "IX_Jobs_BannedByAdminId",
                table: "Jobs");

            migrationBuilder.DropColumn(
                name: "BannedAt",
                table: "Jobs");

            migrationBuilder.DropColumn(
                name: "BannedByAdminId",
                table: "Jobs");

            migrationBuilder.DropColumn(
                name: "BannedReason",
                table: "Jobs");

            migrationBuilder.DropColumn(
                name: "IsBanned",
                table: "Jobs");

            migrationBuilder.DropColumn(
                name: "IsDeleted",
                table: "Employers");

            migrationBuilder.DropColumn(
                name: "IsDeleted",
                table: "Companies");
        }
    }
}
