# agent/tools.py
import os
import requests
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

@tool
def mcp_web_search(query: str) -> str:
    """
    当你需要获取最新的网络资料、新闻或事实依据时，请调用此工具进行网络搜索。
    """
    print(f"\n[Tool Execution] 正在通过 DashScope MCP 搜索: {query}")
    
    url = "https://dashscope.aliyuncs.com/api/v1/mcps/WebSearch/mcp"
    api_key = os.getenv("DASHSCOPE_API_KEY")
    
    if not api_key:
        return "Error: DASHSCOPE_API_KEY 未设置"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "method": "tools/call",
        "params": {
            "name": "web_search",
            "arguments": {
                "query": query
            }
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return str(result.get("result", {}).get("content", "未找到相关内容"))
    except Exception as e:
        return f"搜索失败: {str(e)}"

# ==========================================
# 核心：定义一个包含所有可用工具的列表
# 其他文件只需要 import 这个列表即可
# ==========================================
agent_tools = [mcp_web_search]