<template>
  <div class="app-container">
    <!-- 顶栏 -->
    <header class="app-header">
      <div class="header-content">
        <div class="logo">
          <span class="logo-icon">⚖️</span>
          <h1>DecisionPal</h1>
        </div>
        <p class="subtitle">多智能体对抗演练与决策系统</p>
      </div>
      <div class="header-badge">
        <span class="badge">LangGraph · Multi-Agent</span>
      </div>
    </header>

    <!-- 主内容区 -->
    <main class="app-main">
      <!-- 阶段：输入辩题 -->
      <DebateInput
        v-if="phase === 'input'"
        :loading="loading"
        @start="handleStart"
      />

      <!-- 阶段：资料审核 -->
      <ResearchReview
        v-else-if="phase === 'review_research'"
        :state="state"
        :loading="loading"
        @submit="handleReview"
      />

      <!-- 阶段：反驳反馈 -->
      <RebuttalFeedback
        v-else-if="phase === 'provide_feedback'"
        :state="state"
        :loading="loading"
        @submit="handleFeedback"
      />

      <!-- 阶段：最终结果 -->
      <FinalResults
        v-else-if="phase === 'results'"
        :state="state"
        @restart="handleRestart"
      />

      <!-- 运行中 / 未知 -->
      <LoadingOverlay v-else :message="loadingMessage" />
    </main>

    <!-- 底部 -->
    <footer class="app-footer">
      <p>基于 LangGraph 构建 · Human-in-the-Loop 架构</p>
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import DebateInput from './components/DebateInput.vue'
import ResearchReview from './components/ResearchReview.vue'
import RebuttalFeedback from './components/RebuttalFeedback.vue'
import FinalResults from './components/FinalResults.vue'
import LoadingOverlay from './components/LoadingOverlay.vue'
import { getState, startDebate, submitReview, submitFeedback } from './api.js'

const phase = ref('input')
const state = ref({})
const threadId = ref(null)
const loading = ref(false)
const loadingMessage = ref('系统初始化中...')

async function handleStart(topic) {
  loading.value = true
  loadingMessage.value = '🕵️ Agent A 与 Agent B 正在交替进行全网深度调查，请耐心等待...'
  try {
    const res = await startDebate(topic)
    threadId.value = res.data.thread_id
    phase.value = res.data.phase
    state.value = res.data.state
  } catch (err) {
    alert('启动辩论失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    loading.value = false
  }
}

async function handleReview(payload) {
  loading.value = true
  loadingMessage.value = '⚔️ 双方辩手正在立论与交叉反驳...'
  try {
    const res = await submitReview(
      threadId.value,
      payload.dataA,
      payload.dataB
    )
    phase.value = res.data.phase
    state.value = res.data.state
  } catch (err) {
    alert('提交审核失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    loading.value = false
  }
}

async function handleFeedback(feedback) {
  loading.value = true
  loadingMessage.value = '🛠️ 双方正在吸收反馈修补漏洞，裁判正在撰写最终报告...'
  try {
    const res = await submitFeedback(threadId.value, feedback)
    phase.value = res.data.phase
    state.value = res.data.state
  } catch (err) {
    alert('提交反馈失败: ' + (err.response?.data?.detail || err.message))
  } finally {
    loading.value = false
  }
}

function handleRestart() {
  threadId.value = null
  state.value = {}
  phase.value = 'input'
}
</script>

<style>
/* ========= 全局重置 & CSS 变量 ========= */
*,
*::before,
*::after {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  --bg-primary: #0f1119;
  --bg-secondary: #1a1d2e;
  --bg-card: #222640;
  --bg-card-hover: #2a2f4a;
  --border-color: #2e3350;
  --text-primary: #e8eaf0;
  --text-secondary: #989bb5;
  --text-muted: #6b6f8a;
  --accent-blue: #6c8cff;
  --accent-blue-hover: #5a7af0;
  --accent-green: #4ade80;
  --accent-red: #f87171;
  --accent-orange: #fbbf24;
  --accent-purple: #a78bfa;
  --gradient-1: linear-gradient(135deg, #6c8cff 0%, #a78bfa 100%);
  --gradient-2: linear-gradient(135deg, #4ade80 0%, #22d3ee 100%);
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.4);
  --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.5);
  --shadow-lg: 0 8px 32px rgba(0, 0, 0, 0.6);
  --radius-sm: 8px;
  --radius-md: 14px;
  --radius-lg: 20px;
  --transition: 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

body {
  font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif;
  background: var(--bg-primary);
  color: var(--text-primary);
  min-height: 100vh;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}

/* ========= App 布局 ========= */
.app-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.app-header {
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
  padding: 18px 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-icon {
  font-size: 32px;
}

.logo h1 {
  font-size: 22px;
  font-weight: 700;
  background: var(--gradient-1);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.subtitle {
  color: var(--text-secondary);
  font-size: 14px;
  padding-left: 14px;
  border-left: 1px solid var(--border-color);
}

.header-badge .badge {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  color: var(--text-secondary);
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  letter-spacing: 0.5px;
}

.app-main {
  flex: 1;
  padding: 32px;
  max-width: 1100px;
  width: 100%;
  margin: 0 auto;
}

.app-footer {
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-color);
  padding: 14px 32px;
  text-align: center;
  color: var(--text-muted);
  font-size: 12px;
}

/* ========= 通用组件样式 ========= */
.card {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 28px;
  box-shadow: var(--shadow-sm);
  transition: var(--transition);
}

.card:hover {
  box-shadow: var(--shadow-md);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 28px;
  border: none;
  border-radius: var(--radius-sm);
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: var(--transition);
  color: #fff;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--gradient-1);
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 20px rgba(108, 140, 255, 0.4);
}

.btn-success {
  background: var(--gradient-2);
}

.btn-success:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 20px rgba(74, 222, 128, 0.4);
}

.btn-outline {
  background: transparent;
  border: 1px solid var(--border-color);
  color: var(--text-primary);
}

.btn-outline:hover:not(:disabled) {
  border-color: var(--accent-blue);
  color: var(--accent-blue);
}

.text-input {
  width: 100%;
  padding: 14px 18px;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 15px;
  transition: var(--transition);
  outline: none;
  font-family: inherit;
}

.text-input:focus {
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 3px rgba(108, 140, 255, 0.15);
}

.text-input::placeholder {
  color: var(--text-muted);
}

.textarea {
  resize: vertical;
  min-height: 120px;
  line-height: 1.7;
}

.section-title {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.badge-sm {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
}

.badge-blue {
  background: rgba(108, 140, 255, 0.15);
  color: var(--accent-blue);
}

.badge-green {
  background: rgba(74, 222, 128, 0.15);
  color: var(--accent-green);
}

.badge-red {
  background: rgba(248, 113, 113, 0.15);
  color: var(--accent-red);
}

/* ========= 动画 ========= */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}

.fade-in {
  animation: fadeInUp 0.5s ease-out;
}

/* 滚动条 */
::-webkit-scrollbar {
  width: 6px;
}

::-webkit-scrollbar-track {
  background: var(--bg-secondary);
}

::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: var(--text-muted);
}
</style>
