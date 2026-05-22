<template>
  <div class="ai-action-grid" role="toolbar" aria-label="快捷指令">
    <button
      v-for="act in actions"
      :key="act.id"
      type="button"
      class="ai-action-btn"
      :class="{ 'is-destructive': act.accent }"
      :disabled="busy && act.type === 'command'"
      @click="$emit('action', act)"
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round">
        <template v-if="act.icon === 'calendar'">
          <rect x="3" y="5" width="18" height="16" rx="2" />
          <path d="M8 3v4M16 3v4M3 10h18" />
        </template>
        <template v-else-if="act.icon === 'plus'">
          <path d="M12 5v14M5 12h14" />
        </template>
        <template v-else-if="act.icon === 'list'">
          <path d="M8 6h13M8 12h13M8 18h13" />
        </template>
        <template v-else-if="act.icon === 'stop'">
          <rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor" stroke="none" />
        </template>
      </svg>
      <span>{{ act.label }}</span>
    </button>
  </div>
</template>

<script setup>
import { SECRETARY_ACTIONS } from './secretaryActions'

defineProps({
  busy: { type: Boolean, default: false },
})

defineEmits(['action'])

const actions = SECRETARY_ACTIONS
</script>
