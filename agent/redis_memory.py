# redis_memory.py
from redis import Redis
from langgraph.checkpoint.redis import RedisSaver

# 建立 Redis 连接（可根据需要修改配置）
redis_client = Redis(host='localhost', port=6379, db=0)

# 创建 RedisSaver 实例，后续供工作流使用
memory_saver = RedisSaver(redis_client)