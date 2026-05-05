import json
import os
from langchain_core.messages import HumanMessage
from .state import DecisionState
from .models import pro_llm, con_llm, decision_llm

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
os.makedirs(DATA_DIR, exist_ok=True)
HISTORY_FILE = os.path.join(DATA_DIR, 'history.json')

def node_collect_info(state: DecisionState):
    info = f"网络检索到关于【{state['user_query']}】的背景资料显示该事物具有两面性..."
    return {"collected_info": info}

def node_pro_debater(state: DecisionState):
    prompt = f"基于信息：{state['collected_info']}。请极力支持决策：【{state['user_query']}】。给出3个理由。"
    response = pro_llm.invoke([HumanMessage(content=prompt)])
    return {"pro_argument": response.content}

def node_con_debater(state: DecisionState):
    prompt = f"基于信息：{state['collected_info']}。请极力反对决策：【{state['user_query']}】。指出3个风险。"
    response = con_llm.invoke([HumanMessage(content=prompt)])
    return {"con_argument": response.content}

def node_decision_maker(state: DecisionState):
    prompt = f"决策：{state['user_query']}\n正方：{state['pro_argument']}\n反方：{state['con_argument']}\n请给出客观最终建议。"
    response = decision_llm.invoke([HumanMessage(content=prompt)])
    decision_result = response.content
    
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
        
    return {"final_decision": decision_result}