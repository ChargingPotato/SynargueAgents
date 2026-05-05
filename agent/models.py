import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.chat_models import init_chat_model


load_dotenv()
#print("当前加载的 Key 是:", os.getenv("DASHSCOPE_API_KEY")) # 看看终端里打印出了什么


pro_llm = init_chat_model(
    model = "deepseek-v4-pro",
    model_provider="openai",
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    temperature = 0.7
)

con_llm = init_chat_model(
    model = "deepseek-v4-pro",
    model_provider="openai",
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    temperature = 0.7
)
decision_llm = init_chat_model(
    model = "deepseek-v4-pro",
    model_provider="openai",
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    temperature = 0.2
)
"""
pro_llm = ChatOpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="deepseek-v4-pro",
    temperature=0.7
)

con_llm = ChatOpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="deepseek-v4-pro",
    temperature=0.7
)
decision_llm = ChatOpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY", ""),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    model="deepseek-v4-pro",
    temperature=0.2
)
"""