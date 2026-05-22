<template>
  <img
    src="/logo-fudan.png"
    class="live-brand"
    :class="`live-brand--${size}`"
    :alt="alt"
    width="40"
    height="40"
    decoding="async"
  />
</template>

<script setup>
defineProps({
  size: {
    type: String,
    default: 'md',
    validator: (v) => ['sm', 'md', 'lg'].includes(v),
  },
  alt: {
    type: String,
    default: '复旦大学',
  },
})
</script>

<style scoped>
.live-brand {
  display: block;
  flex-shrink: 0;
  object-fit: contain;
  border-radius: 50%;
  filter: drop-shadow(0 1px 4px rgba(0, 0, 0, 0.35));
}
.live-brand--sm {
  width: 32px;
  height: 32px;
}
.live-brand--md {
  width: 40px;
  height: 40px;
}
.live-brand--lg {
  width: 48px;
  height: 48px;
}
</style>
