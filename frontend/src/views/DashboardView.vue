<template>
  <div class="dashboard">
    <h1 class="page-title">Intelligence Dashboard</h1>

    <div v-if="loading" class="loading-text">Loading...</div>

    <template v-else>
      <!-- Top row: 4 stat cards -->
      <div class="stats-row">
        <div class="stat-card chaos-card">
          <div class="stat-label">Global Chaos Index</div>
          <div class="stat-value chaos-value" :style="{ color: chaosColor }">
            {{ (chaos.global_score ?? chaos.composite_score) != null ? (chaos.global_score ?? chaos.composite_score).toFixed(1) : '--' }}
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Active Sites</div>
          <div class="stat-value">{{ sitesCount }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Total Signals</div>
          <div class="stat-value">{{ signalsCount }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Tracked Entities</div>
          <div class="stat-value">{{ entitiesCount }}</div>
        </div>
      </div>

      <!-- Category bars -->
      <div class="section-box">
        <h2 class="section-heading">Chaos Categories</h2>
        <div class="category-bars">
          <div v-for="cat in categories" :key="cat.key" class="category-row">
            <span class="cat-label">{{ cat.label }}</span>
            <div class="bar-track">
              <div
                class="bar-fill"
                :style="{ width: (cat.score ?? 0) + '%', background: cat.color }"
              ></div>
            </div>
            <span class="cat-score">{{ cat.score != null ? cat.score.toFixed(1) : '--' }}</span>
          </div>
        </div>
      </div>

      <!-- Recent Signals -->
      <div class="section-box">
        <h2 class="section-heading">Recent Signals</h2>
        <div v-if="signals.length === 0" class="empty-state">No signals yet</div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Source</th>
              <th>Category</th>
              <th>Anomaly</th>
              <th>Timestamp</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="sig in signals" :key="sig.id">
              <td class="title-cell">{{ sig.title }}</td>
              <td><span class="badge">{{ sig.source }}</span></td>
              <td><span class="badge badge-cat">{{ sig.category }}</span></td>
              <td>
                <span class="anomaly-num" :style="{ color: anomalyColor(sig.anomaly_score) }">
                  {{ sig.anomaly_score != null ? sig.anomaly_score.toFixed(2) : '--' }}
                </span>
              </td>
              <td class="ts-cell">{{ formatTime(sig.created_at) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <div v-if="error" class="error-text">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getChaos, listSites, listSignals, listEntities } from '../api/intelligence'

const loading = ref(true)
const error = ref('')
const chaos = ref({})
const sitesCount = ref(0)
const signalsCount = ref(0)
const entitiesCount = ref(0)
const signals = ref([])

const chaosColor = computed(() => {
  const s = chaos.value.global_score ?? chaos.value.composite_score
  if (s == null) return '#999'
  if (s < 30) return '#4CAF50'
  if (s < 60) return '#FFC107'
  if (s < 80) return '#FF9800'
  return '#F44336'
})

const categories = computed(() => {
  const cats = chaos.value.category_scores || chaos.value.categories || {}
  return [
    { key: 'finance', label: 'Finance', color: '#2196F3', score: cats.finance },
    { key: 'geopolitical', label: 'Geopolitical', color: '#F44336', score: cats.geopolitical },
    { key: 'supply_chain', label: 'Supply Chain', color: '#FF9800', score: cats.supply_chain },
    { key: 'cyber', label: 'Cyber', color: '#9C27B0', score: cats.cyber },
    { key: 'climate', label: 'Climate', color: '#4CAF50', score: cats.climate },
  ]
})

const anomalyColor = (score) => {
  if (score == null) return '#999'
  if (score < 0.3) return '#4CAF50'
  if (score < 0.6) return '#FFC107'
  if (score < 0.8) return '#FF9800'
  return '#F44336'
}

const formatTime = (ts) => {
  if (!ts) return '--'
  return new Date(ts).toLocaleString()
}

onMounted(async () => {
  try {
    const [chaosRes, sitesRes, signalsRes, entitiesRes, recentRes] = await Promise.allSettled([
      getChaos(),
      listSites(),
      listSignals({ limit: 1 }),
      listEntities({ limit: 1 }),
      listSignals({ limit: 10 }),
    ])

    if (chaosRes.status === 'fulfilled') chaos.value = chaosRes.value.data || chaosRes.value || {}
    if (sitesRes.status === 'fulfilled') {
      const d = sitesRes.value.data || sitesRes.value
      sitesCount.value = Array.isArray(d) ? d.length : (d.count ?? 0)
    }
    if (signalsRes.status === 'fulfilled') {
      const d = signalsRes.value.data || signalsRes.value
      signalsCount.value = d.total ?? (Array.isArray(d) ? d.length : 0)
    }
    if (entitiesRes.status === 'fulfilled') {
      const d = entitiesRes.value.data || entitiesRes.value
      entitiesCount.value = d.total ?? (Array.isArray(d) ? d.length : 0)
    }
    if (recentRes.status === 'fulfilled') {
      const d = recentRes.value.data || recentRes.value
      signals.value = Array.isArray(d) ? d : (d.items || d.results || [])
    }
  } catch (e) {
    error.value = 'Failed to load dashboard data: ' + e.message
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.dashboard {
  font-family: 'Space Grotesk', system-ui, sans-serif;
  max-width: 1200px;
}

.page-title {
  font-size: 1.8rem;
  font-weight: 600;
  margin-bottom: 30px;
  color: #FFFFFF;
}

.loading-text {
  font-family: 'JetBrains Mono', monospace;
  color: #999;
  font-size: 0.9rem;
}

.error-text {
  font-family: 'JetBrains Mono', monospace;
  color: #F44336;
  font-size: 0.85rem;
  margin-top: 15px;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 30px;
}

.stat-card {
  border: 1px solid #333;
  padding: 20px;
  background: #000;
}

.stat-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #999;
  letter-spacing: 0.5px;
  margin-bottom: 8px;
}

.stat-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 2rem;
  font-weight: 700;
  color: #FFFFFF;
}

.chaos-value {
  font-size: 2.5rem;
}

.section-box {
  border: 1px solid #333;
  padding: 20px;
  margin-bottom: 24px;
  background: #000;
}

.section-heading {
  font-size: 1rem;
  font-weight: 600;
  color: #FFFFFF;
  margin-bottom: 20px;
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 0.5px;
}

.category-bars {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.category-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.cat-label {
  width: 100px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: #CCC;
  text-align: right;
}

.bar-track {
  flex: 1;
  height: 16px;
  background: #1a1a1a;
  border: 1px solid #333;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  transition: width 0.5s ease;
}

.cat-score {
  width: 50px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  color: #FFFFFF;
  text-align: right;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.data-table th {
  text-align: left;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #999;
  letter-spacing: 0.5px;
  padding: 8px 12px;
  border-bottom: 1px solid #333;
}

.data-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #1a1a1a;
  color: #CCC;
}

.title-cell {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ts-cell {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #666;
  white-space: nowrap;
}

.badge {
  display: inline-block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  padding: 2px 8px;
  border: 1px solid #444;
  color: #CCC;
  letter-spacing: 0.5px;
}

.badge-cat {
  border-color: #FF4500;
  color: #FF4500;
}

.anomaly-num {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  font-size: 0.85rem;
}

.empty-state {
  color: #666;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  padding: 20px 0;
}

@media (max-width: 768px) {
  .stats-row { grid-template-columns: repeat(2, 1fr); }
}

@media (max-width: 480px) {
  .stats-row { grid-template-columns: 1fr; }
}
</style>
