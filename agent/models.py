import os
from dotenv import load_dotenv
from langchain_deepseek import ChatDeepSeek
from agent.tools import agent_tools

load_dotenv()

api_key = os.getenv("DEEPSEEK_API_KEY")


# 1. 分析与总结模型 (需要极高的客观性和逻辑性，低温度)
analyzer_llm = ChatDeepSeek(
    model="deepseek-reasoner",
    api_key=api_key,
    temperature=0.1,
)

# 2. 资料搜集模型 (需要广泛的知识和判断力)
research_llm = ChatDeepSeek(
    model="deepseek-reasoner",
    api_key=api_key,
    temperature=0.3,
)

research_llm_with_tools = research_llm.bind_tools(agent_tools)


# 3. 辩手模型 (需要创造力和攻击性，高温度)
debater_llm = ChatDeepSeek(
    model="deepseek-reasoner",
    api_key=api_key,
    temperature=0.3,
)
