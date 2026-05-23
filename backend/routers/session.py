from fastapi import APIRouter
from backend.schemas.responses import SessionResponse
from backend.services.session_service import session_store

router = APIRouter(prefix="/api/session", tags=["session"])


@router.post("", response_model=SessionResponse)
async def create_session():
    thread_id = session_store.create()
    return SessionResponse(thread_id=thread_id)
