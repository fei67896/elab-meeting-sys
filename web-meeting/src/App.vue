<template>
  <div class="app">
    <header v-if="showChrome" class="app-header">
      <div class="app-header__inner">
        <router-link to="/" class="brand">
          <BrandLogo size="sm" />
          <span class="brand-text">
            <span class="brand-title">Meeting Secretary</span>
            <span class="brand-sub">智能 AI 会议秘书</span>
          </span>
        </router-link>
        <nav class="topnav">
          <a
            v-for="item in nav"
            :key="item.path"
            :href="`#${item.path}`"
            :class="['topnav__item', { 'is-active': isActive(item.path) }]"
          >{{ item.label }}</a>
        </nav>
        <div class="userbox">
          <span v-if="isGuest" class="tag is-accent">嘉宾</span>
          <span v-else-if="isOwner" class="tag is-primary">主账号</span>
          <span class="userbox__name text-small">{{ user?.display_name || user?.username || '未登录' }}</span>
          <button class="btn btn-sm btn-ghost" @click="onLogout">退出</button>
        </div>
      </div>
    </header>

    <main class="app-main">
      <router-view v-slot="{ Component }">
        <component :is="Component" />
      </router-view>
    </main>

    <footer v-if="showChrome" class="app-footer">
      <div class="app-footer__inner">
        <span class="text-tiny text-dim">
          Linly-Talker-Stream &middot; Meeting Secretary &middot; Apache-2.0
        </span>
        <span class="text-tiny text-dim mono">v0.1.0</span>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuth } from './composables/useAuth'
import BrandLogo from './components/BrandLogo.vue'

const route = useRoute()
const router = useRouter()
const { user, isOwner, isGuest, isAuthed, logout, guestCtx } = useAuth()

// 嘉宾隐藏头部"工作台/会议管理"等导航
const nav = computed(() => {
  if (isOwner.value) {
    return [
      { path: '/', label: '工作台' },
      { path: '/douyin', label: '移动秘书' },
      { path: '/meetings', label: '会议管理' },
      { path: '/history', label: '历史查询' },
      { path: '/settings', label: '设置' },
    ]
  }
  // 嘉宾: 第一条入口跳回自己被邀请的会议
  const items = []
  if (guestCtx.value?.meeting_id) {
    items.push({ path: `/meetings/${guestCtx.value.meeting_id}`, label: '我的会议' })
  } else if (guestCtx.value?.share_token) {
    items.push({ path: `/invite/${guestCtx.value.share_token}`, label: '我的会议' })
  }
  items.push(
    { path: '/douyin', label: '移动秘书' },
    { path: '/history', label: '历史查询' },
    { path: '/settings', label: '设置' },
  )
  return items
})

const isActive = (path) => {
  if (path === '/') return route.path === '/'
  return route.path.startsWith(path)
}

// 登录页/邀请页隐藏 chrome
const showChrome = computed(() => {
  return isAuthed.value && route.name !== 'login' && !route.meta.immersive
})

const onLogout = async () => {
  await logout()
  router.replace({ name: 'login' })
}
</script>

<style scoped>
.app {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-surface);
}

.app-header {
  position: sticky;
  top: 0;
  z-index: 50;
  background: rgba(252, 252, 250, 0.85);
  backdrop-filter: var(--ai-blur);
  -webkit-backdrop-filter: var(--ai-blur);
  border-bottom: 1px solid var(--color-border);
}
.app-header__inner {
  max-width: var(--content-max);
  margin: 0 auto;
  height: var(--header-h);
  padding: 0 var(--space-5);
  display: flex;
  align-items: center;
  gap: var(--space-4);
}
.brand { flex-shrink: 0; }
.topnav { flex: 1; justify-content: flex-end; }
.userbox {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding-left: var(--space-3);
  border-left: 1px solid var(--color-border);
  margin-left: var(--space-2);
}
.userbox__name { color: var(--color-text); }

.brand {
  display: inline-flex;
  align-items: center;
  gap: var(--space-3);
  color: var(--color-text);
}
.brand:hover { color: var(--color-text); }
.brand-text { display: flex; flex-direction: column; line-height: 1.15; }
.brand-title {
  font-family: var(--font-sans);
  font-weight: 600;
  font-size: var(--fs-h4);
  letter-spacing: -0.015em;
  color: var(--color-text);
}
.brand-sub {
  font-size: var(--fs-tiny);
  color: var(--color-text-3);
  font-weight: 400;
}

.topnav { display: flex; align-items: center; gap: 2px; }
.topnav__item {
  padding: 6px 12px;
  font-size: var(--fs-small);
  font-weight: 500;
  color: var(--color-text-2);
  border-radius: var(--radius-sm);
  transition: background var(--dur-fast) var(--ease),
    color var(--dur-fast) var(--ease);
}
.topnav__item:hover {
  color: var(--color-text);
  background: var(--color-surface-2);
}
.topnav__item.is-active {
  color: var(--color-text);
  font-weight: 600;
  background: var(--color-surface-2);
}

.app-main {
  flex: 1;
  width: 100%;
}
.app:has(.ai-mobile) {
  min-height: 100dvh;
  background: var(--color-surface);
}
.app:has(.ai-mobile) .app-main {
  flex: 1;
  min-height: 0;
  padding: 0;
}

.app-footer {
  border-top: 1px solid var(--color-border);
  margin-top: var(--space-7);
  padding: var(--space-4) 0;
  background: var(--color-surface);
}
.app-footer__inner {
  max-width: var(--content-max);
  margin: 0 auto;
  padding: 0 var(--space-5);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
</style>
