using FutureCV.Domain.Entities;
using FutureCV.Domain.Enums;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace FutureCV.Infrastructure.Persistence.Seeders;

/// <summary>
/// Seeds ~500 realistic sample job postings in Development so search, filters,
/// pagination, and AI matching can be tested at realistic catalog scale.
/// </summary>
public static class SampleJobsSeeder
{
    private sealed record RoleTemplate(
        string Title,
        string CategoryKeyword,
        string SkillCategoryHint,
        string[] CoreResponsibilities,
        string[] CoreRequirements);

    private static readonly RoleTemplate[] Templates =
    [
        new(
            ".NET Backend Developer",
            "Backend",
            "Backend",
            [
                "Design and develop high-performance RESTful API services on .NET 8 / ASP.NET Core.",
                "Optimize PostgreSQL queries, design indexes, and ensure data transaction integrity.",
                "Deploy and operate microservices with Docker, Redis, and message queues."
            ],
            [
                "Strong proficiency in C#, .NET Core / .NET 8, and Entity Framework Core.",
                "Solid experience with PostgreSQL or SQL Server, transactions, and SQL performance tuning.",
                "Proficient with Git, Docker, and RESTful API design best practices."
            ]),
        new(
            "Java Spring Boot Developer",
            "Backend",
            "Backend",
            [
                "Develop large-scale backend systems using Java and Spring Boot.",
                "Build distributed architectures and securely integrate payment gateways and third-party services.",
                "Write unit and integration tests and participate in regular code reviews."
            ],
            [
                "Solid experience with Java 17+, Spring Boot, Spring Security, and JPA/Hibernate.",
                "Proficient in relational databases (PostgreSQL/MySQL) and Redis.",
                "Familiarity with Docker, CI/CD pipelines, and microservices architecture."
            ]),
        new(
            "Node.js / NestJS Backend Engineer",
            "Backend",
            "Backend",
            [
                "Build APIs and real-time services powering web and mobile applications.",
                "Optimize asynchronous I/O performance, caching strategies, and JWT/OAuth2 authentication.",
                "Collaborate closely with Frontend and Product teams to deliver features on schedule."
            ],
            [
                "Hands-on experience with Node.js, TypeScript, and NestJS or Express.js.",
                "Experience working with PostgreSQL, MongoDB, and Redis.",
                "Familiarity with Docker, Git, and automated testing."
            ]),
        new(
            "Python / FastAPI Backend Developer",
            "Backend",
            "Backend",
            [
                "Develop data-processing backend services and AI-integrated APIs with Python and FastAPI.",
                "Build background job pipelines, structured logging, and system performance monitoring.",
                "Containerize and deploy services using Docker in Linux environments."
            ],
            [
                "Strong proficiency in Python 3.10+ and FastAPI or Django.",
                "Experience with PostgreSQL, Redis, and REST API design.",
                "Comfortable with Linux, Docker, and writing tests with pytest."
            ]),
        new(
            "Golang Microservices Engineer",
            "Backend",
            "Backend",
            [
                "Develop high-throughput, low-latency backend services in Golang.",
                "Design gRPC/REST APIs and optimize concurrency and memory usage for transaction systems.",
                "Monitor production systems and troubleshoot performance bottlenecks."
            ],
            [
                "Hands-on experience with Golang (goroutines, channels, context).",
                "Proficient in PostgreSQL, Redis, and Docker.",
                "Experience with Kubernetes and CI/CD pipelines is a plus."
            ]),
        new(
            "Frontend React / TypeScript Developer",
            "Frontend",
            "Frontend",
            [
                "Build modern, responsive web interfaces using ReactJS, TypeScript, and Tailwind CSS.",
                "Manage application state effectively and optimize page load speed and Core Web Vitals.",
                "Develop reusable UI component libraries in collaboration with UI/UX Designers."
            ],
            [
                "Proficiency in ReactJS, TypeScript, HTML5/CSS3, and Tailwind CSS.",
                "Experience with TanStack Query, Zustand, or Redux.",
                "Proficient with Git and integrating RESTful APIs."
            ]),
        new(
            "Next.js / Vue.js Frontend Engineer",
            "Frontend",
            "Frontend",
            [
                "Build SEO-friendly SSR/SPA web applications with strong user experience.",
                "Integrate backend APIs, handle complex forms, and ensure web accessibility standards.",
                "Continuously improve build tooling, linting, and frontend automated testing."
            ],
            [
                "Strong proficiency in JavaScript (ES6+), TypeScript, and Next.js or Vue.js.",
                "Solid understanding of HTTP, browser caching, and bundle optimization.",
                "Strong communication and cross-functional teamwork skills."
            ]),
        new(
            "Fullstack Developer (.NET & React)",
            "Fullstack",
            "Backend",
            [
                "Deliver end-to-end business modules from database schema and .NET APIs to React UI.",
                "Participate in requirement analysis, technical solution design, and staging/production releases.",
                "Maintain high code quality through peer code reviews and automated testing."
            ],
            [
                "Experience with C#, ASP.NET Core Web API, and ReactJS/TypeScript.",
                "Proficient with PostgreSQL or SQL Server.",
                "Solid hands-on experience with Git and Docker."
            ]),
        new(
            "Mobile Developer (Flutter / React Native)",
            "Mobile",
            "Mobile",
            [
                "Develop cross-platform iOS and Android mobile apps with smooth, responsive UX.",
                "Optimize rendering performance for large lists, memory usage, and offline support.",
                "Collaborate with Backend teams to integrate APIs, push notifications, and publish to app stores."
            ],
            [
                "Proficiency in Flutter (Dart) or React Native (TypeScript).",
                "Familiarity with building and releasing apps to App Store and Google Play.",
                "Proficient with Git and RESTful API integration."
            ]),
        new(
            "DevOps / Cloud Engineer",
            "DevOps",
            "DevOps",
            [
                "Build and maintain automated CI/CD pipelines for building, testing, and deploying services.",
                "Manage Kubernetes clusters, Docker workloads, and cloud infrastructure (AWS/Azure).",
                "Implement monitoring and alerting systems to maintain a 99.9% operational SLA."
            ],
            [
                "Strong proficiency in Linux, Docker, Kubernetes, and CI/CD pipelines.",
                "Hands-on experience operating cloud infrastructure on AWS or Microsoft Azure.",
                "Security-first mindset with scripting automation skills in Bash or Python."
            ]),
        new(
            "AI / Machine Learning Engineer",
            "Machine Learning",
            "AI/Data",
            [
                "Research, train, and deploy NLP and Machine Learning models for real-world production use cases.",
                "Build data-processing pipelines, evaluate model metrics, and optimize inference latency on CPU/GPU.",
                "Collaborate with Backend engineers to package models into reliable APIs."
            ],
            [
                "Strong proficiency in Python, PyTorch or TensorFlow, and Pandas/NumPy.",
                "Solid foundation in Machine Learning, Deep Learning, or NLP.",
                "Experience containerizing and serving models with Docker and FastAPI."
            ]),
        new(
            "Data Analyst / BI Engineer",
            "Machine Learning",
            "AI/Data",
            [
                "Analyze user behavior data and core business operational metrics.",
                "Build interactive dashboards in Power BI and write optimized SQL queries.",
                "Recommend product and business improvements backed by quantitative insights."
            ],
            [
                "Proficiency in SQL (PostgreSQL/SQL Server) and BI tools such as Power BI.",
                "Experience processing data with Python (Pandas/NumPy) is a plus.",
                "Strong analytical thinking and clear data storytelling skills."
            ]),
        new(
            "QA / Automation Test Engineer",
            "QA",
            "DevOps",
            [
                "Design test plans and test cases, and execute functional, regression, and API testing.",
                "Build automated E2E and API test suites integrated into CI/CD pipelines.",
                "Track bug lifecycles and collaborate with developers to ensure release quality."
            ],
            [
                "Solid understanding of software QA processes and detailed test case design.",
                "Experience writing automated tests (Playwright/Selenium/Python or Postman).",
                "Familiarity with Git and writing SQL queries for data verification."
            ]),
        new(
            "Product / Project Manager (IT)",
            "Product",
            "Management",
            [
                "Plan product roadmaps, manage backlogs, and coordinate Agile/Scrum sprints.",
                "Work directly with clients and stakeholders to clarify business and technical requirements.",
                "Track delivery milestones, manage risks, and ensure high-quality releases."
            ],
            [
                "Proven experience managing software projects in Agile / Scrum environments.",
                "Excellent communication, negotiation, and problem-solving skills.",
                "Ability to read technical documentation; fluent English communication is a strong plus."
            ]),
        new(
            "UI/UX Product Designer",
            "UI / UX",
            "Design",
            [
                "Create wireframes, interactive prototypes, and polished UI designs in Figma.",
                "Build and maintain a consistent Design System across web and mobile products.",
                "Collaborate with PMs and Frontend engineers to verify visual implementation fidelity."
            ],
            [
                "Proficiency in Figma and end-to-end UI/UX prototyping workflows.",
                "Strong grasp of typography, layout, color theory, and responsive design.",
                "Portfolio showcasing shipped web or mobile product designs."
            ]),
        new(
            "Business Development / IT Sales Executive",
            "Business Development",
            "Soft Skills",
            [
                "Prospect, consult, and grow enterprise clients adopting software solutions.",
                "Partner with technical teams to present tailored solutions and prepare proposals.",
                "Nurture existing client accounts and consistently achieve quarterly revenue targets."
            ],
            [
                "Strong negotiation, presentation, and persuasive communication skills.",
                "Experience in B2B sales or software/SaaS solutions is a plus.",
                "Proactive, self-driven, and resilient under revenue targets."
            ]),
        new(
            "Digital Marketing Specialist",
            "Marketing",
            "Soft Skills",
            [
                "Plan and execute SEO, SEM, and paid social advertising campaigns.",
                "Analyze conversion funnels and optimize customer acquisition cost (CAC).",
                "Collaborate on content production to attract both candidates and enterprise clients."
            ],
            [
                "Hands-on experience running digital ads, SEO, and campaign performance analytics.",
                "Creative copywriting skills and effective cross-team collaboration.",
                "Proactive in staying current with tech and recruitment market trends."
            ]),
        new(
            "Talent Acquisition / HR Specialist",
            "Talent Acquisition",
            "Soft Skills",
            [
                "Manage end-to-end IT recruitment cycles from sourcing through onboarding.",
                "Strengthen employer branding and continuously improve candidate experience.",
                "Partner with department leads on quarterly headcount planning."
            ],
            [
                "Experience in technical recruitment or high-volume hiring.",
                "Strong interviewing, candidate assessment, and professional communication skills.",
                "Good English reading comprehension for reviewing technical CVs."
            ])
    ];

    private static readonly string[] Domains =
    [
        "Fintech & Digital Payments",
        "E-Commerce",
        "Enterprise SaaS Platform",
        "Digital Banking",
        "GovTech & Enterprise Digital Transformation",
        "EdTech & Online Learning",
        "Logistics & Supply Chain",
        "HealthTech & Smart Healthcare",
        "AI & Big Data Ecosystem",
        "HRTech & Recruitment Systems"
    ];

    private static readonly string[] CompanySeeds =
    [
        "Viettel Digital Services|0100109106|Telecommunications & Technology|https://viettel.vn|Hanoi",
        "MoMo (M_Service)|0305196215|Fintech & Digital Payments|https://momo.vn|Ho Chi Minh City",
        "Tiki Corporation|0309532909|E-Commerce|https://tiki.vn|Ho Chi Minh City",
        "NashTech Vietnam|0302139871|Software Engineering & Consulting|https://nashtechglobal.com|Ho Chi Minh City",
        "Techcombank Digital|0100230800|Digital Banking|https://techcombank.com|Hanoi",
        "One Mount Group|0108892429|Technology Ecosystem|https://onemount.com|Hanoi"
    ];

    public static async Task SeedAsync(IServiceProvider serviceProvider, int targetTotalJobs = 500)
    {
        using var scope = serviceProvider.CreateScope();
        var context = scope.ServiceProvider.GetRequiredService<ApplicationDbContext>();
        var logger = scope.ServiceProvider.GetService<ILoggerFactory>()?.CreateLogger(nameof(SampleJobsSeeder));

        var poster = await context.Employers.AsNoTracking().FirstOrDefaultAsync();
        if (poster is null)
        {
            logger?.LogWarning("Skipping SampleJobsSeeder because no Employer profile exists yet.");
            return;
        }

        await EnsureEnglishEvidenceDemoJobAsync(context, poster.UserId);

        var existingCount = await context.Jobs.CountAsync(j => !j.IsDeleted);
        if (existingCount >= targetTotalJobs)
        {
            return;
        }

        // Ensure extra verified companies exist for richer filtering
        foreach (var entry in CompanySeeds)
        {
            var parts = entry.Split('|');
            var taxCode = parts[1];
            if (!await context.Companies.AnyAsync(c => c.TaxCode == taxCode))
            {
                context.Companies.Add(new Company
                {
                    Name = parts[0],
                    TaxCode = taxCode,
                    Scale = "1,000+ employees",
                    Industry = parts[2],
                    WebsiteUrl = parts[3],
                    Address = parts[4],
                    Description = $"{parts[0]} is a leading technology enterprise in {parts[2]}.",
                    VerifiedStatus = CompanyVerificationStatus.Verified,
                    VerifiedAt = DateTimeOffset.UtcNow
                });
            }
        }
        await context.SaveChangesAsync();

        var companies = await context.Companies.Where(c => !c.IsDeleted).ToListAsync();
        var categories = await context.JobCategories.ToListAsync();
        var levels = await context.JobLevels.ToListAsync();
        var employmentTypes = await context.EmploymentTypes.ToListAsync();
        var locations = await context.Locations.Where(l => l.ParentId == null).ToListAsync();
        var skills = await context.Skills.ToListAsync();

        if (companies.Count == 0 || categories.Count == 0 || levels.Count == 0 || employmentTypes.Count == 0 || locations.Count == 0)
        {
            logger?.LogWarning("Skipping SampleJobsSeeder due to missing master reference data.");
            return;
        }

        var toCreate = targetTotalJobs - existingCount;
        var rng = new Random(20261119);
        var now = DateTime.UtcNow;
        var jobsToAdd = new List<Job>(toCreate);
        var jobSkillsToAdd = new List<JobSkill>(toCreate * 4);

        for (var i = 0; i < toCreate; i++)
        {
            var template = Templates[i % Templates.Length];
            var domain = Domains[(i / Templates.Length + rng.Next(Domains.Length)) % Domains.Length];
            var company = companies[(i + rng.Next(companies.Count)) % companies.Count];
            var level = levels[rng.Next(levels.Count)];
            var empType = employmentTypes[rng.Next(employmentTypes.Count)];
            var location = locations[rng.Next(locations.Count)];
            var category = categories.FirstOrDefault(c => c.Name.Contains(template.CategoryKeyword, StringComparison.OrdinalIgnoreCase))
                ?? categories[rng.Next(categories.Count)];

            var (salaryMin, salaryMax, expMin, expMax) = EstimateCompensation(level.Name, rng);
            var levelPrefix = ExtractShortLevel(level.Name);
            var title = string.IsNullOrEmpty(levelPrefix)
                ? $"{template.Title} ({domain})"
                : $"{levelPrefix} {template.Title} - {domain}";
            if (title.Length > 280) title = title[..280];

            var expRequirement = expMin > 0
                ? $"At least {expMin} {(expMin == 1 ? "year" : "years")} of experience in a similar role."
                : "Fresh graduates or final-year students with strong foundational knowledge are welcome.";

            var isPending = i % 25 == 24;
            var job = new Job
            {
                Id = Guid.NewGuid(),
                CompanyId = company.Id,
                PostedById = poster.UserId,
                Title = title,
                Description =
                    $"{company.Name} is hiring for a {title} to join our {domain} team.\n\n" +
                    "Key Responsibilities:\n- " + string.Join("\n- ", template.CoreResponsibilities),
                Requirements =
                    "- " + string.Join("\n- ", template.CoreRequirements) +
                    $"\n- {expRequirement}",
                Benefits =
                    $"- Competitive compensation ({salaryMin / 1_000_000} - {salaryMax / 1_000_000} million VND/month) + performance bonus.\n" +
                    "- Premium health insurance, flexible leave policy, and professional training support.\n" +
                    "- Real-world product environment with a clear career progression path.",
                CategoryId = category.Id,
                LevelId = level.Id,
                EmploymentTypeId = empType.Id,
                LocationId = location.Id,
                SalaryMin = salaryMin,
                SalaryMax = salaryMax,
                SalaryCurrency = "VND",
                ExperienceYearsMin = expMin,
                ExperienceYearsMax = expMax,
                Deadline = now.AddDays(15 + rng.Next(75)),
                PositionsCount = 1 + rng.Next(4),
                ApprovalStatus = isPending ? JobApprovalStatus.Pending : JobApprovalStatus.Approved,
                IsActive = true,
                IsExpired = false,
                ViewCount = rng.Next(20, 450),
                CreatedAt = now.AddMinutes(-rng.Next(60 * 24 * 30))
            };

            jobsToAdd.Add(job);

            var matchingSkills = skills
                .Where(s => string.Equals(s.Category, template.SkillCategoryHint, StringComparison.OrdinalIgnoreCase))
                .OrderBy(_ => rng.Next())
                .Take(3)
                .ToList();

            if (matchingSkills.Count < 3)
            {
                var extras = skills.Except(matchingSkills).OrderBy(_ => rng.Next()).Take(3 - matchingSkills.Count);
                matchingSkills.AddRange(extras);
            }

            for (var sIdx = 0; sIdx < matchingSkills.Count; sIdx++)
            {
                jobSkillsToAdd.Add(new JobSkill
                {
                    JobId = job.Id,
                    SkillId = matchingSkills[sIdx].Id,
                    IsRequired = sIdx < 2
                });
            }
        }

        await context.Jobs.AddRangeAsync(jobsToAdd);
        await context.JobSkills.AddRangeAsync(jobSkillsToAdd);
        await context.SaveChangesAsync();

        logger?.LogInformation("SampleJobsSeeder added {Count} sample jobs (total target: {Target}).", jobsToAdd.Count, targetTotalJobs);
    }

    private static (int SalaryMin, int SalaryMax, int ExpMin, int ExpMax) EstimateCompensation(string levelName, Random rng)
    {
        if (levelName.Contains("Intern", StringComparison.OrdinalIgnoreCase))
            return (4_000_000, 8_000_000, 0, 1);
        if (levelName.Contains("Fresher", StringComparison.OrdinalIgnoreCase))
            return (9_000_000, 14_000_000, 0, 1);
        if (levelName.Contains("Junior", StringComparison.OrdinalIgnoreCase))
            return (13_000_000 + rng.Next(3) * 1_000_000, 20_000_000 + rng.Next(3) * 1_000_000, 1, 2);
        if (levelName.Contains("Middle", StringComparison.OrdinalIgnoreCase))
            return (20_000_000 + rng.Next(5) * 1_000_000, 32_000_000 + rng.Next(5) * 1_000_000, 2, 4);
        if (levelName.Contains("Senior", StringComparison.OrdinalIgnoreCase))
            return (32_000_000 + rng.Next(6) * 1_000_000, 50_000_000 + rng.Next(8) * 1_000_000, 4, 7);
        return (45_000_000 + rng.Next(5) * 1_000_000, 70_000_000 + rng.Next(10) * 1_000_000, 5, 10);
    }

    private static string ExtractShortLevel(string levelName)
    {
        if (levelName.Contains("Intern", StringComparison.OrdinalIgnoreCase)) return "Intern";
        if (levelName.Contains("Fresher", StringComparison.OrdinalIgnoreCase)) return "Fresher";
        if (levelName.Contains("Junior", StringComparison.OrdinalIgnoreCase)) return "Junior";
        if (levelName.Contains("Middle", StringComparison.OrdinalIgnoreCase)) return "Middle";
        if (levelName.Contains("Senior", StringComparison.OrdinalIgnoreCase)) return "Senior";
        if (levelName.Contains("Team Leader", StringComparison.OrdinalIgnoreCase)) return "Team Lead";
        if (levelName.Contains("Manager", StringComparison.OrdinalIgnoreCase)) return "Manager";
        return string.Empty;
    }

    private static async Task EnsureEnglishEvidenceDemoJobAsync(ApplicationDbContext context, Guid posterUserId)
    {
        const string demoTitle = "Backend Developer (English JD - AI Evidence Demo)";
        if (await context.Jobs.AnyAsync(j => j.Title == demoTitle && !j.IsDeleted))
        {
            return;
        }

        var company = await context.Companies.FirstOrDefaultAsync(c => !c.IsDeleted);
        if (company is null) return;

        var category = await context.JobCategories.FirstOrDefaultAsync(c => c.Name.Contains("Backend"))
            ?? await context.JobCategories.FirstOrDefaultAsync();
        var level = await context.JobLevels.FirstOrDefaultAsync(l => l.Name.Contains("Middle"))
            ?? await context.JobLevels.FirstOrDefaultAsync();
        var empType = await context.EmploymentTypes.FirstOrDefaultAsync(t => t.Name.Contains("Full-time"))
            ?? await context.EmploymentTypes.FirstOrDefaultAsync();
        var location = await context.Locations.FirstOrDefaultAsync(l => l.Name == "Hà Nội")
            ?? await context.Locations.FirstOrDefaultAsync();

        var job = new Job
        {
            Id = Guid.NewGuid(),
            CompanyId = company.Id,
            PostedById = posterUserId,
            Title = demoTitle,
            Description =
                "We are looking for a Backend Developer to build reliable APIs, data pipelines, and containerized microservices.",
            Requirements =
                "Requirements:\n" +
                "- Required: paid work experience with Python.\n" +
                "- Required: SQL experience in an independent project.\n" +
                "- At least 2 years of experience as a backend developer.\n" +
                "Preferred:\n" +
                "- Experience with Docker and Git.",
            Benefits =
                "- Competitive compensation (25 - 40 million VND/month) + 13th-month bonus.\n" +
                "- Flexible hybrid working model and premium health insurance.",
            CategoryId = category?.Id,
            LevelId = level?.Id,
            EmploymentTypeId = empType?.Id,
            LocationId = location?.Id,
            SalaryMin = 25_000_000,
            SalaryMax = 40_000_000,
            SalaryCurrency = "VND",
            ExperienceYearsMin = 2,
            ExperienceYearsMax = 4,
            Deadline = DateTime.UtcNow.AddMonths(2),
            PositionsCount = 2,
            ApprovalStatus = JobApprovalStatus.Approved,
            IsActive = true,
            IsExpired = false,
            ViewCount = 88,
            CreatedAt = DateTime.UtcNow
        };

        context.Jobs.Add(job);

        var matchedSkills = await context.Skills
            .Where(s => s.Name.Contains("Python") || s.Name.Contains("PostgreSQL") || s.Name.Contains("Docker") || s.Name.Contains("Git"))
            .ToListAsync();

        foreach (var skill in matchedSkills.Take(4))
        {
            context.JobSkills.Add(new JobSkill
            {
                JobId = job.Id,
                SkillId = skill.Id,
                IsRequired = skill.Name.Contains("Python") || skill.Name.Contains("PostgreSQL")
            });
        }

        await context.SaveChangesAsync();
    }
}
