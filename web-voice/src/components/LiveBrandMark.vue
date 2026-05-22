<template>
  <img
    src="/logo-fudan.png"
    class="live-brand"
    :class="[`live-brand--${size}`, tone === 'light' && 'live-brand--light']"
    :alt="alt"
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
  tone: {
    type: String,
    default: 'light',
    validator: (v) => ['light', 'color'].includes(v),
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
}
.live-brand--light {
  filter: brightness(0) invert(1) drop-shadow(0 1px 3px rgba(0, 0, 0, 0.45));
}
.live-brand--sm {
  height: 1.5em;
  width: auto;
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
