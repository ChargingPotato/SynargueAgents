# graph.py
from functools import partial
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import tools_condition
from .redis_memory import sync_saver, async_saver
# 导入你定义的全局状态
from .state import ArgumentState

# 导入你在 node.py 中写好的具体执行逻辑
from .nodes import (
    analyzer_node,  
    verifier_node, 
    human_filter_1_node,
    argument_node, 
    rebuttal_node, 
    human_filter_2_node, 
    refine_node, 
    summary_node,
    research_node_a,        # 引入正方搜索
    search_tools_a_node,    # 引入正方工具
    research_node_b,        # 引入反方搜索
    search_tools_b_node,    # 引入反方工具
)

tools_condition_a = partial(tools_condition, messages_key="messages_a")
tools_condition_b = partial(tools_condition, messages_key="messages_b")

def build_debate_graph(checkpointer=None):
    """构建并编译带有多重人工中断的辩论图结构

    checkpointer: sync_saver（网关）或 async_saver（Worker），默认 sync_saver
    """
    if checkpointer is None:
        checkpointer = sync_saver

    workflow = StateGraph(ArgumentState)

    workflow.add_node("analyze", analyzer_node)
    workflow.add_node("research_a", research_node_a)
    workflow.add_node("search_tools_a", search_tools_a_node)
    workflow.add_node("research_b", research_node_b)
    workflow.add_node("search_tools_b", search_tools_b_node)
    workflow.add_node("verify", verifier_node)
    workflow.add_node("human_filter_1", human_filter_1_node)
    workflow.add_node("argue", argument_node)
    workflow.add_node("rebuttal", rebuttal_node)
    workflow.add_node("human_filter_2", human_filter_2_node)
    workflow.add_node("refine", refine_node)
    workflow.add_node("summarize", summary_node)

    workflow.add_conditional_edges(
        "research_a",
        tools_condition_a,
        {"tools": "search_tools_a", END: "research_b"}
    )
    workflow.add_edge("search_tools_a", "research_a")

    workflow.add_conditional_edges(
        "research_b",
        tools_condition_b,
        {"tools": "search_tools_b", END: "verify"}
    )
    workflow.add_edge("search_tools_b", "research_b")

    workflow.set_entry_point("analyze")
    workflow.add_edge("analyze", "research_a")
    workflow.add_edge("verify", "human_filter_1")
    workflow.add_edge("human_filter_1", "argue")
    workflow.add_edge("argue", "rebuttal")
    workflow.add_edge("rebuttal", "human_filter_2")
    workflow.add_edge("human_filter_2", "refine")
    workflow.add_edge("refine", "summarize")
    workflow.add_edge("summarize", END)

    app = workflow.compile(
        checkpointer=checkpointer,
        interrupt_before=["human_filter_1", "human_filter_2"]
    )
    return app


# 网关使用同步版 (update_state / get_state 主线程安全)
debate_app = build_debate_graph(checkpointer=sync_saver)


def get_async_debate_app():
    """Worker 使用异步版 (ainvoke / astream)"""
    return build_debate_graph(checkpointer=async_saver)