import json
from .state import ArgumentState
from .models import analyzer_llm, research_llm, debater_llm

def analyzer_node(state: ArgumentState):
    """一级论证：分析问题，分为两派"""
    topic = state.get("topic")
    prompt = f"辩题：{topic}。请将其拆分为对立的两派，返回JSON：{{\"side_a\": \"正方观点\", \"side_b\": \"反方观点\"}}"
    # 实际开发中建议使用 Structured Output 强制返回 JSON
    response = analyzer_llm.invoke(prompt)
    try:
        sides = json.loads(response.content.strip('```json\n').strip('```'))
    except:
        sides = {"side_a": "支持", "side_b": "反对"}
    return {"sides": sides}

def research_node(state: ArgumentState):
    """两个agent分别搜集有利资料"""
    topic = state.get("topic")
    sides = state.get("sides", {})
    
    # 模拟并行搜索 (实际可用 asyncio.gather 优化并发)
    # 此处省略具体 Prompt 和 JSON 解析，直接模拟返回结构
    data_a = [{"source": "网络", "content": f"支持 {sides.get('side_a')} 的证据1", "valid": True}]
    data_b = [{"source": "网络", "content": f"支持 {sides.get('side_b')} 的证据1", "valid": True}]
    
    return {"research_data_a": data_a, "research_data_b": data_b}

def verifier_node(state: ArgumentState):
    """第三方Agent进行资料验真打分"""
    data_a = state.get("research_data_a", [])
    # 模拟大模型打分
    for item in data_a:
        item["score"] = 5  # LLM 评估后的分数
    return {"research_data_a": data_a}

def human_filter_1_node(state: ArgumentState):
    """人工介入点 1：判断资料有效性 (空节点，仅用于挂起)"""
    print("--- 等待人工审核搜索资料 ---")
    return {}

def argument_node(state: ArgumentState):
    """根据有效资料进行分析论述"""
    sides = state.get("sides", {})
    # 仅使用人工确认 valid=True 的数据
    valid_a = [d for d in state.get("research_data_a", []) if d.get("valid")]
    
    prompt_a = f"你是正方({sides.get('side_a')})，基于资料 {valid_a} 展开论述。"
    arg_a = debater_llm.invoke(prompt_a).content
    
    return {"arguments": {"side_a": arg_a, "side_b": "反方论述省略..."}}

def rebuttal_node(state: ArgumentState):
    """二级反驳：针对对方论点和资料进行反驳"""
    args = state.get("arguments", {})
    prompt = f"反驳对方的观点：{args.get('side_b')}"
    rebut_a = debater_llm.invoke(prompt).content
    return {"rebuttals": {"side_a_rebut_b": rebut_a, "side_b_rebut_a": "反驳A..."}}

def human_filter_2_node(state: ArgumentState):
    """人工介入点 2：判断反驳合理性 (空节点，仅用于挂起)"""
    print("--- 等待人工审核反驳意见 ---")
    return {}

def refine_node(state: ArgumentState):
    """结合反驳和人工反馈，重新论述"""
    feedback = state.get("human_feedback", "")
    return {"arguments": {"side_a": f"修正后的正方论述 (采纳了建议：{feedback})", "side_b": "修正后的反方论述"}}

def summary_node(state: ArgumentState):
    """三级总结论证：输出最终倾向度"""
    topic = state.get("topic")
    return {
        "final_summary": f"关于 {topic} 的最终辩论总结...",
        "tendency_score": {"side_a": 0.7, "side_b": 0.3}
    }