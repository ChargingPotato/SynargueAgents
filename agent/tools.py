import requests
from bs4 import BeautifulSoup
from langchain_core.tools import tool
import urllib3
import os
from dotenv import load_dotenv

# 压制忽略 SSL 验证带来的警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

@tool
def web_search_tool(query: str) -> str:
    """
    当你需要获取最新的网络资料、新闻或事实依据时，请调用此工具进行网络搜索。
    """
    print(f"\n[Tool Execution] 正在通过 Bing 中国搜索: {query}")
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9" # 强制要求中文结果，防止被重定向到国际版
    }
    
    url = f"https://cn.bing.com/search?q={query}"
    
    try:
        # 🚨 核心修复：加上 verify=False，忽略本地网络环境的 SSL 证书冲突
        response = requests.get(url, headers=headers, timeout=10, verify=False)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        for li in soup.find_all('li', class_='b_algo')[:5]:
            title_tag = li.find('h2')
            p_tag = li.find('p')
            
            if title_tag and p_tag:
                results.append(f"【标题】: {title_tag.text.strip()}\n【内容】: {p_tag.text.strip()}")
        
        if not results:
            return "搜索成功，但未找到相关结果内容。"
            
        return "\n\n".join(results)

    except Exception as e:
        print(f"[Bing Search Error] 错误: {e}")
        return f"搜索执行失败: {str(e)}"

from langchain_tavily import TavilySearch
# 初始化搜索工具
tavily_key = os.getenv("TAVILY_API_KEY")
search_tool = TavilySearch(max_results=2,search_depth="basic")

#tools = [search_tool]

agent_tools = [search_tool]

agent_tools = [web_search_tool]