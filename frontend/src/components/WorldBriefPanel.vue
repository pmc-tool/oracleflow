<template>
  <div class="world-brief-panel">
    <div class="brief-header">
      <span class="brief-title">AI INSIGHTS</span>
      <span class="brief-live-badge">LIVE</span>
    </div>
    <div class="brief-divider"></div>
    <div class="brief-body">
      <div class="brief-section-label">WORLD BRIEF</div>
      <div v-if="loading" class="brief-loading">Generating intelligence brief...</div>
      <div v-else-if="error && !briefHtml" class="brief-fallback">
        <div class="fallback-title">Top Signals</div>
        <div
          v-for="sig in fallbackSignals"
          :key="sig.id"
          class="fallback-item"
        >
          <span class="fallback-dot" :style="{ background: anomalyColor(sig.anomaly_score) }"></span>
          <span class="fallback-text">
            <strong>{{ sig.country_code || '--' }}:</strong> {{ sig.title }}
          </span>
        </div>
      </div>
      <div v-else class="brief-content" v-html="briefHtml"></div>
    </div>
    <div class="brief-footer">
      <span class="brief-meta">Updated: {{ updatedAgo }}</span>
      <span class="brief-meta-sep">|</span>
      <span class="brief-meta">Based on {{ signalCount }} signals</span>
      <button class="brief-refresh-btn" @click="fetchBrief" :disabled="loading">
        Refresh &#8635;
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { getWorldBrief, listSignals } from '../api/intelligence'

const briefData = ref(null)
const fallbackSignals = ref([])
const loading = ref(true)
const error = ref(false)
const lastUpdated = ref(null)
let refreshTimer = null

const briefHtml = computed(() => {
  if (!briefData.value) return ''
  return briefData.value.brief || briefData.value.content || briefData.value.summary || ''
})

const signalCount = computed(() => {
  if (briefData.value && briefData.value.signal_count != null) return briefData.value.signal_count
  return fallbackSignals.value.length || '--'
})

const updatedAgo = computed(() => {
  if (!lastUpdated.value) return '--'
  const diff = Date.now() - lastUpdated.value
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  return `${hours}h ago`
})

function anomalyColor(score) {
  if (score == null || score < 0.3) return '#555'
  if (score < 0.5) return '#FFC107'
  if (score < 0.7) return '#ff8800'
  return '#ff4444'
}

async function fetchBrief() {
  loading.value = true
  error.value = false
  try {
    const res = await getWorldBrief()
    briefData.value = res.data || res
    lastUpdated.value = Date.now()
  } catch {
    error.value = true
    // Fallback: fetch top signals
    try {
      const res = await listSignals({ limit: 5, sort: '-anomaly_score' })
      const d = res.data || res
      fallbackSignals.value = Array.isArray(d) ? d : (d.items || d.results || [])
      lastUpdated.value = Date.now()
    } catch {
      // double failure, silent
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchBrief()
  refreshTimer = setInterval(fetchBrief, 30 * 60 * 1000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
.world-brief-panel {
  background: #0a0a0a;
  border: 1px solid #2a2a2a;
  display: flex;
  flex-direction: column;
}

.brief-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
}

.brief-title {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  font-weight: 700;
  color: #e8e8e8;
  letter-spacing: 1px;
}

.brief-live-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  font-weight: 700;
  color: #4CAF50;
  letter-spacing: 1px;
}

.brief-divider {
  height: 1px;
  background: #2a2a2a;
}

.brief-body {
  padding: 14px 16px;
  border-left: 3px solid #ff8800;
  margin: 12px 16px;
}

.brief-section-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  font-weight: 700;
  color: #888;
  letter-spacing: 1px;
  margin-bottom: 10px;
}

.brief-loading {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #555;
  animation: blink-loading 1.5s ease-in-out infinite;
}

@keyframes blink-loading {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.brief-content {
  font-family: 'Space Grotesk', system-ui, sans-serif;
  font-size: 0.82rem;
  color: #ccc;
  line-height: 1.6;
}

.brief-content :deep(strong) {
  color: #e8e8e8;
}

.brief-content :deep(ul) {
  padding-left: 18px;
  margin: 8px 0;
}

.brief-content :deep(li) {
  margin-bottom: 4px;
}

.brief-fallback {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.fallback-title {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #888;
  font-weight: 600;
  margin-bottom: 4px;
}

.fallback-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}

.fallback-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 5px;
}

.fallback-text {
  font-family: 'Space Grotesk', system-ui, sans-serif;
  font-size: 0.78rem;
  color: #aaa;
  line-height: 1.4;
}

.fallback-text strong {
  color: #ff8800;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
}

.brief-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  border-top: 1px solid #2a2a2a;
}

.brief-meta {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  color: #555;
}

.brief-meta-sep {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  color: #333;
}

.brief-refresh-btn {
  margin-left: auto;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  padding: 2px 10px;
  border: 1px solid #2a2a2a;
  background: transparent;
  color: #777;
  cursor: pointer;
  transition: all 0.15s;
}

.brief-refresh-btn:hover {
  border-color: #ff8800;
  color: #ff8800;
}

.brief-refresh-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
</style>
