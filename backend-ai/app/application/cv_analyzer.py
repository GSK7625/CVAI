"""CV Analyzer application service orchestrating document parsing, extraction, and quality scoring."""

import time

from pydantic import BaseModel, ConfigDict, Field

from app.application.text_sanitization import sanitize_free_text
from app.contracts.common import ResponseMeta
from app.contracts.cv import (
    EducationItem,
    ProjectItem,
    StructuredCv,
    WorkExperienceItem,
)
from app.contracts.cv_analysis import CvAnalysisResponse
from app.core.config import Settings, get_settings
from app.core.exceptions import DocumentParsingError
from app.domain.cv.scoring import evaluate_cv_quality
from app.observability.logging import correlation_id_ctx, get_logger
from app.ports.document_parser import DocumentParserPort
from app.ports.llm import LlmPort
from app.prompts.cv_analysis_v1 import (
    CV_ANALYSIS_SYSTEM_PROMPT_V1,
    CV_ANALYSIS_USER_PROMPT_TEMPLATE_V1,
)
from app.prompts.cv_extraction_v1 import (
    CV_EXTRACTION_SYSTEM_PROMPT_V1,
    CV_EXTRACTION_USER_PROMPT_TEMPLATE_V1,
)

logger = get_logger(__name__)


class CvQualitativeFeedback(BaseModel):
    """Internal application structured model for qualitative critique from LLM."""

    model_config = ConfigDict(extra="forbid")

    strengths: list[str] = Field(default_factory=list, description="Key professional strengths")
    weaknesses: list[str] = Field(default_factory=list, description="Specific areas of weakness")
    improvement_suggestions: list[str] = Field(
        default_factory=list,
        description="Actionable improvement suggestions",
    )


def _build_experience_context(work_experience: list[WorkExperienceItem], max_chars: int = 2000) -> str:
    """Build grounded, PII-sanitized context for work experience, limited to max_chars."""
    if not work_experience:
        return "Chưa có"
    lines: list[str] = []
    for exp in work_experience:
        parts: list[str] = []
        title = exp.job_title or "Vị trí chuyên môn"
        parts.append(f"- {sanitize_free_text(title)}")
        if exp.company:
            parts.append(f"tại {sanitize_free_text(exp.company)}")
        if exp.duration:
            parts.append(f"({sanitize_free_text(exp.duration)})")
        header = " ".join(parts)
        if exp.description:
            clean_desc = sanitize_free_text(exp.description).replace("\n", " ").strip()
            if clean_desc:
                header += f": {clean_desc[:300]}"
        lines.append(header)
    result = "\n".join(lines)
    return result[:max_chars].strip()


def _build_education_context(education: list[EducationItem], max_chars: int = 1000) -> str:
    """Build grounded, PII-sanitized context for education, limited to max_chars."""
    if not education:
        return "Chưa có"
    lines: list[str] = []
    for edu in education:
        parts: list[str] = []
        degree = edu.degree or "Bằng cấp"
        parts.append(f"- {sanitize_free_text(degree)}")
        if edu.institution:
            parts.append(f"tại {sanitize_free_text(edu.institution)}")
        if edu.field_of_study:
            parts.append(f"ngành {sanitize_free_text(edu.field_of_study)}")
        if edu.graduation_year:
            parts.append(f"(Tốt nghiệp: {sanitize_free_text(edu.graduation_year)})")
        lines.append(" ".join(parts))
    result = "\n".join(lines)
    return result[:max_chars].strip()


def _build_project_context(projects: list[ProjectItem], max_chars: int = 2000) -> str:
    """Build grounded, PII-sanitized context for projects, limited to max_chars."""
    if not projects:
        return "Chưa có"
    lines: list[str] = []
    for proj in projects:
        name = sanitize_free_text(proj.name)
        techs = sanitize_free_text(", ".join(proj.technologies)) if proj.technologies else ""
        header = f"- {name}"
        if techs:
            header += f" (Công nghệ: {techs})"
        if proj.description:
            clean_desc = sanitize_free_text(proj.description).replace("\n", " ").strip()
            if clean_desc:
                header += f": {clean_desc[:300]}"
        lines.append(header)
    result = "\n".join(lines)
    return result[:max_chars].strip()


class CvAnalyzerService:
    """Orchestrates CV document parsing, structured data extraction, and quality evaluation."""

    def __init__(self, parser: DocumentParserPort, llm: LlmPort, settings: Settings | None = None) -> None:
        self.parser = parser
        self.llm = llm
        self.settings = settings or get_settings()

    async def analyze_pdf(self, file_bytes: bytes) -> CvAnalysisResponse:
        """Parse raw PDF document and perform end-to-end CV analysis with multimodal OCR fallback."""
        raw_text = ""
        is_scanned_pdf = False

        try:
            raw_text = await self.parser.parse_pdf(file_bytes)
        except DocumentParsingError as exc:
            if exc.details and exc.details.get("reason") == "empty_or_scanned_pdf":
                is_scanned_pdf = True
            else:
                raise

        enable_ocr = getattr(self.settings, "enable_ocr_fallback", True)
        char_threshold = getattr(self.settings, "ocr_min_char_threshold", 50)

        # Trigger OCR fallback if PDF has no extractable text layer or suspiciously few characters
        if enable_ocr and (is_scanned_pdf or len(raw_text.strip()) < char_threshold):
            logger.info(
                "PDF has insufficient text (%d chars). Attempting multimodal OCR fallback...",
                len(raw_text.strip()),
            )
            try:
                ocr_text = await self.llm.extract_text_from_document(
                    document_bytes=file_bytes,
                    mime_type="application/pdf",
                )
                if ocr_text and len(ocr_text.strip()) > len(raw_text.strip()):
                    raw_text = ocr_text.strip()
                    logger.info("Multimodal OCR fallback succeeded (extracted %d chars)", len(raw_text))
            except Exception as ocr_exc:
                logger.warning("Multimodal OCR fallback failed or not supported: %s", ocr_exc)
                if not raw_text.strip():
                    raise DocumentParsingError(
                        "PDF document contains no extractable text and OCR fallback could not read the document",
                        details={"reason": "empty_or_scanned_pdf", "ocr_error": str(ocr_exc)},
                    ) from ocr_exc

        if not raw_text.strip():
            raise DocumentParsingError(
                "PDF document contains no extractable text (it may be a scanned image)",
                details={"reason": "empty_or_scanned_pdf"},
            )

        return await self.analyze_text(raw_text)

    async def analyze_text(self, raw_text: str) -> CvAnalysisResponse:
        """Extract structured CV from raw text and compute quality score and improvement advice."""
        start_time = time.perf_counter()
        correlation_id = correlation_id_ctx.get()

        # Enforce character safety limit consistently with PDF parsing
        if len(raw_text) > self.settings.max_extracted_text_chars:
            raise DocumentParsingError(
                f"CV text length ({len(raw_text)} characters) exceeds maximum allowed limit of "
                f"{self.settings.max_extracted_text_chars} characters",
                details={
                    "reason": "text_limit_exceeded",
                    "max_chars": self.settings.max_extracted_text_chars,
                    "actual_chars": len(raw_text),
                },
            )

        # 1. LLM Structured Extraction (raw CV text contains candidate profile for entity extraction)
        # NOTE (AI-MATCH-002 Exception): Structured CV extraction requires extracting contact fields
        # (full_name, email, phone) as required by the StructuredCv contract. Thus, this extraction path
        # remains an explicit justified exception where raw CV text is provided to the extraction LLM.
        extract_prompt = CV_EXTRACTION_USER_PROMPT_TEMPLATE_V1.format(raw_cv_text=raw_text)
        structured_cv = await self.llm.generate_structured(
            prompt=extract_prompt,
            response_model=StructuredCv,
            system_prompt=CV_EXTRACTION_SYSTEM_PROMPT_V1,
            temperature=0.0,
        )

        # 2. Deterministic Quality Evaluation (Structural Completeness)
        structural_eval = evaluate_cv_quality(structured_cv.model_dump())

        # 3. Redact PII (full_name, email, phone) before second-stage qualitative LLM evaluation
        clean_summary = sanitize_free_text(structured_cv.career_summary) if structured_cv.career_summary else "Chưa có"
        raw_skills = ", ".join(structured_cv.skills) if structured_cv.skills else "Chưa có"
        clean_skills = sanitize_free_text(raw_skills) if raw_skills != "Chưa có" else "Chưa có"
        raw_certs = ", ".join(structured_cv.certificates) if structured_cv.certificates else "Không có"
        clean_certs = sanitize_free_text(raw_certs) if raw_certs != "Không có" else "Không có"

        exp_ctx = _build_experience_context(structured_cv.work_experience, max_chars=2000)
        edu_ctx = _build_education_context(structured_cv.education, max_chars=1000)
        proj_ctx = _build_project_context(structured_cv.projects, max_chars=2000)

        analysis_prompt = CV_ANALYSIS_USER_PROMPT_TEMPLATE_V1.format(
            career_summary=clean_summary,
            skills=clean_skills,
            work_experience=exp_ctx,
            education=edu_ctx,
            projects=proj_ctx,
            certificates=clean_certs,
            cv_score=structural_eval.cv_score,
        )

        # 4. LLM Qualitative Evaluation returning structured feedback model with graceful fallback
        qualitative_feedback: CvQualitativeFeedback
        try:
            qualitative_feedback = await self.llm.generate_structured(
                prompt=analysis_prompt,
                response_model=CvQualitativeFeedback,
                system_prompt=CV_ANALYSIS_SYSTEM_PROMPT_V1,
                temperature=0.1,
            )
        except Exception as exc:
            logger.warning(
                "Qualitative feedback LLM call failed, falling back to deterministic evaluation: %s",
                exc,
            )
            qualitative_feedback = CvQualitativeFeedback(
                strengths=[],
                weaknesses=[],
                improvement_suggestions=[],
            )

        # 5. Merge deterministic and qualitative feedback independently, preserving order and deduplicating
        def _dedup_preserve_order(items: list[str]) -> list[str]:
            return list(dict.fromkeys(item.strip() for item in items if item.strip()))

        merged_strengths = _dedup_preserve_order(structural_eval.strengths + qualitative_feedback.strengths)
        merged_weaknesses = _dedup_preserve_order(structural_eval.weaknesses + qualitative_feedback.weaknesses)
        merged_suggestions = _dedup_preserve_order(
            structural_eval.improvement_suggestions + qualitative_feedback.improvement_suggestions
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        logger.info(
            "Completed CV analysis (score=%d, strengths=%d, weaknesses=%d, elapsed=%.2fms)",
            structural_eval.cv_score,
            len(merged_strengths),
            len(merged_weaknesses),
            elapsed_ms,
        )

        meta = ResponseMeta(
            algorithm_version="cv-v0",
            prompt_version="v1",
            provider=self.llm.provider_name,
            model=self.llm.model_name,
            processing_time_ms=round(elapsed_ms, 2),
            correlation_id=correlation_id,
        )

        return CvAnalysisResponse(
            structured_cv=structured_cv,
            cv_score=structural_eval.cv_score,
            strengths=merged_strengths,
            weaknesses=merged_weaknesses,
            improvement_suggestions=merged_suggestions,
            meta=meta,
            raw_text=raw_text,
        )
