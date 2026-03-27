<template>
  <div class="live-feed">
    <div class="feed-header">
      <div class="feed-header-left">
        <span class="feed-label">LIVE NEWS</span>
        <span class="feed-count-dot"></span>
        <span class="feed-count">{{ filteredSignals.length }}</span>
      </div>
      <div class="feed-header-right">
        <button class="header-btn" title="List view">&#8801;</button>
        <button class="header-btn" title="Grid view">&#10697;</button>
      </div>
    </div>

    <div class="source-tabs">
      <button
        v-for="tab in sourceTabs"
        :key="tab.name"
        class="source-tab"
        :class="{ active: selectedSource === tab.name }"
        @click="selectedSource = tab.name"
      >
        {{ tab.name }}
      </button>
    </div>

    <div v-if="countryFilter" class="filter-bar">
      <span class="filter-label">Filtered: <strong>{{ countryFilter }}</strong></span>
      <button class="clear-filter-btn" @click="$emit('clearFilter')">Clear filter</button>
    </div>

    <div class="feed-scroll">
      <div v-if="loading" class="feed-empty">Loading signals...</div>
      <div v-else-if="filteredSignals.length === 0" class="feed-empty">No signals</div>
      <div
        v-for="sig in filteredSignals"
        :key="sig.id"
        class="signal-card"
      >
        <div class="card-top-row">
          <span class="card-source" :style="{ color: sourceColor(getSourceName(sig)) }">
            {{ getSourceName(sig) }}
          </span>
          <span class="card-time">{{ timeAgo(sig.created_at) }}</span>
        </div>
        <div class="card-headline">{{ sig.title }}</div>
        <div class="card-bottom-row">
          <span
            v-if="threatLevel(sig.anomaly_score)"
            class="threat-badge"
            :class="threatLevel(sig.anomaly_score).cls"
          >
            &#9679; {{ threatLevel(sig.anomaly_score).label }}
          </span>
          <span class="card-country">{{ sig.country_code || '--' }}</span>
          <span class="card-sources-count">{{ getSourceCount(sig) }} source{{ getSourceCount(sig) !== 1 ? 's' : '' }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { listSignals } from '../api/intelligence'

const props = defineProps({
  countryFilter: { type: String, default: '' }
})

defineEmits(['clearFilter'])

const signals = ref([])
const loading = ref(true)
const selectedSource = ref('ALL')
let refreshTimer = null

const SOURCE_COLORS = {
  'Bloomberg': '#ff8800',
  'Sky News': '#c10000',
  'Euronews': '#1a5276',
  'CNN': '#cc0000',
  'CNBC': '#005594',
  'Al Jazeera': '#d2a633',
  'BBC': '#bb1919',
  'Reuters': '#ff6600',
  'Guardian': '#0d6aa8',
  'Politico': '#e00000',
  'AP News': '#e02020',
  'NBC News': '#3d7bca',
  'Fox News': '#003366',
  'NPR': '#3679b5',
  'Washington Post': '#1d1d1d',
  'NY Times': '#567b95',
}

function getSourceName(sig) {
  try {
    if (sig.raw_data_json) {
      const raw = typeof sig.raw_data_json === 'string'
        ? JSON.parse(sig.raw_data_json)
        : sig.raw_data_json
      if (raw.source_name) return raw.source_name
    }
  } catch { /* ignore */ }
  return sig.source || 'Unknown'
}

function getSourceCount(sig) {
  try {
    if (sig.raw_data_json) {
      const raw = typeof sig.raw_data_json === 'string'
        ? JSON.parse(sig.raw_data_json)
        : sig.raw_data_json
      if (raw.source_count) return raw.source_count
    }
  } catch { /* ignore */ }
  return 1
}

function sourceColor(name) {
  return SOURCE_COLORS[name] || '#888'
}

const sourceTabs = computed(() => {
  const counts = {}
  for (const sig of signals.value) {
    const src = getSourceName(sig)
    counts[src] = (counts[src] || 0) + 1
  }
  const sorted = Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 6)
    .map(([name]) => ({ name: name.toUpperCase() }))
  return [{ name: 'ALL' }, ...sorted]
})

const filteredSignals = computed(() => {
  let list = signals.value
  if (selectedSource.value !== 'ALL') {
    list = list.filter(s => getSourceName(s).toUpperCase() === selectedSource.value)
  }
  return list
})

function threatLevel(score) {
  if (score == null) return null
  if (score > 0.7) return { label: 'CRITICAL', cls: 'threat-critical' }
  if (score > 0.5) return { label: 'HIGH', cls: 'threat-high' }
  if (score > 0.3) return { label: 'ELEVATED', cls: 'threat-elevated' }
  return null
}

function timeAgo(ts) {
  if (!ts) return '--'
  const diff = Date.now() - new Date(ts).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  return `${days}d ago`
}

async function fetchSignals() {
  try {
    const params = { limit: 50 }
    if (props.countryFilter) params.country_code = props.countryFilter
    const res = await listSignals(params)
    const d = res.data || res
    signals.value = Array.isArray(d) ? d : (d.items || d.results || [])
  } catch {
    // silent
  } finally {
    loading.value = false
  }
}

watch(() => props.countryFilter, () => {
  loading.value = true
  fetchSignals()
})

onMounted(() => {
  fetchSignals()
  refreshTimer = setInterval(fetchSignals, 60000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
.live-feed {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #0a0a0a;
  border: 1px solid #2a2a2a;
  padding: 12px;
}

.feed-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.feed-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.feed-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  font-weight: 700;
  color: #e8e8e8;
  letter-spacing: 1px;
}

.feed-count-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #4CAF50;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.6); }
  50% { opacity: 0.7; box-shadow: 0 0 0 6px rgba(76, 175, 80, 0); }
}

.feed-count {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  font-weight: 600;
  color: #4CAF50;
}

.feed-header-right {
  display: flex;
  gap: 4px;
}

.header-btn {
  background: transparent;
  border: 1px solid #2a2a2a;
  color: #666;
  font-size: 0.9rem;
  width: 26px;
  height: 26px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
}

.header-btn:hover {
  border-color: #444;
  color: #e8e8e8;
}

.source-tabs {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.source-tab {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  padding: 3px 8px;
  border: 1px solid #2a2a2a;
  background: transparent;
  color: #777;
  cursor: pointer;
  transition: all 0.15s;
  letter-spacing: 0.5px;
  white-space: nowrap;
}

.source-tab:hover {
  border-color: #444;
  color: #ccc;
}

.source-tab.active {
  background: #e8e8e8;
  border-color: #e8e8e8;
  color: #0a0a0a;
  font-weight: 700;
}

.filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  margin-bottom: 8px;
  background: #141414;
  border: 1px solid #2a2a2a;
}

.filter-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #888;
}

.filter-label strong {
  color: #ff8800;
}

.clear-filter-btn {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  padding: 2px 8px;
  border: 1px solid #ff4444;
  background: transparent;
  color: #ff4444;
  cursor: pointer;
  transition: all 0.15s;
}

.clear-filter-btn:hover {
  background: #ff4444;
  color: #fff;
}

.feed-scroll {
  flex: 1;
  overflow-y: auto;
  max-height: 600px;
}

.feed-scroll::-webkit-scrollbar {
  width: 4px;
}

.feed-scroll::-webkit-scrollbar-track {
  background: #0a0a0a;
}

.feed-scroll::-webkit-scrollbar-thumb {
  background: #2a2a2a;
}

.feed-empty {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: #555;
  padding: 20px 0;
}

.signal-card {
  border: 1px solid #2a2a2a;
  background: #141414;
  padding: 10px 12px;
  margin-bottom: 6px;
  transition: border-color 0.15s;
}

.signal-card:hover {
  border-color: #444;
}

.card-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 5px;
}

.card-source {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  font-weight: 600;
  letter-spacing: 0.3px;
}

.card-time {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  color: #555;
}

.card-headline {
  font-family: 'Space Grotesk', system-ui, sans-serif;
  font-size: 0.82rem;
  font-weight: 700;
  color: #e8e8e8;
  line-height: 1.35;
  margin-bottom: 8px;
}

.card-bottom-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.threat-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.5px;
  padding: 1px 6px;
}

.threat-critical {
  color: #ff4444;
}

.threat-high {
  color: #ff8800;
}

.threat-elevated {
  color: #FFC107;
}

.card-country {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  color: #888;
  font-weight: 600;
}

.card-sources-count {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  color: #555;
}
</style>
