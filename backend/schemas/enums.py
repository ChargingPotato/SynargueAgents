from enum import StrEnum


class DebatePhase(StrEnum):
    INPUT = "input"
    RESEARCHING = "researching"
    RUNNING = "running"
    REVIEW_RESEARCH = "review_research"
    PROVIDE_FEEDBACK = "provide_feedback"
    RESULTS = "results"
    ERROR = "error"
