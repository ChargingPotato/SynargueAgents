<template>
  <div class="markdown-content" v-html="renderedHtml"></div>
</template>

<script setup>
import { computed } from 'vue'
import { marked } from 'marked'

const props = defineProps({
  content: { type: String, default: '' },
})

marked.setOptions({
  breaks: true,
  gfm: true,
})

const renderedHtml = computed(() => {
  if (!props.content) return ''
  return marked.parse(props.content)
})
</script>

<style scoped>
.markdown-content :deep(h1) {
  font-size: 22px;
  font-weight: 700;
  margin: 20px 0 12px;
  color: var(--text-primary, #e5e7f0);
  border-bottom: 1px solid var(--border-color, #2a2d45);
  padding-bottom: 8px;
}

.markdown-content :deep(h2) {
  font-size: 18px;
  font-weight: 700;
  margin: 18px 0 10px;
  color: var(--text-primary, #e5e7f0);
}

.markdown-content :deep(h3) {
  font-size: 15px;
  font-weight: 600;
  margin: 14px 0 8px;
  color: var(--text-secondary, #94a3b8);
}

.markdown-content :deep(p) {
  margin: 8px 0;
  line-height: 1.75;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  margin: 8px 0;
  padding-left: 20px;
}

.markdown-content :deep(li) {
  margin: 4px 0;
  line-height: 1.65;
}

.markdown-content :deep(strong) {
  font-weight: 700;
  color: var(--text-primary, #e5e7f0);
}

.markdown-content :deep(em) {
  font-style: italic;
  color: var(--text-secondary, #94a3b8);
}

.markdown-content :deep(code) {
  font-family: 'Fira Code', 'Cascadia Code', 'Consolas', monospace;
  font-size: 12px;
  background: rgba(167, 139, 250, 0.1);
  color: var(--accent-purple, #a78bfa);
  padding: 2px 6px;
  border-radius: 3px;
}

.markdown-content :deep(pre) {
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid var(--border-color, #2a2d45);
  border-radius: 6px;
  padding: 14px 16px;
  margin: 12px 0;
  overflow-x: auto;
}

.markdown-content :deep(pre code) {
  background: none;
  color: var(--text-secondary, #94a3b8);
  padding: 0;
  font-size: 12px;
  line-height: 1.6;
}

.markdown-content :deep(blockquote) {
  border-left: 3px solid var(--accent-blue, #60a5fa);
  padding: 8px 14px;
  margin: 12px 0;
  background: rgba(96, 165, 250, 0.05);
  border-radius: 0 4px 4px 0;
  color: var(--text-secondary, #94a3b8);
}

.markdown-content :deep(a) {
  color: var(--accent-blue, #60a5fa);
  text-decoration: underline;
  text-underline-offset: 2px;
}

.markdown-content :deep(hr) {
  border: none;
  border-top: 1px solid var(--border-color, #2a2d45);
  margin: 16px 0;
}

.markdown-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 12px 0;
  font-size: 13px;
}

.markdown-content :deep(th) {
  background: var(--bg-secondary, #1a1c2e);
  padding: 8px 12px;
  text-align: left;
  font-weight: 600;
  border: 1px solid var(--border-color, #2a2d45);
}

.markdown-content :deep(td) {
  padding: 8px 12px;
  border: 1px solid var(--border-color, #2a2d45);
}

.markdown-content :deep(*) {
  max-width: 100%;
  word-break: break-word;
}
</style>
