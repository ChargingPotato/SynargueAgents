import os
import requests
from dotenv import load_dotenv
from langchain_core.tools import tool

load_dotenv()

BOCHA_API_KEY = os.getenv("BOCHA_API_KEY")


@tool
def bocha_web_search(query: str, count: int = 10) -> str:
    """
    使用 Bocha Web Search API 进行互联网网页搜索。
    当你需要获取最新的网络资料、新闻或事实依据时，请调用此工具。

    参数:
    - query: 搜索关键词
    - count: 返回的搜索结果数量，默认 10 条
    """
    url = "https://api.bochaai.com/v1/web-search"
    headers = {
        "Authorization": f"Bearer {BOCHA_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "query": query,
        "freshness": "noLimit",
        "summary": True,
        "count": count,
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        body = response.json()

        if body.get("code") != 200 or not body.get("data"):
            return f"搜索API请求失败: {body.get('msg', '未知错误')}"

        webpages = body["data"]["webPages"]["value"]
        if not webpages:
            return "未找到相关搜索结果。"

        formatted_results = ""
        for idx, page in enumerate(webpages, start=1):
            formatted_results += (
                f"【结果 {idx}】\n"
                f"标题: {page['name']}\n"
                f"URL: {page['url']}\n"
                f"摘要: {page['summary']}\n"
                f"来源: {page['siteName']}\n"
                f"发布时间: {page.get('dateLastCrawled', '未知')}\n\n"
            )
        return formatted_results.strip()

    except requests.RequestException as e:
        return f"搜索请求失败: {str(e)}"
    except Exception as e:
        return f"搜索结果解析失败: {str(e)}"


agent_tools = [bocha_web_search]
