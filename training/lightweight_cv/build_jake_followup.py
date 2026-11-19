"""Fixed English PDF diagnostic for paired evaluation, never imported by training."""
from build_jake_pilot import OUT, build


PROFILES = [
    ("Jamie Finn", "Test Engineer", "Copper Ferry", "Playwright", "Selenium", "Postman", "pytest",
     "Automated reservation checks in Playwright for our ticketing service.",
     "Built a Selenium harness to replay bookings on a miniature travel site.",
     "Trip Replay", "The ticketing team does not use pytest."),
    ("Drew Page", "Analytics Engineer", "Fallow Foods", "pandas", "SQL", "Airflow", "Redis",
     "Reduced stock discrepancies by merging supplier exports with pandas.",
     "Wrote SQL views to reconcile community pantry orders.",
     "Pantry Counts", "Tracked lot numbers during two supplier recalls."),
    ("Taylor North", "Infrastructure Engineer", "Meridian Weather", "Linux", "Kubernetes", "Python", "AWS",
     "Maintained Linux hosts that archive storm observations.",
     "Deployed a Kubernetes cluster for a personal rainfall map.",
     "Rain Tiles", "Coordinated instrument maintenance with the field team."),
    ("Riley Shaw", "Application Developer", "Graywing Audio", "Kotlin", "JavaScript", "Swift", "Java",
     "Rebuilt the playback queue in Kotlin for the audiobook app.",
     "Created JavaScript controls for a browser-based metronome.",
     "Meter Box", "Implemented bookmarks after collecting feedback from narrators."),
    ("Hayden Cole", "Release Engineer", "Redwood Print", "Docker", "Terraform", "GitHub Actions", "Jenkins",
     "Packaged the print scheduler in Docker and tested restart behavior.",
     "Provisioned a small typesetting service with Terraform.",
     "Letterpress Lab", "Documented the release checklist for late-night maintenance."),
    ("Quinn Bell", "Database Developer", "Canal Freight", "PostgreSQL", "Redis", "Git", "SQL",
     "Optimized a PostgreSQL shipment lookup that operators use at dispatch.",
     "Implemented a Redis cache for an open timetable viewer.",
     "Timetable Desk", "Reconciled manifest totals after schedule changes."),
]


def assessments(profile):
    _, _, _, work, project, listed, missing, work_line, project_line, _, _ = profile
    return [
        (f"Professional experience applying {work}.", 3, "met", work_line, "Experience"),
        (f"Commercial experience using {project}.", 3, "partial", project_line, "Projects"),
        (f"Hands-on project experience with {project}.", 2, "met", project_line, "Projects"),
        (f"Foundational knowledge of {listed}.", 1, "met", f"Additional tools: {listed}.", "Technical Skills"),
        (f"Use {listed} in paid employment.", 3, "partial", f"Additional tools: {listed}.", "Technical Skills"),
        (f"Hands-on experience applying {missing} in a project.", 2, "not_evidenced", None, None),
    ]


if __name__ == "__main__":
    build(PROFILES, OUT.with_name("jake_pdf_followup"), assessments)
