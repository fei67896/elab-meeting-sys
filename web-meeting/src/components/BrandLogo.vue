<template>
  <img
    src="/logo-fudan.png"
    :alt="alt"
    class="brand-logo"
    :class="`brand-logo--${size}`"
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
    default: 'Meeting Secretary',
  },
})
</script>

<style scoped>
.brand-logo {
  display: block;
  flex-shrink: 0;
  object-fit: contain;
  border-radius: 50%;
}
.brand-logo--sm {
  width: 28px;
  height: 28px;
}
.brand-logo--md {
  width: 40px;
  height: 40px;
}
.brand-logo--lg {
  width: 56px;
  height: 56px;
}
</style>
