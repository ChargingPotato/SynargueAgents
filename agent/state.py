from typing import Annotated, List, TypedDict, Dict
from langgraph.graph.message import add_messages

class ArgumentState(TypedDict):
    # 核心元数据
    topic: str
    reference_library: List[str]  # 主题库参考资料

    # 派系观点
    sides: Dict[str, str] # {"side_a": "观点A", "side_b": "观点B"}

    # 资料收集与验证
    # 存储格式: {"source": "...", "content": "...", "score": 5, "valid": True/False}
    research_data_a: List[Dict]
    research_data_b: List[Dict]

    # 论述内容
    arguments: Dict[str, str] # {"side_a": "论点内容", "side_b": "论点内容"}
    rebuttals: Dict[str, str] # {"side_a_rebut_b": "...", "side_b_rebut_a": "..."}

    # 人工干预反馈
    human_feedback: str

    # 最终总结
    final_summary: str
    tendency_score: Dict[str, float] # {"side_a": 0.6, "side_b": 0.4}

    # 搜索迭代计数 (限制每方最多搜索3次)
    search_count_a: int
    search_count_b: int

    # 实时进度消息 (供前端展示当前运行阶段)
    progress_message: str

    # 消息流（用于记录Agent对话历史）
    messages_a: Annotated[list, add_messages]
    messages_b: Annotated[list, add_messages]