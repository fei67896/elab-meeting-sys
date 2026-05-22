<template>
  <div class="login">
    <div class="login__panel card">
      <div class="login__brand">
        <BrandLogo size="md" />
        <p class="ai-eyebrow">MEETING SECRETARY</p>
        <h1 class="ai-large-title">会议秘书</h1>
        <p class="text-small text-muted">登录后与数字人语音对话</p>
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
          {{ submitting ? '登录中…' : '进入对话' }}
        </button>
      </form>
      <p class="text-tiny text-muted">
        与会议秘书共用账号，默认 <code>zhaoyifei</code> / <code>123456</code>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '@shared/composables/useAuth'
import BrandLogo from '@shared/components/BrandLogo.vue'

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
    router.replace(route.query.next || '/')
  } catch (err) {
    error.value = err.message || '登录失败'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.login {
  min-height: 100dvh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--space-5);
}
.login__panel {
  width: 100%;
  max-width: 400px;
  padding: var(--space-6);
  display: flex;
  flex-direction: column;
  gap: var(--space-5);
}
.login__brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: var(--space-2);
}
.login__form {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}
.login__field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: var(--fs-small);
  color: var(--color-text-2);
}
.login__error {
  margin: 0;
  color: var(--color-danger);
  font-size: var(--fs-small);
}
</style>
