<template>
  <div class="voice-app" :class="{ 'is-immersive': immersive }">
    <router-view />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const immersive = computed(() => !!route.meta.immersive)
</script>

<style scoped>
.voice-app {
  min-height: 100%;
  min-height: 100dvh;
  background: var(--color-surface);
}
.voice-app.is-immersive {
  height: 100dvh;
  overflow: hidden;
}
</style>
