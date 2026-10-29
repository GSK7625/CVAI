# AGENTS.md — FutureCV Backend (.NET 8/10 Clean Architecture)

Behavioral guidelines and architectural guardrails for AI coding agents working on the FutureCV Backend.
Rooted in the philosophy of **"Clean Architecture in .NET (Keep It Boring on Purpose)"** (referencing Mukesh Murugan's Clean Architecture guide): placing core business rules at the center, strictly decoupled from databases, UI, and external frameworks.

**Tradeoff:** These guidelines bias toward caution, domain integrity, and architectural discipline over speed. For trivial tasks, use judgment.

---

## 🏗️ 0. Architectural Principles & Layer Boundaries

The backend strictly implements Clean Architecture. The core dependency rule is **unidirectional and inward-pointing**, enforced at **compile-time via .NET Project References**:

```text
FutureCV.Domain  <───  FutureCV.Application  <───  FutureCV.Infrastructure
       ▲                        ▲                                ▲
       │                        │                                │
       └────────────────────────┴─────────────────  FutureCV.Api (Host / Composition Root)
```

```
FutureCV.Domain:          ZERO dependencies. No NuGet packages, no project references.
FutureCV.Application:     Depends ONLY on FutureCV.Domain (and EF Core abstractions: DbSet, IQueryable).
FutureCV.Infrastructure:  Depends on FutureCV.Application and FutureCV.Domain.
FutureCV.Api:             References Infrastructure & Application (Composition Root).
```

---

### 1. `FutureCV.Domain` (Core Business Rules — Zero Dependencies)

- **Rich Domain Model (NOT Anemic):**
  - Entities must **NOT** be anemic bags of public getters and setters (`{ get; set; }`).
  - Use `private set` for properties that represent internal state.
  - Instantiation must happen via **Factory Methods** (e.g., `Job.Create(...)`, `Company.Register(...)`).
  - State changes must occur via **meaningful domain methods** (e.g., `job.Approve(adminId)`, `job.Reject(reason)`, `application.ChangeStatus(newStatus)`).
  - Entities inherit from `BaseEntity` (`src/FutureCV.Domain/Common/BaseEntity.cs`).
- **Domain Invariants & Self-Protection:**
  - Entities are the final guardian of business rules. When business rules or invariants are violated (e.g., salary min > salary max, deadline in the past when publishing), the entity directly throws a `DomainException`.
- **Identity & Indexing:**
  - Use time-ordered **UUID v7** (`Guid.CreateVersion7()`) instead of random `Guid.NewGuid()` to optimize B-Tree clustering and index performance in PostgreSQL.
- **Strict Constraint:**
  - **ZERO NuGet packages** and **ZERO project references**. Never let database, web, or framework concepts leak into this layer.

---

### 2. `FutureCV.Application` (Use Case Orchestration & Abstractions)

- **Feature-Based Modular Structure:**
  - Code is organized under `src/FutureCV.Application/Features/<FeatureName>/`:
    - `DTOs/` — Request/Response models (prefer `record` types for immutability).
    - `Interfaces/` — Feature service contracts (e.g., `IJobService`).
    - `Services/` — Orchestrators that load entities from `IApplicationDbContext`, invoke domain behaviors, and persist state.
    - `Validators/` — Input validation rules using `FluentValidation`.
- **Two-Layer Validation Strategy (Layer 1: Input Validation):**
  - `FluentValidation` validates request shape, formats, string lengths, ranges, and required fields before execution reaches the Domain.
- **Database Abstraction:**
  - Services access persistence strictly through `IApplicationDbContext` (`src/FutureCV.Application/Common/Interfaces/IApplicationDbContext.cs`).
  - Leverage the full power of EF Core LINQ (`.Include()`, `.AsNoTracking()`, `.Where()`) directly through `DbSet<T>`.
- **Flow Control & Result Pattern:**
  - Application services return `ServiceResult<T>` (`src/FutureCV.Application/Common/Models/ServiceResult.cs`) for operational outcomes (`Success`, `NotFound`, `Unauthorized`, `Forbidden`, `Conflict`, `Validation`).
  - **Constraint:** NEVER throw business flow exceptions or reference HTTP status codes in this layer.

---

### 3. `FutureCV.Infrastructure` (Concrete Implementations)

- **EF Core Persistence:**
  - `ApplicationDbContext` implements `IApplicationDbContext` and inherits from `IdentityDbContext<AppUser, ...>`.
  - Use `IEntityTypeConfiguration<T>` in `src/FutureCV.Infrastructure/Persistence/Configurations/` for explicit schema mapping. Do not pollute Domain entities with EF Core attributes (`[Table]`, `[Column]`).
- **External Integrations:**
  - Identity (`AppUser`, ASP.NET Core Identity).
  - External adapters: `CloudinaryFileStorage`, `EmailService`, `JwtTokenService`, `TokenCookieService`.
- **Database Migrations:**
  - All migrations live in `FutureCV.Infrastructure`.

---

### 4. `FutureCV.Api` (Presentation & Composition Root)

- **Thin Endpoints:**
  - Controllers inherit `ApiControllerBase` (`src/FutureCV.Api/Controllers/ApiControllerBase.cs`).
  - Responsibility: Receive request -> invoke Application service -> map outcome to HTTP response via `ToHttpResult(result)`.
  - Controllers contain **ZERO business logic** and **ZERO direct database queries**.
- **Global Error Handling:**
  - Global middleware handles unhandled exceptions and converts `DomainException` into standardized RFC 7807 `ProblemDetails` with HTTP 400 Bad Request instead of 500 Internal Server Error.
- **Composition Root:**
  - `Program.cs` wires up DI via extension methods (`AddApplication()`, `AddInfrastructure()`).

---

### 5. Practical Design: "Keep It Boring on Purpose"

Avoid speculative abstractions that add cognitive overhead without delivering value:
1. **NO Generic Repository & NO Unit of Work:**
   - EF Core's `DbContext` is already a Unit of Work, and `DbSet<T>` is already a Repository. Adding custom generic repository wrappers hides LINQ capabilities (`Include`, projections, batch operations) and creates redundant boilerplate.
2. **NO MediatR Overhead:**
   - Use direct, scoped service classes (`IJobService`, `JobService`). Do not force MediatR commands/queries unless a genuine distributed message bus or event pipeline is required.
3. **NO AutoMapper Magic:**
   - Use explicit manual mapping methods or DTO factory methods (e.g., `JobResponse.FromEntity(job)`). This makes data flow visible, traceable, and compile-safe.
4. **Central Package Management:**
   - All NuGet versions are managed in `backend/Directory.Packages.props`. **NEVER** add `Version="x.x.x"` inside `.csproj`.
5. **Local Orchestration:**
   - Multi-service and PostgreSQL local orchestration uses `.NET Aspire` (`backend/aspire/FutureCV.AppHost`).

---

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before writing code:
- **Determine the Responsibility Layer:**
  - Is this an invariant rule? -> `Domain` (Rich Entity method + `DomainException`).
  - Is this input format validation? -> `Application` (`FluentValidation`).
  - Is this use-case orchestration? -> `Application` (`FeatureService`).
  - Is this schema/query configuration? -> `Infrastructure` (`EntityTypeConfiguration` / `ApplicationDbContext`).
  - Is this route/parameter mapping? -> `Api` (`Controller`).
- **Check Existing Conventions:**
  - Inspect `Features/Job` or `Features/Candidate` before introducing new conventions.
- **Surface Database Tradeoffs:**
  - Entity property modifications require an EF Core migration. Note if schema changes impact existing records or requires default values.
- **Clarify Auth & Dual-Role Implications:**
  - FutureCV supports `Candidate`, `Employer`, and `Admin`. Verify which roles are permitted and how tokens/cookies are affected.

---

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- Implement ONLY what was requested.
- No single-use abstractions, wrappers, or speculative interfaces.
- If a method takes 10 lines of clean LINQ via `IApplicationDbContext`, do not invent a multi-class helper pattern.
- If you write 150 lines and it could be 50 lines following Clean Architecture, rewrite it.

---

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

- **Never reformat adjacent code or reorder existing imports.**
- **Preserve existing coding style:** File-scoped namespaces (`namespace FutureCV...;`), nullable enabled, PascalCase methods, `_camelCase` injected fields.
- **Never edit an applied migration file:** Always generate a new migration.
- **Clean up your own orphans:** Remove any unused usings or DI registrations that your changes made redundant.
- *The test: Every changed line in `git diff` should trace directly to the user's request.*

---

## 4. Goal-Driven Execution & Verification

**Define success criteria. Loop until verified.**

Plan multi-step changes:
```text
1. [Domain / Infrastructure] Entity / Configuration / Migration → verify: dotnet build
2. [Application] DTOs, Validator, Service → verify: dotnet build
3. [Api] Controller endpoint → verify: dotnet build & route check
4. [Verification] Automated test or Swagger check
```

### Essential CLI Commands (Run from `backend/`):

- **Build Solution:**
  ```bash
  dotnet build FutureCV.sln
  ```
- **Run Unit Tests:**
  ```bash
  dotnet test FutureCV.sln
  ```
- **Add Migration:**
  ```bash
  dotnet ef migrations add <Name> --project src/FutureCV.Infrastructure --startup-project src/FutureCV.Api
  ```
- **Update Database:**
  ```bash
  dotnet ef database update --project src/FutureCV.Infrastructure --startup-project src/FutureCV.Api
  ```
- **Run API Locally:**
  ```bash
  dotnet run --project src/FutureCV.Api
  ```
- **Swagger Verification:**
  - HTTP: `http://localhost:5000/swagger`
  - HTTPS: `https://localhost:7000/swagger`

---

**These guidelines are working if:** PR diffs are surgical, Clean Architecture boundaries are strictly enforced at compile time, entities protect their own business invariants, and clarifying questions precede code changes.
