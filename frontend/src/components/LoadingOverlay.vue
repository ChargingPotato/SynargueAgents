<template>
  <div class="loading-overlay fade-in">
    <div class="loading-card card">
      <div class="loading-animation">
        <div class="orb orb-1"></div>
        <div class="orb orb-2"></div>
        <div class="orb orb-3"></div>
      </div>
      <p class="loading-phase">{{ phaseLabel }}</p>
      <p class="loading-message">{{ message }}</p>
      <div class="loading-bar-wrapper">
        <div class="loading-bar"></div>
      </div>
      <p class="loading-hint">AI Agent 正在进行多步推理，请耐心等待...</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  message: {
    type: String,
    default: '处理中...',
  },
})

const phaseLabel = computed(() => {
  const msg = props.message || ''
  if (msg.includes('辩题分析')) return '📋 阶段 1/5: 辩题分析'
  if (msg.includes('搜索') || msg.includes('搜集')) return '🔍 阶段 2/5: 双轨情报搜集'
  if (msg.includes('验真') || msg.includes('打分')) return '⚖️ 阶段 3/5: 资料验真'
  if (msg.includes('立论') || msg.includes('反驳')) return '⚔️ 阶段 4/5: 辩论交锋'
  if (msg.includes('结案') || msg.includes('判决') || msg.includes('裁判')) return '🏆 阶段 5/5: 最终判决'
  return '🔄 处理中...'
})
</script>

<style scoped>
.loading-overlay {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.loading-card {
  text-align: center;
  padding: 50px 60px;
  max-width: 520px;
  width: 100%;
}

.loading-animation {
  display: flex;
  justify-content: center;
  gap: 14px;
  margin-bottom: 28px;
}

.orb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  animation: orbBounce 1.2s ease-in-out infinite;
}

.orb-1 {
  background: var(--accent-blue);
  animation-delay: 0s;
}

.orb-2 {
  background: var(--accent-purple);
  animation-delay: 0.2s;
}

.orb-3 {
  background: var(--accent-green);
  animation-delay: 0.4s;
}

@keyframes orbBounce {
  0%, 80%, 100% {
    transform: scale(1);
    opacity: 0.6;
  }
  40% {
    transform: scale(1.5);
    opacity: 1;
  }
}

.loading-phase {
  font-size: 13px;
  font-weight: 600;
  color: var(--accent-blue);
  margin-bottom: 8px;
  letter-spacing: 0.5px;
}

.loading-message {
  font-size: 15px;
  color: var(--text-secondary);
  margin-bottom: 24px;
  line-height: 1.6;
}

.loading-hint {
  font-size: 12px;
  color: var(--text-secondary);
  opacity: 0.6;
  margin-top: 16px;
}

.loading-bar-wrapper {
  height: 4px;
  background: var(--bg-secondary);
  border-radius: 2px;
  overflow: hidden;
}

.loading-bar {
  height: 100%;
  width: 30%;
  background: var(--gradient-1);
  border-radius: 2px;
  animation: loadingSlide 1.8s ease-in-out infinite;
}

@keyframes loadingSlide {
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(430%);
  }
}
</style>
