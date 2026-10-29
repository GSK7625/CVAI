# 🚀 FutureCV Backend (.NET 8 Clean Architecture)

Tài liệu hướng dẫn cấu trúc, thiết lập và phát triển hệ thống Backend dự án **FutureCV**.

---

## 📐 1. Kiến trúc hệ thống (Clean Architecture)

Mã nguồn Backend được tổ chức theo mô hình **Clean Architecture (Onion Architecture)** giúp tách biệt rõ ràng các tầng trách nhiệm:

```text
backend/
├── FutureCV.sln                  # Solution chính quản lý các sub-projects
├── Directory.Packages.props        # Quản lý tập trung VERSION của các gói NuGet
├── Directory.Build.props           # Cấu hình MSBuild dùng chung (.NET 8, Nullable, Warnings)
├── .editorconfig                   # Quy chuẩn định dạng code C# (File-scoped namespace, style)
│
├── src/
│   ├── FutureCV.Domain/            # [Tầng Core] Chứa Entities, Enums, Value Objects. Không phụ thuộc tầng khác.
│   ├── FutureCV.Application/       # [Tầng Logic] Chứa Use Cases, DTOs, Interfaces (IApplicationDbContext). Chỉ phụ thuộc Domain.
│   ├── FutureCV.Infrastructure/    # [Tầng Hạ tầng] Chứa EF Core, PostgreSQL (Npgsql), Repositories, External Services.
│   └── FutureCV.Api/               # [Tầng API / Entry Point] Controllers, Middleware, Swagger, CORS, DI Composition Root.
│
├── aspire/                         # Cấu hình orchestration (AppHost, ServiceDefaults nếu dùng .NET Aspire)
└── tests/
    └── FutureCV.Domain.Tests/      # Unit tests cho tầng Domain
```

---

## 🛠️ 2. Yêu cầu môi trường (Prerequisites)

* **.NET 8.0 SDK** (phiên bản 8.0 trở lên)
* **PostgreSQL** (phiên bản 15 trở lên)
* **IDE/Editor khuyến nghị**: JetBrains Rider, Visual Studio 2022, hoặc VS Code.

---

## 🚀 3. Hướng dẫn chạy dự án ở máy Local

### **Bước 1: Clone và mở dự án**
Tải mã nguồn về máy và chuyển vào thư mục `backend`:
```bash
cd backend
```

### **Bước 2: Cấu hình Chuỗi kết nối Database**
1. Vào thư mục `src/FutureCV.Api/`.
2. Tạo file `appsettings.Development.json` bằng cách copy nội dung từ file mẫu `appsettings.Development.json.example`:
   ```bash
   cp src/FutureCV.Api/appsettings.Development.json.example src/FutureCV.Api/appsettings.Development.json
   ```
3. Mở file `src/FutureCV.Api/appsettings.Development.json` vừa tạo và điền thông tin tài khoản PostgreSQL ở máy của bạn:
   ```json
   {
     "ConnectionStrings": {
       "DefaultConnection": "Host=localhost;Port=5432;Database=futurecv_db;Username=TÊN_USER_LOCAL;Password=MẬT_KHẨU_LOCAL"
     }
   }
   ```
   > ⚠️ **Lưu ý quan trọng**: File `appsettings.Development.json` đã được cấu hình trong `.gitignore` để **không bao giờ bị push lên GitHub**, tránh lộ mật khẩu cá nhân.

### **Bước 3: Restore & Build dự án**
Mở terminal tại thư mục `backend/` và chạy:
```bash
dotnet restore
dotnet build
```

### **Bước 4: Chạy ứng dụng API**
Chạy ứng dụng bằng lệnh:
```bash
dotnet run --project src/FutureCV.Api
```

### **Bước 5: Truy cập Swagger UI**
Sau khi ứng dụng khởi chạy thành công, truy cập Swagger để kiểm tra và test API tại:
👉 **HTTP**: [http://localhost:5000/swagger](http://localhost:5000/swagger)  
👉 **HTTPS**: [https://localhost:7000/swagger](https://localhost:7000/swagger)

---

## ⚙️ 4. Quy định phát triển dành cho thành viên Team

### 📦 1. Quản lý thư viện NuGet (`Directory.Packages.props`)
* **KHÔNG** ghi đè thuộc tính `Version="x.x.x"` trực tiếp trong file `.csproj` cá nhân của các project.
* Tất cả phiên bản NuGet package phải được khai báo tập trung tại file `Directory.Packages.props` ở thư mục gốc `backend/`.

### ✒️ 2. Quy chuẩn viết Code (`.editorconfig`)
* Sử dụng **File-scoped Namespace** (.NET 6+):
  ```csharp
  namespace FutureCV.Domain.Entities; // ✅ Đúng
  ```
  thay vì namespace dạng khối ngoặc `{ }`.
* Đặt tên Entity kế thừa từ `BaseEntity` (`src/FutureCV.Domain/Common/BaseEntity.cs`).

### 🗄️ 3. Quy trình làm việc với Database (EF Core Migration)
Khi thêm hoặc sửa đổi Entity trong tầng `FutureCV.Domain`:
1. Khai báo `DbSet<YourEntity>` trong `ApplicationDbContext.cs` (`src/FutureCV.Infrastructure/Persistence/`).
2. Tạo Migration mới bằng lệnh:
   ```bash
   dotnet ef migrations add <Tên_Migration> --project src/FutureCV.Infrastructure --startup-project src/FutureCV.Api
   ```
3. Cập nhật Database:
   ```bash
   dotnet ef database update --project src/FutureCV.Infrastructure --startup-project src/FutureCV.Api
   ```
4. Reset / Làm rỗng Database về trạng thái ban đầu:
   - Rollback xóa toàn bộ bảng qua EF Core:
     ```bash
     dotnet ef database update 0 --project src/FutureCV.Infrastructure --startup-project src/FutureCV.Api
     ```
   - Tạo lại toàn bộ bảng rỗng (chạy lại migration):
     ```bash
     dotnet ef database update --project src/FutureCV.Infrastructure --startup-project src/FutureCV.Api
     ```

---

## 🤝 5. Liên hệ & Đóng góp
Nếu gặp khó khăn trong quá trình thiết lập môi trường, hãy liên hệ với trưởng nhóm hoặc tạo issue trên repository dự án.
