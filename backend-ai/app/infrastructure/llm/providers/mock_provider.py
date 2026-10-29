"""Mock LLM provider for fast unit/integration testing and offline development."""

import re
from typing import Any, TypeVar

from pydantic import BaseModel

from app.ports.llm import LlmPort

T = TypeVar("T", bound=BaseModel)


class MockLlmProvider(LlmPort):
    """Mock LLM implementation that generates realistic deterministic responses without network calls."""

    @property
    def provider_name(self) -> str:
        """Return provider identifier."""
        return "mock"

    @property
    def model_name(self) -> str:
        """Return mock model identifier."""
        return "mock-deterministic"

    async def aclose(self) -> None:
        """No-op cleanup for mock provider."""
        return

    async def generate_text(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.3,
    ) -> str:
        """Generate mock response text based on prompt context."""
        if "<<<BEGIN UNTRUSTED EVALUATION DATA>>>" in prompt:
            job_title_m = re.search(r"Vị trí công việc:\s*([^\n\r]+)", prompt)
            score_m = re.search(r"Điểm phù hợp tổng thể:\s*(\d+)", prompt)
            matched_m = re.search(r"Kỹ năng khớp:\s*([^\n\r]+)", prompt)
            missing_m = re.search(r"Kỹ năng còn thiếu:\s*([^\n\r]+)", prompt)
            exp_cmp_m = re.search(r"Đánh giá kinh nghiệm:\s*([^\n\r]+)", prompt)

            job_title = job_title_m.group(1).strip() if job_title_m else "vị trí tuyển dụng"
            score = int(score_m.group(1)) if score_m else 50
            matched = matched_m.group(1).strip() if matched_m else "Không có"
            missing = missing_m.group(1).strip() if missing_m else "Không có"
            exp_cmp = exp_cmp_m.group(1).strip() if exp_cmp_m else ""

            if score >= 85:
                return (
                    f"Ứng viên có nền tảng vững chắc và độ tương thích rất cao ({score}%) với vị trí {job_title}. "
                    f"Hồ sơ đáp ứng trọn vẹn các kỹ năng cốt lõi bắt buộc ({matched}). "
                    f"{exp_cmp} "
                    f"Ứng viên hoàn toàn tự tin để ứng tuyển và có triển vọng cao vượt qua vòng sơ loại."
                )

            if score >= 50:
                missing_part = (
                    f"còn thiếu các kỹ năng trọng yếu ({missing})"
                    if missing != "Không có"
                    else "cần củng cố thêm kinh nghiệm chuyên sâu"
                )
                return (
                    f"Ứng viên có tiềm năng với vị trí {job_title} (Độ phù hợp: {score}%). "
                    f"Đã đáp ứng một số kỹ năng yêu cầu ({matched}), tuy nhiên {missing_part}. "
                    f"{exp_cmp} "
                    f"Khuyến nghị ứng viên làm nổi bật thêm các dự án thực tế liên quan để tăng sức cạnh tranh."
                )

            return (
                f"Hồ sơ hiện tại có độ tương thích chưa cao ({score}%) so với yêu cầu của vị trí {job_title}. "
                f"Ứng viên còn thiếu các kỹ năng bắt buộc cốt lõi ({missing}). "
                f"{exp_cmp} "
                f"Khuyến nghị ứng viên bổ sung các dự án thực chiến hoặc trau dồi thêm các kỹ năng "
                f"còn thiếu trước khi nộp hồ sơ."
            )

        if "CV Review" in prompt or "phản hồi" in prompt or "đánh giá" in prompt.lower():
            return "Ứng viên có nền tảng vững chắc về kỹ năng công nghệ và dự án thực tế."
        if "giải thích" in prompt.lower() or "phù hợp" in prompt.lower():
            return (
                "Ứng viên đáp ứng tốt các yêu cầu cốt lõi của vị trí tuyển dụng. "
                "Có kinh nghiệm thực tiễn và kỹ năng phù hợp với định hướng công việc."
            )
        return (
            "Chào bạn, tôi là FutureCV Career Assistant. Tôi sẵn sàng hỗ trợ giải đáp mọi thắc mắc sự nghiệp của bạn."
        )

    async def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
        system_prompt: str | None = None,
        temperature: float = 0.1,
    ) -> T:
        """Generate structured response instance conforming to response_model."""
        if response_model.__name__ == "StructuredCv":
            from app.domain.cv.heuristic_extractor import extract_structured_cv_heuristically

            if "<<<BEGIN UNTRUSTED CV DOCUMENT>>>" in prompt:
                start = prompt.find("<<<BEGIN UNTRUSTED CV DOCUMENT>>>") + len("<<<BEGIN UNTRUSTED CV DOCUMENT>>>")
                end = prompt.find("<<<END UNTRUSTED CV DOCUMENT>>>", start)
                raw_cv_text = prompt[start:end].strip() if end != -1 else prompt[start:].strip()
            else:
                raw_cv_text = prompt

            extracted = extract_structured_cv_heuristically(raw_cv_text)
            return response_model.model_validate(extracted.model_dump())

        if response_model.__name__ == "CvQualitativeFeedback":
            return response_model.model_validate(
                {
                    "strengths": [
                        "Hồ sơ trình bày rõ ràng, cấu trúc các phần chuyên nghiệp.",
                        "Kỹ năng chuyên môn cốt lõi phù hợp tốt với định hướng công việc.",
                    ],
                    "weaknesses": [
                        "Cần bổ sung thêm số liệu định lượng (metrics/KPIs) để làm nổi bật tác động của các dự án.",
                    ],
                    "improvement_suggestions": [
                        "Bổ sung các kết quả định lượng cụ thể trong phần mô tả kinh nghiệm và dự án.",
                        "Làm rõ vai trò kỹ thuật chính trong các dự án công nghệ tiêu biểu.",
                    ],
                }
            )

        if response_model.__name__ == "MatchExplanation":
            import re
            m_matched = re.search(r"Matched skills:\s*\n([^\n]+)", prompt)
            m_missing = re.search(r"Missing required skills:\s*\n([^\n]+)", prompt)
            matched_str = m_matched.group(1).strip() if m_matched else ""
            missing_str = m_missing.group(1).strip() if m_missing else ""

            matched_list = [s.strip() for s in matched_str.split(",") if s.strip() and s.strip() != "Không có"]
            missing_list = [s.strip() for s in missing_str.split(",") if s.strip() and s.strip() != "Không có"]

            summary = "Mức độ phù hợp tốt. Ứng viên đáp ứng phần lớn các kỹ năng và yêu cầu của vị trí tuyển dụng."
            if "Mức độ phù hợp thấp" in prompt or "Score band: low" in prompt:
                summary = "Mức độ phù hợp thấp. Ứng viên chưa đáp ứng một số kỹ năng bắt buộc của vị trí."
            elif "Phù hợp một phần" in prompt or "Score band: partial" in prompt:
                summary = (
                    "Phù hợp một phần. Ứng viên đáp ứng một số tiêu chí "
                    "nhưng vẫn còn thiếu hụt các yêu cầu cốt lõi của vị trí."
                )
            elif "Mức độ phù hợp cao" in prompt or "Score band: strong" in prompt:
                summary = (
                    "Mức độ phù hợp cao theo các tiêu chí đã được hệ thống đánh giá. "
                    "Vẫn cần xác minh các yêu cầu chưa có đủ bằng chứng trong CV."
                )

            strengths = []
            for s in matched_list[:3]:
                clean_s = re.sub(r"\s*\((?:preferred|ưu tiên)\)", "", s, flags=re.IGNORECASE).strip()
                strengths.append({
                    "item": clean_s,
                    "statement": f"CV có đề cập kỹ năng {clean_s}.",
                    "evidence_source": "cv.skills",
                    "evidence_text": clean_s,
                })
            gaps = []
            for s in missing_list[:3]:
                clean_s = re.sub(r"\s*\((?:preferred|ưu tiên)\)", "", s, flags=re.IGNORECASE).strip()
                gaps.append({
                    "requirement": clean_s,
                    "statement": f"Chưa đủ bằng chứng về kỹ năng bắt buộc {clean_s}.",
                })

            return response_model.model_validate(
                {
                    "summary": summary,
                    "strengths": strengths,
                    "gaps": gaps,
                    "recommendations": [
                        "Tiếp tục hoàn thiện các kỹ năng chuyên môn cốt lõi."
                    ],
                }
            )

        mock_data: dict[str, Any] = {}
        for field_name, field_info in response_model.model_fields.items():
            annotation = field_info.annotation
            args = getattr(annotation, "__args__", ())
            origin = getattr(annotation, "__origin__", None)

            if annotation is str or (isinstance(annotation, type) and issubclass(annotation, str)):
                mock_data[field_name] = f"Mock {field_name}"
            elif annotation is int:
                mock_data[field_name] = 85
            elif annotation is float:
                mock_data[field_name] = 3.5
            elif origin is list:
                if args and (args[0] is str or (isinstance(args[0], type) and issubclass(args[0], str))):
                    mock_data[field_name] = [f"Mock {field_name} item 1", f"Mock {field_name} item 2"]
                else:
                    mock_data[field_name] = []
            elif origin is dict:
                mock_data[field_name] = {}
            else:
                mock_data[field_name] = None

        return response_model.model_validate(mock_data)

    async def extract_text_from_document(
        self,
        document_bytes: bytes,
        mime_type: str = "application/pdf",
        instruction: str | None = None,
    ) -> str:
        """Mock multimodal document text extraction."""
        return (
            "Nguyễn Văn An\n"
            "Email: nguyenvanan@example.com | Điện thoại: 0912345678\n\n"
            "TÓM TẮT NGHỀ NGHIỆP\n"
            "Kỹ sư phần mềm Fullstack với hơn 3 năm kinh nghiệm phát triển hệ thống web quy mô lớn.\n\n"
            "KINH NGHIỆM LÀM VIỆC\n"
            "Công ty Công nghệ ABC - Senior Backend Developer (2022 - 2024)\n"
            "- Thiết kế và tối ưu kiến trúc Microservices sử dụng Python FastAPI và .NET Core.\n"
            "- Tối ưu hóa cơ sở dữ liệu PostgreSQL và Redis caching giảm 40% độ trễ hệ thống.\n\n"
            "HỌC VẤN\n"
            "Đại học Bách Khoa Hà Nội - Kỹ sư Công nghệ Thông tin (2018 - 2022)\n"
            "- Tốt nghiệp loại Giỏi, GPA 3.6/4.0.\n\n"
            "KỸ NĂNG CHUYÊN MÔN\n"
            "Python, C#, FastAPI, .NET Core, Docker, PostgreSQL, React, TypeScript, Git, Redis."
        )

