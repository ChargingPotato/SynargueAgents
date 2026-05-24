"""
DecisionPal 独立 Worker 进程
============================

持久运行的守护进程，监听 Redis 队列 `debate_tasks`，执行 LangGraph 辩论工作流。

启动方式：
    python backend/worker.py

环境变量：
    DP_REDIS_URL  — Redis 连接地址，默认 redis://localhost:6379/0
    DEEPSEEK_API_KEY — DeepSeek API 密钥
    BOCHA_API_KEY    — Bocha 搜索 API 密钥
"""

import asyncio
import signal
import traceback

from agent.graph import get_async_debate_app
from agent.redis_memory import redis_client, async_saver
from backend.utils.redis_queue import pop_task, set_error, DEBATE_QUEUE_KEY


async def process_task(debate_app, payload: dict) -> None:
    thread_id = payload["thread_id"]
    action = payload["action"]
    config = {"configurable": {"thread_id": thread_id}}

    prefix = f"[Worker]"
    short_id = thread_id[:8]

    if action == "start":
        state_payload = payload.get("state_payload", {})
        print(f"{prefix} 🚀 开始执行 start thread={short_id} topic={state_payload.get('topic', '?')[:30]}")
        await debate_app.ainvoke(state_payload, config)
        print(f"{prefix} ✅ start 执行完毕 thread={short_id}")

    elif action == "resume":
        print(f"{prefix} 🔄 恢复执行 thread={short_id}")
        await debate_app.ainvoke(None, config)
        print(f"{prefix} ✅ resume 执行完毕 thread={short_id}")


async def main_loop() -> None:
    await async_saver.asetup()
    debate_app = get_async_debate_app()

    print(f"[Worker] 🔧 启动 DecisionPal Worker")
    print(f"[Worker] 📡 监听 Redis 队列: {DEBATE_QUEUE_KEY}")

    shutdown = False

    def handle_signal(signum, frame):
        nonlocal shutdown
        print(f"\n[Worker] ⏹️ 收到信号 {signum}，等待当前任务完成后退出...")
        shutdown = True

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    while not shutdown:
        try:
            payload = pop_task(redis_client, timeout=1)
        except Exception as e:
            print(f"[Worker] ⚠️ 队列连接异常: {e}，3 秒后重试...")
            await asyncio.sleep(3)
            continue

        if payload is None:
            continue

        thread_id = payload.get("thread_id", "?")
        action = payload.get("action", "?")

        try:
            await process_task(debate_app, payload)
        except Exception as e:
            error_msg = f"[Worker] ❌ 任务失败 thread={thread_id[:8]} | {type(e).__name__}: {e}"
            print(error_msg)
            traceback.print_exc()
            try:
                set_error(
                    redis_client,
                    thread_id,
                    str(e),
                    type(e).__name__,
                    traceback.format_exc(),
                )
                print(f"[Worker] 📝 错误已写入 Redis: debate_error:{thread_id[:8]}")
            except Exception as redis_err:
                print(f"[Worker] ⚠️ 无法写入错误到 Redis: {redis_err}")

    print("[Worker] 👋 Worker 已退出")


if __name__ == "__main__":
    asyncio.run(main_loop())
