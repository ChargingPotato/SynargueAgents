<template>
  <div class="loading-overlay fade-in">
    <div class="loading-card card">
      <div class="loading-animation">
        <div class="orb orb-1"></div>
        <div class="orb orb-2"></div>
        <div class="orb orb-3"></div>
      </div>
      <p class="loading-message">{{ message }}</p>
      <div class="loading-bar-wrapper">
        <div class="loading-bar"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  message: {
    type: String,
    default: '处理中...',
  },
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
  max-width: 480px;
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

.loading-message {
  font-size: 15px;
  color: var(--text-secondary);
  margin-bottom: 24px;
  line-height: 1.6;
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
