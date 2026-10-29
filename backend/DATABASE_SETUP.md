# Backend Configuration Guide

## Database Setup

### Option 1: SQL Server LocalDB (Recommended for Windows Development)
LocalDB is already configured in `appsettings.Development.json`:
```json
"DefaultConnection": "Server=(localdb)\\mssqllocaldb;Database=FutureCV;Trusted_Connection=true;..."
```

**Setup LocalDB:**
1. Verify LocalDB is installed: `sqllocaldb info`
2. If not installed, download SQL Server Express with LocalDB
3. Run migrations:
   ```powershell
   cd backend/src/FutureCV.Api
   dotnet ef database update
   ```

### Option 2: SQL Server Express
Update connection string in `appsettings.Development.json`:
```json
"DefaultConnection": "Server=localhost\\SQLEXPRESS;Database=FutureCV;Trusted_Connection=true;TrustServerCertificate=true"
```

### Option 3: PostgreSQL
1. Install PostgreSQL
2. Update connection string:
```json
"DefaultConnection": "Host=localhost;Port=5432;Database=FutureCV;Username=postgres;Password=yourpassword"
```
3. Change provider in `FutureCV.Infrastructure.csproj` to `Npgsql.EntityFrameworkCore.PostgreSQL`

### Option 4: SQLite (Simplest for Quick Start)
1. Update connection string:
```json
"DefaultConnection": "Data Source=futurecv.db"
```
2. Change provider in `DependencyInjection.cs` to `UseSqlite`

## JWT Secret Key
**⚠️ IMPORTANT**: Change the JWT SecretKey in production!
```json
"JwtSettings": {
  "SecretKey": "CHANGE-THIS-IN-PRODUCTION-min-32-chars",
  ...
}
```

## Email Configuration (Optional)
For forgot password feature, configure SMTP:
```json
"EmailSettings": {
  "SmtpServer": "smtp.gmail.com",
  "SmtpPort": 587,
  "SenderEmail": "your-email@gmail.com",
  "Username": "your-email@gmail.com",
  "Password": "your-app-password"
}
```

**Gmail App Password:**
1. Enable 2FA on your Google account
2. Go to Security > App passwords
3. Generate password for "Mail"

## Google OAuth (Optional)
1. Create project at https://console.cloud.google.com
2. Enable Google+ API
3. Create OAuth 2.0 credentials
4. Update `appsettings.Development.json`:
```json
"GoogleAuth": {
  "ClientId": "your-client-id.apps.googleusercontent.com"
}
```

## File Upload
Default settings:
- Max size: 5MB
- Allowed: PDF, DOC, DOCX
- Path: `wwwroot/uploads`

Create upload directory:
```powershell
mkdir backend/src/FutureCV.Api/wwwroot/uploads
```

## CORS
Frontend URLs are already configured:
- http://localhost:5173 (Vite default)
- http://localhost:3000

## Quick Start

1. **Choose database option** (recommend LocalDB for Windows)
2. **Run migrations:**
   ```powershell
   cd backend/src/FutureCV.Api
   dotnet ef database update
   ```
3. **Start backend:**
   ```powershell
   dotnet run
   ```
4. **API will run on:** http://localhost:5000

## Troubleshooting

### "Connection string not found"
- Make sure `appsettings.Development.json` exists
- Check ASPNETCORE_ENVIRONMENT is set to "Development"

### "SQL Server not found"
- Install SQL Server LocalDB or Express
- Or switch to SQLite (easiest option)

### Database migration errors
```powershell
# Reset database
dotnet ef database drop
dotnet ef database update
```
