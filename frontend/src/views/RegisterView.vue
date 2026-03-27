<template>
  <div class="register-page">
    <div class="register-card">
      <div class="brand">
        <h1 class="brand-title">Create Account</h1>
        <p class="brand-subtitle">Join OracleFlow Intelligence Platform</p>
      </div>

      <form class="register-form" @submit.prevent="handleRegister">
        <div class="form-group">
          <label class="form-label" for="name">Full Name</label>
          <input
            id="name"
            v-model="form.name"
            type="text"
            class="form-input"
            placeholder="Jane Doe"
            required
            autocomplete="name"
          />
        </div>

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
            placeholder="Min 8 characters"
            required
            autocomplete="new-password"
            minlength="8"
          />
        </div>

        <div class="form-group">
          <label class="form-label" for="confirm_password">Confirm Password</label>
          <input
            id="confirm_password"
            v-model="form.confirm_password"
            type="password"
            class="form-input"
            placeholder="Re-enter password"
            required
            autocomplete="new-password"
            minlength="8"
          />
        </div>

        <div v-if="error" class="error-msg">{{ error }}</div>

        <button type="submit" class="submit-btn" :disabled="loading">
          <span v-if="loading">Creating account...</span>
          <span v-else>Create Account <span class="arrow">&rarr;</span></span>
        </button>
      </form>

      <div class="form-footer">
        <p class="footer-text">
          Already have an account?
          <router-link to="/login" class="footer-link accent">Login</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { register } from '../api/auth'
import { setAuth } from '../stores/auth'

const router = useRouter()

const form = reactive({
  name: '',
  email: '',
  password: '',
  confirm_password: '',
})

const error = ref('')
const loading = ref(false)

async function handleRegister() {
  error.value = ''

  if (form.password !== form.confirm_password) {
    error.value = 'Passwords do not match'
    return
  }

  loading.value = true

  try {
    const res = await register({
      name: form.name,
      email: form.email,
      password: form.password,
    })
    const { token, user, org } = res.data || res
    setAuth(token, user, org)
    router.push('/onboarding')
  } catch (err) {
    error.value = err?.response?.data?.message || err?.message || 'Registration failed'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  background: #0a0a0a;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'SF Mono', 'JetBrains Mono', 'Fira Code', monospace;
  padding: 20px;
}

.register-card {
  width: 100%;
  max-width: 480px;
  background: #141414;
  border: 1px solid #222;
  border-radius: 4px;
  padding: 48px 40px;
}

.brand {
  text-align: center;
  margin-bottom: 36px;
}

.brand-title {
  font-size: 1.4rem;
  font-weight: 800;
  letter-spacing: 2px;
  color: #e8e8e8;
  margin: 0 0 6px 0;
}

.brand-subtitle {
  font-size: 0.78rem;
  color: #666;
  letter-spacing: 0.5px;
  margin: 0;
}

.register-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
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
  margin-top: 24px;
  text-align: center;
}

.footer-link {
  color: #666;
  text-decoration: none;
  font-size: 0.8rem;
  transition: color 0.2s;
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
</style>
