"""Career Assistant application service orchestrating conversational career guidance."""

import time

from app.application.text_sanitization import sanitize_free_text
from app.contracts.career import CareerAssistantRequest, CareerAssistantResponse
from app.contracts.common import ResponseMeta
from app.domain.matching.experience_match import calculate_total_experience_years
from app.observability.logging import correlation_id_ctx, get_logger
from app.ports.llm import LlmPort
from app.prompts.career_v1 import (
    CAREER_ASSISTANT_SYSTEM_PROMPT_V1,
    CAREER_ASSISTANT_USER_TEMPLATE_V1,
)

logger = get_logger(__name__)


class CareerAssistantService:
    """Conversational career guidance layer consuming authorized context provided by ASP.NET Core."""

    def __init__(self, llm: LlmPort) -> None:
        self.llm = llm

    async def chat(self, req: CareerAssistantRequest) -> CareerAssistantResponse:
        """Process candidate inquiry with minimal context and delimited conversation history."""
        start_time = time.perf_counter()
        correlation_id = correlation_id_ctx.get()

        # Build minimal career context (PII minimized: no candidate_id, full name, email, or phone;
        # free text is deterministically sanitized for email and phone redaction)
        context_parts: list[str] = []
        if req.context:
            if req.context.cv:
                cv = req.context.cv
                if cv.career_summary:
                    clean_summary = sanitize_free_text(cv.career_summary)
                    if clean_summary:
                        context_parts.append(f"Tóm tắt định hướng: {clean_summary}")
                if cv.skills:
                    clean_skills = [sanitize_free_text(s) for s in cv.skills if s and s.strip()]
                    clean_skills = [s for s in clean_skills if s]
                    if clean_skills:
                        context_parts.append(f"Kỹ năng ứng viên: {', '.join(clean_skills)}")
                years = calculate_total_experience_years(cv.work_experience)
                if years > 0:
                    context_parts.append(f"Tổng số năm kinh nghiệm: {years:.1f} năm")
            if req.context.job:
                job = req.context.job
                clean_title = sanitize_free_text(job.title)
                if clean_title:
                    context_parts.append(f"Vị trí công việc đang quan tâm: {clean_title}")
                if job.required_skills:
                    clean_req = [sanitize_free_text(s) for s in job.required_skills if s and s.strip()]
                    clean_req = [s for s in clean_req if s]
                    if clean_req:
                        context_parts.append(f"Kỹ năng yêu cầu: {', '.join(clean_req)}")
                if job.preferred_skills:
                    clean_pref = [sanitize_free_text(s) for s in job.preferred_skills if s and s.strip()]
                    clean_pref = [s for s in clean_pref if s]
                    if clean_pref:
                        context_parts.append(f"Kỹ năng ưu tiên: {', '.join(clean_pref)}")
                if job.description:
                    clean_job_desc = sanitize_free_text(job.description)
                    if clean_job_desc:
                        context_parts.append(f"Mô tả công việc: {clean_job_desc}")
            if req.context.match_result:
                mr = req.context.match_result
                context_parts.append(f"Điểm phù hợp hiện tại: {mr.match_score}/100")
                if mr.matched_skills:
                    clean_matched = [sanitize_free_text(s) for s in mr.matched_skills if s and s.strip()]
                    clean_matched = [s for s in clean_matched if s]
                    if clean_matched:
                        context_parts.append(f"Kỹ năng đã khớp: {', '.join(clean_matched)}")
                if mr.missing_skills:
                    clean_missing = [sanitize_free_text(s) for s in mr.missing_skills if s and s.strip()]
                    clean_missing = [s for s in clean_missing if s]
                    if clean_missing:
                        context_parts.append(f"Kỹ năng còn thiếu: {', '.join(clean_missing)}")
                if mr.experience_comparison:
                    clean_exp_cmp = sanitize_free_text(mr.experience_comparison)
                    if clean_exp_cmp:
                        context_parts.append(f"Đánh giá kinh nghiệm: {clean_exp_cmp}")
                if mr.education_comparison:
                    clean_edu_cmp = sanitize_free_text(mr.education_comparison)
                    if clean_edu_cmp:
                        context_parts.append(f"Đánh giá học vấn: {clean_edu_cmp}")
                if mr.project_domain_relevance:
                    clean_proj_rel = sanitize_free_text(mr.project_domain_relevance)
                    if clean_proj_rel:
                        context_parts.append(f"Độ phù hợp dự án: {clean_proj_rel}")
                if mr.match_explanation:
                    clean_mr_exp = sanitize_free_text(mr.match_explanation)
                    if clean_mr_exp:
                        context_parts.append(f"Giải thích kết quả khớp: {clean_mr_exp}")

        context_str = "\n".join(context_parts) if context_parts else "Không có thông tin hồ sơ bổ sung."

        # Format delimited conversation history (sanitizing content for email and phone numbers)
        history_parts = [f"[{msg.role}]: {sanitize_free_text(msg.content)}" for msg in req.history[-10:]]
        chat_history_str = "\n".join(history_parts) if history_parts else "Chưa có lượt trò chuyện trước đó."

        prompt = CAREER_ASSISTANT_USER_TEMPLATE_V1.format(
            context_str=context_str,
            chat_history_str=chat_history_str,
            user_message=sanitize_free_text(req.message),
        )

        reply = await self.llm.generate_text(
            prompt=prompt,
            system_prompt=CAREER_ASSISTANT_SYSTEM_PROMPT_V1,
            temperature=0.4,
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        followups = [
            "Làm thế nào để bổ sung các kỹ năng còn thiếu vào CV hiệu quả?",
            "Gợi ý cho tôi cách viết Cover Letter gây ấn tượng cho vị trí này.",
            "Lộ trình học tập đề xuất để nâng cao điểm phù hợp là gì?",
        ]

        logger.info("Career assistant answered query (len=%d, elapsed=%.2fms)", len(reply), elapsed_ms)

        meta = ResponseMeta(
            algorithm_version="career-v0",
            prompt_version="v1",
            provider=self.llm.provider_name,
            model=self.llm.model_name,
            processing_time_ms=round(elapsed_ms, 2),
            correlation_id=correlation_id,
        )

        return CareerAssistantResponse(
            reply=reply,
            suggested_followups=followups,
            meta=meta,
        )
