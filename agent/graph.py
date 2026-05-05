from langgraph.graph import StateGraph, END
from .state import DecisionState
from .nodes import node_collect_info, node_pro_debater, node_con_debater, node_decision_maker
from redis_memory import memory_saver

workflow = StateGraph(DecisionState)

workflow.add_node("Collect", node_collect_info)
workflow.add_node("Pro_Debate", node_pro_debater)
workflow.add_node("Con_Debate", node_con_debater)
workflow.add_node("Make_Decision", node_decision_maker)

workflow.set_entry_point("Collect")
workflow.add_edge("Collect", "Pro_Debate")
workflow.add_edge("Pro_Debate", "Con_Debate")
workflow.add_edge("Con_Debate", "Make_Decision")
workflow.add_edge("Make_Decision", END)

agent_app = workflow.compile()