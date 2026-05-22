<template>
  <ol class="agenda" v-if="agendas.length">
    <li v-for="(a, i) in agendas" :key="a.id || i" class="agenda__item">
      <span class="agenda__seq">{{ String(a.seq || i + 1).padStart(2, '0') }}</span>
      <div class="agenda__body">
        <p class="agenda__topic">{{ a.topic }}</p>
        <div class="agenda__meta">
          <span class="tag is-primary text-tiny">{{ categoryLabel(a.category) }}</span>
          <span class="tag text-tiny">{{ a.mode === 'offline' ? '线下' : '线上' }}</span>
          <span v-if="a.owner" class="text-tiny text-muted">主讲: {{ a.owner }}</span>
          <span v-if="a.duration_min" class="text-tiny text-muted">{{ a.duration_min }} 分钟</span>
        </div>
        <p v-if="a.notes" class="text-small text-muted">{{ a.notes }}</p>
      </div>
    </li>
  </ol>
  <p v-else class="text-muted text-small">尚未添加议程。</p>
</template>

<script setup>
import { CATEGORY_LABEL } from '../utils/format'
defineProps({ agendas: { type: Array, default: () => [] } })
const categoryLabel = (v) => CATEGORY_LABEL[v] || v || '综合'
</script>

<style scoped>
.agenda {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.agenda__item {
  display: grid;
  grid-template-columns: 36px 1fr;
  gap: var(--space-3);
  padding: var(--space-3) 0;
  border-bottom: 1px solid var(--color-border);
}
.agenda__item:last-child { border-bottom: 0; }
.agenda__seq {
  font-family: var(--font-serif);
  font-weight: 700;
  color: var(--color-primary);
  font-size: var(--fs-h4);
}
.agenda__topic {
  margin: 0 0 4px;
  font-family: var(--font-serif);
  font-size: var(--fs-h4);
  font-weight: 600;
}
.agenda__meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  align-items: center;
  margin-top: 4px;
}
</style>
