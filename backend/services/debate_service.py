"""
辩论工作流编排服务 (v2 — Redis 队列架构)
===========================================

核心设计思想：
1. Gateway-Worker 分离：FastAPI 网关仅负责读写状态、推送队列消息，不执行 LLM 调用。
2. 独立 Worker 进程监听 Redis 队列，执行 debate_app.ainvoke()。
3. 进程重启安全：所有状态持久化在 Redis（RedisSaver + 错误 key），
   网关和 Worker 均无本地内存状态。

流程概览：
  FastAPI 网关                    Redis                       Worker 进程
  ────────────                  ───────                     ────────────
  start_debate ──LPUSH──→  debate_tasks  ←──BRPOP── 执行 ainvoke(input)
  submit_review ──update_state──→ checkpoint ←──读取状态
                ──LPUSH──→  debate_tasks  ←──BRPOP── 执行 ainvoke(None)
  submit_feedback 同 submit_review 模式
  get_current_state ──get_state──→ checkpoint
                   ──get_error──→ debate_error:{id}
"""

import traceback
from uuid import uuid4

from agent.graph import debate_app
from agent.redis_memory import redis_client
from backend.utils.serialization import state_to_dict, determine_phase
from backend.utils.redis_queue import push_task, get_error


class DebateService:
    """
    辩论工作流编排器 (Gateway 侧)

    本类仅运行在 FastAPI 进程内，职责：
    - 入队任务 (push_task)
    - 注入人类数据 (update_state)
    - 查询状态 (get_state + get_error)

    所有 ainvoke 调用均发生在独立的 Worker 进程中。
    """

    def _config(self, thread_id: str) -> dict:
        return {"configurable": {"thread_id": thread_id}}

    async def start_debate(self, topic: str) -> tuple[str, dict, str]:
        """
        启动新辩论：生成 thread_id，推入 Redis 队列，立即返回。

        不再使用 asyncio.create_task —— Worker 进程会异步拾取并执行。
        """
        thread_id = str(uuid4())

        push_task(
            redis_client,
            thread_id,
            "start",
            state_payload={"topic": topic, "reference_library": []},
        )

        print(f"[DebateService] 📨 任务已入队 thread={thread_id[:8]} topic={topic[:30]}")

        return (
            thread_id,
            {"topic": topic, "progress_message": "📨 辩论任务已提交，等待 Worker 处理..."},
            "researching",
        )

    def get_current_state(self, thread_id: str) -> tuple[dict, str]:
        """
        查询指定会话的当前状态（供前端轮询）

        先检查 Redis 错误 key，再读 LangGraph 检查点。
        如果检查点尚不存在（Worker 未处理），返回 researching。
        """
        # 优先检查 Worker 写入的异常
        err = get_error(redis_client, thread_id)
        if err:
            return err, "error"

        config = self._config(thread_id)

        try:
            state = debate_app.get_state(config)
        except Exception as e:
            # 检查点尚不存在（Worker 还未执行 / Redis 中无记录），不算错误
            return (
                {"progress_message": "⏳ 等待 Worker 开始处理..."},
                "researching",
            )

        if state is None or state.values is None:
            return (
                {"progress_message": "⏳ 等待 Worker 开始处理..."},
                "researching",
            )

        state_dict = state_to_dict(state.values)
        phase = determine_phase(state)

        return state_dict, phase

    async def submit_review(
        self, thread_id: str, data_a: list, data_b: list
    ) -> tuple[dict, str]:
        """
        人工介入 1：注入审核后的资料到检查点，推入 resume 任务，读取并返回当前状态。
        """
        config = self._config(thread_id)

        try:
            print(f"[DebateService] 📝 提交资料审核 thread={thread_id[:8]}...")

            debate_app.update_state(
                config,
                {"research_data_a": data_a, "research_data_b": data_b},
                as_node="human_filter_1",
            )

            push_task(redis_client, thread_id, "resume")

            state = debate_app.get_state(config)
            return state_to_dict(state.values), determine_phase(state)

        except Exception as e:
            print(f"[DebateService] ❌ submit_review 失败: {e}")
            traceback.print_exc()
            raise

    async def submit_feedback(
        self, thread_id: str, feedback: str
    ) -> tuple[dict, str]:
        """
        人工介入 2：注入人类反馈到检查点，推入 resume 任务，读取并返回当前状态。
        """
        config = self._config(thread_id)

        try:
            print(f"[DebateService] 💬 提交裁判反馈 thread={thread_id[:8]}...")

            debate_app.update_state(
                config,
                {"human_feedback": feedback},
                as_node="human_filter_2",
            )

            push_task(redis_client, thread_id, "resume")

            state = debate_app.get_state(config)
            return state_to_dict(state.values), determine_phase(state)

        except Exception as e:
            print(f"[DebateService] ❌ submit_feedback 失败: {e}")
            traceback.print_exc()
            raise


debate_service = DebateService()
