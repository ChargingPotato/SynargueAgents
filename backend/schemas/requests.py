from pydantic import BaseModel, Field


class StartDebateRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=500)


class ReviewResearchRequest(BaseModel):
    thread_id: str = Field(..., min_length=1)
    research_data_a: list[dict] = Field(default_factory=list)
    research_data_b: list[dict] = Field(default_factory=list)


class SubmitFeedbackRequest(BaseModel):
    thread_id: str = Field(..., min_length=1)
    human_feedback: str = Field(default="", max_length=2000)
