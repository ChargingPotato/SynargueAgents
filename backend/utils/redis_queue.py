import json
from redis import Redis

DEBATE_QUEUE_KEY = "debate_tasks"
ERROR_PREFIX = "debate_error"


def push_task(
    redis_client: Redis,
    thread_id: str,
    action: str,
    state_payload: dict | None = None,
) -> None:
    """LPUSH 任务到 debate_tasks 队列"""
    payload = {
        "thread_id": thread_id,
        "action": action,
    }
    if state_payload is not None:
        payload["state_payload"] = state_payload
    redis_client.lpush(DEBATE_QUEUE_KEY, json.dumps(payload, ensure_ascii=False))


def pop_task(redis_client: Redis, timeout: int = 0) -> dict | None:
    """BRPOP 阻塞式出队一条任务，返回解析后的 dict 或 None"""
    result = redis_client.brpop(DEBATE_QUEUE_KEY, timeout=timeout)
    if result is None:
        return None
    _, raw = result
    return json.loads(raw)


def set_error(
    redis_client: Redis,
    thread_id: str,
    message: str,
    error_type: str = "",
    traceback_str: str = "",
) -> None:
    """将 Worker 异常写入 Redis，供 gateway 轮询读取"""
    key = f"{ERROR_PREFIX}:{thread_id}"
    data = {
        "_error": message,
        "_error_type": error_type,
        "_error_traceback": traceback_str,
    }
    redis_client.set(key, json.dumps(data, ensure_ascii=False), ex=3600)


def get_error(redis_client: Redis, thread_id: str) -> dict | None:
    """读取 Worker 异常信息，读取后立即删除"""
    key = f"{ERROR_PREFIX}:{thread_id}"
    raw = redis_client.get(key)
    if raw is None:
        return None
    redis_client.delete(key)
    return json.loads(raw)


def get_queue_length(redis_client: Redis) -> int:
    """获取当前队列中待处理任务数"""
    return redis_client.llen(DEBATE_QUEUE_KEY)
