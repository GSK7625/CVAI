using FutureCV.Domain.Entities;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace FutureCV.Infrastructure.Persistence.Seeders;

/// <summary>
/// Seeds reference / master data (Job Categories, Levels, Employment Types, Locations, Skills)
/// into the database on application startup if the tables are empty.
/// Idempotent: checks for existence before adding.
/// </summary>
public static class ReferenceDataSeeder
{
    public static async Task SeedAsync(IServiceProvider serviceProvider)
    {
        using var scope = serviceProvider.CreateScope();
        var context = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
        var logger = scope.ServiceProvider.GetService<ILoggerFactory>()?.CreateLogger(nameof(ReferenceDataSeeder));

        try
        {
            await SeedEmploymentTypesAsync(context);
            await SeedJobLevelsAsync(context);
            await SeedJobCategoriesAsync(context);
            await SeedLocationsAsync(context);
            await SeedSkillsAsync(context);

            await context.SaveChangesAsync();
            logger?.LogInformation("Master reference data verified / seeded successfully.");
        }
        catch (Exception ex)
        {
            logger?.LogError(ex, "An error occurred while seeding reference data.");
            throw;
        }
    }

    private static async Task SeedEmploymentTypesAsync(ApplicationDbContext context)
    {
        if (await context.EmploymentTypes.AnyAsync()) return;

        var types = new List<EmploymentType>
        {
            new() { Name = "Toàn thời gian (Full-time)" },
            new() { Name = "Bán thời gian (Part-time)" },
            new() { Name = "Làm việc từ xa (Remote)" },
            new() { Name = "Làm việc kết hợp (Hybrid)" },
            new() { Name = "Thực tập (Internship)" },
            new() { Name = "Thời vụ / Freelance" }
        };

        await context.EmploymentTypes.AddRangeAsync(types);
    }

    private static async Task SeedJobLevelsAsync(ApplicationDbContext context)
    {
        if (await context.JobLevels.AnyAsync()) return;

        var levels = new List<JobLevel>
        {
            new() { Name = "Intern / Thực tập sinh" },
            new() { Name = "Fresher" },
            new() { Name = "Junior" },
            new() { Name = "Middle" },
            new() { Name = "Senior" },
            new() { Name = "Trưởng nhóm (Team Leader)" },
            new() { Name = "Quản lý / Trưởng phòng (Manager)" },
            new() { Name = "Giám đốc / Điều hành (Director / Executive)" }
        };

        await context.JobLevels.AddRangeAsync(levels);
    }

    private static async Task SeedJobCategoriesAsync(ApplicationDbContext context)
    {
        if (await context.JobCategories.AnyAsync()) return;

        var categories = new List<JobCategory>();

        // 1. Công nghệ thông tin
        var it = new JobCategory { Name = "Công nghệ thông tin / Phần mềm" };
        categories.Add(it);
        categories.AddRange(new[]
        {
            new JobCategory { Name = "Lập trình Backend (.NET, Java, Node.js)", Parent = it },
            new JobCategory { Name = "Lập trình Frontend (React, Vue, Angular)", Parent = it },
            new JobCategory { Name = "Lập trình Fullstack", Parent = it },
            new JobCategory { Name = "Lập trình Di động (Mobile App: Flutter, React Native, iOS, Android)", Parent = it },
            new JobCategory { Name = "DevOps / Điện toán đám mây (Cloud / CI/CD)", Parent = it },
            new JobCategory { Name = "Trí tuệ nhân tạo & Học máy (AI / Machine Learning / Data Science)", Parent = it },
            new JobCategory { Name = "Kiểm thử phần mềm (QA / QC / Tester)", Parent = it },
            new JobCategory { Name = "Quản lý dự án & Sản phẩm CNTT (Product / Project Manager / Scrum Master)", Parent = it },
            new JobCategory { Name = "Quản trị cơ sở dữ liệu & Hệ thống (DBA / System Admin)", Parent = it },
            new JobCategory { Name = "An toàn thông tin / An ninh mạng (Cyber Security)", Parent = it }
        });

        // 2. Kinh doanh / Bán hàng
        var sales = new JobCategory { Name = "Kinh doanh / Bán hàng" };
        categories.Add(sales);
        categories.AddRange(new[]
        {
            new JobCategory { Name = "Nhân viên kinh doanh (Sales Executive / B2C)", Parent = sales },
            new JobCategory { Name = "Phát triển kinh doanh (Business Development / B2B)", Parent = sales },
            new JobCategory { Name = "Tư vấn bán hàng / Telesales", Parent = sales },
            new JobCategory { Name = "Quản lý khách hàng doanh nghiệp (Key Account Manager - KAM)", Parent = sales }
        });

        // 3. Marketing / Truyền thông
        var marketing = new JobCategory { Name = "Marketing / Truyền thông / Quảng cáo" };
        categories.Add(marketing);
        categories.AddRange(new[]
        {
            new JobCategory { Name = "Digital Marketing (SEO / SEM / Ads)", Parent = marketing },
            new JobCategory { Name = "Sáng tạo nội dung (Content Creator / Copywriter)", Parent = marketing },
            new JobCategory { Name = "Quản trị thương hiệu (Brand Marketing)", Parent = marketing },
            new JobCategory { Name = "Tổ chức sự kiện & PR (Quan hệ công chúng)", Parent = marketing }
        });

        // 4. Thiết kế / Sáng tạo
        var design = new JobCategory { Name = "Thiết kế / Sáng tạo nghệ thuật" };
        categories.Add(design);
        categories.AddRange(new[]
        {
            new JobCategory { Name = "Thiết kế UI / UX (Giao diện & Trải nghiệm người dùng)", Parent = design },
            new JobCategory { Name = "Thiết kế đồ họa (Graphic Design)", Parent = design },
            new JobCategory { Name = "Dựng video & Hoạt hình (Video Editor / Motion Graphics)", Parent = design },
            new JobCategory { Name = "Thiết kế 3D / Đồ họa Game (3D Artist)", Parent = design }
        });

        // 5. Nhân sự / Hành chính
        var hr = new JobCategory { Name = "Nhân sự / Hành chính / Pháp chế" };
        categories.Add(hr);
        categories.AddRange(new[]
        {
            new JobCategory { Name = "Tuyển dụng nhân tài (Talent Acquisition / Recruitment)", Parent = hr },
            new JobCategory { Name = "Lương & Phúc lợi (C&B Specialist)", Parent = hr },
            new JobCategory { Name = "Hành chính văn phòng (Office Admin)", Parent = hr },
            new JobCategory { Name = "Pháp chế doanh nghiệp (Legal Specialist)", Parent = hr }
        });

        // 6. Tài chính / Kế toán / Ngân hàng
        var finance = new JobCategory { Name = "Tài chính / Kế toán / Ngân hàng" };
        categories.Add(finance);
        categories.AddRange(new[]
        {
            new JobCategory { Name = "Kế toán tổng hợp / Kế toán nội bộ", Parent = finance },
            new JobCategory { Name = "Kế toán thuế", Parent = finance },
            new JobCategory { Name = "Phân tích tài chính (Financial Analyst)", Parent = finance },
            new JobCategory { Name = "Kiểm toán (Auditor)", Parent = finance }
        });

        // 7. Chăm sóc khách hàng / Vận hành
        var cs = new JobCategory { Name = "Chăm sóc khách hàng / Vận hành" };
        categories.Add(cs);
        categories.AddRange(new[]
        {
            new JobCategory { Name = "Chăm sóc khách hàng (Customer Support / Care)", Parent = cs },
            new JobCategory { Name = "Vận hành thương mại điện tử (E-Commerce Operations)", Parent = cs },
            new JobCategory { Name = "Chuỗi cung ứng & Logistics (Supply Chain / Logistics)", Parent = cs }
        });

        await context.JobCategories.AddRangeAsync(categories);
    }

    private static async Task SeedLocationsAsync(ApplicationDbContext context)
    {
        if (await context.Locations.AnyAsync()) return;

        var locations = new List<Location>();

        // Hà Nội
        var hanoi = new Location { Name = "Hà Nội" };
        locations.Add(hanoi);
        locations.AddRange(new[]
        {
            new Location { Name = "Quận Cầu Giấy", Parent = hanoi },
            new Location { Name = "Quận Nam Từ Liêm", Parent = hanoi },
            new Location { Name = "Quận Bắc Từ Liêm", Parent = hanoi },
            new Location { Name = "Quận Ba Đình", Parent = hanoi },
            new Location { Name = "Quận Đống Đa", Parent = hanoi },
            new Location { Name = "Quận Thanh Xuân", Parent = hanoi },
            new Location { Name = "Quận Hai Bà Trưng", Parent = hanoi },
            new Location { Name = "Quận Hoàn Kiếm", Parent = hanoi },
            new Location { Name = "Quận Hà Đông", Parent = hanoi },
            new Location { Name = "Quận Hoàng Mai", Parent = hanoi }
        });

        // TP. Hồ Chí Minh
        var hcm = new Location { Name = "TP. Hồ Chí Minh" };
        locations.Add(hcm);
        locations.AddRange(new[]
        {
            new Location { Name = "Quận 1", Parent = hcm },
            new Location { Name = "Quận 3", Parent = hcm },
            new Location { Name = "Quận 7", Parent = hcm },
            new Location { Name = "Quận Bình Thạnh", Parent = hcm },
            new Location { Name = "Quận Tân Bình", Parent = hcm },
            new Location { Name = "Quận Phú Nhuận", Parent = hcm },
            new Location { Name = "Thành phố Thủ Đức", Parent = hcm },
            new Location { Name = "Quận 10", Parent = hcm }
        });

        // Các tỉnh / thành phố khác
        locations.AddRange(new[]
        {
            new Location { Name = "Đà Nẵng" },
            new Location { Name = "Hải Phòng" },
            new Location { Name = "Cần Thơ" },
            new Location { Name = "Bình Dương" },
            new Location { Name = "Đồng Nai" },
            new Location { Name = "Bắc Ninh" },
            new Location { Name = "Quảng Ninh" },
            new Location { Name = "Khánh Hòa (Nha Trang)" },
            new Location { Name = "Toàn quốc / Làm việc từ xa" }
        });

        await context.Locations.AddRangeAsync(locations);
    }

    private static async Task SeedSkillsAsync(ApplicationDbContext context)
    {
        if (await context.Skills.AnyAsync()) return;

        var skills = new List<Skill>
        {
            // Backend
            new() { Name = "C#", Category = "Backend" },
            new() { Name = ".NET Core / .NET 8", Category = "Backend" },
            new() { Name = "ASP.NET Core Web API", Category = "Backend" },
            new() { Name = "Entity Framework Core", Category = "Backend" },
            new() { Name = "Java", Category = "Backend" },
            new() { Name = "Spring Boot", Category = "Backend" },
            new() { Name = "Node.js", Category = "Backend" },
            new() { Name = "Express.js / NestJS", Category = "Backend" },
            new() { Name = "Python", Category = "Backend" },
            new() { Name = "Django / FastAPI", Category = "Backend" },
            new() { Name = "Golang", Category = "Backend" },
            new() { Name = "PHP / Laravel", Category = "Backend" },

            // Frontend
            new() { Name = "HTML5 / CSS3", Category = "Frontend" },
            new() { Name = "JavaScript (ES6+)", Category = "Frontend" },
            new() { Name = "TypeScript", Category = "Frontend" },
            new() { Name = "ReactJS", Category = "Frontend" },
            new() { Name = "Next.js", Category = "Frontend" },
            new() { Name = "Vue.js", Category = "Frontend" },
            new() { Name = "Angular", Category = "Frontend" },
            new() { Name = "Tailwind CSS", Category = "Frontend" },
            new() { Name = "Redux / Zustand", Category = "Frontend" },

            // Mobile
            new() { Name = "Flutter", Category = "Mobile" },
            new() { Name = "React Native", Category = "Mobile" },
            new() { Name = "Swift (iOS)", Category = "Mobile" },
            new() { Name = "Kotlin (Android)", Category = "Mobile" },

            // Database
            new() { Name = "PostgreSQL", Category = "Database" },
            new() { Name = "Microsoft SQL Server", Category = "Database" },
            new() { Name = "MySQL", Category = "Database" },
            new() { Name = "MongoDB", Category = "Database" },
            new() { Name = "Redis", Category = "Database" },
            new() { Name = "Elasticsearch", Category = "Database" },

            // DevOps & Cloud
            new() { Name = "Git / GitHub / GitLab", Category = "DevOps" },
            new() { Name = "Docker", Category = "DevOps" },
            new() { Name = "Kubernetes", Category = "DevOps" },
            new() { Name = "CI / CD Pipeline", Category = "DevOps" },
            new() { Name = "Amazon Web Services (AWS)", Category = "Cloud" },
            new() { Name = "Microsoft Azure", Category = "Cloud" },
            new() { Name = "Linux / Bash Script", Category = "DevOps" },

            // AI & Data
            new() { Name = "Machine Learning", Category = "AI/Data" },
            new() { Name = "Deep Learning", Category = "AI/Data" },
            new() { Name = "Natural Language Processing (NLP)", Category = "AI/Data" },
            new() { Name = "OpenCV", Category = "AI/Data" },
            new() { Name = "Pandas / NumPy", Category = "AI/Data" },
            new() { Name = "PyTorch / TensorFlow", Category = "AI/Data" },
            new() { Name = "Data Analysis / Power BI", Category = "AI/Data" },

            // Design
            new() { Name = "Figma", Category = "Design" },
            new() { Name = "Adobe Photoshop", Category = "Design" },
            new() { Name = "Adobe Illustrator", Category = "Design" },
            new() { Name = "UI/UX Prototyping", Category = "Design" },

            // Soft skills / Management
            new() { Name = "Tiếng Anh (Giao tiếp tốt)", Category = "Language" },
            new() { Name = "Tiếng Nhật (N3 trở lên)", Category = "Language" },
            new() { Name = "Quản lý dự án (Agile / Scrum)", Category = "Management" },
            new() { Name = "Giao tiếp & Làm việc nhóm", Category = "Soft Skills" },
            new() { Name = "Kỹ năng đàm phán & Thuyết trình", Category = "Soft Skills" },
            new() { Name = "Tư duy giải quyết vấn đề", Category = "Soft Skills" }
        };

        await context.Skills.AddRangeAsync(skills);
    }
}
