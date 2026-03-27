<template>
  <div class="simulations-page">
    <div class="page-header">
      <h1 class="page-title">Simulations</h1>
      <router-link to="/simulate" class="new-sim-btn">New Simulation +</router-link>
    </div>

    <div class="filter-bar">
      <div class="filter-group">
        <label class="filter-label">Status</label>
        <select v-model="statusFilter" class="filter-select" @change="fetchSimulations">
          <option value="all">All</option>
          <option value="running">Running</option>
          <option value="completed">Completed</option>
          <option value="failed">Failed</option>
          <option value="preparing">Preparing</option>
        </select>
      </div>
      <div class="filter-group">
        <label class="filter-label">From</label>
        <input type="date" v-model="dateFrom" class="filter-input" @change="fetchSimulations" />
      </div>
      <div class="filter-group">
        <label class="filter-label">To</label>
        <input type="date" v-model="dateTo" class="filter-input" @change="fetchSimulations" />
      </div>
    </div>

    <div v-if="loading" class="loading-state">Loading simulations...</div>

    <div v-else-if="filteredSimulations.length === 0" class="empty-state">
      <p class="empty-text">No simulations yet. Run your first one.</p>
      <router-link to="/simulate" class="empty-link">Start a Simulation &rarr;</router-link>
    </div>

    <div v-else class="sim-list">
      <div
        v-for="sim in paginatedSimulations"
        :key="sim.simulation_id"
        class="sim-card"
        @click="navigateTo(sim)"
      >
        <div class="sim-card-top">
          <span class="sim-title">{{ sim.simulation_requirement || sim.project_name || sim.simulation_id }}</span>
          <span :class="['status-badge', statusClass(sim)]">{{ statusLabel(sim) }}</span>
        </div>
        <div class="sim-card-meta">
          <span class="meta-item">{{ relativeTime(sim.created_at) }}</span>
          <span class="meta-sep">&middot;</span>
          <span class="meta-item">{{ sim.profiles_count || sim.entities_count || 0 }} agents</span>
          <span class="meta-sep">&middot;</span>
          <span class="meta-item">{{ sim.current_round || 0 }}/{{ sim.total_rounds || '?' }} rounds</span>
        </div>
      </div>
    </div>

    <div v-if="totalPages > 1" class="pagination">
      <button
        class="page-btn"
        :disabled="currentPage <= 1"
        @click="currentPage--"
      >&laquo; Prev</button>
      <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
      <button
        class="page-btn"
        :disabled="currentPage >= totalPages"
        @click="currentPage++"
      >Next &raquo;</button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getSimulationHistory } from '../api/intelligence'

const router = useRouter()

const loading = ref(true)
const simulations = ref([])
const statusFilter = ref('all')
const dateFrom = ref('')
const dateTo = ref('')
const currentPage = ref(1)
const perPage = 12

async function fetchSimulations() {
  loading.value = true
  currentPage.value = 1
  try {
    const res = await getSimulationHistory()
    if (res.data && res.data.success) {
      simulations.value = res.data.data || []
    }
  } catch (e) {
    simulations.value = []
  } finally {
    loading.value = false
  }
}

const filteredSimulations = computed(() => {
  let list = simulations.value
  if (statusFilter.value !== 'all') {
    list = list.filter(s => {
      const st = effectiveStatus(s)
      return st === statusFilter.value
    })
  }
  if (dateFrom.value) {
    const from = new Date(dateFrom.value)
    list = list.filter(s => new Date(s.created_at) >= from)
  }
  if (dateTo.value) {
    const to = new Date(dateTo.value)
    to.setHours(23, 59, 59, 999)
    list = list.filter(s => new Date(s.created_at) <= to)
  }
  return list
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredSimulations.value.length / perPage)))

const paginatedSimulations = computed(() => {
  const start = (currentPage.value - 1) * perPage
  return filteredSimulations.value.slice(start, start + perPage)
})

function effectiveStatus(sim) {
  const rs = (sim.runner_status || '').toLowerCase()
  const st = (sim.status || '').toLowerCase()
  if (rs === 'running' || st === 'running') return 'running'
  if (st === 'completed' || rs === 'completed') return 'completed'
  if (st === 'failed' || rs === 'failed') return 'failed'
  if (st === 'preparing' || st === 'building_graph') return 'preparing'
  return st || 'pending'
}

function statusClass(sim) {
  const s = effectiveStatus(sim)
  if (s === 'running') return 'badge-running'
  if (s === 'completed') return 'badge-completed'
  if (s === 'failed') return 'badge-failed'
  if (s === 'preparing' || s === 'building_graph') return 'badge-preparing'
  return 'badge-pending'
}

function statusLabel(sim) {
  const s = effectiveStatus(sim)
  return s.charAt(0).toUpperCase() + s.slice(1)
}

function relativeTime(dateStr) {
  if (!dateStr) return ''
  const now = Date.now()
  const then = new Date(dateStr).getTime()
  const diff = now - then
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  if (days < 30) return `${days}d ago`
  return new Date(dateStr).toLocaleDateString()
}

function navigateTo(sim) {
  const s = effectiveStatus(sim)
  if (s === 'completed' && sim.report_id) {
    router.push(`/report/${sim.report_id}`)
  } else {
    router.push(`/simulation/${sim.simulation_id}/start`)
  }
}

onMounted(fetchSimulations)
</script>

<style scoped>
.simulations-page {
  padding: 40px;
  max-width: 960px;
  margin: 0 auto;
  color: #e0e0e0;
  font-family: 'Space Grotesk', system-ui, sans-serif;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 28px;
}

.page-title {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.6rem;
  font-weight: 700;
  color: #ffffff;
  margin: 0;
}

.new-sim-btn {
  background: #FF4500;
  color: #fff;
  padding: 8px 18px;
  border-radius: 6px;
  text-decoration: none;
  font-weight: 600;
  font-size: 0.85rem;
  transition: background 0.15s;
}

.new-sim-btn:hover {
  background: #e03e00;
}

.filter-bar {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.filter-label {
  font-size: 0.7rem;
  color: #888;
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 1px;
  text-transform: uppercase;
}

.filter-select,
.filter-input {
  background: #111;
  border: 1px solid #333;
  color: #e0e0e0;
  padding: 6px 10px;
  border-radius: 4px;
  font-size: 0.85rem;
  font-family: 'Space Grotesk', system-ui, sans-serif;
}

.filter-select:focus,
.filter-input:focus {
  outline: none;
  border-color: #FF4500;
}

.loading-state {
  text-align: center;
  padding: 60px 0;
  color: #666;
  font-size: 0.95rem;
}

.empty-state {
  text-align: center;
  padding: 80px 0;
}

.empty-text {
  color: #666;
  font-size: 1rem;
  margin-bottom: 12px;
}

.empty-link {
  color: #FF4500;
  text-decoration: none;
  font-weight: 600;
  font-size: 0.95rem;
}

.empty-link:hover {
  text-decoration: underline;
}

.sim-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.sim-card {
  background: #0a0a0a;
  border: 1px solid #222;
  border-radius: 8px;
  padding: 16px 20px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}

.sim-card:hover {
  border-color: #FF4500;
  background: #111;
}

.sim-card-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 8px;
}

.sim-title {
  font-weight: 600;
  font-size: 0.95rem;
  color: #fff;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.status-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
}

.badge-running {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.badge-completed {
  background: rgba(34, 197, 94, 0.15);
  color: #22c55e;
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.badge-failed {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.badge-preparing {
  background: rgba(234, 179, 8, 0.15);
  color: #eab308;
  border: 1px solid rgba(234, 179, 8, 0.3);
}

.badge-pending {
  background: rgba(156, 163, 175, 0.15);
  color: #9ca3af;
  border: 1px solid rgba(156, 163, 175, 0.3);
}

.sim-card-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8rem;
  color: #777;
}

.meta-sep {
  color: #444;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 28px;
}

.page-btn {
  background: #111;
  border: 1px solid #333;
  color: #ccc;
  padding: 6px 14px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
  font-family: 'Space Grotesk', system-ui, sans-serif;
  transition: border-color 0.15s;
}

.page-btn:hover:not(:disabled) {
  border-color: #FF4500;
  color: #fff;
}

.page-btn:disabled {
  opacity: 0.35;
  cursor: default;
}

.page-info {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: #888;
}
</style>
