<template>
  <div class="rebuttal-feedback fade-in">
    <div class="alert-banner warning">
      <span class="alert-icon">⚠️</span>
      <div>
        <strong>流程已暂停 — 请人类裁判给出指导意见</strong>
        <p>双方已完成交叉反驳，审阅后给出你的场外指导</p>
      </div>
    </div>

    <h2 class="section-title">
      📌 辩题：<span class="topic-highlight">{{ store.topic }}</span>
    </h2>

    <div class="debate-grid">
      <!-- 正方 -->
      <div class="debate-panel side-a">
        <div class="panel-header">
          <span class="badge-sm badge-blue">🔵 正方</span>
          <strong>{{ store.sides.side_a || '正方' }}</strong>
        </div>

        <div class="argument-block">
          <h4>📜 一级论述</h4>
          <MarkdownContent class="content-box" :content="store.arguments.side_a || '暂无'" />
        </div>

        <div class="rebuttal-block">
          <h4>⚔️ 针对反方的交叉反驳</h4>
          <MarkdownContent class="content-box rebuttal-box" :content="store.rebuttals.side_a_rebut_b || '暂无'" />
        </div>
      </div>

      <!-- 反方 -->
      <div class="debate-panel side-b">
        <div class="panel-header">
          <span class="badge-sm badge-red">🔴 反方</span>
          <strong>{{ store.sides.side_b || '反方' }}</strong>
        </div>

        <div class="argument-block">
          <h4>📜 一级论述</h4>
          <MarkdownContent class="content-box" :content="store.arguments.side_b || '暂无'" />
        </div>

        <div class="rebuttal-block">
          <h4>⚔️ 针对正方的交叉反驳</h4>
          <MarkdownContent class="content-box rebuttal-box" :content="store.rebuttals.side_b_rebut_a || '暂无'" />
        </div>
      </div>
    </div>

    <div class="feedback-section card">
      <h3>🧠 裁判场外指导</h3>
      <p class="feedback-hint">
        请指出双方辩论中的漏洞，或指定他们接下来的主攻方向（可选）
      </p>
      <textarea
        v-model="feedback"
        class="text-input textarea"
        placeholder="例如：正方不要纠结于细节数据，请从宏观经济学角度重新升华你们的结论。（留空则表示无需指导意见）"
      ></textarea>
      <div class="feedback-actions">
        <button
          class="btn btn-primary"
          :disabled="store.loading"
          @click="handleSubmit"
        >
          <span v-if="store.loading" class="spinner"></span>
          {{ store.loading ? '处理中...' : '🔥 提交指导意见，生成结案陈词与最终判决' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useDebateStore } from '../stores/debate.js'
import MarkdownContent from '../components/MarkdownContent.vue'

const store = useDebateStore()
const feedback = ref('')

function handleSubmit() {
  if (store.loading) return
  store.submitFeedback(feedback.value.trim())
}
</script>

<style scoped>
.rebuttal-feedback {
  max-width: 1100px;
  margin: 0 auto;
}

.alert-banner {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 18px 22px;
  border-radius: var(--radius-sm);
  margin-bottom: 28px;
}

.alert-banner.warning {
  background: rgba(251, 191, 36, 0.1);
  border: 1px solid rgba(251, 191, 36, 0.3);
}

.alert-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.alert-banner strong {
  display: block;
  font-size: 15px;
  margin-bottom: 4px;
}

.alert-banner p {
  color: var(--text-secondary);
  font-size: 13px;
}

.topic-highlight {
  color: var(--accent-blue);
}

.debate-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 28px;
}

.debate-panel {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.debate-panel.side-a {
  border-top: 3px solid var(--accent-blue);
}

.debate-panel.side-b {
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

.argument-block,
.rebuttal-block {
  padding: 16px 18px;
  border-bottom: 1px solid var(--border-color);
}

.argument-block:last-child,
.rebuttal-block:last-child {
  border-bottom: none;
}

.argument-block h4,
.rebuttal-block h4 {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 10px;
}

.content-box {
  background: var(--bg-secondary);
  border-radius: var(--radius-sm);
  padding: 14px 16px;
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-primary);
}

.rebuttal-box {
  border-left: 3px solid var(--accent-orange);
}

.feedback-section {
  margin-bottom: 20px;
}

.feedback-section h3 {
  font-size: 17px;
  margin-bottom: 6px;
}

.feedback-hint {
  color: var(--text-secondary);
  font-size: 13px;
  margin-bottom: 16px;
}

.feedback-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  display: inline-block;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .debate-grid {
    grid-template-columns: 1fr;
  }
}
</style>
