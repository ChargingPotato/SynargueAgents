<template>
  <nav class="phase-tabs">
    <button
      v-for="phase in phases"
      :key="phase"
      class="tab-btn"
      :class="{ active: phase === activePhase }"
      @click="$emit('select', phase)"
    >
      <span class="tab-icon">{{ phaseMap[phase]?.icon || '📌' }}</span>
      <span class="tab-label">{{ phaseMap[phase]?.label || phase }}</span>
    </button>
  </nav>
</template>

<script setup>
defineProps({
  phases: { type: Array, default: () => [] },
  activePhase: { type: String, default: 'input' },
  phaseMap: { type: Object, default: () => ({}) },
})

defineEmits(['select'])
</script>

<style scoped>
.phase-tabs {
  display: flex;
  gap: 6px;
  padding: 12px 24px;
  background: var(--bg-secondary, #1a1c2e);
  border-bottom: 1px solid var(--border-color, #2a2d45);
  overflow-x: auto;
  -webkit-overflow-scrolling: touch;
}

.phase-tabs::-webkit-scrollbar {
  height: 0;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px;
  border-radius: var(--radius-sm, 8px);
  border: 1px solid transparent;
  background: transparent;
  color: var(--text-muted, #64748b);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
  flex-shrink: 0;
}

.tab-btn:hover {
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-secondary, #94a3b8);
}

.tab-btn.active {
  background: var(--bg-card, #222640);
  border-color: var(--accent-blue, #60a5fa);
  color: var(--text-primary, #e5e7f0);
  box-shadow: 0 2px 8px rgba(96, 165, 250, 0.12);
}

.tab-icon {
  font-size: 15px;
}

.tab-label {
  font-size: 13px;
}

@media (max-width: 640px) {
  .phase-tabs {
    padding: 10px 12px;
    gap: 4px;
  }

  .tab-btn {
    padding: 8px 12px;
    font-size: 12px;
  }

  .tab-label {
    font-size: 11px;
  }
}
</style>
