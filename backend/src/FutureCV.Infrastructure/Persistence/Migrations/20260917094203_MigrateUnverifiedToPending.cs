using Microsoft.EntityFrameworkCore.Migrations;

#nullable disable

namespace FutureCV.Infrastructure.Persistence.Migrations
{
    /// <inheritdoc />
    public partial class MigrateUnverifiedToPending : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            // Migrate all existing 'Unverified' records to 'Pending'
            // PostgreSQL stores enum as varchar, so we use string comparison
            migrationBuilder.Sql(
                @"UPDATE ""Companies"" 
                  SET ""VerifiedStatus"" = 'Pending' 
                  WHERE ""VerifiedStatus"" = 'Unverified';");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {

        }
    }
}
