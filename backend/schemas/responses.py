from pydantic import BaseModel
from .enums import DebatePhase


class SessionResponse(BaseModel):
    thread_id: str
    phase: DebatePhase = DebatePhase.INPUT


class StateResponse(BaseModel):
    thread_id: str
    phase: DebatePhase
    state: dict
    next_nodes: list[str] = []


class DebateStepResponse(BaseModel):
    thread_id: str
    phase: DebatePhase
    state: dict
    next_nodes: list[str] = []


class ErrorResponse(BaseModel):
    detail: str
    phase: DebatePhase | None = None
