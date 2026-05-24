<template>
  <div class="app-container">
    <header class="app-header">
      <div class="header-content">
        <div class="logo">
          <span class="logo-icon">⚖️</span>
          <h1>Synargue</h1>
        </div>
        <p class="subtitle">多智能体对抗演练与决策系统</p>
      </div>
      <div class="header-badge">
        <span class="badge">LangGraph · Multi-Agent</span>
      </div>
    </header>

    <main class="app-main">
      <LoadingOverlay
        v-if="store.loading"
        :message="store.progressMessage || store.loadingMessage"
      />
      <div v-else-if="store.error" class="error-banner card">
        <div class="error-icon">❌</div>
        <h3>执行出错</h3>
        <p class="error-detail">{{ store.error }}</p>
        <div v-if="store.errorTraceback" class="error-trace">
          <details>
            <summary>📋 查看完整错误堆栈 (开发者调试用)</summary>
            <pre class="trace-content">{{ store.errorTraceback }}</pre>
          </details>
        </div>
        <button class="btn btn-primary" @click="store.reset()">返回首页</button>
      </div>
      <template v-else>
        <PhaseTabs
          :phases="store.availablePhases"
          :activePhase="store.activePhase"
          :phaseMap="phaseLabelMap"
          @select="store.setActivePhase"
        />
        <div class="phase-content">
          <DebateInput v-show="store.activePhase === 'input'" />
          <ResearchReview v-show="store.activePhase === 'review_research'" />
          <RebuttalFeedback v-show="store.activePhase === 'provide_feedback'" />
          <FinalResults v-show="store.activePhase === 'results'" />
        </div>
      </template>
    </main>

    <footer class="app-footer">
      <p>基于 LangGraph 构建 · Human-in-the-Loop 架构</p>
    </footer>
  </div>
</template>

<script setup>
import { useDebateStore } from './stores/debate.js'
import LoadingOverlay from './components/LoadingOverlay.vue'
import PhaseTabs from './components/PhaseTabs.vue'
import DebateInput from './views/DebateInput.vue'
import ResearchReview from './views/ResearchReview.vue'
import RebuttalFeedback from './views/RebuttalFeedback.vue'
import FinalResults from './views/FinalResults.vue'

const store = useDebateStore()

const phaseLabelMap = {
  input:             { icon: '📋', label: '辩题输入' },
  review_research:   { icon: '🔍', label: '资料审核' },
  provide_feedback:  { icon: '💬', label: '交叉反驳' },
  results:           { icon: '📊', label: '最终结果' },
}
</script>

<style>
.phase-content {
  min-height: 60vh;
}

.error-banner {
  max-width: 700px;
  margin: 40px auto;
  text-align: center;
}

.error-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.error-banner h3 {
  font-size: 20px;
  margin-bottom: 12px;
  color: #f87171;
}

.error-detail {
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 16px;
  white-space: pre-wrap;
  word-break: break-word;
}

.error-trace {
  text-align: left;
  margin-bottom: 20px;
}

.error-trace details {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 8px;
  padding: 10px 14px;
}

.error-trace summary {
  cursor: pointer;
  font-size: 13px;
  color: var(--text-secondary);
  user-select: none;
}

.trace-content {
  margin-top: 10px;
  font-size: 11px;
  line-height: 1.5;
  max-height: 300px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-break: break-all;
  color: #ef4444;
  background: rgba(239, 68, 68, 0.05);
  padding: 10px;
  border-radius: 4px;
}
</style>
