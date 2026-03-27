<template>
  <div class="admin-dashboard">
    <h1 class="page-title">Admin Dashboard</h1>

    <div v-if="!isAdmin" class="error-text">Access denied. Admin role required.</div>

    <template v-else>
      <div v-if="loading" class="loading-text">Loading admin data...</div>

      <template v-else>
        <!-- Platform Stats -->
        <div class="stats-row">
          <div class="stat-card">
            <div class="stat-label">Total Users</div>
            <div class="stat-value">{{ stats.users }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Organizations</div>
            <div class="stat-value">{{ stats.organizations }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Total Signals</div>
            <div class="stat-value">{{ stats.signals }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Monitored Sites</div>
            <div class="stat-value">{{ stats.sites }}</div>
          </div>
        </div>

        <div class="stats-row">
          <div class="stat-card">
            <div class="stat-label">Simulations</div>
            <div class="stat-value">{{ stats.simulations }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-label">Tracked Entities</div>
            <div class="stat-value">{{ stats.entities }}</div>
          </div>
        </div>

        <!-- Plan Distribution -->
        <div class="section-box">
          <h2 class="section-heading">Plan Distribution</h2>
          <div class="plan-grid">
            <div v-for="plan in planDist" :key="plan.name" class="plan-row">
              <span class="plan-name">{{ plan.name.toUpperCase() }}</span>
              <div class="bar-track">
                <div
                  class="bar-fill"
                  :style="{ width: plan.pct + '%', background: plan.color }"
                ></div>
              </div>
              <span class="plan-count">{{ plan.count }}</span>
            </div>
          </div>
        </div>
      </template>

      <div v-if="error" class="error-text">{{ error }}</div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { authState } from '../../stores/auth'
import service from '../../api/index'

const isAdmin = computed(() => authState.user?.role === 'admin')

const loading = ref(true)
const error = ref('')

const stats = ref({
  users: 0,
  organizations: 0,
  signals: 0,
  sites: 0,
  simulations: 0,
  entities: 0,
})

const planDist = ref([
  { name: 'free', count: 0, pct: 0, color: '#555' },
  { name: 'watch', count: 0, pct: 0, color: '#FF4500' },
  { name: 'command', count: 0, pct: 0, color: '#FFa500' },
  { name: 'warroom', count: 0, pct: 0, color: '#FF2222' },
])

async function fetchStats() {
  try {
    // Fetch usage data as a proxy for admin stats
    const usageRes = await service.get('/api/billing/usage')
    const usage = usageRes.data || usageRes
    stats.value.sites = usage.sites_used || 0
    stats.value.users = usage.users_used || 1
    stats.value.organizations = 1

    // Fetch signals count
    try {
      const sigRes = await service.get('/api/signals')
      const sigData = sigRes.data || sigRes
      stats.value.signals = Array.isArray(sigData) ? sigData.length : (sigData.total || 0)
    } catch { stats.value.signals = 0 }

    // Fetch entities count
    try {
      const entRes = await service.get('/api/entities')
      const entData = entRes.data || entRes
      stats.value.entities = Array.isArray(entData) ? entData.length : (entData.total || 0)
    } catch { stats.value.entities = 0 }

    // Update plan distribution based on current org
    const currentPlan = usage.plan || 'free'
    planDist.value = planDist.value.map(p => ({
      ...p,
      count: p.name === currentPlan ? 1 : 0,
      pct: p.name === currentPlan ? 100 : 0,
    }))
  } catch (e) {
    error.value = e?.message || 'Failed to load admin data'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (isAdmin.value) {
    fetchStats()
  } else {
    loading.value = false
  }
})
</script>

<style scoped>
.admin-dashboard {
  padding: 30px 40px;
  max-width: 1200px;
  color: #e8e8e8;
  font-family: 'Space Grotesk', system-ui, sans-serif;
}

.page-title {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.4rem;
  font-weight: 700;
  color: #FF4500;
  margin: 0 0 30px;
  letter-spacing: 1px;
}

.loading-text {
  color: #666;
  font-size: 0.9rem;
  padding: 40px 0;
}

.error-text {
  color: #FF4500;
  background: rgba(255, 69, 0, 0.1);
  border: 1px solid rgba(255, 69, 0, 0.3);
  border-radius: 4px;
  padding: 12px 16px;
  font-size: 0.85rem;
  margin-top: 10px;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  background: #141414;
  border: 1px solid #222;
  border-radius: 4px;
  padding: 20px;
}

.stat-label {
  font-size: 0.75rem;
  color: #888;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  margin-bottom: 8px;
}

.stat-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.6rem;
  font-weight: 700;
  color: #e8e8e8;
}

.section-box {
  background: #141414;
  border: 1px solid #222;
  border-radius: 4px;
  padding: 24px;
  margin-top: 20px;
}

.section-heading {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  color: #888;
  letter-spacing: 1px;
  text-transform: uppercase;
  margin: 0 0 20px;
}

.plan-grid {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.plan-row {
  display: flex;
  align-items: center;
  gap: 14px;
}

.plan-name {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: #aaa;
  width: 80px;
  letter-spacing: 1px;
}

.bar-track {
  flex: 1;
  height: 8px;
  background: #1a1a1a;
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 4px;
  transition: width 0.4s ease;
}

.plan-count {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  color: #e8e8e8;
  width: 30px;
  text-align: right;
}
</style>
