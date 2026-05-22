<template>
  <div class="login">
    <div class="login__panel">
      <div class="login__brand">
        <BrandLogo size="md" />
        <p class="ai-eyebrow login__eyebrow">AI MEETING SECRETARY</p>
        <h1 class="ai-large-title login__title">会议秘书</h1>
        <p class="login__sub">登录以管理你的会议与议程</p>
      </div>

      <form @submit.prevent="submit" class="login__form">
        <label class="login__field">
          <span>用户名</span>
          <input v-model="username" class="input" autocomplete="username" autofocus required />
        </label>
        <label class="login__field">
          <span>密码</span>
          <input v-model="password" class="input" type="password" autocomplete="current-password" required />
        </label>
        <p v-if="error" class="login__error">{{ error }}</p>
        <button class="btn btn-primary btn-lg" :disabled="submitting" type="submit">
          {{ submitting ? '登录中…' : '登录' }}
        </button>
      </form>

      <p class="login__hint text-tiny text-muted">
        主账号默认 <code>zhaoyifei</code> / <code>123456</code>。
        如果你是通过分享链接进入, 请使用浏览器返回原链接即可自动登录。
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '../composables/useAuth'
import BrandLogo from '../components/BrandLogo.vue'

const router = useRouter()
const route = useRoute()
const { login } = useAuth()

const username = ref('zhaoyifei')
const password = ref('')
const submitting = ref(false)
const error = ref('')

const submit = async () => {
  error.value = ''
  submitting.value = true
  try {
    await login(username.value.trim(), password.value)
    const next = route.query.next || '/'
    router.replace(next)
  } catch (err) {
    error.value = err.message || '登录失败'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.login {
  min-height: 100vh;
  background: var(--color-surface);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-5);
}
.login__panel {
  width: 100%;
  max-width: 380px;
  display: flex;
  flex-direction: column;
  gap: var(--space-6);
}
.login__brand {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--space-3);
  margin-bottom: var(--space-2);
}
.login__eyebrow { margin: 0; }
.login__title {
  margin: 0;
  font-size: var(--fs-h1);
}
.login__sub {
  margin: 0;
  font-size: var(--fs-small);
  color: var(--color-text-2);
}

.login__form {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}
.login__field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: var(--fs-small);
}
.login__field span {
  font-weight: 500;
  color: var(--color-text);
}
.login__error {
  margin: 0;
  padding: 8px 12px;
  background: var(--color-danger-soft);
  color: var(--color-danger);
  border-radius: var(--radius-sm);
  font-size: var(--fs-small);
}
.login__hint {
  margin: 0;
  padding-top: var(--space-3);
  border-top: 1px solid var(--color-border);
  font-size: var(--fs-tiny);
  color: var(--color-text-3);
  line-height: var(--lh-snug);
}
.login__hint code {
  background: var(--color-surface-2);
  padding: 1px 5px;
  border-radius: 3px;
  font-family: var(--font-mono);
  color: var(--color-text);
}
</style>
