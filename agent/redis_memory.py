import os
from redis import Redis
from langgraph.checkpoint.redis import RedisSaver, AsyncRedisSaver

REDIS_URL = os.getenv("DP_REDIS_URL", "redis://localhost:6379/0")

redis_client = Redis.from_url(REDIS_URL)

# 同步版：供网关使用（update_state / get_state，主线程安全）
sync_saver = RedisSaver(redis_client=redis_client)

# 异步版：供 Worker 使用（ainvoke / astream）
async_saver = AsyncRedisSaver(redis_url=REDIS_URL)