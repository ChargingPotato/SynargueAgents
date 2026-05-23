def state_to_dict(state_values: dict | None) -> dict:
    """将状态中的复杂对象转为可 JSON 序列化的字典"""
    if not state_values:
        return {}
    result = {}
    for key, value in state_values.items():
        if key in ("messages", "messages_a", "messages_b"):
            result[key] = [
                {"role": type(m).__name__, "content": str(m.content)[:500]}
                for m in value
            ]
        elif isinstance(value, (dict, list)):
            result[key] = value
        else:
            result[key] = str(value) if value is not None else ""
    return result


def determine_phase(state) -> str:
    """从图状态推导当前阶段"""
    next_nodes = state.next or []
    values = state.values or {}

    if len(next_nodes) == 0 and "topic" not in values:
        return "input"
    if "human_filter_1" in next_nodes:
        return "review_research"
    if "human_filter_2" in next_nodes:
        return "provide_feedback"
    if len(next_nodes) == 0 and "final_summary" in values:
        return "results"
    return "researching"
