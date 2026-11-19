export interface BuilderCvPersonalInfo {
  fullName?: string;
  title?: string;
  email?: string;
  phone?: string;
  location?: string;
  website?: string;
  summary?: string;
}

export interface BuilderCvExperience {
  role?: string;
  company?: string;
  startDate?: string;
  endDate?: string;
  description?: string;
}

export interface BuilderCvEducation {
  degree?: string;
  school?: string;
  startDate?: string;
  endDate?: string;
  gpa?: string;
}

export interface BuilderCvTextInput {
  personalInfo: BuilderCvPersonalInfo;
  experiences: BuilderCvExperience[];
  educations: BuilderCvEducation[];
  skills: string[];
}

const MAX_BUILDER_RAW_TEXT_CHARS = 30000;

/**
 * Formats CV Builder state into clean plain text so the Evidence AI pipeline
 * can analyze Builder-created CVs without requiring OCR on rasterized PDFs.
 */
export function buildBuilderCvPlainText(input: BuilderCvTextInput): string {
  const lines: string[] = [];
  const { personalInfo, experiences, educations, skills } = input;

  if (personalInfo.fullName?.trim()) lines.push(personalInfo.fullName.trim());
  if (personalInfo.title?.trim()) lines.push(personalInfo.title.trim());

  const contact = [
    personalInfo.email?.trim(),
    personalInfo.phone?.trim(),
    personalInfo.location?.trim(),
    personalInfo.website?.trim(),
  ].filter((v): v is string => Boolean(v));
  if (contact.length > 0) lines.push(contact.join(" | "));

  if (personalInfo.summary?.trim()) {
    lines.push("", "SUMMARY", personalInfo.summary.trim());
  }

  const validExperiences = experiences.filter(
    (e) => e.role?.trim() || e.company?.trim() || e.description?.trim(),
  );
  if (validExperiences.length > 0) {
    lines.push("", "EXPERIENCE");
    for (const exp of validExperiences) {
      const header = [exp.role?.trim(), exp.company?.trim()].filter(Boolean).join(" - ");
      const dates = [exp.startDate?.trim(), exp.endDate?.trim()].filter(Boolean).join(" - ");
      const titleLine = dates ? `${header} (${dates})` : header;
      if (titleLine) lines.push(titleLine);
      if (exp.description?.trim()) lines.push(exp.description.trim());
    }
  }

  const validEducations = educations.filter(
    (ed) => ed.degree?.trim() || ed.school?.trim(),
  );
  if (validEducations.length > 0) {
    lines.push("", "EDUCATION");
    for (const ed of validEducations) {
      const header = [ed.degree?.trim(), ed.school?.trim()].filter(Boolean).join(" - ");
      const dates = [ed.startDate?.trim(), ed.endDate?.trim()].filter(Boolean).join(" - ");
      const meta = [dates, ed.gpa?.trim() ? `GPA: ${ed.gpa.trim()}` : ""].filter(Boolean).join(", ");
      lines.push(meta ? `${header} (${meta})` : header);
    }
  }

  const cleanSkills = skills.map((s) => s.trim()).filter(Boolean);
  if (cleanSkills.length > 0) {
    lines.push("", "SKILLS", cleanSkills.join(", "));
  }

  const result = lines.join("\n").trim();
  return result.length > MAX_BUILDER_RAW_TEXT_CHARS
    ? result.slice(0, MAX_BUILDER_RAW_TEXT_CHARS)
    : result;
}
