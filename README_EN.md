# Synargue

[中文](README.md) · [English](README_EN.md)

A multi-agent debate and decision-making system powered by LangGraph. Two AI agents (pro/con) conduct structured debates on any topic — gathering evidence via web search, cross-examining each other's arguments, and ultimately receiving a verdict from an AI judge.

## Tech Stack

| Layer        | Technology             |
| ------------ | ---------------------- |
| Frontend     | Vue 3 + Pinia + Vite   |
| Backend      | FastAPI + Pydantic v2  |
| AI Workflow  | LangGraph + LangChain  |
| LLM          | DeepSeek               |
| Search       | BochaAI Web Search     |
| Message Queue| Redis                  |

## Workflow

1. **Analyze** — Break the topic into pro and con positions
2. **Research** — Both sides independently search the web for evidence
3. **Verify** — A neutral judge scores each piece of evidence (1-5)
4. **Filter** 🔴 Human-in-the-loop — User selects credible sources
5. **Argue** — Both sides write opening arguments
6. **Rebuttal** — Cross-examine the opponent's claims
7. **Feedback** 🔴 Human-in-the-loop — User provides guidance as referee
8. **Refine** — Both sides strengthen their case with the feedback
9. **Verdict** — AI judge delivers a summary and weighted score

## Quick Start

### Prerequisites

- Python 3.13+
- Node.js
- Redis
- uv package manager

### Install

```bash
# Python dependencies
uv sync

# Frontend dependencies
cd frontend && npm install && cd ..
```

### Configure

Create a `.env` file:

```env
DEEPSEEK_API_KEY=sk-your-deepseek-key
BOCHA_API_KEY=sk-your-bocha-search-key
```

### Run

One-click launch (recommended):

```powershell
.\start.ps1
```

Or start the three services separately:

```bash
# Terminal 1: Worker
uv run python -m backend.worker

# Terminal 2: FastAPI
uv run uvicorn backend.main:app --host 0.0.0.0 --port 8000

# Terminal 3: Frontend dev server
cd frontend && npm run dev
```

Open `http://localhost:5173` in your browser.

## Project Structure

```text
Synargue/
├── agent/                 # LangGraph debate workflow (10-node StateGraph)
│   ├── graph.py           # Workflow definition
│   ├── nodes.py           # Node execution logic
│   ├── state.py           # State schema
│   ├── models.py          # LLM configuration
│   └── tools.py           # Web search tool
├── backend/               # FastAPI gateway + Worker
│   ├── main.py            # API entry point
│   ├── worker.py          # Redis queue consumer
│   ├── routers/           # API routes
│   ├── services/          # Business logic
│   └── utils/             # Utility functions
├── frontend/              # Vue 3 frontend
│   └── src/
│       ├── views/         # Page components
│       ├── stores/        # Pinia state management
│       └── components/    # Shared components
└── start.ps1              # One-click launch script
```

## License

MIT License
