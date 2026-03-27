<template>
  <div class="login-page">
    <div class="login-card">
      <div class="brand">
        <h1 class="brand-title">ORACLEFLOW</h1>
        <p class="brand-subtitle">Intelligence Platform</p>
      </div>

      <form class="login-form" @submit.prevent="handleLogin">
        <div class="form-group">
          <label class="form-label" for="email">Email</label>
          <input
            id="email"
            v-model="form.email"
            type="email"
            class="form-input"
            placeholder="operator@oracleflow.io"
            required
            autocomplete="email"
          />
        </div>

        <div class="form-group">
          <label class="form-label" for="password">Password</label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            class="form-input"
            placeholder="Enter password"
            required
            autocomplete="current-password"
          />
        </div>

        <div v-if="error" class="error-msg">{{ error }}</div>

        <button type="submit" class="submit-btn" :disabled="loading">
          <span v-if="loading">Authenticating...</span>
          <span v-else>Sign In <span class="arrow">&rarr;</span></span>
        </button>
      </form>

      <div class="form-footer">
        <span class="footer-link forgot-hint" @click="showForgotMsg = !showForgotMsg">Forgot password?</span>
        <span v-if="showForgotMsg" class="forgot-msg">Contact support to reset your password.</span>
        <p class="footer-text">
          Don't have an account?
          <router-link to="/register" class="footer-link accent">Register</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '../api/auth'
import { setAuth } from '../stores/auth'

const router = useRouter()

const form = reactive({
  email: '',
  password: '',
})

const error = ref('')
const loading = ref(false)
const showForgotMsg = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true

  try {
    const res = await login(form.email, form.password)
    const { token, user, org } = res.data || res
    setAuth(token, user, org)
    router.push('/intel')
  } catch (err) {
    error.value = err?.response?.data?.message || err?.message || 'Invalid credentials'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: #0a0a0a;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'SF Mono', 'JetBrains Mono', 'Fira Code', monospace;
  padding: 20px;
}

.login-card {
  width: 100%;
  max-width: 420px;
  background: #141414;
  border: 1px solid #222;
  border-radius: 4px;
  padding: 48px 40px;
}

.brand {
  text-align: center;
  margin-bottom: 40px;
}

.brand-title {
  font-size: 1.6rem;
  font-weight: 800;
  letter-spacing: 3px;
  color: #e8e8e8;
  margin: 0 0 6px 0;
}

.brand-subtitle {
  font-size: 0.8rem;
  color: #666;
  letter-spacing: 1px;
  text-transform: uppercase;
  margin: 0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 0.75rem;
  color: #888;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.form-input {
  background: #0a0a0a;
  border: 1px solid #2a2a2a;
  border-radius: 3px;
  padding: 12px 14px;
  font-family: inherit;
  font-size: 0.9rem;
  color: #e8e8e8;
  outline: none;
  transition: border-color 0.2s;
}

.form-input::placeholder {
  color: #444;
}

.form-input:focus {
  border-color: #FF4500;
}

.error-msg {
  background: rgba(255, 69, 0, 0.1);
  border: 1px solid rgba(255, 69, 0, 0.3);
  border-radius: 3px;
  padding: 10px 14px;
  font-size: 0.8rem;
  color: #FF4500;
}

.submit-btn {
  background: #FF4500;
  color: #fff;
  border: none;
  border-radius: 3px;
  padding: 14px;
  font-family: inherit;
  font-size: 0.9rem;
  font-weight: 700;
  letter-spacing: 0.5px;
  cursor: pointer;
  transition: background 0.2s, opacity 0.2s;
  margin-top: 4px;
}

.submit-btn:hover:not(:disabled) {
  background: #e03e00;
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.submit-btn .arrow {
  font-family: sans-serif;
}

.form-footer {
  margin-top: 28px;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.footer-link {
  color: #666;
  text-decoration: none;
  font-size: 0.8rem;
  transition: color 0.2s;
}

.footer-link:hover {
  color: #e8e8e8;
}

.footer-link.accent {
  color: #FF4500;
}

.footer-link.accent:hover {
  color: #ff6a33;
}

.footer-text {
  color: #555;
  font-size: 0.8rem;
  margin: 0;
}

.forgot-hint {
  cursor: pointer;
}

.forgot-msg {
  display: block;
  font-size: 0.75rem;
  color: #888;
  margin-top: -4px;
}
</style>
