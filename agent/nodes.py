import json
from .state import ArgumentState
from .models import analyzer_llm, research_llm, debater_llm ,research_llm_with_tools
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import ToolNode
from .mcptools import agent_tools

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


# ==========================================
# 核心修改 1：实例化两个独立的工具执行节点
# 虽然它们用的是同一套工具箱(agent_tools)，但在图中是两个不同的工位
# ==========================================
search_tools_a_node = ToolNode(agent_tools)
search_tools_b_node = ToolNode(agent_tools)

# ==========================================
# Agent A (正方) 搜索与提取节点
# ==========================================
def research_node_a(state: ArgumentState):
    """Agent A：寻找支持正方的资料，并在结束时提取为 JSON"""
    topic = state.get("topic")
    sides = state.get("sides", {})
    messages = state.get("messages", [])
    
    # 1. 注入角色与任务
    if not any("我是正方情报官" in msg.content for msg in messages if isinstance(msg, HumanMessage)):
        system_prompt = (
            f"[我是正方情报官]\n辩题：{topic}。\n你的立场是：支持【正方】({sides.get('side_a')})。\n"
            f"请使用网络搜索工具，寻找对正方有利的数据资料。搜集完成后，整理你的正方相关资料。"
        )
        messages.append(HumanMessage(content=system_prompt))
    
    # 2. 调用大模型
    response = research_llm_with_tools.invoke(messages)
    
    # 3. 【核心修复】：判断是否是最终输出，如果是，进行 JSON 结构化提取
    if not response.tool_calls:
        print("--- Agent A 资料搜集完毕，正在格式化为 JSON ---")
        extract_prompt = (
            f"请从以下资料中提取对正方有利的资料，严格返回 JSON 数组格式（不要包含任何其他文本）：\n"
            f"[{{\"source\": \"资料来源(若无则写网络)\", \"content\": \"具体的论据内容\"}}]\n\n"
            f"报告内容：\n{response.content}"
        )
        # 用严谨的模型 (analyzer_llm) 来做格式提取
        json_response = analyzer_llm.invoke([HumanMessage(content=extract_prompt)])
        
        try:
            clean_json = json_response.content.strip('```json\n').strip('```')
            data_a = json.loads(clean_json)
        except Exception as e:
            print(f"[警告] Agent A JSON解析失败: {e}")
            # 兜底：如果提取失败，把整段话塞进去保证流程不断
            data_a = [{"source": "Agent A 报告", "content": response.content}]
            
        # 【关键点】：同时更新 messages (留存聊天记录) 和 research_data_a (结构化数据)
        return {"messages": [response], "research_data_a": data_a}
        
    # 如果还在调用工具，就只更新 messages 让他继续循环
    return {"messages": [response]}


# ==========================================
# Agent B (反方) 搜索与提取节点
# ==========================================
def research_node_b(state: ArgumentState):
    """Agent B：寻找支持反方的资料，并在结束时提取为 JSON"""
    topic = state.get("topic")
    sides = state.get("sides", {})
    messages = state.get("messages", [])
    
    # 1. 注入角色与任务
    if not any("我是反方情报官" in msg.content for msg in messages if isinstance(msg, HumanMessage)):
        system_prompt = (
            f"[我是反方情报官]\n辩题：{topic}。\n你的立场是：支持【反方】({sides.get('side_b')})。\n"
            f"请务必使用网络搜索工具，寻找对反方有利的证据。搜集完成后，总结你的反方调查结果。"
        )
        messages.append(HumanMessage(content=system_prompt))
    
    # 2. 调用大模型
    response = research_llm_with_tools.invoke(messages)
    
    # 3. 【核心修复】：判断是否是最终输出，如果是，进行 JSON 结构化提取
    if not response.tool_calls:
        print("--- Agent B 资料搜集完毕，正在格式化为 JSON ---")
        extract_prompt = (
            f"请从以下报告中提取对反方有利的证据，严格返回 JSON 数组格式（不要包含任何其他文本）：\n"
            f"[{{\"source\": \"资料来源(若无则写网络)\", \"content\": \"具体的论据内容\"}}]\n\n"
            f"报告内容：\n{response.content}"
        )
        
        json_response = analyzer_llm.invoke([HumanMessage(content=extract_prompt)])
        
        try:
            clean_json = json_response.content.strip('```json\n').strip('```')
            data_b = json.loads(clean_json)
        except Exception as e:
            print(f"[警告] Agent B JSON解析失败: {e}")
            data_b = [{"source": "Agent B 报告", "content": response.content}]
            
        # 【关键点】：同时更新 messages (留存聊天记录) 和 research_data_b (结构化数据)
        return {"messages": [response], "research_data_b": data_b}
        
    return {"messages": [response]}

def verifier_node(state: ArgumentState):
    """
    第三方 Agent 进行资料验真打分。
    客观评估正反双方搜集到的证据的权威性和逻辑说服力。
    """
    print("--- ⚖️ 裁判 Agent 正在对双方资料进行独立验真与打分 ---")
    topic = state.get("topic", "未知辩题")
    
    # 获取上一步由 research_node 提取出来的结构化 JSON 数据
    data_a = state.get("research_data_a", [])
    data_b = state.get("research_data_b", [])
    
    # ---------------------------------------------------------
    # 核心闭包函数：为了代码复用，专门定义一个给单条数据打分的逻辑
    # ---------------------------------------------------------
    def evaluate_evidence(evidence_list, side_name):
        verified_list = []
        for item in evidence_list:
            content = item.get("content", "")
            source = item.get("source", "未知来源")
            
            # 1. 构造极其严格的打分裁判 Prompt
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
            
            try:
                # 2. 调用大模型进行打分
                response = analyzer_llm.invoke([HumanMessage(content=prompt)])
                score_text = response.content.strip()
                
                # 3. 强转为整型，并限制在 1-5 分之间，防止大模型抽风
                score = int(score_text)
                score = max(1, min(5, score)) 
                
            except Exception as e:
                # 4. 企业级兜底逻辑：如果大模型不听话输出了长句子导致 int() 报错，系统不崩溃，默认给及格分
                print(f"[验真警告] {side_name}打分解析失败，默认给中立分3分。大模型原话: {response.content}")
                score = 3 
            
            # 5. 更新数据的分数，并默认标记为有效（等待人工最终审核）
            item["score"] = score
            item["valid"] = True 
            verified_list.append(item)
            
        return verified_list

    # ---------------------------------------------------------
    # 分别对正方和反方的数据执行验真打分
    # ---------------------------------------------------------
    if data_a:
        print(f"正在逐条评估正方({len(data_a)}条)资料...")
        verified_a = evaluate_evidence(data_a, "正方")
    else:
        verified_a = []

    if data_b:
        print(f"正在逐条评估反方({len(data_b)}条)资料...")
        verified_b = evaluate_evidence(data_b, "反方")
    else:
        verified_b = []
    
    # 将打分完毕的最新数据写回全局状态
    return {
        "research_data_a": verified_a, 
        "research_data_b": verified_b
    }

def human_filter_1_node(state: ArgumentState):
    """人工介入点 1：判断资料有效性 (空节点，仅用于挂起)"""
    print("--- 等待人工审核搜索资料 ---")
    return {}

def argument_node(state: ArgumentState):
    """
    一级论证节点：
    正反双方根据人工确认有效的资料，分别生成己方的一级论述（立论）。
    """
    print("--- 🗣️ Agents 正在进行一级论证立论 ---")
    topic = state.get("topic", "未知辩题")
    sides = state.get("sides", {})
    
    # 【核心逻辑】：仅提取人工在界面上保留的 (valid=True) 的数据
    valid_a = [d for d in state.get("research_data_a", []) if d.get("valid")]
    valid_b = [d for d in state.get("research_data_b", []) if d.get("valid")]
    
    # ---------------------------------------------------------
    # 1. 正方立论 (Agent A)
    # ---------------------------------------------------------
    prompt_a = (
        f"当前辩题：{topic}。\n"
        f"你是正方一辩，你的核心立场是：【{sides.get('side_a')}】。\n"
        f"请基于以下经过验证的真实可靠资料，展开你的『一级论述』（立论）：\n"
        f"{valid_a}\n\n"
        f"要求：\n"
        f"1. 充分利用资料中的数据和事实作为你的论据。\n"
        f"2. 逻辑严密，条理清晰（可以分点论述）。\n"
        f"（如果提供的资料为空，请凭借你的常识和逻辑推演进行立论）。\n"
        f"请直接输出你的观点和证明，不需要多余的问候语。"
    )
    arg_a = debater_llm.invoke([HumanMessage(content=prompt_a)]).content

    # ---------------------------------------------------------
    # 2. 反方立论 (Agent B)
    # ---------------------------------------------------------
    prompt_b = (
        f"当前辩题：{topic}。\n"
        f"你是反方一辩，你的核心立场是：【{sides.get('side_b')}】。\n"
        f"请基于以下经过验证的真实可靠资料，展开你的『一级论述』（立论）：\n"
        f"{valid_b}\n\n"
        f"要求：\n"
        f"1. 充分利用资料中的数据和事实作为你的论据。\n"
        f"2. 逻辑严密，条理清晰（可以分点论述）。\n"
        f"（如果提供的资料为空，请凭借你的常识和逻辑推演进行立论）。\n"
        f"请直接输出你的观点和证明，不需要多余的问候语。"
    )
    arg_b = debater_llm.invoke([HumanMessage(content=prompt_b)]).content

    # ---------------------------------------------------------
    # 3. 将双方论点写入全局状态
    # ---------------------------------------------------------
    return {
        "arguments": {
            "side_a": arg_a, 
            "side_b": arg_b
        }
    }

def rebuttal_node(state: ArgumentState):
    """
    二级反驳节点：
    双方交换视角，针对对方的【一级论述】和【所引用的资料】进行精准的交叉反驳。
    """
    print("--- ⚔️ Agents 正在进行激烈的二级交叉反驳 ---")
    topic = state.get("topic", "未知辩题")
    sides = state.get("sides", {})
    args = state.get("arguments", {})
    
    # 1. 提取双方在上一步生成的一级论述
    arg_a = args.get("side_a", "正方未提供有效论述。")
    arg_b = args.get("side_b", "反方未提供有效论述。")
    
    # 2. 提取双方经过人工筛选的有效资料池 (用于防守和反击)
    valid_a = [d for d in state.get("research_data_a", []) if d.get("valid")]
    valid_b = [d for d in state.get("research_data_b", []) if d.get("valid")]
    
    # ---------------------------------------------------------
    # 3. 正方反驳反方 (Agent A)
    # ---------------------------------------------------------
    prompt_a_rebuts_b = (
        f"当前辩题：{topic}。\n"
        f"你是正方二辩，你的核心立场是：【{sides.get('side_a')}】。\n"
        f"现在轮到你进行反驳。以下是【反方】的论述及其所依赖的资料：\n"
        f"【反方论述】：\n{arg_b}\n\n"
        f"【反方依赖的资料】：\n{valid_b}\n\n"
        f"【你己方拥有的资料】：\n{valid_a}\n\n"
        f"你的反驳任务（请条理清晰地分点阐述）：\n"
        f"1. 破防资料：指出反方资料可能存在的片面性、样本偏差或时效性等问题。\n"
        f"2. 破防逻辑：直接攻击反方论述中的核心逻辑漏洞。\n"
        f"3. 巩固己方：利用己方资料或常识，对反方的论点进行反驳。\n"
        f"要求条理清晰。直接输出你的反驳辩词。"
    )
    rebuttal_a = debater_llm.invoke([HumanMessage(content=prompt_a_rebuts_b)]).content

    # ---------------------------------------------------------
    # 4. 反方反驳正方 (Agent B)
    # ---------------------------------------------------------
    prompt_b_rebuts_a = (
        f"当前辩题：{topic}。\n"
        f"你是反方二辩，你的核心立场是：【{sides.get('side_b')}】。\n"
        f"现在轮到你进行反驳。以下是【正方】的论述及其所依赖的资料：\n"
        f"【正方论述】：\n{arg_a}\n\n"
        f"【正方依赖的资料】：\n{valid_a}\n\n"
        f"【你己方拥有的资料】：\n{valid_b}\n\n"
        f"你的反驳任务（请条理清晰地分点阐述）：\n"
        f"1. 破防资料：指出正方资料可能存在的片面性、样本偏差或时效性等问题。\n"
        f"2. 破防逻辑：直接攻击正方论述中的核心逻辑漏洞。\n"
        f"3. 巩固己方：利用己方资料或常识，对正方的论点进行反驳。\n"
        f"要求条理清晰。直接输出你的反驳辩词。"
    )
    rebuttal_b = debater_llm.invoke([HumanMessage(content=prompt_b_rebuts_a)]).content

    # ---------------------------------------------------------
    # 5. 更新全局状态
    # ---------------------------------------------------------
    return {
        "rebuttals": {
            "side_a_rebut_b": rebuttal_a, 
            "side_b_rebut_a": rebuttal_b
        }
    }

def human_filter_2_node(state: ArgumentState):
    """人工介入点 2：判断反驳合理性 (空节点，仅用于挂起)"""
    print("--- 等待人工审核反驳意见 ---")
    return {}

def refine_node(state: ArgumentState):
    """
    最终修正与升华节点（结案陈词）：
    双方吸收对方的反驳意见和人类裁判的反馈，修补逻辑漏洞，输出最终版的强化论述。
    """
    print("--- 🛠️ Agents 正在结合反馈进行最终的强化论述 ---")
    
    topic = state.get("topic", "未知辩题")
    sides = state.get("sides", {})
    args = state.get("arguments", {})
    rebuttals = state.get("rebuttals", {})
    feedback = state.get("human_feedback", "无特殊指导意见。")
    
    # 提取初版论述
    arg_a = args.get("side_a", "")
    arg_b = args.get("side_b", "")
    
    # 提取对方的攻击
    rebut_against_a = rebuttals.get("side_b_rebut_a", "反方未进行有效反驳。")
    rebut_against_b = rebuttals.get("side_a_rebut_b", "正方未进行有效反驳。")
    
    # 提取有效资料池（作为防守底气）
    valid_a = [d for d in state.get("research_data_a", []) if d.get("valid")]
    valid_b = [d for d in state.get("research_data_b", []) if d.get("valid")]

    # ---------------------------------------------------------
    # 1. 正方最终修正 (Agent A)
    # ---------------------------------------------------------
    prompt_a_refine = (
        f"当前辩题：{topic}。\n"
        f"你是正方，核心立场：【{sides.get('side_a')}】。\n"
        f"这是辩论的最后环节（结案陈词）。请仔细阅读以下上下文：\n\n"
        f"【你的初版论述】：\n{arg_a}\n\n"
        f"【对方对你的攻击】：\n{rebut_against_a}\n\n"
        f"【人类裁判的指导意见】：\n{feedback}\n\n"
        f"【你手中的武器（有效资料）】：\n{valid_a}\n\n"
        f"你的任务：\n"
        f"1. 深刻吸纳人类裁判的指导意见，这决定了你最终的得分。\n"
        f"2. 针对对方的攻击，修补你初版论述中的逻辑漏洞，或者进行强有力的防守反击。\n"
        f"3. 整合升华，输出你最终版的、无懈可击的【正方结案陈词】。\n"
        f"要求：条理清晰，逻辑清晰。"
    )
    refined_arg_a = debater_llm.invoke([HumanMessage(content=prompt_a_refine)]).content

    # ---------------------------------------------------------
    # 2. 反方最终修正 (Agent B)
    # ---------------------------------------------------------
    prompt_b_refine = (
        f"当前辩题：{topic}。\n"
        f"你是反方，核心立场：【{sides.get('side_b')}】。\n"
        f"这是辩论的最后环节（结案陈词）。请仔细阅读以下上下文：\n\n"
        f"【你的初版论述】：\n{arg_b}\n\n"
        f"【对方对你的攻击】：\n{rebut_against_b}\n\n"
        f"【人类裁判的指导意见】：\n{feedback}\n\n"
        f"【你手中的武器（有效资料）】：\n{valid_b}\n\n"
        f"你的任务：\n"
        f"1. 深刻吸纳人类裁判的指导意见，这决定了你最终的得分。\n"
        f"2. 针对对方的攻击，修补你初版论述中的逻辑漏洞，或者进行强有力的防守反击。\n"
        f"3. 整合升华，输出你最终版的、无懈可击的【反方结案陈词】。\n"
        f"要求：条理清晰，逻辑清晰。"
    )
    refined_arg_b = debater_llm.invoke([HumanMessage(content=prompt_b_refine)]).content

    # ---------------------------------------------------------
    # 3. 覆盖写入全局状态
    # ---------------------------------------------------------
    return {
        "arguments": {
            "side_a": refined_arg_a, 
            "side_b": refined_arg_b
        }
    }

def summary_node(state: ArgumentState):
    """
    三级总结论证节点（结案总结）：
    作为最终的客观裁判，结合双方的结案陈词，给出终局总结报告和倾向度打分。
    """
    print("--- ⚖️ 首席裁判 Agent 正在生成最终辩论总结与倾向度打分 ---")
    
    topic = state.get("topic", "未知辩题")
    sides = state.get("sides", {})
    args = state.get("arguments", {})
    
    # 获取双方经过 refine_node 升华后的最终论述
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
        f"2. 给出对双方表现的客观倾向度打分（tendency_score），两者之和必须等于 1.0（例如觉得正方表现略好，可以是 side_a: 0.6, side_b: 0.4）。\n\n"
        f"请务必严格按照以下 JSON 格式输出（不要包含 ```json 等 markdown 标记，也不要输出任何多余的解释文本）：\n"
        f"{{\n"
        f"  \"final_summary\": \"这里写你的深度总结报告...\",\n"
        f"  \"tendency_score\": {{\"side_a\": 0.6, \"side_b\": 0.4}}\n"
        f"}}"
    )
    
    try:
        # 召唤裁判模型
        response = analyzer_llm.invoke([HumanMessage(content=prompt)])
        
        # 清理可能附带的 Markdown 代码块标记，确保 JSON 纯净
        clean_json = response.content.strip('```json\n').strip('```').strip()
        result = json.loads(clean_json)
        
        final_summary = result.get("final_summary", "裁判总结生成失败。")
        tendency_score = result.get("tendency_score", {"side_a": 0.5, "side_b": 0.5})
        
        # 二次校验倾向度总和是否为 1 (浮点数容差处理)
        score_a = tendency_score.get("side_a", 0.5)
        score_b = tendency_score.get("side_b", 0.5)
        if abs((score_a + score_b) - 1.0) > 0.01:
            # 如果大模型数学不好，强制归一化
            total = score_a + score_b
            tendency_score = {"side_a": round(score_a/total, 2), "side_b": round(score_b/total, 2)}
            
    except Exception as e:
        print(f"[裁判解析警告] 最终总结 JSON 解析失败: {e}")
        print(f"大模型原始输出: {response.content}")
        # 企业级兜底逻辑
        final_summary = "由于系统解析异常，未能生成格式化的最终总结。详情请见后台日志。"
        tendency_score = {"side_a": 0.5, "side_b": 0.5} # 兜底平局
        
    return {
        "final_summary": final_summary,
        "tendency_score": tendency_score
    }