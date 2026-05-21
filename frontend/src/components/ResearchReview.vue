<template>
  <div class="research-review fade-in">
    <div class="alert-banner warning">
      <span class="alert-icon">⚠️</span>
      <div>
        <strong>流程已暂停 — 请人类裁判介入</strong>
        <p>双方已完成情报搜集与第三方验真，请审阅并筛选资料</p>
      </div>
    </div>

    <h2 class="section-title">
      📌 辩题：<span class="topic-highlight">{{ state.topic || '加载中...' }}</span>
    </h2>

    <div class="review-grid">
      <!-- 正方 -->
      <div class="side-panel side-a">
        <div class="side-header">
          <span class="badge-sm badge-blue">🔵 正方</span>
          <strong>{{ state.sides?.side_a || '正方观点' }}</strong>
        </div>
        <div class="items-list">
          <div
            v-for="(item, i) in localDataA"
            :key="'a_' + i"
            class="research-item"
            :class="{ excluded: !item.valid }"
          >
            <label class="item-checkbox">
              <input
                type="checkbox"
                v-model="item.valid"
                class="custom-checkbox"
              />
              <div class="item-content">
                <span class="item-source">{{ item.source || '网络来源' }}</span>
                <p class="item-text">{{ item.content }}</p>
                <div class="item-score">
                  <span
                    v-for="s in 5"
                    :key="s"
                    class="star"
                    :class="{ filled: s <= (item.score || 3) }"
                  >★</span>
                  <span class="score-label">裁判评分</span>
                </div>
              </div>
            </label>
          </div>
          <div v-if="localDataA.length === 0" class="empty-hint">
            暂无正方资料
          </div>
        </div>
      </div>

      <!-- 反方 -->
      <div class="side-panel side-b">
        <div class="side-header">
          <span class="badge-sm badge-red">🔴 反方</span>
          <strong>{{ state.sides?.side_b || '反方观点' }}</strong>
        </div>
        <div class="items-list">
          <div
            v-for="(item, i) in localDataB"
            :key="'b_' + i"
            class="research-item"
            :class="{ excluded: !item.valid }"
          >
            <label class="item-checkbox">
              <input
                type="checkbox"
                v-model="item.valid"
                class="custom-checkbox"
              />
              <div class="item-content">
                <span class="item-source">{{ item.source || '网络来源' }}</span>
                <p class="item-text">{{ item.content }}</p>
                <div class="item-score">
                  <span
                    v-for="s in 5"
                    :key="s"
                    class="star"
                    :class="{ filled: s <= (item.score || 3) }"
                  >★</span>
                  <span class="score-label">裁判评分</span>
                </div>
              </div>
            </label>
          </div>
          <div v-if="localDataB.length === 0" class="empty-hint">
            暂无反方资料
          </div>
        </div>
      </div>
    </div>

    <div class="submit-area">
      <p class="hint-text">取消勾选你认为不可靠的资料，它们将被排除在后续辩论之外</p>
      <button
        class="btn btn-success"
        :disabled="loading"
        @click="emitSubmit"
      >
        <span v-if="loading" class="spinner"></span>
        {{ loading ? '处理中...' : '✅ 确认资料库，生成一级立论与交叉反驳' }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  state: Object,
  loading: Boolean,
})

const emit = defineEmits(['submit'])

const localDataA = ref([])
const localDataB = ref([])

watch(() => props.state, (newState) => {
  if (newState) {
    localDataA.value = (newState.research_data_a || []).map(item => ({
      ...item,
      valid: item.valid !== false,
    }))
    localDataB.value = (newState.research_data_b || []).map(item => ({
      ...item,
      valid: item.valid !== false,
    }))
  }
}, { immediate: true, deep: true })

function emitSubmit() {
  emit('submit', {
    dataA: localDataA.value,
    dataB: localDataB.value,
  })
}
</script>

<style scoped>
.research-review {
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

.review-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 28px;
}

.side-panel {
  background: var(--bg-card);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.side-panel.side-a {
  border-top: 3px solid var(--accent-blue);
}

.side-panel.side-b {
  border-top: 3px solid var(--accent-red);
}

.side-header {
  padding: 16px 20px;
  background: var(--bg-secondary);
  display: flex;
  align-items: center;
  gap: 10px;
  border-bottom: 1px solid var(--border-color);
}

.side-header strong {
  font-size: 14px;
}

.items-list {
  padding: 12px;
  max-height: 500px;
  overflow-y: auto;
}

.research-item {
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  margin-bottom: 10px;
  transition: var(--transition);
}

.research-item:hover {
  border-color: var(--text-muted);
}

.research-item.excluded {
  opacity: 0.45;
  border-color: transparent;
  background: rgba(255,255,255,0.02);
}

.item-checkbox {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px;
  cursor: pointer;
}

.custom-checkbox {
  margin-top: 3px;
  width: 18px;
  height: 18px;
  accent-color: var(--accent-blue);
  flex-shrink: 0;
  cursor: pointer;
}

.item-content {
  flex: 1;
  min-width: 0;
}

.item-source {
  display: inline-block;
  font-size: 11px;
  font-weight: 600;
  color: var(--accent-purple);
  background: rgba(167, 139, 250, 0.1);
  padding: 2px 8px;
  border-radius: 10px;
  margin-bottom: 6px;
}

.item-text {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 8px;
}

.item-score {
  display: flex;
  align-items: center;
  gap: 4px;
}

.star {
  font-size: 14px;
  color: var(--border-color);
}

.star.filled {
  color: var(--accent-orange);
}

.score-label {
  font-size: 11px;
  color: var(--text-muted);
  margin-left: 6px;
}

.empty-hint {
  text-align: center;
  padding: 30px;
  color: var(--text-muted);
  font-size: 13px;
}

.submit-area {
  text-align: center;
}

.hint-text {
  color: var(--text-muted);
  font-size: 13px;
  margin-bottom: 16px;
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
  .review-grid {
    grid-template-columns: 1fr;
  }
}
</style>
