from typing import TypedDict

class DecisionState(TypedDict):
    user_query: str
    history_context: str
    collected_info: str
    pro_argument: str
    con_argument: str
    final_decision: str