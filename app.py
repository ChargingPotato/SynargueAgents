import streamlit as st
import uuid
from agent.graph import debate_app  # 假设你的 graph.py 中暴露了编译好的 app 对象

st.set_page_config(page_title="多智能体辩论系统", page_icon="⚖️", layout="wide")
st.title("⚖️ 个人决策分析助手 (带人工审核)")

# ==========================================
# 1. 初始化会话与线程 ID
# ==========================================
# 必须为每一次对话生成一个唯一的 thread_id，LangGraph 靠这个去数据库里找挂起的状态
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

# 设置 LangGraph 的运行配置
config = {"configurable": {"thread_id": st.session_state.thread_id}}

# 获取当前图的运行状态
current_state = debate_app.get_state(config)
# current_state.next 会返回一个列表，告诉你下一步准备运行什么节点。
# 如果图被挂起，它会包含设置了 interrupt_before 的节点名称。
next_nodes = current_state.next 
state_values = current_state.values # 当前全局 ArgumentState 里的数据

# ==========================================
# 2. 界面路由控制 (根据图的状态展示不同界面)
# ==========================================

# 阶段 A：初始状态，等待用户输入辩题
if len(next_nodes) == 0 and "topic" not in state_values:
    query = st.text_input("请输入你正在纠结的决策：", placeholder="例如：我想辞职做独立开发者，合适吗？")
    if st.button("开始辩论与分析", type="primary"):
        if not query:
            st.warning("请先输入决策内容！")
        else:
            with st.spinner("Agent 正在拆分派系并全网搜集资料，请稍候..."):
                # 首次启动图流程
                debate_app.invoke({"topic": query, "reference_library": []}, config)
                st.rerun() # 刷新页面，进入下一个状态

# 阶段 B：第一次人工介入 (资料审核挂起)
elif "human_filter_1" in next_nodes:
    st.warning("⚠️ 流程已暂停：Agent 已收集完资料，等待人类审核有效性。")
    st.subheader(f"辩题：{state_values.get('topic')}")
    
    with st.form("filter_1_form"):
        st.write("请勾选您认为**有效且合理**的资料（未勾选的将在后续辩论中被剔除）：")
        
        col1, col2 = st.columns(2)
        data_a = state_values.get("research_data_a", [])
        data_b = state_values.get("research_data_b", [])
        
        # 渲染正方资料审核选框
        with col1:
            st.success(f"👍 正方观点：{state_values.get('sides', {}).get('side_a')}")
            for i, item in enumerate(data_a):
                item['valid'] = st.checkbox(
                    f"[{item.get('source', '未知')}] {item.get('content')} (AI评分: {item.get('score', 0)})", 
                    value=True, 
                    key=f"a_{i}"
                )
        
        # 渲染反方资料审核选框
        with col2:
            st.error(f"👎 反方观点：{state_values.get('sides', {}).get('side_b')}")
            for i, item in enumerate(data_b):
                item['valid'] = st.checkbox(
                    f"[{item.get('source', '未知')}] {item.get('content')} (AI评分: {item.get('score', 0)})", 
                    value=True, 
                    key=f"b_{i}"
                )
                
        if st.form_submit_button("确认资料有效性，进入一级论证", type="primary"):
            with st.spinner("正在生成一级论证与交叉反驳..."):
                # 1. 更新人工修改后的状态
                debate_app.update_state(
                    config, 
                    {"research_data_a": data_a, "research_data_b": data_b}
                )
                # 2. 传入 None 恢复执行，图会继续跑到 human_filter_2
                debate_app.invoke(None, config)
                st.rerun()

# 阶段 C：第二次人工介入 (反驳审核挂起)
elif "human_filter_2" in next_nodes:
    st.warning("⚠️ 流程已暂停：Agent 已完成交叉反驳，等待人类指导。")
    
    col1, col2 = st.columns(2)
    with col1:
        st.success("正方一级论述与反驳")
        st.write(state_values.get("arguments", {}).get("side_a"))
        st.info("反驳对方：\n" + state_values.get("rebuttals", {}).get("side_a_rebut_b", ""))
        
    with col2:
        st.error("反方一级论述与反驳")
        st.write(state_values.get("arguments", {}).get("side_b"))
        st.info("反驳对方：\n" + state_values.get("rebuttals", {}).get("side_b_rebut_a", ""))
        
    with st.form("filter_2_form"):
        feedback = st.text_area("请给出您的指导意见（裁判点评）:", placeholder="例如：正方的反驳不够犀利，请结合投入产出比重新论述。")
        if st.form_submit_button("提交反馈，生成最终总结", type="primary"):
            with st.spinner("正在结合反馈重新论述并生成总结..."):
                debate_app.update_state(config, {"human_feedback": feedback})
                debate_app.invoke(None, config)
                st.rerun()

# 阶段 D：完成状态，展示最终结果
elif len(next_nodes) == 0 and "final_summary" in state_values:
    st.balloons()
    st.subheader("🧠 最终决策总结")
    st.info(state_values.get("final_summary"))
    
    scores = state_values.get("tendency_score", {})
    st.write(f"**最终倾向度：** 正方 {scores.get('side_a', 0)*100}% | 反方 {scores.get('side_b', 0)*100}%")
    
    st.divider()
    st.subheader("辩论复盘")
    col1, col2 = st.columns(2)
    with col1:
        st.success("正方最终论述")
        st.write(state_values.get("arguments", {}).get("side_a"))
    with col2:
        st.error("反方最终论述")
        st.write(state_values.get("arguments", {}).get("side_b"))
        
    if st.button("开始新的辩论"):
        # 清除当前的 thread_id，强制开启全新的流程
        del st.session_state.thread_id
        st.rerun()