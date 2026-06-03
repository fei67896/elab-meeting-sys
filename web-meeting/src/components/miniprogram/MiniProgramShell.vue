<template>
  <div class="wx-mini wx-shell">
    <div class="wx-shell__phone">
      <header class="wx-nav">
        <button type="button" class="wx-nav__back" aria-label="返回" @click="router.push('/')">‹</button>
        <h1 class="wx-nav__title">{{ title }}</h1>
        <div class="wx-nav__capsule" aria-hidden="true">
          <span /><span />
        </div>
      </header>

      <main class="wx-shell__body">
        <slot />
      </main>

      <nav class="wx-tabbar" aria-label="底部导航">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          type="button"
          class="wx-tabbar__item"
          :class="{ 'is-active': activeTab === tab.id }"
          @click="onTab(tab)"
        >
          <span class="wx-tabbar__icon">{{ tabIcon(tab.id) }}</span>
          <span class="wx-tabbar__label">{{ tab.label }}</span>
        </button>
      </nav>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { MINI_TABS } from './miniActions'

defineProps({
  title: { type: String, default: '会议秘书' },
  activeTab: { type: String, default: 'secretary' },
})

const router = useRouter()
const tabs = MINI_TABS

function tabIcon(id) {
  return ({ secretary: '💬', meetings: '📅', mine: '👤' }[id] || '·')
}

function onTab(tab) {
  if (tab.path !== '/mini') router.push(tab.path)
}
</script>

<style scoped>
.wx-shell {
  min-height: 100dvh;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: var(--space-4) var(--space-3) var(--space-6);
  background: var(--wx-bg);
}

.wx-shell__phone {
  width: min(var(--wx-phone-w), 100%);
  min-height: min(780px, calc(100dvh - var(--space-8)));
  display: flex;
  flex-direction: column;
  background: var(--wx-card);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12);
  overflow: hidden;
}

.wx-nav {
  flex-shrink: 0;
  display: grid;
  grid-template-columns: 40px 1fr 72px;
  align-items: center;
  height: 48px;
  padding: 0 8px;
  border-bottom: 1px solid var(--wx-border);
  background: var(--wx-card);
}
.wx-nav__back {
  border: 0;
  background: transparent;
  font-size: 28px;
  line-height: 1;
  color: var(--wx-text);
  cursor: pointer;
  padding: 0;
}
.wx-nav__title {
  margin: 0;
  text-align: center;
  font-size: 16px;
  font-weight: 600;
  color: var(--wx-text);
}
.wx-nav__capsule {
  justify-self: end;
  display: flex;
  align-items: center;
  gap: 6px;
  height: 28px;
  padding: 0 10px;
  border: 1px solid var(--wx-border);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.9);
}
.wx-nav__capsule span {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--wx-text-2);
}

.wx-shell__body {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #f7f7f7;
}

.wx-tabbar {
  flex-shrink: 0;
  display: flex;
  height: var(--wx-tab-h);
  border-top: 1px solid var(--wx-border);
  background: #fafafa;
  padding-bottom: env(safe-area-inset-bottom);
}
.wx-tabbar__item {
  flex: 1;
  border: 0;
  background: transparent;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  cursor: pointer;
  color: var(--wx-text-2);
  font-size: 10px;
}
.wx-tabbar__item.is-active {
  color: var(--wx-green);
}
.wx-tabbar__icon {
  font-size: 18px;
  line-height: 1;
}
.wx-tabbar__label {
  font-size: 10px;
}
</style>
