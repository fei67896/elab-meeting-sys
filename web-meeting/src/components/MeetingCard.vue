<template>
  <router-link :to="`/meetings/${meeting.id}`" class="mcard card is-interactive">
    <header class="mcard__head">
      <h4 class="mcard__title">{{ meeting.title }}</h4>
      <span class="tag" :class="statusClass">{{ statusLabel }}</span>
    </header>

    <div class="mcard__meta">
      <span class="mcard__time">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <circle cx="12" cy="12" r="9" stroke="currentColor" stroke-width="1.5"/>
          <path d="M12 7v5l3 2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
        </svg>
        {{ formatDateTime(meeting.start_time) }}
      </span>
      <span class="mcard__rel text-tiny text-dim">{{ formatRelative(meeting.start_time) }}</span>
    </div>

    <p v-if="meeting.description" class="mcard__desc text-small text-muted">
      {{ meeting.description }}
    </p>

    <footer class="mcard__foot">
      <div class="mcard__participants">
        <template v-if="participants.length">
          <span
            v-for="p in participants.slice(0, 4)"
            :key="p.id || p.name"
            class="avatar"
            :title="p.name"
          >{{ initial(p.name) }}</span>
          <span v-if="participants.length > 4" class="avatar avatar--more">
            +{{ participants.length - 4 }}
          </span>
        </template>
        <span v-else class="text-tiny text-dim">无参会人</span>
      </div>
      <span class="text-tiny text-dim mono">{{ meeting.meeting_code }}</span>
    </footer>
  </router-link>
</template>

<script setup>
import { computed } from 'vue'
import { formatDateTime, formatRelative, STATUS_LABEL, STATUS_TAG_CLASS } from '../utils/format'

const props = defineProps({
  meeting: { type: Object, required: true },
})

const participants = computed(() => props.meeting.participants || [])
const statusLabel = computed(() => STATUS_LABEL[props.meeting.status] || props.meeting.status)
const statusClass = computed(() => STATUS_TAG_CLASS[props.meeting.status] || '')

const initial = (name) => {
  if (!name) return '?'
  // 中文取最后一字，英文取首字母
  const ch = name.trim()
  return /[\u4e00-\u9fa5]/.test(ch) ? ch.slice(-1) : ch.slice(0, 1).toUpperCase()
}
</script>

<style scoped>
.mcard {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  padding: var(--space-4);
  color: inherit;
  text-decoration: none;
}
.mcard:hover { color: inherit; }

.mcard__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
}
.mcard__title {
  font-family: var(--font-serif);
  font-size: var(--fs-h4);
  font-weight: 600;
  margin: 0;
  letter-spacing: -0.005em;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.mcard__meta {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  color: var(--color-text-2);
  font-size: var(--fs-small);
}
.mcard__time { display: inline-flex; align-items: center; gap: 6px; }

.mcard__desc {
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.mcard__foot {
  margin-top: auto;
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-2);
}
.mcard__participants {
  display: inline-flex;
  align-items: center;
  gap: -4px;
}
.avatar {
  width: 26px;
  height: 26px;
  margin-left: -6px;
  border-radius: 50%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--color-text);
  color: var(--color-text-inverse);
  font-size: 11px;
  font-weight: 600;
  border: 2px solid var(--color-bg);
}
.avatar:first-child { margin-left: 0; }
.avatar--more { background: var(--color-surface-2); color: var(--color-text-2); }
</style>
