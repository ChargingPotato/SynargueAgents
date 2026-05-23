import json
import traceback
from datetime import datetime
from .state import ArgumentState
from .models import analyzer_llm, research_llm, debater_llm, research_llm_with_tools
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import ToolNode
from .tools import agent_tools

# ==========================================
# 搜索迭代上限
# ==========================================
MAX_SEARCH_ITERATIONS = 3


def _ts() -> str:
    """返回带时间戳的前缀，方便日志追踪"""
    return f"[{datetime.now().strftime('%H:%M:%S')}]"



async def analyzer_node(state: ArgumentState):
    """[节点 1/9] 分析问题，拆分为正反两派"""
    print(f"{_ts()} 📋 [analyze] 正在分析问题...")
    topic = state.get("topic")
    try:
        prompt = f"话题：{topic}。请将其拆分为对立的两个简洁观点，返回JSON：{{\"side_a\": \"正方观点\", \"side_b\": \"反方观点\"}}"
        response = await analyzer_llm.ainvoke(prompt)
        sides = json.loads(response.content.strip('```json\n').strip('```'))
        print(f"{_ts()} ✅ [analyze] 题目拆分完成: 正方={sides.get('side_a')}, 反方={sides.get('side_b')}")
    except Exception as e:
        print(f"{_ts()} ⚠️ [analyze] JSON解析失败({e})，使用默认观点")
        sides = {"side_a": "支持", "side_b": "反对"}
    return {
        "sides": sides,
        "progress_message": f"✅ 题目分析完成 → 正方: {sides.get('side_a', '支持')} | 反方: {sides.get('side_b', '反对')}"
    }


# ==========================================
# 实例化两个独立的工具执行节点
# ==========================================
search_tools_a_node = ToolNode(agent_tools, messages_key="messages_a")
search_tools_b_node = ToolNode(agent_tools, messages_key="messages_b")


# ==========================================
# 通用搜索节点工厂函数
# ==========================================
async def _research_node(
    state: ArgumentState,
    side_label: str,
    side_key: str,
    count_key: str,
    data_key: str,
    role_intro: str,
    opposite_label: str,
    messages_key: str,
):
    """
    通用搜索节点：限制最多 MAX_SEARCH_ITERATIONS 次搜索，超限后强制汇总。
    """
    topic = state.get("topic")
    sides = state.get("sides", {})
    messages = state.get(messages_key, [])
    count = state.get(count_key, 0) + 1

    print(f"{_ts()} 🔍 [{side_label}] 进入搜索节点 (第 {count} 次)")

    # --- 首次进入时注入角色 ---
    if not any(role_intro in msg.content for msg in messages if isinstance(msg, HumanMessage)):
        system_prompt = (
            f"[{role_intro}]\n话题：{topic}。\n你的立场是：支持【{side_label}】({sides.get(side_key)})。\n"
            f"请使用网络搜索工具，寻找对{side_label}有利的数据资料。搜集完成后，整理调查结果。"
        )
        messages.append(HumanMessage(content=system_prompt))
        print(f"{_ts()} 📝 [{side_label}] 已注入角色提示词")

    # --- 核心：超过搜索上限，强制汇总 ---
    if count > MAX_SEARCH_ITERATIONS:
        print(f"{_ts()} ⛔ [{side_label}] 搜索已达上限 ({MAX_SEARCH_ITERATIONS}次)，强制汇总")
        force_prompt = HumanMessage(
            content=f"你已达到搜索次数上限({MAX_SEARCH_ITERATIONS}次)。请立即基于已有的搜索结果，"
            f"整理出对{side_label}有利的论据报告。不要尝试继续搜索。"
        )
        response = await research_llm.ainvoke(messages + [force_prompt])
        data = await _extract_json(response, side_label, data_key)
        return {
            messages_key: [response],
            data_key: data,
            count_key: count,
            "progress_message": f"⛔ {side_label}资料搜集完成 (已达{MAX_SEARCH_ITERATIONS}次搜索上限)"
        }

    # --- 正常调用 (带工具) ---
    try:
        response = await research_llm_with_tools.ainvoke(messages)
    except Exception as e:
        print(f"{_ts()} ❌ [{side_label}] LLM调用失败: {e}")
        traceback.print_exc()
        return {
            messages_key: [HumanMessage(content=f"[系统错误] {side_label}搜索调用失败: {e}")],
            count_key: count,
            "progress_message": f"❌ {side_label}搜索出错: {str(e)[:80]}"
        }

    # --- 没有工具调用 = 搜索完成 ---
    if not response.tool_calls:
        print(f"{_ts()} ✅ [{side_label}] 搜索完毕 (共 {count} 轮)，正在提取 JSON...")
        data = await _extract_json(response, side_label, data_key)
        return {
            messages_key: [response],
            data_key: data,
            count_key: count,
            "progress_message": f"✅ {side_label}资料搜集完成 (共 {count} 轮搜索, {len(data)} 条资料)"
        }

    # --- 还有工具调用 = 继续搜索 ---
    tool_names = [tc.get("name", "?") for tc in response.tool_calls]
    print(f"{_ts()} 🔄 [{side_label}] 第 {count} 轮调用工具: {tool_names}")
    return {
        messages_key: [response],
        count_key: count,
        "progress_message": f"🔍 {side_label}正在进行第 {count} 轮网络搜索..."
    }


async def _extract_json(response, side_label: str, data_key: str) -> list:
    """从 LLM 响应中提取结构化 JSON 资料"""
    extract_prompt = (
        f"请从以下报告中提取对{side_label}有利的证据，严格返回 JSON 数组格式（不要包含任何其他文本）：\n"
        f"[{{\"source\": \"资料来源(若无则写网络)\", \"content\": \"具体的论据内容\"}}]\n\n"
        f"报告内容：\n{response.content}"
    )
    try:
        json_response = await analyzer_llm.ainvoke([HumanMessage(content=extract_prompt)])
        clean_json = json_response.content.strip('```json\n').strip('```').strip()
        data = json.loads(clean_json)
        print(f"{_ts()} 📊 [{side_label}] JSON 提取成功: {len(data)} 条")
        return data
    except Exception as e:
        print(f"{_ts()} ⚠️ [{side_label}] JSON解析失败({e})，使用原始内容兜底")
        traceback.print_exc()
        return [{"source": f"{side_label}搜索报告", "content": str(response.content)[:2000]}]


# ==========================================
# Agent A (正方) 搜索节点
# ==========================================
async def research_node_a(state: ArgumentState):
    return await _research_node(
        state,
        side_label="正方",
        side_key="side_a",
        count_key="search_count_a",
        data_key="research_data_a",
        role_intro="我是正方情报官",
        opposite_label="反方",
        messages_key="messages_a",
    )


# ==========================================
# Agent B (反方) 搜索节点
# ==========================================
async def research_node_b(state: ArgumentState):
    return await _research_node(
        state,
        side_label="反方",
        side_key="side_b",
        count_key="search_count_b",
        data_key="research_data_b",
        role_intro="我是反方情报官",
        opposite_label="正方",
        messages_key="messages_b",
    )

async def verifier_node(state: ArgumentState):
    """
    [节点 4/9] 第三方 Agent 进行资料验真打分。
    """
    print(f"{_ts()} ⚖️ [verify] 裁判开始对双方资料逐条验真打分...")
    topic = state.get("topic", "未知辩题")
    data_a = state.get("research_data_a", [])
    data_b = state.get("research_data_b", [])

    async def evaluate_evidence(evidence_list, side_name):
        verified_list = []
        for idx, item in enumerate(evidence_list):
            content = item.get("content", "")
            source = item.get("source", "未知来源")
            print(f"{_ts()}   📝 [verify] 正在评估{side_name}第{idx+1}条: {source[:30]}...")

            prompt = (
                f"当前辩题：{topic}。\n"
                f"以下是一条支持【{side_name}】的论据资料：\n"
                f"资料来源：{source}\n"
                f"资料内容：{content}\n\n"
                f"请作为客观的中立裁判，对这条资料的有效性和说服力进行打分（1-5分）。\n"
                f"评分标准：\n"
                f"5分：来源极其权威，数据详实，逻辑严密，具有决定性说服力。\n"
                f"4分：来源可靠，有具体的数据或事实支撑。\n"
                f"3分：普通观点或二手来源，有一定的参考价值。\n"
                f"2分：缺乏具体数据，逻辑牵强。\n"
                f"1分：来源不明，充满主观臆断、事实错误或逻辑漏洞。\n\n"
                f"请严格按照要求：仅输出一个纯数字（1, 2, 3, 4, 5），绝对不要输出任何标点符号、解释或其他文本。"
            )

            llm_response = None
            try:
                llm_response = await analyzer_llm.ainvoke([HumanMessage(content=prompt)])
                score_text = llm_response.content.strip()
                score = int(score_text)
                score = max(1, min(5, score))
            except Exception as e:
                raw = llm_response.content if llm_response else '<LLM未响应>'
                print(f"{_ts()} ⚠️ [verify] {side_name}第{idx+1}条打分失败({e})，原始输出: {raw}")
                score = 3

            item["score"] = score
            item["valid"] = True
            verified_list.append(item)

        return verified_list

    if data_a:
        print(f"{_ts()} 📊 [verify] 正方资料 {len(data_a)} 条，开始逐条评估...")
        verified_a = await evaluate_evidence(data_a, "正方")
    else:
        verified_a = []

    if data_b:
        print(f"{_ts()} 📊 [verify] 反方资料 {len(data_b)} 条，开始逐条评估...")
        verified_b = await evaluate_evidence(data_b, "反方")
    else:
        verified_b = []

    print(f"{_ts()} ✅ [verify] 验真完成: 正方{len(verified_a)}条, 反方{len(verified_b)}条")
    return {
        "research_data_a": verified_a,
        "research_data_b": verified_b,
        "progress_message": f"✅ 资料验真打分完成 (正方{len(verified_a)}条 / 反方{len(verified_b)}条)"
    }


async def human_filter_1_node(state: ArgumentState):
    """[节点 5/9] 人工介入点 1：资料审核 (空节点，仅用于挂起)"""
    print(f"{_ts()} ⏸️ [human_filter_1] 流程暂停，等待人工审核搜索资料...")
    return {
        "progress_message": "⏸️ 资料搜集与验真完成，请人类裁判审核并筛选资料"
    }


async def argument_node(state: ArgumentState):
    """
    [节点 6/9] 一级论证：双方根据有效资料展开立论。
    """
    print(f"{_ts()} 🗣️ [argue] 双方辩手开始一级立论...")
    topic = state.get("topic", "未知辩题")
    sides = state.get("sides", {})
    valid_a = [d for d in state.get("research_data_a", []) if d.get("valid")]
    valid_b = [d for d in state.get("research_data_b", []) if d.get("valid")]

    try:
        prompt_a = (
            f"当前辩题：{topic}。\n你是正方一辩，核心立场：【{sides.get('side_a')}】。\n"
            f"请基于以下经过验证的资料展开『一级论述』：\n{valid_a}\n\n"
            f"要求：充分利用数据事实，逻辑严密，条理清晰。如资料为空，用常识推演。"
        )
        arg_a = (await debater_llm.ainvoke([HumanMessage(content=prompt_a)])).content
        print(f"{_ts()}   ✅ [argue] 正方立论完成 ({len(arg_a)} 字)")

        prompt_b = (
            f"当前辩题：{topic}。\n你是反方一辩，核心立场：【{sides.get('side_b')}】。\n"
            f"请基于以下经过验证的资料展开『一级论述』：\n{valid_b}\n\n"
            f"要求：充分利用数据事实，逻辑严密，条理清晰。如资料为空，用常识推演。"
        )
        arg_b = (await debater_llm.ainvoke([HumanMessage(content=prompt_b)])).content
        print(f"{_ts()}   ✅ [argue] 反方立论完成 ({len(arg_b)} 字)")

    except Exception as e:
        print(f"{_ts()} ❌ [argue] 立论阶段出错: {e}")
        traceback.print_exc()
        return {
            "arguments": {"side_a": f"[系统错误] 正方立论失败: {e}", "side_b": f"[系统错误] 反方立论失败: {e}"},
            "progress_message": f"❌ 立论阶段出错: {str(e)[:100]}"
        }

    return {
        "arguments": {"side_a": arg_a, "side_b": arg_b},
        "progress_message": "✅ 双方一级立论完成，即将进入交叉反驳..."
    }


async def rebuttal_node(state: ArgumentState):
    """
    [节点 7/9] 二级反驳：双方交叉攻击对方论述。
    """
    print(f"{_ts()} ⚔️ [rebuttal] 双方开始交叉反驳...")
    topic = state.get("topic", "未知辩题")
    sides = state.get("sides", {})
    args = state.get("arguments", {})
    arg_a = args.get("side_a", "正方未提供有效论述。")
    arg_b = args.get("side_b", "反方未提供有效论述。")
    valid_a = [d for d in state.get("research_data_a", []) if d.get("valid")]
    valid_b = [d for d in state.get("research_data_b", []) if d.get("valid")]

    try:
        prompt_a_rebuts_b = (
            f"当前辩题：{topic}。\n你是正方二辩，立场：【{sides.get('side_a')}】。\n"
            f"【反方论述】：\n{arg_b}\n\n【反方资料】：\n{valid_b}\n\n【己方资料】：\n{valid_a}\n\n"
            f"请从资料可靠性、逻辑漏洞两方面反驳反方，并巩固己方立场。"
        )
        rebuttal_a = (await debater_llm.ainvoke([HumanMessage(content=prompt_a_rebuts_b)])).content
        print(f"{_ts()}   ✅ [rebuttal] 正方反驳完成 ({len(rebuttal_a)} 字)")

        prompt_b_rebuts_a = (
            f"当前辩题：{topic}。\n你是反方二辩，立场：【{sides.get('side_b')}】。\n"
            f"【正方论述】：\n{arg_a}\n\n【正方资料】：\n{valid_a}\n\n【己方资料】：\n{valid_b}\n\n"
            f"请从资料可靠性、逻辑漏洞两方面反驳正方，并巩固己方立场。"
        )
        rebuttal_b = (await debater_llm.ainvoke([HumanMessage(content=prompt_b_rebuts_a)])).content
        print(f"{_ts()}   ✅ [rebuttal] 反方反驳完成 ({len(rebuttal_b)} 字)")

    except Exception as e:
        print(f"{_ts()} ❌ [rebuttal] 反驳阶段出错: {e}")
        traceback.print_exc()
        return {
            "rebuttals": {"side_a_rebut_b": f"[错误] {e}", "side_b_rebut_a": f"[错误] {e}"},
            "progress_message": f"❌ 反驳阶段出错: {str(e)[:100]}"
        }

    return {
        "rebuttals": {"side_a_rebut_b": rebuttal_a, "side_b_rebut_a": rebuttal_b},
        "progress_message": "✅ 双方交叉反驳完成，等待人类裁判指导意见..."
    }


async def human_filter_2_node(state: ArgumentState):
    """[节点 8/9] 人工介入点 2：反驳审核 (空节点，仅用于挂起)"""
    print(f"{_ts()} ⏸️ [human_filter_2] 流程暂停，等待人类裁判给出指导意见...")
    return {
        "progress_message": "⏸️ 交叉反驳完成，请人类裁判审阅并给出指导意见"
    }


async def refine_node(state: ArgumentState):
    """
    [节点 9/9] 结案陈词：双方吸收反馈，修补漏洞，输出最终强化论述。
    """
    print(f"{_ts()} 🛠️ [refine] 双方吸收反馈，撰写结案陈词...")
    topic = state.get("topic", "未知辩题")
    sides = state.get("sides", {})
    args = state.get("arguments", {})
    rebuttals = state.get("rebuttals", {})
    feedback = state.get("human_feedback", "无特殊指导意见。")

    arg_a = args.get("side_a", "")
    arg_b = args.get("side_b", "")
    rebut_against_a = rebuttals.get("side_b_rebut_a", "反方未进行有效反驳。")
    rebut_against_b = rebuttals.get("side_a_rebut_b", "正方未进行有效反驳。")
    valid_a = [d for d in state.get("research_data_a", []) if d.get("valid")]
    valid_b = [d for d in state.get("research_data_b", []) if d.get("valid")]

    try:
        prompt_a_refine = (
            f"当前辩题：{topic}。\n你是正方，立场：【{sides.get('side_a')}】。\n"
            f"【你的初版论述】：\n{arg_a}\n\n【对方对你的攻击】：\n{rebut_against_a}\n\n"
            f"【人类裁判指导意见】：\n{feedback}\n\n【你的有效资料】：\n{valid_a}\n\n"
            f"请吸收裁判意见，修补逻辑漏洞，输出最终【正方结案陈词】。"
        )
        refined_arg_a = (await debater_llm.ainvoke([HumanMessage(content=prompt_a_refine)])).content
        print(f"{_ts()}   ✅ [refine] 正方结案陈词完成 ({len(refined_arg_a)} 字)")

        prompt_b_refine = (
            f"当前辩题：{topic}。\n你是反方，立场：【{sides.get('side_b')}】。\n"
            f"【你的初版论述】：\n{arg_b}\n\n【对方对你的攻击】：\n{rebut_against_b}\n\n"
            f"【人类裁判指导意见】：\n{feedback}\n\n【你的有效资料】：\n{valid_b}\n\n"
            f"请吸收裁判意见，修补逻辑漏洞，输出最终【反方结案陈词】。"
        )
        refined_arg_b = (await debater_llm.ainvoke([HumanMessage(content=prompt_b_refine)])).content
        print(f"{_ts()}   ✅ [refine] 反方结案陈词完成 ({len(refined_arg_b)} 字)")

    except Exception as e:
        print(f"{_ts()} ❌ [refine] 结案陈词阶段出错: {e}")
        traceback.print_exc()
        return {
            "arguments": {"side_a": f"[错误] {e}", "side_b": f"[错误] {e}"},
            "progress_message": f"❌ 结案陈词阶段出错: {str(e)[:100]}"
        }

    return {
        "arguments": {"side_a": refined_arg_a, "side_b": refined_arg_b},
        "progress_message": "✅ 双方结案陈词完成，首席裁判正在生成最终判决..."
    }


async def summary_node(state: ArgumentState):
    """
    [节点 10/10] 终局裁判：生成总结报告和倾向度打分。
    """
    print(f"{_ts()} ⚖️ [summarize] 首席裁判生成最终总结与打分...")
    topic = state.get("topic", "未知辩题")
    sides = state.get("sides", {})
    args = state.get("arguments", {})
    arg_a = args.get("side_a", "正方未提供最终论述。")
    arg_b = args.get("side_b", "反方未提供最终论述。")

    # 构造要求严格返回 JSON 的裁判 Prompt
    prompt = (
        f"你现在是这场辩论的首席裁判。辩题是：【{topic}】。\n"
        f"正方立场：{sides.get('side_a')}\n"
        f"反方立场：{sides.get('side_b')}\n\n"
        f"以下是双方经过多轮交锋后，给出的最终结案陈词：\n"
        f"【正方最终陈词】：\n{arg_a}\n\n"
        f"【反方最终陈词】：\n{arg_b}\n\n"
        f"请你完成以下任务：\n"
        f"1. 撰写一段客观、深度的辩论总结（final_summary），点出双方的核心交锋点、各自的逻辑优势，以及最终的结论性洞察。\n"
        f"2. 给出对双方表现的客观倾向度打分（tendency_score），两者之和必须等于 1.0。\n\n"
        f"请务必严格按照以下 JSON 格式输出（不要包含 ```json 等 markdown 标记）：\n"
        f"{{\n"
        f"  \"final_summary\": \"深度总结报告...\",\n"
        f"  \"tendency_score\": {{\"side_a\": 0.6, \"side_b\": 0.4}}\n"
        f"}}"
    )

    llm_response = None
    try:
        llm_response = await analyzer_llm.ainvoke([HumanMessage(content=prompt)])
        clean_json = llm_response.content.strip('```json\n').strip('```').strip()
        result = json.loads(clean_json)

        final_summary = result.get("final_summary", "裁判总结生成失败。")
        tendency_score = result.get("tendency_score", {"side_a": 0.5, "side_b": 0.5})

        # 校验倾向度总和是否为 1
        score_a = tendency_score.get("side_a", 0.5)
        score_b = tendency_score.get("side_b", 0.5)
        if abs((score_a + score_b) - 1.0) > 0.01:
            total = score_a + score_b
            tendency_score = {"side_a": round(score_a / total, 2), "side_b": round(score_b / total, 2)}

        print(f"{_ts()} ✅ [summarize] 最终判决完成 → 正方 {tendency_score['side_a']} : 反方 {tendency_score['side_b']}")

    except Exception as e:
        raw = llm_response.content if llm_response else '<LLM未响应>'
        print(f"{_ts()} ❌ [summarize] 裁判总结解析失败: {e}")
        print(f"{_ts()}    LLM原始输出: {raw[:300]}")
        traceback.print_exc()
        final_summary = f"系统解析异常，未能生成格式化总结。错误: {e}"
        tendency_score = {"side_a": 0.5, "side_b": 0.5}

    return {
        "final_summary": final_summary,
        "tendency_score": tendency_score,
        "progress_message": f"✅ 辩论完成！最终倾向度 → 正方 {tendency_score.get('side_a', 0.5)} : 反方 {tendency_score.get('side_b', 0.5)}"
    }