<template>
  <div class="debate-input fade-in">
    <div class="hero-section">
      <div class="hero-icon">⚖️</div>
      <h2>开启一场深度辩论</h2>
      <p>
        系统将实例化两个立场对立的 AI Agent，自动在全网搜集证据，
        并进行激烈的交叉反驳。您在关键节点可介入指导。
      </p>
    </div>

    <div class="input-card card">
      <label class="input-label">请输入辩题或纠结的决策</label>
      <input
        v-model="topic"
        type="text"
        class="text-input topic-input"
        placeholder="例如：燃油车是否会在10年内被彻底淘汰？"
        @keydown.enter="handleStart"
      />
      <div class="input-actions">
        <button
          class="btn btn-primary start-btn"
          :disabled="!topic.trim() || store.loading"
          @click="handleStart"
        >
          <span v-if="store.loading" class="spinner"></span>
          <span v-else>🚀</span>
          {{ store.loading ? '辩论启动中...' : '启动多智能体辩论' }}
        </button>
      </div>
    </div>

    <div class="features">
      <div class="feature-item">
        <span class="feature-icon">🔍</span>
        <div>
          <strong>双轨情报搜集</strong>
          <p>正反双方独立搜索网络资料</p>
        </div>
      </div>
      <div class="feature-item">
        <span class="feature-icon">⚔️</span>
        <div>
          <strong>交叉反驳</strong>
          <p>双方针对对方论点进行激烈反驳</p>
        </div>
      </div>
      <div class="feature-item">
        <span class="feature-icon">👨‍⚖️</span>
        <div>
          <strong>人类裁判介入</strong>
          <p>关键节点人工审核与指导</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useDebateStore } from '../stores/debate.js'

const store = useDebateStore()
const topic = ref('')

function handleStart() {
  if (!topic.value.trim() || store.loading) return
  store.startDebate(topic.value.trim())
}
</script>

<style scoped>
.debate-input {
  max-width: 720px;
  margin: 0 auto;
  padding-top: 20px;
}

.hero-section {
  text-align: center;
  margin-bottom: 40px;
}

.hero-icon {
  font-size: 64px;
  margin-bottom: 16px;
}

.hero-section h2 {
  font-size: 30px;
  font-weight: 700;
  margin-bottom: 12px;
  background: var(--gradient-1);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-section p {
  color: var(--text-secondary);
  font-size: 15px;
  max-width: 500px;
  margin: 0 auto;
  line-height: 1.7;
}

.input-card {
  margin-bottom: 40px;
}

.input-label {
  display: block;
  font-weight: 600;
  font-size: 15px;
  margin-bottom: 14px;
  color: var(--text-primary);
}

.topic-input {
  font-size: 16px;
  padding: 16px 20px;
  margin-bottom: 20px;
}

.input-actions {
  display: flex;
  justify-content: flex-end;
}

.start-btn {
  padding: 14px 36px;
  font-size: 16px;
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.features {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
}

.feature-item {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  padding: 20px;
  display: flex;
  gap: 14px;
  align-items: flex-start;
}

.feature-icon {
  font-size: 26px;
  flex-shrink: 0;
}

.feature-item strong {
  display: block;
  font-size: 14px;
  margin-bottom: 4px;
}

.feature-item p {
  color: var(--text-secondary);
  font-size: 13px;
}

@media (max-width: 640px) {
  .features {
    grid-template-columns: 1fr;
  }
}
</style>
