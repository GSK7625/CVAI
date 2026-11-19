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
                Scale = "10,000+ employees",
                Industry = "Information Technology / Software",
                WebsiteUrl = "https://fptsoftware.com",
                Address = "FPT Building, Duy Tan Street, Dich Vong Hau Ward, Cau Giay District, Hanoi",
                Description = "FPT Software is a subsidiary of FPT Corporation and a leading IT services and digital transformation provider in Asia.",
                VerifiedStatus = CompanyVerificationStatus.Verified,
                VerifiedAt = DateTimeOffset.UtcNow
            };

            var vngCompany = new Company
            {
                Name = "VNG Corporation",
                TaxCode = "0303538435",
                LogoUrl = "https://upload.wikimedia.org/wikipedia/vi/thumb/9/91/VNG_Corporation_logo.svg/1200px-VNG_Corporation_logo.svg.png",
                Scale = "1,000 - 5,000 employees",
                Industry = "Information Technology / Gaming & Internet",
                WebsiteUrl = "https://vng.com.vn",
                Address = "Z06 Street No. 13, Tan Thuan Dong Ward, District 7, Ho Chi Minh City",
                Description = "VNG is a leading technology company in Vietnam with a diverse product ecosystem including Zalo, ZaloPay, and VNG Games.",
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
                Description = "FPT Software is seeking talented Senior .NET Backend Engineers to join our team building large-scale digital transformation software solutions for global enterprise clients.\n\nKey Responsibilities:\n- Design, develop, and maintain microservices backend systems using .NET 8 / C#.\n- Design relational database schemas (PostgreSQL) and optimize high-performance queries.\n- Integrate message brokers (RabbitMQ/Kafka) and distributed caching (Redis).\n- Containerize applications with Docker and collaborate with DevOps on CI/CD pipelines.",
                Requirements = "- At least 3 - 5 years of software development experience with .NET Core / .NET 8 and C#.\n- Proficiency in Entity Framework Core, LINQ, and standards-compliant RESTful Web API design.\n- Solid experience with PostgreSQL or other RDBMS, with deep understanding of Indexing and Transactions.\n- Hands-on experience with Docker and Git.\n- Familiarity with Cloud platforms (AWS/Azure) or Microservices architecture is a plus.",
                Benefits = "- Competitive compensation from 25 - 42 million VND/month + 13th-month salary and project bonuses.\n- Comprehensive FPT Care health insurance for employees and family members.\n- Dynamic environment, flexible hybrid working model, and international onsite opportunities.",
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
                Description = "VNG Corporation is looking for a talented Frontend Engineer to craft smooth web application interfaces serving millions of users.\n\nKey Responsibilities:\n- Build modern Single Page Applications with React, TypeScript, and Tailwind CSS.\n- Optimize rendering performance, Web Vitals, and responsive user experiences.",
                Requirements = "- At least 2 years of experience with React, TypeScript, and HTML5/CSS3.\n- Proficient with Git and integrating RESTful APIs.",
                Benefits = "- Salary 18 - 30 million VND/month + business performance bonus.\n- Free lunch at the office, on-site gym, and recreational lounge.",
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
                Title = "AI / Machine Learning Engineering Intern",
                Description = "AI/ML talent internship program at FPT Software with hands-on exposure to real-world GenAI and LLM projects.",
                Requirements = "- Final-year student or recent graduate majoring in IT, Applied Mathematics, or Artificial Intelligence.\n- Solid Python foundation with knowledge of Machine Learning and Deep Learning.",
                Benefits = "- Attractive internship allowance of 6 - 8 million VND/month.\n- Opportunity to convert to a full-time role after 3 months.",
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

            // Job 4: Fullstack Developer (FPT Software - Da Nang)
            var job4 = new Job
            {
                CompanyId = fptCompany.Id,
                PostedById = recruiterUser.Id,
                Title = "Fullstack Developer (.NET 8 & React)",
                Description = "Deliver end-to-end enterprise solutions from Backend APIs to Frontend UI for international partners at FPT Da Nang.\n\nResponsibilities:\n- Build Web APIs in C# .NET 8 and interactive UIs in React.\n- Optimize data queries and integrate third-party systems.",
                Requirements = "- 2+ years of Fullstack experience with C#, .NET Web API, and React/TypeScript.\n- Familiarity with SQL Server or PostgreSQL.",
                Benefits = "- Salary 20 - 32 million VND/month plus foreign language allowance.\n- Modern coastal campus in Da Nang with an open engineering culture.",
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

            // Job 5: Senior Cloud & DevOps Engineer (VNG Corporation - Ho Chi Minh City)
            var job5 = new Job
            {
                CompanyId = vngCompany.Id,
                PostedById = recruiterUser.Id,
                Title = "Senior Cloud & DevOps Engineer (AWS / K8s)",
                Description = "Design, deploy, and automate large-scale cloud infrastructure serving tens of millions of users across the VNG ecosystem.\n\nResponsibilities:\n- Operate Kubernetes clusters on AWS Cloud.\n- Build automated CI/CD pipelines using GitLab CI and GitHub Actions.",
                Requirements = "- 4+ years of infrastructure operations experience with Docker, Kubernetes (K8s), and AWS Cloud.\n- Proficient in building automated CI/CD pipelines and Linux Administration.",
                Benefits = "- Salary 35 - 55 million VND/month plus company ESOP stock options.\n- Flexible Hybrid work policy and high-end workstation allowance.",
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

            // Job 6: Mobile App Developer (FPT Software - Hanoi)
            var job6 = new Job
            {
                CompanyId = fptCompany.Id,
                PostedById = recruiterUser.Id,
                Title = "Mobile App Developer (Flutter / React Native)",
                Description = "Develop modern cross-platform mobile applications for international Fintech and E-Commerce projects.\n\nResponsibilities:\n- Build smooth mobile apps for both iOS and Android.\n- Integrate RESTful APIs and optimize overall user experience.",
                Requirements = "- 2+ years of mobile app development experience with Flutter or React Native.\n- Strong understanding of State Management, RESTful APIs, and mobile performance optimization.",
                Benefits = "- Compensation 16 - 26 million VND/month + project bonuses.\n- Sponsored training and international professional certifications.",
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
                Description = "Develop low-latency payment processing and real-time messaging systems handling hundreds of thousands of transactions per second.\n\nResponsibilities:\n- Build high-performance microservices with Golang and gRPC.\n- Design distributed caching with Redis and optimize PostgreSQL storage.",
                Requirements = "- 3+ years of backend development experience with Golang.\n- Deep understanding of Concurrency, Memory Management, Redis caching, and High Availability architectures.",
                Benefits = "- Negotiable salary from 30 - 50 million VND/month commensurate with skills.\n- 100% Remote work with flexible hours.",
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

            // Job 8: UI / UX Product Designer (VNG Corporation - Ho Chi Minh City)
            var job8 = new Job
            {
                CompanyId = vngCompany.Id,
                PostedById = recruiterUser.Id,
                Title = "UI / UX Product Designer",
                Description = "Conduct user behavior research, build Design Systems, and craft interfaces for market-leading digital products.\n\nResponsibilities:\n- Design wireframes, interactive prototypes, and high-fidelity UI in Figma.\n- Collaborate closely with Frontend engineers to deliver pixel-accurate UI.",
                Requirements = "- 2+ years of UI/UX design experience for Web and Mobile apps using Figma.\n- Real-world portfolio demonstrating strong User-Centered Design thinking.",
                Benefits = "- Salary 18 - 28 million VND/month + attractive annual bonus.\n- Creative environment with annual learning and conference budget.",
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

            // Job 9: Automation QA / QC Engineer (FPT Software - Hanoi)
            var job9 = new Job
            {
                CompanyId = fptCompany.Id,
                PostedById = recruiterUser.Id,
                Title = "Automation QA / QC Engineer (Python / Selenium)",
                Description = "Build and evolve test automation frameworks integrated with CI/CD to ensure continuous software quality across Agile sprints.\n\nResponsibilities:\n- Write automated test scripts for APIs and Web UI.\n- Track, analyze, and report defects in project management tools.",
                Requirements = "- 2+ years of Automation Testing experience with Python or Java.\n- Experience in API testing, Performance Testing, and CI/CD pipeline integration.",
                Benefits = "- Salary 15 - 25 million VND/month with bi-annual salary reviews.\n- Career growth path to QA Lead on large multinational projects.",
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
                Description = "Shape product vision, manage the Product Backlog, and lead engineering teams building next-generation digital transformation products.\n\nResponsibilities:\n- Partner with stakeholders to clarify business and technical requirements.\n- Plan releases, track sprint velocity, and optimize team delivery.",
                Requirements = "- 4+ years of experience as a Product Owner, TPM, or Technical Project Manager.\n- Strong technical background, ability to bridge business needs and engineering solutions, and fluent English.",
                Benefits = "- Compensation 35 - 55 million VND/month commensurate with impact.\n- Performance bonus and VIP healthcare package.",
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
