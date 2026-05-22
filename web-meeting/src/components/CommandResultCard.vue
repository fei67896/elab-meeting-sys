<template>
  <section class="result card">
    <header class="result__header">
      <h3 class="result__title">最近一次执行</h3>
      <span v-if="result" class="tag is-primary">{{ result.intent || 'unknown' }}</span>
    </header>

    <div v-if="!result" class="result__empty text-muted text-small">
      还没有执行任何指令。发出第一条指令试试看，例如：
      <em>"查一下下周一的会"</em>。
    </div>

    <template v-else>
      <p class="result__reply">{{ result.reply_text }}</p>

      <div v-if="hasParams" class="result__block">
        <h4 class="result__block-title">解析的参数</h4>
        <pre class="result__code">{{ pretty(result.params) }}</pre>
      </div>

      <div v-if="hasResult" class="result__block">
        <h4 class="result__block-title">执行返回</h4>
        <pre class="result__code">{{ pretty(result.result) }}</pre>
      </div>
    </template>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  result: { type: Object, default: null },
})

const hasParams = computed(() =>
  props.result && props.result.params && Object.keys(props.result.params).length > 0
)
const hasResult = computed(() =>
  props.result && props.result.result && (
    Array.isArray(props.result.result) || Object.keys(props.result.result || {}).length > 0
  )
)

const pretty = (v) => JSON.stringify(v, null, 2)
</script>

<style scoped>
.result {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.result__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-3);
}
.result__title {
  font-size: var(--fs-h3);
  font-weight: 600;
  margin: 0;
}
.result__empty {
  padding: var(--space-4);
  background: var(--color-surface);
  border-radius: var(--radius);
  border: 1px solid var(--color-border);
}
.result__reply {
  margin: 0;
  padding: var(--space-3) var(--space-4);
  background: var(--color-surface);
  border-left: 3px solid var(--color-text);
  border-radius: 0 var(--radius) var(--radius) 0;
  font-size: var(--fs-body);
  line-height: 1.6;
  color: var(--color-text);
}
.result__block { display: flex; flex-direction: column; gap: 4px; }
.result__block-title {
  margin: 0;
  font-size: var(--fs-tiny);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-2);
}
.result__code {
  margin: 0;
  padding: var(--space-3);
  background: var(--color-surface-2);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  font-family: var(--font-mono);
  font-size: var(--fs-small);
  line-height: 1.5;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 240px;
  overflow: auto;
  color: var(--color-text);
}
</style>
