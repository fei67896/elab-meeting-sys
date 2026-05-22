<template>
  <div class="ai-mobile ai-page">
    <div class="ai-mobile__wrap">
      <header class="ai-mobile__header">
        <router-link to="/" class="ai-link">← 工作台</router-link>
        <div class="ai-mobile__heading">
          <h1 class="ai-mobile__title">AI 秘书</h1>
          <span class="ai-mobile__live">
            <span class="ai-status-dot" aria-hidden="true"></span>
            在线
          </span>
        </div>
        <p class="ai-mobile__sub">语音或文字下达指令</p>
      </header>
      <div class="ai-panel ai-mobile__card">
        <slot />
      </div>
      <p class="ai-footnote">Linly-Talker · Studio</p>
    </div>
  </div>
</template>

<style src="./feed-light.css"></style>

<style scoped>
.ai-mobile {
  min-height: 100dvh;
  padding: var(--space-4);
  padding-bottom: max(var(--space-6), env(safe-area-inset-bottom));
  background: var(--color-surface);
}
.ai-mobile__wrap {
  max-width: 440px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
.ai-mobile__header {
  padding: var(--space-2) var(--space-1) 0;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
}
.ai-mobile__heading {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-top: var(--space-2);
}
.ai-mobile__title {
  margin: 0;
  font-size: var(--fs-h1);
  font-weight: 600;
  letter-spacing: -0.02em;
}
.ai-mobile__live {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  font-size: var(--fs-tiny);
  font-weight: 500;
  color: var(--color-live);
  background: var(--color-live-soft);
  border-radius: var(--radius-pill);
}
.ai-mobile__sub {
  margin: 0;
  font-size: var(--fs-small);
  color: var(--color-text-2);
}
.ai-mobile__card {
  overflow: hidden;
}
</style>
