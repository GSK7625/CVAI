using FutureCV.Application.Common.Interfaces;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace FutureCV.Api.Controllers;

/// <summary>
/// Read-only lookup endpoint for the shared Skills table.
/// Used by the frontend to populate skill selection dropdowns.
/// </summary>
[AllowAnonymous]
[Route("api/skills")]
public class SkillsController : ApiControllerBase
{
    private readonly IApplicationDbContext _context;

    public SkillsController(IApplicationDbContext context)
    {
        _context = context;
    }

    /// <summary>
    /// Returns the list of available skills, with optional search and category filter.
    /// Results are ordered alphabetically by name.
    /// </summary>
    [HttpGet]
    [ProducesResponseType(StatusCodes.Status200OK)]
    [ResponseCache(Duration = 3600)] // Skills change rarely — cache 1 hour
    public async Task<IActionResult> GetSkills(
        [FromQuery] string? search,
        [FromQuery] string? category,
        CancellationToken cancellationToken)
    {
        var query = _context.Skills.AsNoTracking();

        if (!string.IsNullOrWhiteSpace(search))
            query = query.Where(s => s.Name.ToLower().Contains(search.ToLower()));

        if (!string.IsNullOrWhiteSpace(category))
            query = query.Where(s => s.Category == category);

        var skills = await query
            .OrderBy(s => s.Name)
            .Select(s => new { s.Id, s.Name, s.Category })
            .ToListAsync(cancellationToken);

        return Ok(skills);
    }
}
