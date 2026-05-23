"""
辩论工作流编排服务
====================

核心设计思想：
1. Fire-and-Forget 模式：start_debate 启动后台异步任务后立即返回，不阻塞 HTTP 请求
2. 人机协作断点：LangGraph 工作流有两个 interrupt_before 断点（human_filter_1 / human_filter_2），
   本服务负责在断点处注入人类输入后恢复执行
3. 错误信箱机制：异步后台任务的异常无法直接抛给调用方，通过 _task_errors 字典中转给轮询查询
"""

import asyncio
import traceback
from uuid import uuid4

from agent.graph import debate_app

# state_to_dict: 将 LangGraph 内部的复杂对象（Message、ToolMessage 等）序列化为纯字典
# determine_phase: 根据图的 next 节点列表和 values 内容判断当前处于哪个辩论阶段
from backend.utils.serialization import state_to_dict, determine_phase


class DebateService:
    """
    辩论工作流编排器

    职责：
    - 启动新的辩论会话（异步后台执行，不阻塞 HTTP 响应）
    - 查询会话的当前状态和所处阶段
    - 在人工断点处注入数据并恢复工作流继续执行

    注意：本类以模块级单例形式使用（见文件底部），所有请求共享同一个实例，
    _task_errors 是内存级存储，服务重启后会清空。
    """

    def __init__(self):
        """
        初始化辩论服务
        """
        self._task_errors: dict[str, dict] = {}

    def _config(self, thread_id: str) -> dict:
        """
        构建 LangGraph 所需的 config 字典

        参数：
            thread_id: 会话唯一标识（UUID 字符串）

        返回：
            {"configurable": {"thread_id": "..."}} 格式的配置字典
        """
        return {"configurable": {"thread_id": thread_id}}

    async def _run_graph_until_breakpoint(self, config: dict, input_data: dict):
        """
        在后台异步执行辩论工作流，直到遇到断点或正常结束

        这是 start_debate 启动的后台任务的实际执行体。它会一直运行直到三种情况之一发生：
        1. 遇到 interrupt_before 断点（human_filter_1 或 human_filter_2）→ 自动暂停，不抛异常
        2. 图执行到 END 节点 → 正常结束
        3. 抛出未捕获异常 → 记录到 _task_errors 错误信箱

        为什么不能直接在路由中 await 它？
        —— debate_app.ainvoke() 是一个"长时间运行"的协程，可能耗时数十秒甚至数分钟。
        如果路由直接 await，HTTP 请求会一直挂起直到 AI 调用完成，导致超时。

        参数：
            config:     LangGraph 配置字典，包含 thread_id
            input_data: 图的初始输入，如 {"topic": "...", "reference_library": [...]}
        """
        thread_id = config["configurable"]["thread_id"]

        try:
            # 打印启动日志，只显示 thread_id 前8位避免日志过长
            print(f"[DebateService] 🚀 启动辩论工作流 thread={thread_id[:8]}...")

            # 核心调用：异步执行辩论图
            # - input_data 作为图的初始状态注入
            # - config 中的 thread_id 用于 MemorySaver 记录每一步的状态快照
            # - 遇到 interrupt_before 断点时，ainvoke 会正常返回（不抛异常）
            #   此时可以通过 get_state 查询暂停时的状态
            await debate_app.ainvoke(input_data, config)

            # 能走到这里说明图已经完整执行到 END（没有被断点恢复后再次暂停）
            print(f"[DebateService] ✅ 工作流执行完成 thread={thread_id[:8]}")

        except Exception as e:
            # 捕获所有异常并存入错误信箱
            # 注意：这里不重新抛出，因为这是后台独立任务，抛出也没有调用方接收
            error_detail = {
                "message": str(e),                  # 人类可读的错误描述
                "type": type(e).__name__,           # 异常类型，方便前端分类处理
                "traceback": traceback.format_exc(), # 完整调用栈，用于问题定位
            }
            self._task_errors[thread_id] = error_detail

            # 双重日志输出：简洁版（控制台）+ 完整调用栈
            print(f"[DebateService] ❌ 工作流出错 thread={thread_id[:8]} | {type(e).__name__}: {e}")
            traceback.print_exc()

    async def start_debate(self, topic: str) -> tuple[str, dict, str]:
        """
        启动一个新的辩论会话

        这是整个辩论流程的入口方法。采用 fire-and-forget（发射后不管）模式：
        1. 生成全局唯一的 thread_id（UUID4）
        2. 用 asyncio.create_task 创建后台异步任务执行辩论图（不等待结果）
        3. 立即返回 thread_id 和初始状态给路由层，路由层立即响应前端

        前端拿到返回值后，通过轮询 GET /api/state/{thread_id} 来跟踪辩论进度。

        参数：
            topic: 辩题文本（1~500 字符），如 "是否应该实行四天工作制？"

        返回：
            tuple[str, dict, str]:
            - thread_id:     新创建的会话唯一标识（UUID 字符串）
            - state_dict:    初始状态字典，包含 topic 和进度提示文字
            - phase:         当前阶段字符串，此处固定为 "researching"
        """
        # 生成全局唯一的会话 ID（UUID4 基于随机数，碰撞概率极低）
        thread_id = str(uuid4())

        # 构建 LangGraph 所需的配置字典
        config = self._config(thread_id)

        # =============================================================
        # Fire-and-Forget 的关键：asyncio.create_task
        # =============================================================
        # asyncio.create_task 将协程包装为 Task 对象并立即调度到事件循环中执行，
        # 但不会阻塞当前协程——调用瞬间返回，流程继续往下走。
        # 后台任务会在独立的执行上下文中运行，遇到断点或异常自行处理。
        task = asyncio.create_task(
            self._run_graph_until_breakpoint(
                config,
                {
                    "topic": topic,           # 辩题文本，注入到图的初始状态
                    "reference_library": [],  # 初始参考资料为空列表，后续可由调研节点填充
                }
            )
        )

        # 注册任务完成回调：无论成功执行还是抛出异常，都会打印完成日志
        # t.exception() 返回 None 表示任务正常完成，否则返回捕获的异常对象
        task.add_done_callback(
            lambda t: print(
                f"[DebateService] Task完成 thread={thread_id[:8]}, 异常={t.exception()}"
            )
            if t.exception() else None
        )

        # 立即返回——不等待后台任务执行
        # 此时 AI 工作流可能才跑到 analyze 阶段，前端需要通过轮询获取实际进度
        return (
            thread_id,
            {"topic": topic, "progress_message": "🔍 正在分析辩题..."},
            "researching",
        )

    def get_current_state(self, thread_id: str) -> tuple[dict, str]:
        """
        查询指定会话的当前状态（供前端轮询使用）

        参数：
            thread_id: 要查询的会话 ID

        返回：
            tuple[dict, str]:
            - state_dict: 序列化后的状态字典，可直接 JSON 序列化返回给前端
            - phase: 当前阶段，取值包括：
              "input" | "researching" | "review_research" | "provide_feedback"
              | "results" | "error"
        """
        config = self._config(thread_id)

        # 从 MemorySaver 检查点中读取当前状态快照
        # 如果 thread_id 对应的会话尚未执行或已过期，可能抛出异常
        try:
            state = debate_app.get_state(config)
        except Exception as e:
            return (
                {"_error": f"获取状态失败: {e}",
                 "progress_message": f"❌ 状态查询出错: {e}"},
                "error",
            )

        # 将 LangGraph 内部的状态对象序列化为 JSON 兼容的纯字典
        # 例如：HumanMessage 对象 → {"role": "HumanMessage", "content": "..."}
        state_dict = state_to_dict(state.values)

        # 根据 state.next（下一步待执行的节点列表）和 state.values（当前值）
        # 判断辩论目前处于哪个阶段：
        # - human_filter_1 在 next 中 → "review_research"（等待人类审核调研资料）
        # - human_filter_2 在 next 中 → "provide_feedback"（等待人类反馈反驳意见）
        # - next 为空且有 final_summary → "results"（辩论已结束）
        # - 其他情况 → "researching"（AI 正在调研中）
        phase = determine_phase(state)

        # 检查错误信箱：后台异步任务是否有未处理的异常
        if thread_id in self._task_errors:
            err = self._task_errors[thread_id]
            # 将错误详情合并到状态字典中，前端可以据此展示错误信息
            state_dict["_error"] = err["message"]           # 人类可读的错误消息
            state_dict["_error_type"] = err["type"]         # 异常类名，方便前端分类
            state_dict["_error_traceback"] = err["traceback"]  # 完整调用栈，仅调试用
            phase = "error"  # 覆盖阶段为 error，前端可据此展示错误 UI

        return state_dict, phase

    async def submit_review(
        self, thread_id: str, data_a: list, data_b: list
    ) -> tuple[dict, str]:
        """
        在第一个人工断点（资料审核）处注入数据并恢复工作流继续执行

        这是 LangGraph 人机协作（Human-in-the-Loop）模式的标准实现，分为三步：

        1. 工作流已在 human_filter_1 之前自动暂停 ⏸️
        2. 调用 update_state 注入人类审核（或修改）后的调研数据，
           as_node="human_filter_1" 表示"以 human_filter_1 节点的身份写入这些值"，
           这样 LangGraph 会认为该节点已经执行完毕
        3. 调用 ainvoke(None) 从断点之后继续执行（None 表示没有新输入，沿用现有状态）
        4. 图继续执行：argue → rebuttal → 在 human_filter_2 前再次暂停

        参数：
            thread_id: 会话 ID，用于定位到正确的会话状态链
            data_a:    正方（A 方）的调研资料列表，列表元素为字典
            data_b:    反方（B 方）的调研资料列表，列表元素为字典

        返回：
            tuple[dict, str]: (序列化后的状态字典, 当前阶段字符串)

        异常：
            如果执行过程中出错，打印日志和调用栈后重新抛出，由路由层的 try/except
            捕获并转换为 HTTPException(500) 返回给前端
        """
        config = self._config(thread_id)

        try:
            print(f"[DebateService] 📝 提交资料审核 thread={thread_id[:8]}...")

            # 步骤 1：在断点处更新状态
            # update_state 的三个关键参数：
            # - config:   包含 thread_id，定位到正确会话的状态链
            # - values:   要注入的状态数据（调研资料）
            # - as_node:  ★ 关键参数！表示以 human_filter_1 节点的身份写入这些值
            #   写入后 LangGraph 会标记 human_filter_1 为"已完成"，
            #   后续 ainvoke 将从 human_filter_1 的下一个节点（argue）继续执行
            debate_app.update_state(
                config,
                {"research_data_a": data_a, "research_data_b": data_b},
                as_node="human_filter_1",
            )

            # 步骤 2：从断点之后继续执行
            # 传入 None 表示没有新的图输入，工作流从当前检查点继续
            # 执行路径：argue → rebuttal → 在 human_filter_2 前自动暂停
            await debate_app.ainvoke(None, config)

            # 步骤 3：读取执行后的最新状态并返回
            state = debate_app.get_state(config)
            return state_to_dict(state.values), determine_phase(state)

        except Exception as e:
            print(f"[DebateService] ❌ submit_review 失败: {e}")
            traceback.print_exc()
            raise  # 重新抛出异常，由路由层的 try/except 转换为 HTTP 500 响应

    async def submit_feedback(
        self, thread_id: str, feedback: str
    ) -> tuple[dict, str]:
        """
        在第二个人工断点（反驳反馈）处注入人类意见并恢复工作流执行

        这是辩论流程的最后一个人工交互环节。工作流已在 human_filter_2 之前暂停，
        等待人类对 AI 生成的正反方反驳内容提供反馈意见。

        执行流程与 submit_review 完全一致：
        1. update_state(as_node="human_filter_2") 注入人类的反馈意见
        2. ainvoke(None) 从断点之后恢复执行
        3. 图执行最后阶段：refine（根据反馈精炼）→ summarize（生成总结）→ END
        4. 读取最终状态并返回

        参数：
            thread_id: 会话 ID
            feedback:  人类的反馈意见文本（0~2000 字符），可以为空字符串表示无意见

        返回：
            tuple[dict, str]: (序列化后的状态字典, 当前阶段)
            正常完成时 phase 为 "results"，状态字典中包含 final_summary 等最终结果

        异常：
            执行失败时打印日志后重新抛出异常
        """
        config = self._config(thread_id)

        try:
            print(f"[DebateService] 💬 提交裁判反馈 thread={thread_id[:8]}...")

            # 步骤 1：在第二个断点注入人类反馈
            # as_node="human_filter_2" 让 LangGraph 认为该节点已完成，值为 human_feedback
            debate_app.update_state(
                config,
                {"human_feedback": feedback},
                as_node="human_filter_2",
            )

            # 步骤 2：继续执行到最后
            # 执行路径：refine（根据反馈调整论点）→ summarize（生成最终总结）→ END
            await debate_app.ainvoke(None, config)

            # 步骤 3：读取最终状态
            state = debate_app.get_state(config)
            return state_to_dict(state.values), determine_phase(state)

        except Exception as e:
            print(f"[DebateService] ❌ submit_feedback 失败: {e}")
            traceback.print_exc()
            raise  # 重新抛出异常，由路由层统一处理


# =============================================================================
# 模块级单例
# =============================================================================
# 整个应用共享一个 DebateService 实例，所有请求共用同一个 _task_errors 字典。
# 这意味着服务重启后所有后台任务引用和错误记录都会丢失——
# 生产环境中应考虑将状态持久化到 Redis（项目中已有 agent/redis_memory.py 预留能力）。
debate_service = DebateService()
