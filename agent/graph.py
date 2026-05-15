# graph.py
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import tools_condition
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

def build_debate_graph():
    """
    构建并编译带有多重人工中断的辩论图结构
    """
    # 1. 实例化图容器，绑定 ArgumentState 状态蓝图
    workflow = StateGraph(ArgumentState)

    # 2. 注册所有的业务节点
    workflow.add_node("analyze", analyzer_node)
    #workflow.add_node("research", research_node)

    workflow.add_node("research_a", research_node_a)
    workflow.add_node("search_tools_a", search_tools_a_node)
    workflow.add_node("research_b", research_node_b)
    workflow.add_node("search_tools_b", search_tools_b_node)    

    workflow.add_node("verify", verifier_node)
    workflow.add_node("human_filter_1", human_filter_1_node) # 第一次中断点：资料审核
    workflow.add_node("argue", argument_node)
    
    workflow.add_node("rebuttal", rebuttal_node)
    workflow.add_node("human_filter_2", human_filter_2_node) # 第二次中断点：反驳反馈
    workflow.add_node("refine", refine_node)
    
    workflow.add_node("summarize", summary_node)

    #条件边
    workflow.add_conditional_edges(
        "research_a",
        tools_condition,
        {
            "tools": "search_tools_a", # 如果 A 要搜集资料，去 A 的工具箱
            END: "research_b"          # 【关键】如果 A 觉得搜够了，把接力棒传给 B
        }
    )
    workflow.add_edge("search_tools_a", "research_a")

    workflow.add_conditional_edges(
        "research_b",
        tools_condition,
        {
            "tools": "search_tools_b", # 如果 B 要搜集资料，去 B 的工具箱
            END: "verify"              # 【关键】如果 B 觉得搜够了，双方情报搜集完毕，进入第三方验真
        }
    )
    workflow.add_edge("search_tools_b", "research_b")

    # 3. 编排完整的工作流转路径
    workflow.set_entry_point("analyze")
    workflow.add_edge("analyze", "research_a")
    workflow.add_edge("analyze", "research_b")
    workflow.add_edge("research_b", "verify")
    workflow.add_edge("verify", "human_filter_1")
    workflow.add_edge("human_filter_1", "argue")
    workflow.add_edge("argue", "rebuttal")
    workflow.add_edge("rebuttal", "human_filter_2")
    workflow.add_edge("human_filter_2", "refine")
    workflow.add_edge("refine", "summarize")
    workflow.add_edge("summarize", END)

    # ==========================================
    # 4. 核心：引入持久化记忆载体
    # ==========================================
    # MemorySaver() 会在内存中记录每一步的 State。
    # 当图被中断挂起时，Streamlit 刷新也不会丢失这些数据。
    memory = MemorySaver()

    # 5. 编译，并设置两次中断拦截
    app = workflow.compile(
        checkpointer=memory,
        interrupt_before=["human_filter_1", "human_filter_2"]
    )
    
    return app

# 提供一个编译好的单例实例，供 app.py 直接 import 并在前端调用
debate_app = build_debate_graph()