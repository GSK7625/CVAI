using FutureCV.Domain.Entities;
using FutureCV.Domain.Enums;
using FutureCV.Infrastructure.Identity;
using Microsoft.AspNetCore.Identity;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace FutureCV.Infrastructure.Persistence.Seeders;

/// <summary>
/// Seeds realistic demo/presentation data for FutureCV:
/// - Companies: FPT Software (Verified), VNG Corporation (Verified) with public CDN logos
/// - Recruiter user and profile linked to FPT Software
/// - Candidate 1 (Nguyen Van A): Fully populated profile, education, experience, candidate skills
/// - Candidate 2 (Tran Thi B): Fresh candidate account for live submission testing
/// - 10 Jobs across diverse categories, levels, and locations (8 Approved, 2 Pending for Admin demo)
/// - CV, AI evaluation, and JobApplications are left unseeded to allow live presentation uploads
/// Idempotent: checks for existence before adding.
/// </summary>
public static class DemoDataSeeder
{
    public static async Task SeedAsync(IServiceProvider serviceProvider)
    {
        using var scope = serviceProvider.CreateScope();
        var context = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
        var userManager = scope.ServiceProvider.GetRequiredService<UserManager<AppUser>>();
        var logger = scope.ServiceProvider.GetService<ILoggerFactory>()?.CreateLogger(nameof(DemoDataSeeder));

        try
        {
            // Check if demo recruiter already exists to ensure idempotency
            var recruiterEmail = "recruiter@fpt.com";
            if (await userManager.FindByEmailAsync(recruiterEmail) != null)
            {
                return;
            }

            logger?.LogInformation("Seeding demo presentation data...");

            // -----------------------------------------------------------------
            // 1. Seed Companies
            // -----------------------------------------------------------------
            var fptCompany = new Company
            {
                Name = "FPT Software",
                TaxCode = "0101778162",
                LogoUrl = "https://upload.wikimedia.org/wikipedia/commons/thumb/1/11/FPT_logo_2010.svg/1200px-FPT_logo_2010.svg.png",
                Scale = "10000+ nhân viên",
                Industry = "Công nghệ thông tin / Phần mềm",
                WebsiteUrl = "https://fptsoftware.com",
                Address = "Tòa nhà FPT, Phố Duy Tân, Phường Dịch Vọng Hậu, Quận Cầu Giấy, Hà Nội",
                Description = "FPT Software là công ty thành viên thuộc Tập đoàn FPT, nhà cung cấp dịch vụ công nghệ thông tin và chuyển đổi số hàng đầu tại khu vực Châu Á.",
                VerifiedStatus = CompanyVerificationStatus.Verified,
                VerifiedAt = DateTimeOffset.UtcNow
            };

            var vngCompany = new Company
            {
                Name = "VNG Corporation",
                TaxCode = "0303538435",
                LogoUrl = "https://upload.wikimedia.org/wikipedia/vi/thumb/9/91/VNG_Corporation_logo.svg/1200px-VNG_Corporation_logo.svg.png",
                Scale = "1000 - 5000 nhân viên",
                Industry = "Công nghệ thông tin / Game & Internet",
                WebsiteUrl = "https://vng.com.vn",
                Address = "Z06 Đường số 13, Phường Tân Thuận Đông, Quận 7, TP. Hồ Chí Minh",
                Description = "VNG là doanh nghiệp công nghệ hàng đầu Việt Nam với hệ sinh thái sản phẩm phong phú: Zalo, ZaloPay, VNG Games...",
                VerifiedStatus = CompanyVerificationStatus.Verified,
                VerifiedAt = DateTimeOffset.UtcNow
            };

            await context.Companies.AddRangeAsync(fptCompany, vngCompany);
            await context.SaveChangesAsync();

            // -----------------------------------------------------------------
            // 2. Seed Recruiter Account & Employer Profile
            // -----------------------------------------------------------------
            var recruiterUser = new AppUser
            {
                Id = Guid.NewGuid(),
                UserName = recruiterEmail,
                Email = recruiterEmail,
                EmailConfirmed = true,
                CreatedAt = DateTimeOffset.UtcNow,
                UpdatedAt = DateTimeOffset.UtcNow
            };

            var recruiterCreateResult = await userManager.CreateAsync(recruiterUser, "Recruiter@123456");
            if (recruiterCreateResult.Succeeded)
            {
                await userManager.AddToRoleAsync(recruiterUser, "Employer");
            }

            var employerProfile = new Employer
            {
                UserId = recruiterUser.Id,
                FullName = "Lê Thị Tuyển Dụng",
                Position = "Lead Technical Talent Acquisition",
                Phone = "0987654321",
                CompanyId = fptCompany.Id,
                Company = fptCompany
            };

            await context.Employers.AddAsync(employerProfile);
            await context.SaveChangesAsync();

            // -----------------------------------------------------------------
            // 3. Seed Candidate 1 (Nguyễn Văn A - Primary Showcase Profile)
            // -----------------------------------------------------------------
            var cand1Email = "nguyenvana@gmail.com";
            var cand1User = new AppUser
            {
                Id = Guid.NewGuid(),
                UserName = cand1Email,
                Email = cand1Email,
                EmailConfirmed = true,
                CreatedAt = DateTimeOffset.UtcNow,
                UpdatedAt = DateTimeOffset.UtcNow
            };

            var cand1CreateResult = await userManager.CreateAsync(cand1User, "Candidate@123456");
            if (cand1CreateResult.Succeeded)
            {
                await userManager.AddToRoleAsync(cand1User, "Candidate");
            }

            var cand1Profile = new Candidate
            {
                UserId = cand1User.Id,
                FullName = "Nguyễn Văn A",
                Phone = "0912345678",
                Address = "Quận Cầu Giấy, Hà Nội",
                Gender = "Nam",
                DateOfBirth = new DateTime(1998, 5, 20, 0, 0, 0, DateTimeKind.Utc),
                Summary = "Kỹ sư phần mềm với 4+ năm kinh nghiệm phát triển hệ thống backend phân tán bằng .NET Core, C# và PostgreSQL. Có kiến thức vững chắc về Clean Architecture, Microservices, Message Broker và tối ưu hóa hiệu năng cơ sở dữ liệu.",
                DesiredPosition = "Senior .NET Backend Developer",
                DesiredSalaryMin = 25000000,
                DesiredSalaryMax = 42000000,
                ProfileUpdatedAt = DateTimeOffset.UtcNow
            };

            await context.Candidates.AddAsync(cand1Profile);
            await context.SaveChangesAsync();

            // Education & Experience
            var edu = new Education
            {
                CandidateId = cand1Profile.Id,
                School = "Đại học Bách Khoa Hà Nội",
                Degree = "Kỹ sư",
                Major = "Công nghệ Thông tin",
                StartYear = 2016,
                EndYear = 2021,
                Description = "Tốt nghiệp loại Giỏi, chuyên ngành Công nghệ Phần mềm"
            };

            var exp = new Experience
            {
                CandidateId = cand1Profile.Id,
                CompanyName = "Tập đoàn Công nghiệp - Viễn thông Quân đội (Viettel)",
                Position = "Backend Software Engineer",
                StartDate = new DateOnly(2021, 8, 1),
                EndDate = new DateOnly(2024, 6, 30),
                IsCurrent = false,
                Description = "Phát triển và bảo trì các dịch vụ backend microservices bằng .NET 8, PostgreSQL và RabbitMQ phục vụ hàng triệu người dùng. Tối ưu hóa truy vấn SQL và triển khai hệ thống qua Docker CI/CD."
            };

            await context.Educations.AddAsync(edu);
            await context.Experiences.AddAsync(exp);

            // Lookup existing skills from ReferenceDataSeeder
            var csharpSkill = await context.Skills.FirstOrDefaultAsync(s => s.Name == "C#");
            var dotnetSkill = await context.Skills.FirstOrDefaultAsync(s => s.Name.Contains(".NET"));
            var pgSkill = await context.Skills.FirstOrDefaultAsync(s => s.Name == "PostgreSQL");
            var dockerSkill = await context.Skills.FirstOrDefaultAsync(s => s.Name == "Docker");
            var gitSkill = await context.Skills.FirstOrDefaultAsync(s => s.Name.Contains("Git"));
            var awsSkill = await context.Skills.FirstOrDefaultAsync(s => s.Name.Contains("AWS"));
            var reactSkill = await context.Skills.FirstOrDefaultAsync(s => s.Name.Contains("React"));
            var tsSkill = await context.Skills.FirstOrDefaultAsync(s => s.Name.Contains("TypeScript"));

            if (csharpSkill != null)
                await context.CandidateSkills.AddAsync(new CandidateSkill { CandidateId = cand1Profile.Id, SkillId = csharpSkill.Id, Level = SkillLevel.Advanced, Years = 4 });
            if (dotnetSkill != null)
                await context.CandidateSkills.AddAsync(new CandidateSkill { CandidateId = cand1Profile.Id, SkillId = dotnetSkill.Id, Level = SkillLevel.Advanced, Years = 4 });
            if (pgSkill != null)
                await context.CandidateSkills.AddAsync(new CandidateSkill { CandidateId = cand1Profile.Id, SkillId = pgSkill.Id, Level = SkillLevel.Advanced, Years = 4 });
            if (dockerSkill != null)
                await context.CandidateSkills.AddAsync(new CandidateSkill { CandidateId = cand1Profile.Id, SkillId = dockerSkill.Id, Level = SkillLevel.Intermediate, Years = 2 });
            if (gitSkill != null)
                await context.CandidateSkills.AddAsync(new CandidateSkill { CandidateId = cand1Profile.Id, SkillId = gitSkill.Id, Level = SkillLevel.Advanced, Years = 4 });

            await context.SaveChangesAsync();

            // -----------------------------------------------------------------
            // 4. Seed Candidate 2 (Trần Thị B - Fresh account for live demo)
            // -----------------------------------------------------------------
            var cand2Email = "tranthib@gmail.com";
            var cand2User = new AppUser
            {
                Id = Guid.NewGuid(),
                UserName = cand2Email,
                Email = cand2Email,
                EmailConfirmed = true,
                CreatedAt = DateTimeOffset.UtcNow,
                UpdatedAt = DateTimeOffset.UtcNow
            };

            var cand2CreateResult = await userManager.CreateAsync(cand2User, "Candidate@123456");
            if (cand2CreateResult.Succeeded)
            {
                await userManager.AddToRoleAsync(cand2User, "Candidate");
            }

            var cand2Profile = new Candidate
            {
                UserId = cand2User.Id,
                FullName = "Trần Thị B",
                Phone = "0923456789",
                Address = "Quận Đống Đa, Hà Nội",
                Gender = "Nữ",
                DateOfBirth = new DateTime(2002, 11, 10, 0, 0, 0, DateTimeKind.Utc),
                Summary = "Sinh viên mới tốt nghiệp ngành Công nghệ thông tin, đam mê phát triển ứng dụng web hiện đại với .NET và React.",
                DesiredPosition = "Junior Software Developer",
                DesiredSalaryMin = 10000000,
                DesiredSalaryMax = 15000000,
                ProfileUpdatedAt = DateTimeOffset.UtcNow
            };

            await context.Candidates.AddAsync(cand2Profile);
            await context.SaveChangesAsync();

            // -----------------------------------------------------------------
            // 5. Seed 10 Realistic Jobs with Associated Skills
            // -----------------------------------------------------------------
            var backendCategory = await context.JobCategories.FirstOrDefaultAsync(c => c.Name.Contains("Lập trình Backend"))
                ?? await context.JobCategories.FirstOrDefaultAsync(c => c.Name.Contains("Công nghệ thông tin"));
            var frontendCategory = await context.JobCategories.FirstOrDefaultAsync(c => c.Name.Contains("Lập trình Frontend")) ?? backendCategory;
            var fullstackCategory = await context.JobCategories.FirstOrDefaultAsync(c => c.Name.Contains("Lập trình Fullstack")) ?? backendCategory;
            var mobileCategory = await context.JobCategories.FirstOrDefaultAsync(c => c.Name.Contains("Lập trình Di động")) ?? backendCategory;
            var devopsCategory = await context.JobCategories.FirstOrDefaultAsync(c => c.Name.Contains("DevOps")) ?? backendCategory;
            var aiCategory = await context.JobCategories.FirstOrDefaultAsync(c => c.Name.Contains("Trí tuệ nhân tạo")) ?? backendCategory;
            var qaCategory = await context.JobCategories.FirstOrDefaultAsync(c => c.Name.Contains("Kiểm thử")) ?? backendCategory;
            var pmCategory = await context.JobCategories.FirstOrDefaultAsync(c => c.Name.Contains("Quản lý dự án")) ?? backendCategory;
            var designCategory = await context.JobCategories.FirstOrDefaultAsync(c => c.Name.Contains("Thiết kế UI"))
                ?? await context.JobCategories.FirstOrDefaultAsync(c => c.Name.Contains("Thiết kế")) ?? backendCategory;

            var internLevel = await context.JobLevels.FirstOrDefaultAsync(l => l.Name.Contains("Intern"));
            var middleLevel = await context.JobLevels.FirstOrDefaultAsync(l => l.Name.Contains("Middle"));
            var seniorLevel = await context.JobLevels.FirstOrDefaultAsync(l => l.Name.Contains("Senior"));
            var managerLevel = await context.JobLevels.FirstOrDefaultAsync(l => l.Name.Contains("Manager"));

            var fullTime = await context.EmploymentTypes.FirstOrDefaultAsync(t => t.Name.Contains("Full-time"));
            var remote = await context.EmploymentTypes.FirstOrDefaultAsync(t => t.Name.Contains("Remote"));
            var hybrid = await context.EmploymentTypes.FirstOrDefaultAsync(t => t.Name.Contains("Hybrid"));

            var hanoiLoc = await context.Locations.FirstOrDefaultAsync(l => l.Name == "Hà Nội");
            var hcmLoc = await context.Locations.FirstOrDefaultAsync(l => l.Name.Contains("Hồ Chí Minh"));
            var danangLoc = await context.Locations.FirstOrDefaultAsync(l => l.Name.Contains("Đà Nẵng"));
            var remoteLoc = await context.Locations.FirstOrDefaultAsync(l => l.Name.Contains("Toàn quốc") || l.Name.Contains("từ xa")) ?? hanoiLoc;

            // Lookup additional skills for the 10 demo jobs (csharpSkill, dotnetSkill, pgSkill, dockerSkill, gitSkill, awsSkill, reactSkill, tsSkill are already declared above)
            var sqlServerSkill = await context.Skills.FirstOrDefaultAsync(s => s.Name.Contains("SQL Server"));
            var k8sSkill = await context.Skills.FirstOrDefaultAsync(s => s.Name == "Kubernetes");
            var pythonSkill = await context.Skills.FirstOrDefaultAsync(s => s.Name == "Python");
            var golangSkill = await context.Skills.FirstOrDefaultAsync(s => s.Name == "Golang");
            var flutterSkill = await context.Skills.FirstOrDefaultAsync(s => s.Name == "Flutter");
            var reactNativeSkill = await context.Skills.FirstOrDefaultAsync(s => s.Name == "React Native");
            var redisSkill = await context.Skills.FirstOrDefaultAsync(s => s.Name == "Redis");
            var figmaSkill = await context.Skills.FirstOrDefaultAsync(s => s.Name == "Figma");
            var agileSkill = await context.Skills.FirstOrDefaultAsync(s => s.Name.Contains("Agile"));
            var cicdSkill = await context.Skills.FirstOrDefaultAsync(s => s.Name.Contains("CI / CD"));
            var mlSkill = await context.Skills.FirstOrDefaultAsync(s => s.Name.Contains("Machine Learning"));

            // Job 1: Primary Target Job (FPT Software - Senior .NET)
            var job1 = new Job
            {
                CompanyId = fptCompany.Id,
                PostedById = recruiterUser.Id,
                Title = "Senior .NET Backend Developer",
                Description = "FPT Software đang tìm kiếm các kỹ sư Senior .NET Backend tài năng gia nhập đội ngũ phát triển các giải pháp phần mềm chuyển đổi số quy mô lớn cho khách hàng toàn cầu.\n\nTrách nhiệm chính:\n- Tham gia thiết kế, phát triển và bảo trì các hệ thống backend microservices sử dụng .NET 8 / C#.\n- Thiết kế kiến trúc cơ sở dữ liệu quan hệ (PostgreSQL) và tối ưu hóa truy vấn hiệu năng cao.\n- Tích hợp các hệ thống message broker (RabbitMQ/Kafka) và bộ nhớ đệm (Redis).\n- Triển khai ứng dụng containerized qua Docker và phối hợp CI/CD với đội ngũ DevOps.",
                Requirements = "- Tối thiểu 3 - 5 năm kinh nghiệm phát triển phần mềm với .NET Core / .NET 8 và C#.\n- Thành thạo Entity Framework Core, LINQ, và thiết kế RESTful Web API chuẩn RFC.\n- Kinh nghiệm vững chắc với PostgreSQL hoặc các RDBMS khác, hiểu sâu về Indexing và Transaction.\n- Có kinh nghiệm làm việc với Docker và Git.\n- Ưu tiên ứng viên có hiểu biết về Cloud (AWS/Azure) hoặc kiến trúc Microservices.",
                Benefits = "- Thu nhập cạnh tranh từ 25 - 42 triệu/tháng + tháng lương 13 và thưởng dự án.\n- Chế độ bảo hiểm sức khỏe toàn diện FPT Care cho bản thân và gia đình.\n- Môi trường làm việc năng động, hybrid linh hoạt và cơ hội onsite nước ngoài.",
                CategoryId = backendCategory?.Id,
                LevelId = seniorLevel?.Id,
                EmploymentTypeId = fullTime?.Id,
                LocationId = hanoiLoc?.Id,
                SalaryMin = 25000000,
                SalaryMax = 42000000,
                SalaryCurrency = "VND",
                ExperienceYearsMin = 3,
                ExperienceYearsMax = 5,
                Deadline = DateTime.UtcNow.AddMonths(2),
                PositionsCount = 3,
                ApprovalStatus = JobApprovalStatus.Approved,
                IsActive = true,
                IsExpired = false,
                ViewCount = 142
            };

            // Job 2: Frontend React Engineer (VNG Corporation)
            var job2 = new Job
            {
                CompanyId = vngCompany.Id,
                PostedById = recruiterUser.Id,
                Title = "Frontend React / TypeScript Engineer",
                Description = "VNG Corporation tìm kiếm Frontend Engineer tài năng xây dựng giao diện ứng dụng web trải nghiệm mượt mà, phục vụ hàng triệu người dùng.\n\nTrách nhiệm chính:\n- Xây dựng giao diện Single Page Application hiện đại với React, TypeScript và Tailwind CSS.\n- Tối ưu hóa hiệu năng render, Web Vitals và trải nghiệm người dùng responsive.",
                Requirements = "- Tối thiểu 2 năm kinh nghiệm với React, TypeScript và HTML5/CSS3.\n- Sử dụng thành thạo Git và làm việc với RESTful API.",
                Benefits = "- Mức lương 18 - 30 triệu/tháng + thưởng hiệu quả kinh doanh.\n- Ăn trưa miễn phí tại công ty, phòng gym và khu vui chơi giải trí.",
                CategoryId = frontendCategory?.Id,
                LevelId = middleLevel?.Id,
                EmploymentTypeId = fullTime?.Id,
                LocationId = hcmLoc?.Id,
                SalaryMin = 18000000,
                SalaryMax = 30000000,
                SalaryCurrency = "VND",
                ExperienceYearsMin = 2,
                ExperienceYearsMax = 4,
                Deadline = DateTime.UtcNow.AddMonths(1),
                PositionsCount = 2,
                ApprovalStatus = JobApprovalStatus.Approved,
                IsActive = true,
                IsExpired = false,
                ViewCount = 89
            };

            // Job 3: AI Intern (FPT Software - Pending for Admin demo)
            var job3 = new Job
            {
                CompanyId = fptCompany.Id,
                PostedById = recruiterUser.Id,
                Title = "Thực tập sinh Lập trình AI / Machine Learning",
                Description = "Chương trình thực tập sinh tài năng về AI/ML tại FPT Software, cơ hội tiếp cận các dự án GenAI, LLM thực tế.",
                Requirements = "- Sinh viên năm cuối hoặc mới tốt nghiệp chuyên ngành CNTT, Toán tin, Trí tuệ nhân tạo.\n- Có nền tảng Python, hiểu biết về Machine Learning và Deep Learning.",
                Benefits = "- Trợ cấp thực tập hấp dẫn 6 - 8 triệu/tháng.\n- Cơ hội trở thành nhân viên chính thức sau 3 tháng.",
                CategoryId = aiCategory?.Id,
                LevelId = internLevel?.Id,
                EmploymentTypeId = fullTime?.Id,
                LocationId = hanoiLoc?.Id,
                SalaryMin = 6000000,
                SalaryMax = 8000000,
                SalaryCurrency = "VND",
                ExperienceYearsMin = 0,
                ExperienceYearsMax = 1,
                Deadline = DateTime.UtcNow.AddMonths(1),
                PositionsCount = 5,
                ApprovalStatus = JobApprovalStatus.Pending,
                IsActive = true,
                IsExpired = false,
                ViewCount = 12
            };

            // Job 4: Fullstack Developer (FPT Software - Đà Nẵng)
            var job4 = new Job
            {
                CompanyId = fptCompany.Id,
                PostedById = recruiterUser.Id,
                Title = "Fullstack Developer (.NET 8 & React)",
                Description = "Phát triển toàn diện giải pháp Enterprise từ Backend API đến Frontend UI cho đối tác quốc tế tại chi nhánh FPT Đà Nẵng.\n\nTrách nhiệm:\n- Xây dựng Web API bằng C# .NET 8 và giao diện tương tác bằng React.\n- Tối ưu hóa truy vấn dữ liệu và tích hợp hệ thống bên thứ ba.",
                Requirements = "- 2+ năm kinh nghiệm Fullstack với C#, .NET Web API và React/TypeScript.\n- Hiểu biết về cơ sở dữ liệu SQL Server hoặc PostgreSQL.",
                Benefits = "- Lương 20 - 32 triệu/tháng, phụ cấp ngoại ngữ.\n- Môi trường làm việc ven biển Đà Nẵng hiện đại, văn hóa cởi mở.",
                CategoryId = fullstackCategory?.Id,
                LevelId = middleLevel?.Id,
                EmploymentTypeId = fullTime?.Id,
                LocationId = danangLoc?.Id,
                SalaryMin = 20000000,
                SalaryMax = 32000000,
                SalaryCurrency = "VND",
                ExperienceYearsMin = 2,
                ExperienceYearsMax = 4,
                Deadline = DateTime.UtcNow.AddMonths(2),
                PositionsCount = 2,
                ApprovalStatus = JobApprovalStatus.Approved,
                IsActive = true,
                IsExpired = false,
                ViewCount = 65
            };

            // Job 5: Senior Cloud & DevOps Engineer (VNG Corporation - TP. Hồ Chí Minh)
            var job5 = new Job
            {
                CompanyId = vngCompany.Id,
                PostedById = recruiterUser.Id,
                Title = "Senior Cloud & DevOps Engineer (AWS / K8s)",
                Description = "Chịu trách nhiệm thiết kế, triển khai và tự động hóa hạ tầng Cloud quy mô lớn phục vụ hàng chục triệu người dùng của hệ sinh thái VNG.\n\nTrách nhiệm:\n- Vận hành cụm Kubernetes trên AWS Cloud.\n- Xây dựng CI/CD pipeline tự động hóa với GitLab CI/GitHub Actions.",
                Requirements = "- 4+ năm kinh nghiệm vận hành hệ thống với Docker, Kubernetes (K8s) và AWS Cloud.\n- Thành thạo xây dựng CI/CD pipeline tự động hóa và Linux Administration.",
                Benefits = "- Lương 35 - 55 triệu/tháng, ESOP cổ phần công ty.\n- Chế độ làm việc Hybrid linh hoạt, phụ cấp thiết bị làm việc cao cấp.",
                CategoryId = devopsCategory?.Id,
                LevelId = seniorLevel?.Id,
                EmploymentTypeId = hybrid?.Id,
                LocationId = hcmLoc?.Id,
                SalaryMin = 35000000,
                SalaryMax = 55000000,
                SalaryCurrency = "VND",
                ExperienceYearsMin = 4,
                ExperienceYearsMax = 7,
                Deadline = DateTime.UtcNow.AddMonths(2),
                PositionsCount = 2,
                ApprovalStatus = JobApprovalStatus.Approved,
                IsActive = true,
                IsExpired = false,
                ViewCount = 110
            };

            // Job 6: Mobile App Developer (FPT Software - Hà Nội)
            var job6 = new Job
            {
                CompanyId = fptCompany.Id,
                PostedById = recruiterUser.Id,
                Title = "Mobile App Developer (Flutter / React Native)",
                Description = "Tham gia phát triển các ứng dụng di động đa nền tảng hiện đại cho các dự án Fintech và E-Commerce quốc tế.\n\nTrách nhiệm:\n- Xây dựng ứng dụng di động mượt mà cho iOS & Android.\n- Tích hợp RESTful API và tối ưu hóa trải nghiệm người dùng.",
                Requirements = "- 2+ năm kinh nghiệm phát triển ứng dụng di động với Flutter hoặc React Native.\n- Có kiến thức tốt về quản lý State, RESTful API và tối ưu hóa hiệu năng ứng dụng.",
                Benefits = "- Thu nhập 16 - 26 triệu/tháng + thưởng dự án.\n- Được tài trợ học và thi các chứng chỉ chuyên môn quốc tế.",
                CategoryId = mobileCategory?.Id,
                LevelId = middleLevel?.Id,
                EmploymentTypeId = fullTime?.Id,
                LocationId = hanoiLoc?.Id,
                SalaryMin = 16000000,
                SalaryMax = 26000000,
                SalaryCurrency = "VND",
                ExperienceYearsMin = 2,
                ExperienceYearsMax = 4,
                Deadline = DateTime.UtcNow.AddMonths(1),
                PositionsCount = 3,
                ApprovalStatus = JobApprovalStatus.Approved,
                IsActive = true,
                IsExpired = false,
                ViewCount = 74
            };

            // Job 7: Golang Distributed Backend Engineer (VNG Corporation - Remote)
            var job7 = new Job
            {
                CompanyId = vngCompany.Id,
                PostedById = recruiterUser.Id,
                Title = "Golang Backend Engineer (Distributed Systems)",
                Description = "Phát triển hệ thống xử lý thanh toán và tin nhắn thời gian thực độ trễ thấp, chịu tải cao hàng trăm ngàn transactions/giây.\n\nTrách nhiệm:\n- Xây dựng microservices hiệu năng cao với Golang và gRPC.\n- Thiết kế bộ nhớ đệm phân tán với Redis và tối ưu hóa lưu trữ PostgreSQL.",
                Requirements = "- 3+ năm kinh nghiệm phát triển backend với Golang.\n- Hiểu sâu về Concurrency, Memory Management, Redis cache và kiến trúc High Availability.",
                Benefits = "- Mức lương 30 - 50 triệu/tháng thỏa thuận theo năng lực.\n- 100% làm việc từ xa (Remote), thời gian làm việc linh hoạt.",
                CategoryId = backendCategory?.Id,
                LevelId = seniorLevel?.Id,
                EmploymentTypeId = remote?.Id,
                LocationId = remoteLoc?.Id,
                SalaryMin = 30000000,
                SalaryMax = 50000000,
                SalaryCurrency = "VND",
                ExperienceYearsMin = 3,
                ExperienceYearsMax = 6,
                Deadline = DateTime.UtcNow.AddMonths(2),
                PositionsCount = 2,
                ApprovalStatus = JobApprovalStatus.Approved,
                IsActive = true,
                IsExpired = false,
                ViewCount = 98
            };

            // Job 8: UI / UX Product Designer (VNG Corporation - TP. Hồ Chí Minh)
            var job8 = new Job
            {
                CompanyId = vngCompany.Id,
                PostedById = recruiterUser.Id,
                Title = "UI / UX Product Designer",
                Description = "Nghiên cứu hành vi người dùng, xây dựng Design System và thiết kế giao diện cho các sản phẩm số dẫn đầu thị trường.\n\nTrách nhiệm:\n- Thiết kế wireframe, prototype và hoàn thiện UI trên Figma.\n- Phối hợp chặt chẽ với Frontend team để hiện thực hóa giao diện thiết kế.",
                Requirements = "- 2+ năm kinh nghiệm thiết kế UI/UX cho ứng dụng Web và Mobile trên Figma.\n- Có Portfolio dự án thực tế thể hiện tư duy thiết kế lấy người dùng làm trung tâm (User-Centered Design).",
                Benefits = "- Lương 18 - 28 triệu/tháng + thưởng năm hấp dẫn.\n- Môi trường sáng tạo, tài trợ ngân sách tham gia các khóa học chuyên sâu.",
                CategoryId = designCategory?.Id,
                LevelId = middleLevel?.Id,
                EmploymentTypeId = fullTime?.Id,
                LocationId = hcmLoc?.Id,
                SalaryMin = 18000000,
                SalaryMax = 28000000,
                SalaryCurrency = "VND",
                ExperienceYearsMin = 2,
                ExperienceYearsMax = 5,
                Deadline = DateTime.UtcNow.AddMonths(1),
                PositionsCount = 1,
                ApprovalStatus = JobApprovalStatus.Approved,
                IsActive = true,
                IsExpired = false,
                ViewCount = 82
            };

            // Job 9: Automation QA / QC Engineer (FPT Software - Hà Nội)
            var job9 = new Job
            {
                CompanyId = fptCompany.Id,
                PostedById = recruiterUser.Id,
                Title = "Automation QA / QC Engineer (Python / Selenium)",
                Description = "Xây dựng và phát triển framework kiểm thử tự động, tích hợp CI/CD để đảm bảo chất lượng phần mềm liên tục trong các sprint Agile.\n\nTrách nhiệm:\n- Viết test script tự động cho API và Web UI.\n- Theo dõi, phân tích và báo cáo lỗi trên hệ thống quản lý dự án.",
                Requirements = "- 2+ năm kinh nghiệm kiểm thử tự động (Automation Testing) với Python hoặc Java.\n- Kinh nghiệm kiểm thử API, Performance Testing và hiểu biết về CI/CD pipeline.",
                Benefits = "- Lương 15 - 25 triệu/tháng, xét tăng lương định kỳ 2 lần/năm.\n- Cơ hội thăng tiến lên QA Lead và tham gia các dự án lớn đa quốc gia.",
                CategoryId = qaCategory?.Id,
                LevelId = middleLevel?.Id,
                EmploymentTypeId = fullTime?.Id,
                LocationId = hanoiLoc?.Id,
                SalaryMin = 15000000,
                SalaryMax = 25000000,
                SalaryCurrency = "VND",
                ExperienceYearsMin = 2,
                ExperienceYearsMax = 4,
                Deadline = DateTime.UtcNow.AddMonths(1),
                PositionsCount = 2,
                ApprovalStatus = JobApprovalStatus.Approved,
                IsActive = true,
                IsExpired = false,
                ViewCount = 53
            };

            // Job 10: Technical Product Manager (FPT Software - Pending for Admin demo)
            var job10 = new Job
            {
                CompanyId = fptCompany.Id,
                PostedById = recruiterUser.Id,
                Title = "Technical Product Manager (TPM / Scrum Master)",
                Description = "Định hình tầm nhìn sản phẩm, quản lý Product Backlog và dẫn dắt đội ngũ kỹ sư phát triển sản phẩm công nghệ chuyển đổi số thế hệ mới.\n\nTrách nhiệm:\n- Làm việc với các bên liên quan để làm rõ yêu cầu nghiệp vụ và kỹ thuật.\n- Lập kế hoạch release, quản lý tiến độ sprint và tối ưu hóa năng suất nhóm.",
                Requirements = "- 4+ năm kinh nghiệm làm việc trong vai trò Product Owner, TPM hoặc Technical Project Manager.\n- Nền tảng kỹ thuật vững chắc, khả năng kết nối giữa yêu cầu kinh doanh và giải pháp kỹ thuật, tiếng Anh thành thạo.",
                Benefits = "- Mức thu nhập 35 - 55 triệu/tháng tương xứng với năng lực.\n- Thưởng hiệu quả kinh doanh và gói chăm sóc sức khỏe VIP.",
                CategoryId = pmCategory?.Id,
                LevelId = managerLevel?.Id,
                EmploymentTypeId = fullTime?.Id,
                LocationId = hanoiLoc?.Id,
                SalaryMin = 35000000,
                SalaryMax = 55000000,
                SalaryCurrency = "VND",
                ExperienceYearsMin = 4,
                ExperienceYearsMax = 8,
                Deadline = DateTime.UtcNow.AddMonths(2),
                PositionsCount = 1,
                ApprovalStatus = JobApprovalStatus.Pending,
                IsActive = true,
                IsExpired = false,
                ViewCount = 41
            };

            await context.Jobs.AddRangeAsync(job1, job2, job3, job4, job5, job6, job7, job8, job9, job10);
            await context.SaveChangesAsync();

            // Link skills to Job 1 (Senior .NET)
            if (csharpSkill != null) await context.JobSkills.AddAsync(new JobSkill { JobId = job1.Id, SkillId = csharpSkill.Id, IsRequired = true });
            if (dotnetSkill != null) await context.JobSkills.AddAsync(new JobSkill { JobId = job1.Id, SkillId = dotnetSkill.Id, IsRequired = true });
            if (pgSkill != null) await context.JobSkills.AddAsync(new JobSkill { JobId = job1.Id, SkillId = pgSkill.Id, IsRequired = true });
            if (dockerSkill != null) await context.JobSkills.AddAsync(new JobSkill { JobId = job1.Id, SkillId = dockerSkill.Id, IsRequired = true });
            if (awsSkill != null) await context.JobSkills.AddAsync(new JobSkill { JobId = job1.Id, SkillId = awsSkill.Id, IsRequired = false });

            // Link skills to Job 2 (Frontend React)
            if (reactSkill != null) await context.JobSkills.AddAsync(new JobSkill { JobId = job2.Id, SkillId = reactSkill.Id, IsRequired = true });
            if (tsSkill != null) await context.JobSkills.AddAsync(new JobSkill { JobId = job2.Id, SkillId = tsSkill.Id, IsRequired = true });
            if (gitSkill != null) await context.JobSkills.AddAsync(new JobSkill { JobId = job2.Id, SkillId = gitSkill.Id, IsRequired = false });

            // Link skills to Job 3 (AI Intern)
            if (pythonSkill != null) await context.JobSkills.AddAsync(new JobSkill { JobId = job3.Id, SkillId = pythonSkill.Id, IsRequired = true });
            if (mlSkill != null) await context.JobSkills.AddAsync(new JobSkill { JobId = job3.Id, SkillId = mlSkill.Id, IsRequired = true });

            // Link skills to Job 4 (Fullstack .NET & React)
            if (csharpSkill != null) await context.JobSkills.AddAsync(new JobSkill { JobId = job4.Id, SkillId = csharpSkill.Id, IsRequired = true });
            if (dotnetSkill != null) await context.JobSkills.AddAsync(new JobSkill { JobId = job4.Id, SkillId = dotnetSkill.Id, IsRequired = true });
            if (reactSkill != null) await context.JobSkills.AddAsync(new JobSkill { JobId = job4.Id, SkillId = reactSkill.Id, IsRequired = true });
            if (sqlServerSkill != null) await context.JobSkills.AddAsync(new JobSkill { JobId = job4.Id, SkillId = sqlServerSkill.Id, IsRequired = false });

            // Link skills to Job 5 (DevOps AWS & K8s)
            if (dockerSkill != null) await context.JobSkills.AddAsync(new JobSkill { JobId = job5.Id, SkillId = dockerSkill.Id, IsRequired = true });
            if (k8sSkill != null) await context.JobSkills.AddAsync(new JobSkill { JobId = job5.Id, SkillId = k8sSkill.Id, IsRequired = true });
            if (awsSkill != null) await context.JobSkills.AddAsync(new JobSkill { JobId = job5.Id, SkillId = awsSkill.Id, IsRequired = true });
            if (cicdSkill != null) await context.JobSkills.AddAsync(new JobSkill { JobId = job5.Id, SkillId = cicdSkill.Id, IsRequired = false });

            // Link skills to Job 6 (Mobile Flutter / React Native)
            if (flutterSkill != null) await context.JobSkills.AddAsync(new JobSkill { JobId = job6.Id, SkillId = flutterSkill.Id, IsRequired = true });
            if (reactNativeSkill != null) await context.JobSkills.AddAsync(new JobSkill { JobId = job6.Id, SkillId = reactNativeSkill.Id, IsRequired = false });
            if (gitSkill != null) await context.JobSkills.AddAsync(new JobSkill { JobId = job6.Id, SkillId = gitSkill.Id, IsRequired = true });

            // Link skills to Job 7 (Golang Backend)
            if (golangSkill != null) await context.JobSkills.AddAsync(new JobSkill { JobId = job7.Id, SkillId = golangSkill.Id, IsRequired = true });
            if (dockerSkill != null) await context.JobSkills.AddAsync(new JobSkill { JobId = job7.Id, SkillId = dockerSkill.Id, IsRequired = true });
            if (redisSkill != null) await context.JobSkills.AddAsync(new JobSkill { JobId = job7.Id, SkillId = redisSkill.Id, IsRequired = true });
            if (pgSkill != null) await context.JobSkills.AddAsync(new JobSkill { JobId = job7.Id, SkillId = pgSkill.Id, IsRequired = false });

            // Link skills to Job 8 (UI/UX Designer)
            if (figmaSkill != null) await context.JobSkills.AddAsync(new JobSkill { JobId = job8.Id, SkillId = figmaSkill.Id, IsRequired = true });

            // Link skills to Job 9 (Automation QA)
            if (pythonSkill != null) await context.JobSkills.AddAsync(new JobSkill { JobId = job9.Id, SkillId = pythonSkill.Id, IsRequired = true });
            if (cicdSkill != null) await context.JobSkills.AddAsync(new JobSkill { JobId = job9.Id, SkillId = cicdSkill.Id, IsRequired = false });
            if (gitSkill != null) await context.JobSkills.AddAsync(new JobSkill { JobId = job9.Id, SkillId = gitSkill.Id, IsRequired = true });

            // Link skills to Job 10 (TPM)
            if (agileSkill != null) await context.JobSkills.AddAsync(new JobSkill { JobId = job10.Id, SkillId = agileSkill.Id, IsRequired = true });
            if (gitSkill != null) await context.JobSkills.AddAsync(new JobSkill { JobId = job10.Id, SkillId = gitSkill.Id, IsRequired = false });

            await context.SaveChangesAsync();

            logger?.LogInformation("Demo presentation data seeded successfully.");
        }
        catch (Exception ex)
        {
            logger?.LogError(ex, "An error occurred while seeding demo presentation data.");
            throw;
        }
    }
}
