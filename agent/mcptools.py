import os
import asyncio
import nest_asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.tools import StructuredTool
from dotenv import load_dotenv

load_dotenv()

# 允许在已有事件循环的环境中（如 Streamlit）嵌套调用 asyncio.run()
nest_asyncio.apply()


async def get_mcp_tools():
    """异步从阿里云 MCP 服务获取网络搜索工具集"""
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
    tools = await client.get_tools()
    return tools


def _wrap_mcp_tool_for_sync(mcp_tool):
    """
    为 MCP 纯异步工具补充同步调用能力。

    langchain_mcp_adapters 返回的 StructuredTool 只有 coroutine（异步），
    没有 func（同步），导致 LangGraph 的 ToolNode 调用 tool.invoke() 时
    抛出 NotImplementedError。

    此函数用 asyncio.run() 将异步协程包装为同步函数，同时保留原始
    coroutine 供 bind_tools / LLM 异步路径使用。
    """
    async_coro = mcp_tool.coroutine

    def sync_func(**kwargs):
        return asyncio.run(async_coro(**kwargs))

    return StructuredTool(
        name=mcp_tool.name,
        description=mcp_tool.description,
        args_schema=mcp_tool.args_schema,
        func=sync_func,         # ToolNode 同步调用走这里
        coroutine=async_coro,   # LLM / bind_tools 异步路径保留
    )


# nest_asyncio.apply() 保证在 Streamlit 事件循环中也能安全执行 asyncio.run()
_async_tools = asyncio.run(get_mcp_tools())
agent_tools = [_wrap_mcp_tool_for_sync(t) for t in _async_tools]
