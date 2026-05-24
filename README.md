# Synargue

[中文](README.md) · [English](README_EN.md)

基于 LangGraph 的多智能体辩论与决策系统。两名 AI 智能体（正方/反方）针对任意话题进行结构化辩论，通过联网搜索收集证据、交叉质询，最终由 AI 裁判作出裁决。

## 技术栈

| 层级     | 技术                   |
| -------- | ---------------------- |
| 前端     | Vue 3 + Pinia + Vite   |
| 后端     | FastAPI + Pydantic v2  |
| AI 编排  | LangGraph + LangChain  |
| LLM      | DeepSeek               |
| 搜索     | BochaAI Web Search     |
| 消息队列 | Redis                  |

## 工作流

1. **分析** — 将话题拆分为正反立场
2. **研究** — 双方独立联网搜索收集证据
3. **验证** — 第三方裁判对证据可信度评分（1-5）
4. **筛选** 🔴 人在环中 — 用户勾选可信资料
5. **辩论** — 双方撰写一级论证
6. **反驳** — 交叉质询对方论点
7. **反馈** 🔴 人在环中 — 用户提供裁判指导意见
8. **修正** — 双方根据反馈完善陈词
9. **裁决** — AI 裁判生成总结报告及倾向性评分

## 快速开始

### 环境要求

- Python 3.13+
- Node.js
- Redis
- uv 包管理器

### 安装

```bash
# Python 依赖
uv sync

# 前端依赖
cd frontend && npm install && cd ..
```

### 配置

创建 `.env` 文件：

```env
DEEPSEEK_API_KEY=sk-your-deepseek-key
BOCHA_API_KEY=sk-your-bocha-search-key
```

### 运行

一键启动（推荐）：

```powershell
.\start.ps1
```

或分别启动三个服务：

```bash
# 终端 1: Worker
uv run python -m backend.worker

# 终端 2: FastAPI
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000

# 终端 3: 前端开发服务器
cd frontend && npm run dev
```

访问 `http://localhost:5173` 即可使用。

## 项目结构

```text
Synargue/
├── agent/                 # LangGraph 辩论工作流（10 节点 StateGraph）
│   ├── graph.py           # 工作流定义
│   ├── nodes.py           # 节点执行逻辑
│   ├── state.py           # 状态 Schema
│   ├── models.py          # LLM 配置
│   └── tools.py           # 联网搜索工具
├── backend/               # FastAPI 网关 + Worker
│   ├── main.py            # API 入口
│   ├── worker.py          # Redis 队列消费者
│   ├── routers/           # API 路由
│   ├── services/          # 业务逻辑
│   └── utils/             # 工具函数
├── frontend/              # Vue 3 前端
│   └── src/
│       ├── views/         # 页面组件（输入/审核/反馈/结果）
│       ├── stores/        # Pinia 状态管理
│       └── components/    # 通用组件
└── start.ps1              # 一键启动脚本
```

## 许可

MIT License
