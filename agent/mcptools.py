import os
from langchain_mcp_adapters.client import MultiServerMCPClient
import asyncio

async def get_mcp_tools():
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    client = MultiServerMCPClient({
        "aliyun_websearch": {
            "transport": "http",
            "url": "https://dashscope.aliyuncs.com/api/v1/mcps/WebSearch/mcp",
            "headers": {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
        }
    })
    # 必须异步获取
    tools = await client.get_tools()
    return tools

web_search_tool = asyncio.run(get_mcp_tools())
agent_tools = [web_search_tool]
