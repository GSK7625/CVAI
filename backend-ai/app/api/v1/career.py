"""Endpoints for Career Assistant conversational counseling."""

from fastapi import APIRouter, Depends, status

from app.api.deps import get_career_assistant_service, verify_internal_api_key
from app.application.career_assistant import CareerAssistantService
from app.contracts.career import CareerAssistantRequest, CareerAssistantResponse

router = APIRouter(
    prefix="/career",
    tags=["Career Assistant"],
    dependencies=[Depends(verify_internal_api_key)],
)


@router.post(
    "/chat",
    response_model=CareerAssistantResponse,
    status_code=status.HTTP_200_OK,
    summary="Chat with Career Assistant using candidate and job context",
)
async def career_chat(
    req: CareerAssistantRequest,
    service: CareerAssistantService = Depends(get_career_assistant_service),
) -> CareerAssistantResponse:
    """
    Conversational career counseling endpoint.
    Consumes authorized context (CV, Job, MatchResult) provided by ASP.NET Core
    to guide candidates on overcoming skill gaps and CV improvements.
    """
    return await service.chat(req)
