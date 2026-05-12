import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()
api_key = os.getenv("DASHSCOPE_API_KEY")
base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"

# 1. 分析与总结模型 (需要极高的客观性和逻辑性，低温度)
analyzer_llm = init_chat_model(
    model="deepseek-v4-pro",
    model_provider="openai",
    base_url=base_url,
    api_key=api_key,
    temperature=0.1
)

# 2. 资料搜集与验真模型 (需要广泛的知识和判断力)
research_llm = init_chat_model(
    model="deepseek-v4-pro",
    model_provider="openai",
    base_url=base_url,
    api_key=api_key,
    temperature=0.3
)

# 3. 辩手模型 (需要创造力和攻击性，高温度)
debater_llm = init_chat_model(
    model="deepseek-v4-pro",
    model_provider="openai",
    base_url=base_url,
    api_key=api_key,
    temperature=0.7
)