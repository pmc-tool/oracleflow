<template>
  <div class="settings-page">
    <h1 class="page-title">Settings</h1>

    <!-- Tabs -->
    <div class="tabs">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="tab-btn"
        :class="{ active: activeTab === tab.key }"
        @click="activeTab = tab.key"
      >{{ tab.label }}</button>
    </div>

    <!-- Profile Tab -->
    <div v-if="activeTab === 'profile'" class="tab-panel">
      <h2 class="section-heading">Profile</h2>
      <form class="settings-form" @submit.prevent="updateProfile">
        <div class="form-group">
          <label class="form-label">Name</label>
          <input v-model="profileForm.name" type="text" class="form-input" />
        </div>
        <div class="form-group">
          <label class="form-label">Email</label>
          <input :value="authState.user?.email" type="email" class="form-input" disabled />
        </div>
        <div class="form-group">
          <label class="form-label">New Password (leave blank to keep current)</label>
          <input v-model="profileForm.password" type="password" class="form-input" placeholder="Min 8 characters" />
        </div>
        <div v-if="profileMsg" class="success-msg">{{ profileMsg }}</div>
        <div v-if="profileErr" class="error-msg">{{ profileErr }}</div>
        <button type="submit" class="action-btn" :disabled="profileLoading">
          {{ profileLoading ? 'Saving...' : 'Save Changes' }}
        </button>
      </form>
    </div>

    <!-- Organization Tab -->
    <div v-if="activeTab === 'organization'" class="tab-panel">
      <h2 class="section-heading">Organization</h2>
      <div class="info-row">
        <span class="info-label">Organization</span>
        <span class="info-value">{{ authState.org?.name || '--' }}</span>
      </div>
      <div class="info-row">
        <span class="info-label">Plan</span>
        <span class="plan-badge" :class="'plan-' + (authState.org?.plan || 'free')">
          {{ (authState.org?.plan || 'free').toUpperCase() }}
        </span>
      </div>
      <div class="info-row">
        <span class="info-label">Members</span>
        <span class="info-value">{{ authState.user?.name }} ({{ authState.user?.role }})</span>
      </div>
    </div>

    <!-- Billing Tab -->
    <div v-if="activeTab === 'billing'" class="tab-panel">
      <h2 class="section-heading">Billing &amp; Usage</h2>

      <div v-if="usageLoading" class="loading-text">Loading usage data...</div>

      <template v-else>
        <div class="info-row">
          <span class="info-label">Current Plan</span>
          <span class="plan-badge" :class="'plan-' + usage.plan">
            {{ usage.plan.toUpperCase() }}
          </span>
        </div>

        <!-- Usage Bars -->
        <div class="usage-section">
          <div class="usage-item">
            <div class="usage-header">
              <span class="usage-label">Sites</span>
              <span class="usage-nums">{{ usage.sites_used }} / {{ usage.sites_limit }}</span>
            </div>
            <div class="usage-bar-track">
              <div class="usage-bar-fill" :style="{ width: usagePct(usage.sites_used, usage.sites_limit) + '%' }"></div>
            </div>
          </div>
          <div class="usage-item">
            <div class="usage-header">
              <span class="usage-label">Simulations (this month)</span>
              <span class="usage-nums">{{ usage.simulations_used }} / {{ usage.simulations_limit }}</span>
            </div>
            <div class="usage-bar-track">
              <div class="usage-bar-fill" :style="{ width: usagePct(usage.simulations_used, usage.simulations_limit) + '%' }"></div>
            </div>
          </div>
          <div class="usage-item">
            <div class="usage-header">
              <span class="usage-label">Intel Panels</span>
              <span class="usage-nums">{{ usage.panels_used }} / {{ usage.panels_limit }}</span>
            </div>
            <div class="usage-bar-track">
              <div class="usage-bar-fill" :style="{ width: usagePct(usage.panels_used, usage.panels_limit) + '%' }"></div>
            </div>
          </div>
          <div class="usage-item">
            <div class="usage-header">
              <span class="usage-label">Categories</span>
              <span class="usage-nums">{{ usage.categories_used }} / {{ usage.categories_limit }}</span>
            </div>
            <div class="usage-bar-track">
              <div class="usage-bar-fill" :style="{ width: usagePct(usage.categories_used, usage.categories_limit) + '%' }"></div>
            </div>
          </div>
          <div class="usage-item">
            <div class="usage-header">
              <span class="usage-label">Users</span>
              <span class="usage-nums">{{ usage.users_used }} / {{ usage.users_limit }}</span>
            </div>
            <div class="usage-bar-track">
              <div class="usage-bar-fill" :style="{ width: usagePct(usage.users_used, usage.users_limit) + '%' }"></div>
            </div>
          </div>
        </div>

        <!-- Upgrade -->
        <div v-if="usage.plan === 'free'" class="upgrade-section">
          <p class="upgrade-text">Upgrade to unlock more sites, simulations, panels, categories, and team members.</p>
          <div class="plan-cards">
            <div v-for="plan in upgradePlans" :key="plan.key" class="plan-card">
              <div class="plan-card-name">{{ plan.name }}</div>
              <div class="plan-card-price">${{ plan.price }}<span class="price-period">/mo</span></div>
              <div class="plan-card-features">
                <div>{{ plan.sites >= 999 ? 'Unlimited' : plan.sites }} sites</div>
                <div>{{ plan.simulations >= 999 ? 'Unlimited' : plan.simulations }} simulations/mo</div>
                <div>{{ plan.panels >= 999 ? 'All' : plan.panels }} panels</div>
                <div>{{ plan.categories >= 12 ? 'All' : plan.categories }} categories</div>
                <div>{{ plan.users >= 999 ? 'Unlimited' : plan.users }} users</div>
              </div>
              <button class="action-btn" @click="handleUpgrade(plan.key)">
                Upgrade
              </button>
            </div>
          </div>
        </div>

        <div v-else class="manage-section">
          <button class="action-btn secondary" @click="handlePortal">
            Manage Subscription
          </button>
        </div>
      </template>
    </div>

    <!-- API Keys Tab -->
    <div v-if="activeTab === 'api'" class="tab-panel">
      <h2 class="section-heading">API Keys</h2>
      <div class="placeholder-box">
        <span class="placeholder-icon">&#128274;</span>
        <p class="placeholder-text">API key management coming soon.</p>
        <p class="placeholder-sub">You will be able to generate keys for programmatic access to the OracleFlow API.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { authState } from '../stores/auth'
import service from '../api/index'
import { getUsage, createCheckout, createPortal } from '../api/billing'

const tabs = [
  { key: 'profile', label: 'Profile' },
  { key: 'organization', label: 'Organization' },
  { key: 'billing', label: 'Billing' },
  { key: 'api', label: 'API Keys' },
]

const activeTab = ref('profile')

// --- Profile ---
const profileForm = reactive({
  name: authState.user?.name || '',
  password: '',
})
const profileMsg = ref('')
const profileErr = ref('')
const profileLoading = ref(false)

async function updateProfile() {
  profileMsg.value = ''
  profileErr.value = ''
  profileLoading.value = true
  try {
    const body = { name: profileForm.name }
    if (profileForm.password) body.password = profileForm.password
    await service.put('/api/auth/profile', body)
    profileMsg.value = 'Profile updated successfully.'
    profileForm.password = ''
  } catch (e) {
    profileErr.value = e?.message || 'Failed to update profile'
  } finally {
    profileLoading.value = false
  }
}

// --- Billing / Usage ---
const usageLoading = ref(true)
const usage = ref({
  plan: 'free',
  sites_used: 0, sites_limit: 1,
  simulations_used: 0, simulations_limit: 1,
  users_used: 1, users_limit: 1,
  panels_used: 6, panels_limit: 6,
  categories_used: 0, categories_limit: 3,
})

const upgradePlans = [
  { key: 'scout', name: 'Scout', price: 49, sites: 2, simulations: 3, users: 1, panels: 10, categories: 5 },
  { key: 'strategist', name: 'Strategist', price: 199, sites: 5, simulations: 10, users: 3, panels: 15, categories: 8 },
  { key: 'commander', name: 'Commander', price: 999, sites: 25, simulations: 50, users: 10, panels: 30, categories: 12 },
  { key: 'sovereign', name: 'Sovereign', price: 5000, sites: 999, simulations: 999, users: 999, panels: 999, categories: 12 },
]

function usagePct(used, limit) {
  if (!limit || limit <= 0) return 0
  return Math.min(100, Math.round((used / limit) * 100))
}

async function fetchUsage() {
  try {
    const res = await getUsage()
    const data = res.data || res
    usage.value = { ...usage.value, ...data }
  } catch {
    // keep defaults
  } finally {
    usageLoading.value = false
  }
}

async function handleUpgrade(plan) {
  try {
    const res = await createCheckout(plan)
    const data = res.data || res
    if (data.checkout_url) {
      window.location.href = data.checkout_url
    }
  } catch (e) {
    alert(e?.message || 'Could not start checkout. Stripe may not be configured.')
  }
}

async function handlePortal() {
  try {
    const res = await createPortal()
    const data = res.data || res
    if (data.portal_url) {
      window.location.href = data.portal_url
    }
  } catch (e) {
    alert(e?.message || 'Could not open billing portal.')
  }
}

onMounted(() => {
  profileForm.name = authState.user?.name || ''
  fetchUsage()
})
</script>

<style scoped>
.settings-page {
  padding: 30px 40px;
  max-width: 900px;
  color: #e8e8e8;
  font-family: 'Space Grotesk', system-ui, sans-serif;
}

.page-title {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.4rem;
  font-weight: 700;
  color: #FF4500;
  margin: 0 0 24px;
  letter-spacing: 1px;
}

/* Tabs */
.tabs {
  display: flex;
  gap: 0;
  border-bottom: 1px solid #222;
  margin-bottom: 30px;
}

.tab-btn {
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: #888;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  letter-spacing: 0.5px;
  padding: 10px 20px;
  cursor: pointer;
  transition: color 0.2s, border-color 0.2s;
}

.tab-btn:hover {
  color: #e8e8e8;
}

.tab-btn.active {
  color: #FF4500;
  border-bottom-color: #FF4500;
}

/* Tab panel */
.tab-panel {
  animation: fadeIn 0.15s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.section-heading {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  color: #888;
  letter-spacing: 1px;
  text-transform: uppercase;
  margin: 0 0 20px;
}

/* Form */
.settings-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
  max-width: 480px;
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

.form-input:focus {
  border-color: #FF4500;
}

.form-input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.form-input::placeholder {
  color: #444;
}

.success-msg {
  background: rgba(0, 200, 80, 0.1);
  border: 1px solid rgba(0, 200, 80, 0.3);
  border-radius: 3px;
  padding: 10px 14px;
  font-size: 0.8rem;
  color: #00c850;
}

.error-msg {
  background: rgba(255, 69, 0, 0.1);
  border: 1px solid rgba(255, 69, 0, 0.3);
  border-radius: 3px;
  padding: 10px 14px;
  font-size: 0.8rem;
  color: #FF4500;
}

.action-btn {
  background: #FF4500;
  color: #fff;
  border: none;
  border-radius: 3px;
  padding: 12px 24px;
  font-family: inherit;
  font-size: 0.85rem;
  font-weight: 700;
  letter-spacing: 0.5px;
  cursor: pointer;
  transition: background 0.2s, opacity 0.2s;
  align-self: flex-start;
}

.action-btn:hover:not(:disabled) {
  background: #e03e00;
}

.action-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.action-btn.secondary {
  background: #222;
  color: #e8e8e8;
}

.action-btn.secondary:hover:not(:disabled) {
  background: #333;
}

/* Info rows */
.info-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 0;
  border-bottom: 1px solid #1a1a1a;
}

.info-label {
  font-size: 0.8rem;
  color: #888;
  width: 120px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-value {
  font-size: 0.95rem;
  color: #e8e8e8;
}

.plan-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 1px;
  padding: 4px 12px;
  border-radius: 3px;
  display: inline-block;
}

.plan-free { background: #222; color: #888; }
.plan-scout { background: rgba(59, 130, 246, 0.15); color: #3b82f6; }
.plan-strategist { background: rgba(255, 69, 0, 0.15); color: #FF4500; }
.plan-commander { background: rgba(255, 165, 0, 0.15); color: #FFa500; }
.plan-sovereign { background: rgba(255, 34, 34, 0.15); color: #FF2222; }

/* Usage */
.usage-section {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.usage-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.usage-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.usage-label {
  font-size: 0.8rem;
  color: #aaa;
}

.usage-nums {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: #e8e8e8;
}

.usage-bar-track {
  height: 6px;
  background: #1a1a1a;
  border-radius: 3px;
  overflow: hidden;
}

.usage-bar-fill {
  height: 100%;
  background: #FF4500;
  border-radius: 3px;
  transition: width 0.4s ease;
}

/* Upgrade */
.upgrade-section {
  margin-top: 30px;
}

.upgrade-text {
  color: #888;
  font-size: 0.85rem;
  margin: 0 0 20px;
}

.plan-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 16px;
}

.plan-card {
  background: #141414;
  border: 1px solid #222;
  border-radius: 4px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.plan-card-name {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1rem;
  font-weight: 700;
  color: #FF4500;
  letter-spacing: 1px;
}

.plan-card-price {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.5rem;
  font-weight: 800;
  color: #e8e8e8;
}

.price-period {
  font-size: 0.8rem;
  font-weight: 400;
  color: #666;
}

.plan-card-features {
  font-size: 0.8rem;
  color: #aaa;
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex: 1;
}

.manage-section {
  margin-top: 30px;
}

/* Placeholder */
.placeholder-box {
  background: #141414;
  border: 1px solid #222;
  border-radius: 4px;
  padding: 40px;
  text-align: center;
}

.placeholder-icon {
  font-size: 2rem;
  display: block;
  margin-bottom: 12px;
}

.placeholder-text {
  font-size: 1rem;
  color: #aaa;
  margin: 0 0 8px;
}

.placeholder-sub {
  font-size: 0.8rem;
  color: #666;
  margin: 0;
}

.loading-text {
  color: #666;
  font-size: 0.9rem;
  padding: 20px 0;
}
</style>
