"""
FastAPI 后端 —— 为 Vue 前端提供 REST API
不修改任何现有代码，仅包装 debate_app
"""
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agent.graph import debate_app

app = FastAPI(title="DecisionPal API", version="1.0.0")

# 允许跨域
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 存储活跃的 thread_id
sessions: dict[str, str] = {}


class StartRequest(BaseModel):
    topic: str


class ReviewRequest(BaseModel):
    thread_id: str
    research_data_a: list[dict]
    research_data_b: list[dict]


class FeedbackRequest(BaseModel):
    thread_id: str
    human_feedback: str


def _get_config(thread_id: str):
    return {"configurable": {"thread_id": thread_id}}


def _state_to_dict(state_values: dict) -> dict:
    """将状态中的复杂对象转为可 JSON 序列化的字典"""
    result = {}
    for k, v in (state_values or {}).items():
        if k == "messages":
            # 消息列表转为字符串列表
            result[k] = [{"role": type(m).__name__, "content": str(m.content)[:500]} for m in v]
        elif isinstance(v, dict):
            result[k] = v
        elif isinstance(v, list):
            result[k] = v
        else:
            result[k] = str(v) if v is not None else ""
    return result


def _get_phase(state, thread_id: str):
    """判断当前所处的阶段"""
    next_nodes = state.next or []
    state_values = state.values or {}

    if len(next_nodes) == 0 and "topic" not in state_values:
        return "input"
    elif "human_filter_1" in next_nodes:
        return "review_research"
    elif "human_filter_2" in next_nodes:
        return "provide_feedback"
    elif len(next_nodes) == 0 and "final_summary" in state_values:
        return "results"
    else:
        return "running"


# ==================== API 路由 ====================

@app.post("/api/session")
def create_session():
    """创建新会话"""
    thread_id = str(uuid.uuid4())
    sessions[thread_id] = thread_id
    return {"thread_id": thread_id, "phase": "input"}


@app.get("/api/state/{thread_id}")
def get_state(thread_id: str):
    """获取当前状态"""
    try:
        config = _get_config(thread_id)
        state = debate_app.get_state(config)
        state_values = _state_to_dict(state.values)
        phase = _get_phase(state, thread_id)

        return {
            "thread_id": thread_id,
            "phase": phase,
            "state": state_values,
            "next_nodes": state.next,
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"会话不存在: {str(e)}")


@app.post("/api/debate/start")
def start_debate(req: StartRequest):
    """启动辩论"""
    thread_id = str(uuid.uuid4())
    config = _get_config(thread_id)

    try:
        debate_app.invoke(
            {"topic": req.topic, "reference_library": []}, config
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动辩论失败: {str(e)}")

    state = debate_app.get_state(config)
    phase = _get_phase(state, thread_id)
    state_values = _state_to_dict(state.values)

    return {
        "thread_id": thread_id,
        "phase": phase,
        "state": state_values,
    }


@app.post("/api/debate/review")
def submit_review(req: ReviewRequest):
    """提交资料审核结果，继续辩论"""
    config = _get_config(req.thread_id)

    try:
        debate_app.update_state(
            config,
            {"research_data_a": req.research_data_a, "research_data_b": req.research_data_b},
            as_node="human_filter_1",
        )
        debate_app.invoke(None, config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提交审核失败: {str(e)}")

    state = debate_app.get_state(config)
    phase = _get_phase(state, req.thread_id)

    return {
        "thread_id": req.thread_id,
        "phase": phase,
        "state": _state_to_dict(state.values),
    }


@app.post("/api/debate/feedback")
def submit_feedback(req: FeedbackRequest):
    """提交人类反馈，生成最终结果"""
    config = _get_config(req.thread_id)

    try:
        debate_app.update_state(
            config,
            {"human_feedback": req.human_feedback},
            as_node="human_filter_2",
        )
        debate_app.invoke(None, config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"提交反馈失败: {str(e)}")

    state = debate_app.get_state(config)
    phase = _get_phase(state, req.thread_id)

    return {
        "thread_id": req.thread_id,
        "phase": phase,
        "state": _state_to_dict(state.values),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
