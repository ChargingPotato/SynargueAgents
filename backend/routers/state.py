from fastapi import APIRouter, HTTPException
from backend.schemas.responses import StateResponse
from backend.services.debate_service import debate_service
from backend.services.session_service import session_store

router = APIRouter(prefix="/api/state", tags=["state"])


@router.get("/{thread_id}", response_model=StateResponse)
async def get_state(thread_id: str):
    if not session_store.exists(thread_id):
        raise HTTPException(status_code=404, detail="会话不存在")
    try:
        state_dict, phase = debate_service.get_current_state(thread_id)
        return StateResponse(
            thread_id=thread_id,
            phase=phase,
            state=state_dict,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
