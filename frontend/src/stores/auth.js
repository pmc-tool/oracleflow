import { reactive } from 'vue'

const state = reactive({
  token: localStorage.getItem('of_token') || null,
  user: null,
  org: null,
  plan: 'free',
})

export function setAuth(token, user, org) {
  state.token = token
  state.user = user
  state.org = org
  state.plan = org?.plan || 'free'
  localStorage.setItem('of_token', token)
}

export function clearAuth() {
  state.token = null
  state.user = null
  state.org = null
  state.plan = 'free'
  localStorage.removeItem('of_token')
}

export function isAuthenticated() {
  return !!state.token
}

export function getToken() {
  return state.token
}

export { state as authState }
