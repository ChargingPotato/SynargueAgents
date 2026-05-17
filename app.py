import streamlit as st
import uuid
# 确保这里是从绝对路径导入你编译好的图
from agent.graph import debate_app  

st.set_page_config(page_title="Multi-Agent 深度辩论系统", page_icon="⚖️", layout="wide")
st.title("⚖️ 多智能体对抗演练与决策系统")
st.caption("基于 LangGraph 构建的双轨搜索与人类干预 (Human-in-the-Loop) 架构")

# ==========================================
# 1. 初始化会话与线程 ID
# ==========================================
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

# 设置配置，用于 LangGraph 的 Checkpointer 追踪历史
config = {"configurable": {"thread_id": st.session_state.thread_id}}

# 获取当前图的执行状态
current_state = debate_app.get_state(config)
next_nodes = current_state.next 
state_values = current_state.values 

# ==========================================
# 2. 界面路由控制
# ==========================================

# 阶段 A：初始状态，等待输入
if len(next_nodes) == 0 and "topic" not in state_values:
    st.info("👋 欢迎！系统将实例化两个立场对立的 Agent，自动在全网搜集证据并进行激烈的交叉反驳。")
    query = st.text_input("请输入辩题或纠结的决策：", placeholder="例如：燃油车是否会在10年内被彻底淘汰？")
    if st.button("🚀 启动多智能体辩论", type="primary"):
        if not query:
            st.warning("请先输入辩题！")
        else:
            with st.spinner("🕵️‍♂️ Agent A 与 Agent B 正在交替进行全网深度调查，并由裁判模型进行打分，请耐心等待（约需1-2分钟）..."):
                # 初始化触发图的运行
                debate_app.invoke({"topic": query, "reference_library": []}, config)
                st.rerun()

# 阶段 B：第一次人工介入 (资料审核)
elif "human_filter_1" in next_nodes:
    st.warning("⚠️ **流程已暂停**：双方已完成情报搜集与第三方验真。请人类裁判介入！")
    st.subheader(f"📌 辩题：{state_values.get('topic')}")
    
    with st.form("filter_1_form"):
        st.write("请审阅以下资料（裁判模型已打分）。您可以**取消勾选**认为不可靠的资料，它们将被踢出后续的辩论环节：")
        
        col1, col2 = st.columns(2)
        data_a = state_values.get("research_data_a", [])
        data_b = state_values.get("research_data_b", [])
        
        st.write("🔍 Debug: 当前状态中的 data_a =", data_a)
        st.write("🔍 Debug: 当前状态中的 data_b =", data_b)
        
        with col1:
            st.success(f"🔵 正方观点：{state_values.get('sides', {}).get('side_a')}")
            for i, item in enumerate(data_a):
                stars = "⭐" * item.get("score", 3)
                item['valid'] = st.checkbox(
                    f"[{item.get('source')}] {item.get('content')} \n\n裁判打分: {stars}", 
                    value=item.get("valid", True), 
                    key=f"a_{i}"
                )
        
        with col2:
            st.error(f"🔴 反方观点：{state_values.get('sides', {}).get('side_b')}")
            for i, item in enumerate(data_b):
                stars = "⭐" * item.get("score", 3)
                item['valid'] = st.checkbox(
                    f"[{item.get('source')}] {item.get('content')} \n\n裁判打分: {stars}", 
                    value=item.get("valid", True), 
                    key=f"b_{i}"
                )
                
        if st.form_submit_button("✅ 确认资料库，生成一级立论与交叉反驳", type="primary"):
            with st.spinner("⚔️ 双方辩手正在根据你批准的资料进行立论与激烈的交叉反驳..."):
                # 显式指定 as_node，防止 InvalidUpdateError 报错
                debate_app.update_state(
                    config, 
                    {"research_data_a": data_a, "research_data_b": data_b},
                    as_node="human_filter_1"
                )
                # 恢复图的运行
                debate_app.invoke(None, config)
                st.rerun()

# 阶段 C：第二次人工介入 (反驳审核与场外指导)
elif "human_filter_2" in next_nodes:
    st.warning("⚠️ **流程已暂停**：双方已完成交叉反驳，请人类裁判给出指导意见！")
    
    col1, col2 = st.columns(2)
    with col1:
        st.success("🔵 正方立论与反击")
        with st.expander("展开查看正方『一级论述』"):
            st.write(state_values.get("arguments", {}).get("side_a"))
        st.info("⚔️ 针对反方的交叉反驳：\n\n" + state_values.get("rebuttals", {}).get("side_a_rebut_b", ""))
        
    with col2:
        st.error("🔴 反方立论与反击")
        with st.expander("展开查看反方『一级论述』"):
            st.write(state_values.get("arguments", {}).get("side_b"))
        st.info("⚔️ 针对正方的交叉反驳：\n\n" + state_values.get("rebuttals", {}).get("side_b_rebut_a", ""))
        
    with st.form("filter_2_form"):
        st.write("### 🧠 裁判场外指导")
        feedback = st.text_area("请指出双方辩论中的漏洞，或指定他们接下来的主攻方向：", placeholder="例如：正方不要纠结于细节数据，请从宏观经济学角度重新升华你们的结论。")
        
        if st.form_submit_button("🔥 提交指导意见，生成结案陈词与最终判决", type="primary"):
            with st.spinner("🛠️ 双方正在吸收你的反馈修补漏洞，裁判正在撰写最终报告..."):
                # 显式指定 as_node，防止 InvalidUpdateError 报错
                debate_app.update_state(
                    config, 
                    {"human_feedback": feedback},
                    as_node="human_filter_2"
                )
                debate_app.invoke(None, config)
                st.rerun()

# 阶段 D：完成状态，展示最终结果
elif len(next_nodes) == 0 and "final_summary" in state_values:
    st.balloons()
    
    scores = state_values.get("tendency_score", {})
    score_a = int(scores.get('side_a', 0.5) * 100)
    score_b = int(scores.get('side_b', 0.5) * 100)
    
    st.subheader(f"📊 最终裁判倾向度：正方 {score_a}% vs 反方 {score_b}%")
    st.progress(scores.get('side_a', 0.5))
    
    st.divider()
    st.subheader("🧠 裁判总结报告")
    st.info(state_values.get("final_summary"))
    
    st.divider()
    st.subheader("🎤 双方最终结案陈词")
    col1, col2 = st.columns(2)
    with col1:
        st.success("🔵 正方结案陈词")
        st.write(state_values.get("arguments", {}).get("side_a"))
    with col2:
        st.error("🔴 反方结案陈词")
        st.write(state_values.get("arguments", {}).get("side_b"))
        
    if st.button("🔄 开启新一轮辩论"):
        del st.session_state.thread_id
        st.rerun()