<template>
  <teleport to="body">
    <transition name="modal">
      <div v-if="open" class="modal" role="dialog" aria-modal="true" @click.self="$emit('close')">
        <div class="modal__panel">
          <header class="modal__header">
            <h3 class="modal__title">{{ title }}</h3>
            <button class="btn btn-sm btn-ghost" @click="$emit('close')" aria-label="关闭">×</button>
          </header>
          <div class="modal__body">
            <slot />
          </div>
        </div>
      </div>
    </transition>
  </teleport>
</template>

<script setup>
defineProps({
  open: { type: Boolean, default: false },
  title: { type: String, default: '' },
})
defineEmits(['close'])
</script>

<style scoped>
.modal {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.35);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: var(--space-4);
}
.modal__panel {
  width: 100%;
  max-width: 560px;
  max-height: 90vh;
  overflow-y: auto;
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-3);
}
.modal__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-3) var(--space-5);
  border-bottom: 1px solid var(--color-border);
  position: sticky;
  top: 0;
  background: var(--color-bg);
  z-index: 1;
}
.modal__title {
  font-family: var(--font-serif);
  font-size: var(--fs-h3);
  margin: 0;
}
.modal__body {
  padding: var(--space-5);
}

.modal-enter-active, .modal-leave-active {
  transition: opacity var(--dur) var(--ease);
}
.modal-enter-active .modal__panel,
.modal-leave-active .modal__panel {
  transition: transform var(--dur) var(--ease);
}
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-from .modal__panel { transform: translateY(8px); }
.modal-leave-to .modal__panel { transform: translateY(8px); }
</style>
