"""Generate six synthetic one-page Jake-style resumes and PDF-grounded rubric labels."""
import json
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from pdf_text import extract_pdf
from pipeline import file_hash, validate_input

OUT = Path(__file__).resolve().parents[1] / "datasets/jake_pdf_pilot"

# The statements explicitly distinguish personal work from project and list-only claims.
PROFILES = [
    ("Alex Reed", "Backend Developer", "Northline Transit", "Python", "Java", "Redis", "Docker",
     "At Northline Transit I wrote Python jobs to reconcile missed fare payments.",
     "I built an independent Java project to flag missing station codes.",
     "Fare Ledger", "Compared settlement totals with operator reports before each release."),
    ("Sam Park", "Backend Developer", "Beacon Archive", "Java", "Python", "Docker", "Redis",
     "I used Java at Beacon Archive to restore interrupted document imports.",
     "For my own Python project I indexed scanned catalogues by accession number.",
     "Shelf Index", "Added retry tests for corrupt records and reviewed import failures with support."),
    ("Robin Vale", "Frontend Developer", "Orchard Studio", "JavaScript", "React", "CSS", "React Native",
     "I maintained the JavaScript checkout form at Orchard Studio and fixed duplicate submissions.",
     "I prototyped a React appointment calendar in an independent project.",
     "Open Calendar", "Tested keyboard navigation with the design team before release."),
    ("Casey Lin", "Mobile Developer", "Lakehouse Maps", "React Native", "TypeScript", "React", "Java",
     "I shipped React Native map controls as a mobile developer at Lakehouse Maps.",
     "My independent TypeScript project turns walking routes into printable itineraries.",
     "Route Cards", "Added offline-state tests for routes with missing coordinates."),
    ("Avery Dale", "Data Analyst", "Delta Orchard", "SQL", "Python", "Tableau", "Spark",
     "I wrote SQL checks at Delta Orchard to find duplicate shipment records.",
     "I used Python in a personal project to compare harvest dates across regions.",
     "Harvest Notes", "Summarized late deliveries for operations staff each Friday."),
    ("Morgan Brook", "Platform Engineer", "Tern Systems", "Docker", "Terraform", "AWS", "Kubernetes",
     "At Tern Systems I packaged the nightly billing worker with Docker.",
     "I used Terraform in a personal project to recreate a small staging network.",
     "Staging Lab", "Documented the rollback procedure after testing it with the on-call engineer."),
]


def build(profiles=PROFILES, directory=OUT, assessment_builder=None):
    directory.mkdir(parents=True, exist_ok=True)
    cases = []
    for i, profile in enumerate(profiles, 1):
        name, role, employer, paid, project, listed, absent, work_line, proj_line, title, detail = profile
        filename = f"resume-{i:02}.pdf"
        pdf = canvas.Canvas(str(directory / filename), pagesize=letter, invariant=1)
        pdf.setTitle(f"{name} | Resume")
        def line(y, text, font="Times-Roman", size=12, x=52):
            if pdf.stringWidth(text, font, size) > 560 - x:
                raise ValueError(f"Line exceeds page width: {text}")
            pdf.setFont(font, size)
            pdf.drawString(x, y, text)
        def section(y, label):
            line(y, label, "Times-Bold", 15)
            pdf.line(52, y - 5, 560, y - 5)
        pdf.setFont("Times-Bold", 26)
        pdf.drawCentredString(306, 732, name)
        pdf.setFont("Times-Roman", 11)
        pdf.drawCentredString(306, 710, f"{role}  |  {name.lower().replace(' ', '.')}@example.org")
        section(653, "Education")
        line(621, "Westfield Institute of Technology", "Times-Bold")
        line(602, "B.S. in Computer Science", "Times-Italic")
        section(550, "Experience")
        line(517, role, "Times-Bold")
        pdf.setFont("Times-Roman", 11)
        pdf.drawRightString(560, 517, "Jan 2024 - Jun 2025")
        line(497, employer, "Times-Italic")
        line(472, "- " + work_line, size=11, x=62)
        line(451, "- " + detail, size=11, x=62)
        section(395, "Projects")
        line(362, title, "Times-Bold")
        line(337, "- " + proj_line, size=11, x=62)
        section(284, "Technical Skills")
        skills_line = f"Additional tools: {listed}."
        line(251, skills_line)
        pdf.save()
        cv = extract_pdf((directory / filename).read_bytes())
        casespec = [
            (f"Use {paid} during paid employment.", 3, "met", work_line, "Experience"),
            (f"Use {project} during paid employment.", 3, "partial", proj_line, "Projects"),
            (f"Apply {project} in an independent project.", 2, "met", proj_line, "Projects"),
            (f"Apply {listed} in an independent project.", 2, "partial", skills_line, "Technical Skills"),
            (f"Use {absent} during paid employment.", 3, "not_evidenced", None, None),
        ]
        reqs, labels = [], []
        if assessment_builder is not None:
            casespec = assessment_builder(profile)
        headings = ["Education", "Experience", "Projects", "Technical Skills"]
        for j, (query, weight, status, quote, heading) in enumerate(casespec, 1):
            rid = f"r{j}"
            reqs.append(dict(id=rid, text=query, weight=weight))
            span = None
            if quote:
                start = cv.index(quote)
                assert cv.count(quote) == 1
                assert max((h for h in headings if cv.index(h) < start), key=cv.index) == heading
                span = dict(start=start, end=start + len(quote), page=1, section=heading)
            labels.append(dict(id=rid, status=status, evidence=quote, span=span))
        prefix = "jake-pilot" if directory == OUT else directory.name
        row = dict(sample_id=f"{prefix}-{i:02}", pdf=filename, pdf_sha256=file_hash(directory / filename),
                   cv_text=cv, requirements=reqs, target=dict(assessments=labels))
        validate_input(row)
        cases.append(row)
    (directory / "cases.json").write_text(json.dumps(dict(source="synthetic_authored", split="pdf_diagnostic",
        language="en", samples=cases), ensure_ascii=False, indent=2) + "\n", encoding="utf8")


if __name__ == "__main__":
    build()
