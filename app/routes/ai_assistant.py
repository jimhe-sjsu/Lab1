from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.ai import AIChatRequest, AIChatResponse
from app.services.ai_service import find_recommendations

router = APIRouter(prefix="/ai-assistant", tags=["AI Assistant"])


@router.post("/chat", response_model=AIChatResponse)
def ai_chat(
    request: AIChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    payload = find_recommendations(
        db=db,
        current_user=current_user,
        message=request.message,
        conversation_history=[item.model_dump() for item in request.conversation_history],
    )
    return AIChatResponse(**payload)
