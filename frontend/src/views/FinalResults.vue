<template>
  <div class="final-results fade-in">
    <div class="celebration">
      <span class="confetti">🎉</span>
      <span class="confetti delay-1">🎊</span>
      <span class="confetti delay-2">✨</span>
    </div>

    <h2 class="results-title">📊 辩论结果</h2>

    <!-- 评分卡 -->
    <div class="score-card card">
      <div class="score-row">
        <div class="score-side side-a">
          <span class="badge-sm badge-blue">🔵 正方</span>
          <span class="score-value">{{ scoreA }}%</span>
          <span class="score-label-text">{{ store.sides.side_a || '正方' }}</span>
        </div>

        <div class="score-vs">
          <span>VS</span>
        </div>

        <div class="score-side side-b">
          <span class="badge-sm badge-red">🔴 反方</span>
          <span class="score-value">{{ scoreB }}%</span>
          <span class="score-label-text">{{ store.sides.side_b || '反方' }}</span>
        </div>
      </div>

      <div class="progress-bar-wrapper">
        <div class="progress-bar">
          <div
            class="progress-fill side-a-fill"
            :style="{ width: scoreA + '%' }"
          ></div>
          <div
            class="progress-fill side-b-fill"
            :style="{ width: scoreB + '%' }"
          ></div>
        </div>
      </div>
    </div>

    <!-- 裁判总结 -->
    <div class="summary-section card">
      <h3>🧠 裁判总结报告</h3>
      <MarkdownContent class="summary-content" :content="store.finalSummary || '暂无总结'" />
    </div>

    <!-- 双方结案陈词 -->
    <h3 class="section-title">🎤 双方最终结案陈词</h3>
    <div class="closing-grid">
      <div class="closing-panel side-a">
        <div class="panel-header">
          <span class="badge-sm badge-blue">🔵 正方</span>
          <strong>结案陈词</strong>
        </div>
        <MarkdownContent class="closing-content" :content="store.arguments.side_a || '暂无'" />
      </div>
      <div class="closing-panel side-b">
        <div class="panel-header">
          <span class="badge-sm badge-red">🔴 反方</span>
          <strong>结案陈词</strong>
        </div>
        <MarkdownContent class="closing-content" :content="store.arguments.side_b || '暂无'" />
      </div>
    </div>

    <!-- 重新开始 -->
    <div class="restart-area">
      <button class="btn btn-outline" @click="store.reset()">
        🔄 开启新一轮辩论
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useDebateStore } from '../stores/debate.js'
import MarkdownContent from '../components/MarkdownContent.vue'

const store = useDebateStore()

const scoreA = computed(() => {
  const s = store.tendencyScore.side_a
  return Math.round((s || 0.5) * 100)
})

const scoreB = computed(() => {
  const s = store.tendencyScore.side_b
  return Math.round((s || 0.5) * 100)
})
</script>

<style scoped>
.final-results {
  max-width: 900px;
  margin: 0 auto;
}

.celebration {
  text-align: center;
  font-size: 48px;
  margin-bottom: 10px;
}

.confetti {
  display: inline-block;
  animation: bounce 1s ease-in-out infinite;
}

.confetti.delay-1 {
  animation-delay: 0.2s;
}

.confetti.delay-2 {
  animation-delay: 0.4s;
}

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-12px); }
}

.results-title {
  text-align: center;
  font-size: 26px;
  margin-bottom: 28px;
}

.score-card {
  text-align: center;
  margin-bottom: 24px;
}

.score-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 40px;
  margin-bottom: 24px;
}

.score-side {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.score-value {
  font-size: 48px;
  font-weight: 800;
  letter-spacing: -1px;
}

.side-a .score-value {
  color: var(--accent-blue);
}

.side-b .score-value {
  color: var(--accent-red);
}

.score-label-text {
  font-size: 13px;
  color: var(--text-secondary);
  max-width: 160px;
  text-align: center;
}

.score-vs {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--bg-secondary);
  border: 2px solid var(--border-color);
  font-weight: 700;
  font-size: 16px;
  color: var(--text-muted);
}

.progress-bar-wrapper {
  padding: 0 10px;
}

.progress-bar {
  height: 12px;
  background: var(--bg-secondary);
  border-radius: 6px;
  overflow: hidden;
  display: flex;
}

.progress-fill {
  height: 100%;
  transition: width 1s ease-out;
}

.side-a-fill {
  background: var(--gradient-1);
}

.side-b-fill {
  background: linear-gradient(135deg, #f87171 0%, #fb923c 100%);
}

.summary-section {
  margin-bottom: 24px;
}

.summary-section h3 {
  font-size: 17px;
  margin-bottom: 14px;
}

.summary-content {
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
  padding: 18px;
  font-size: 14px;
  line-height: 1.8;
  color: var(--text-primary);
  border-left: 3px solid var(--accent-purple);
}

.closing-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 32px;
}

.closing-panel {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.closing-panel.side-a {
  border-top: 3px solid var(--accent-blue);
}

.closing-panel.side-b {
  border-top: 3px solid var(--accent-red);
}

.panel-header {
  padding: 14px 18px;
  background: var(--bg-secondary);
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid var(--border-color);
}

.panel-header strong {
  font-size: 14px;
}

.closing-content {
  padding: 16px 18px;
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-secondary);
  max-height: 300px;
  overflow-y: auto;
}

.restart-area {
  text-align: center;
  padding: 20px 0 40px;
}

@media (max-width: 768px) {
  .score-row {
    gap: 20px;
  }

  .score-value {
    font-size: 36px;
  }

  .closing-grid {
    grid-template-columns: 1fr;
  }
}
</style>
