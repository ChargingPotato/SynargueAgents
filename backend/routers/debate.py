from fastapi import APIRouter, HTTPException
from backend.schemas.requests import (
    StartDebateRequest,
    ReviewResearchRequest,
    SubmitFeedbackRequest,
)
from backend.schemas.responses import DebateStepResponse
from backend.services.debate_service import debate_service
from backend.services.session_service import session_store

router = APIRouter(prefix="/api/debate", tags=["debate"])


@router.post("/start", response_model=DebateStepResponse)
async def start_debate(req: StartDebateRequest):
    try:
        thread_id, state_dict, phase = await debate_service.start_debate(req.topic)
        session_store._sessions[thread_id] = None  # 注册会话
        return DebateStepResponse(
            thread_id=thread_id,
            phase=phase,
            state=state_dict,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动辩论失败: {str(e)}")


@router.post("/review", response_model=DebateStepResponse)
async def submit_review(req: ReviewResearchRequest):
    if not session_store.exists(req.thread_id):
        raise HTTPException(status_code=404, detail="会话不存在")
    try:
        state_dict, phase = await debate_service.submit_review(
            req.thread_id, req.research_data_a, req.research_data_b
        )
        return DebateStepResponse(
            thread_id=req.thread_id,
            phase=phase,
            state=state_dict,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提交审核失败: {str(e)}")


@router.post("/feedback", response_model=DebateStepResponse)
async def submit_feedback(req: SubmitFeedbackRequest):
    if not session_store.exists(req.thread_id):
        raise HTTPException(status_code=404, detail="会话不存在")
    try:
        state_dict, phase = await debate_service.submit_feedback(
            req.thread_id, req.human_feedback
        )
        return DebateStepResponse(
            thread_id=req.thread_id,
            phase=phase,
            state=state_dict,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提交反馈失败: {str(e)}")
