import streamlit as st
import json
import os
from agent.graph import agent_app

st.set_page_config(page_title="AI 决策助手", page_icon="⚖️", layout="wide")
st.title("⚖️ 个人决策分析助手")

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
HISTORY_FILE = os.path.join(DATA_DIR, 'history.json')
history = ""
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        history_data = json.load(f)
        history = history_data.get("final_decision", "")

query = st.text_input("请输入你正在纠结的决策：", placeholder="例如：我想辞职做独立开发者，合适吗？")

if st.button("开始辩论与分析", type="primary"):
    if not query:
        st.warning("请先输入决策内容！")
    else:
        with st.spinner("AI 调查与辩论中，请稍候..."):
            initial_state = {"user_query": query, "history_context": history}
            result_state = agent_app.invoke(initial_state)

            st.divider()
            st.subheader("🌐 背景信息")
            st.write(result_state.get("collected_info"))
            
            col1, col2 = st.columns(2)
            with col1:
                st.success("👍 正方 (支持)")
                st.write(result_state.get("pro_argument"))
            with col2:
                st.error("👎 反方 (反对)")
                st.write(result_state.get("con_argument"))
                
            st.divider()
            st.subheader("🧠 最终决策结论")
            st.info(result_state.get("final_decision"))
            st.caption("本次辩论数据已保存入库。")