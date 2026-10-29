"""Endpoints for CV Analysis and Quality Evaluation."""

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status

from app.api.deps import get_cv_analyzer_service, get_settings_dep, verify_internal_api_key
from app.application.cv_analyzer import CvAnalyzerService
from app.contracts.cv_analysis import CvAnalysisContentRequest, CvAnalysisResponse
from app.core.config import Settings
from app.core.exceptions import DocumentSizeLimitExceededError

router = APIRouter(
    prefix="/cv",
    tags=["CV Analyzer"],
    dependencies=[Depends(verify_internal_api_key)],
)

UPLOAD_CHUNK_SIZE = 64 * 1024  # 64 KB chunks for bounded stream processing


@router.post(
    "/analyze",
    response_model=CvAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload PDF CV or send raw text for structured extraction and quality scoring",
)
async def analyze_cv_file(
    file: UploadFile = File(..., description="PDF format CV file"),
    service: CvAnalyzerService = Depends(get_cv_analyzer_service),
    settings: Settings = Depends(get_settings_dep),
) -> CvAnalysisResponse:
    """
    CV Analyzer pipeline:
    1. Validate document format and media type.
    2. Stream upload in bounded 64KB chunks up to max limit (prevents memory DoS).
    3. Extract text with page and character safety constraints.
    4. Extract structured CV entities using LLM.
    5. Deterministically score completeness and generate qualitative improvement advice.
    """
    is_pdf_content_type = file.content_type == "application/pdf"
    is_pdf_extension = bool(file.filename and file.filename.lower().endswith(".pdf"))

    if not is_pdf_content_type and not is_pdf_extension:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF documents are supported for CV analysis",
        )

    # Bounded chunked reading to prevent memory exhaustion DoS
    buffer = bytearray()
    max_bytes = settings.max_upload_size_bytes

    while chunk := await file.read(UPLOAD_CHUNK_SIZE):
        buffer.extend(chunk)
        if len(buffer) > max_bytes:
            raise DocumentSizeLimitExceededError(
                max_size_bytes=max_bytes,
                actual_size_bytes=len(buffer),
            )

    return await service.analyze_pdf(bytes(buffer))


@router.post(
    "/analyze-text",
    response_model=CvAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze trusted pre-extracted CV text directly",
)
async def analyze_cv_text(
    req: CvAnalysisContentRequest,
    service: CvAnalyzerService = Depends(get_cv_analyzer_service),
) -> CvAnalysisResponse:
    """Analyze pre-extracted CV text content provided directly by ASP.NET Core."""
    return await service.analyze_text(req.raw_text)


@router.post(
    "/improve",
    response_model=CvAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Compatibility endpoint: Evaluate CV and return concrete improvement suggestions",
)
async def improve_cv(
    req: CvAnalysisContentRequest,
    service: CvAnalyzerService = Depends(get_cv_analyzer_service),
) -> CvAnalysisResponse:
    """
    Compatibility alias for CV improvement.
    CV improvement is part of CvAnalysis and returns quality score with actionable suggestions.
    """
    return await service.analyze_text(req.raw_text)
