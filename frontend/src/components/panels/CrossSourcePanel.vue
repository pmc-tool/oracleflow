<template>
  <BasePanel panelId="cross-source" title="CROSS-SOURCE SIGNAL AGGREGATOR">
    <template #default>
      <div class="cs-list">
        <div
          v-for="(signal, idx) in topSignals"
          :key="signal.id"
          class="cs-item"
        >
          <div class="cs-item__header">
            <span class="cs-item__num">{{ idx + 1 }}</span>
            <span class="cs-item__icon">{{ getIcon(signal) }}</span>
            <span class="cs-item__type">{{ getTypeLabel(signal) }}</span>
            <span
              class="cs-item__severity"
              :class="'cs-severity--' + getSeverity(signal).toLowerCase()"
            >{{ getSeverity(signal) }}</span>
          </div>
          <div class="cs-item__meta">
            <span class="cs-item__location">{{ signal.country_code || 'Global' }}</span>
            <span class="cs-item__dot">&middot;</span>
            <span v-if="signal.category" class="cs-item__category">{{ signal.category }}</span>
            <span v-if="signal.category" class="cs-item__dot">&middot;</span>
            <span class="cs-item__time">{{ formatTimeAgo(signal.timestamp) }}</span>
            <span class="threat-dot" :class="'threat-dot--' + getThreatDotClass(signal)"></span>
          </div>
          <div class="cs-item__summary">
            <a
              v-if="getSourceUrl(signal)"
              :href="getSourceUrl(signal)"
              target="_blank"
              rel="noopener noreferrer"
              class="cs-item__link"
            >{{ signal.title }}</a>
            <span v-else>{{ signal.title }}</span>
          </div>
        </div>

        <div v-if="topSignals.length === 0 && !loading" class="cs-empty">
          No cross-source signals available
        </div>
        <div v-if="loading" class="cs-empty">
          Loading signals...
        </div>
      </div>
    </template>
  </BasePanel>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import BasePanel from '../BasePanel.vue'
import { listSignals } from '../../api/intelligence'

const signals = ref([])
const loading = ref(false)
let refreshInterval = null

const topSignals = computed(() => {
  return [...signals.value]
    .sort((a, b) => (b.anomaly_score || 0) - (a.anomaly_score || 0))
    .slice(0, 8)
})

function getIcon(signal) {
  const type = (signal.signal_type || '').toLowerCase()
  const cat = (signal.category || '').toLowerCase()
  if (type.includes('conflict') || type.includes('battle')) return '\u2694'
  if (type.includes('earthquake')) return '\ud83c\udf0b'
  if (type.includes('wildfire') || type.includes('fire')) return '\ud83d\udd25'
  if (cat.includes('geopolitical')) return '\u26a0'
  if (cat.includes('climate')) return '\ud83c\udf0d'
  if (cat.includes('finance') || cat.includes('economy')) return '\ud83d\udcc8'
  return '\ud83d\udcf0'
}

function getTypeLabel(signal) {
  const type = (signal.signal_type || signal.category || 'INTEL').toUpperCase()
  if (type.length > 12) return type.slice(0, 12)
  return type
}

function getSeverity(signal) {
  const score = signal.anomaly_score || 0
  if (score >= 0.8) return 'CRITICAL'
  if (score >= 0.6) return 'HIGH'
  if (score >= 0.4) return 'ELEVATED'
  return 'NORMAL'
}

function getSourceUrl(signal) {
  if (signal.source_url) return signal.source_url
  try {
    const raw = signal.raw_data_json
    if (typeof raw === 'string') {
      const parsed = JSON.parse(raw)
      return parsed.link || parsed.url || parsed.source_url || null
    }
    if (raw && typeof raw === 'object') {
      return raw.link || raw.url || raw.source_url || null
    }
  } catch { /* ignore */ }
  return null
}

function getThreatDotClass(signal) {
  const score = signal.anomaly_score || 0
  if (score > 0.8) return 'red'
  if (score > 0.6) return 'orange'
  if (score > 0.4) return 'yellow'
  return 'green'
}

function formatTimeAgo(dateStr) {
  if (!dateStr) return ''
  const now = Date.now()
  const then = new Date(dateStr).getTime()
  const diff = Math.floor((now - then) / 1000)
  if (diff < 60) return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

async function fetchSignals() {
  loading.value = true
  try {
    const res = await listSignals({ limit: 50 })
    const data = res.data?.data || res.data?.results || res.data || []
    signals.value = Array.isArray(data) ? data : []
  } catch (err) {
    console.error('[CrossSourcePanel] fetch error:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchSignals()
  refreshInterval = setInterval(fetchSignals, 90000)
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})
</script>

<style scoped>
.cs-list {
  overflow-y: auto;
  flex: 1;
}

.cs-item {
  padding: 10px 12px;
  border-bottom: 1px solid var(--wm-border, #2a2a2a);
  transition: background 0.15s ease;
}

.cs-item:hover {
  background: var(--wm-surface-hover, #1e1e1e);
}

.cs-item__header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.cs-item__num {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  font-weight: 700;
  color: var(--wm-text-dim, #888);
  min-width: 16px;
}

.cs-item__icon {
  font-size: 12px;
}

.cs-item__type {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  font-weight: 600;
  color: var(--wm-text, #e8e8e8);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.cs-item__severity {
  margin-left: auto;
  font-family: 'SF Mono', monospace;
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  padding: 1px 6px;
  border-radius: 2px;
}

.cs-severity--critical {
  background: var(--wm-critical, #ff4444);
  color: #ffffff;
}

.cs-severity--high {
  background: var(--wm-high, #ff8800);
  color: #ffffff;
}

.cs-severity--elevated {
  background: var(--wm-elevated, #ffaa00);
  color: #1a1a1a;
}

.cs-severity--normal {
  background: var(--wm-border, #2a2a2a);
  color: var(--wm-text-dim, #888);
}

.cs-item__meta {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
  padding-left: 22px;
}

.cs-item__location {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  color: var(--wm-text-dim, #888);
}

.cs-item__dot {
  color: var(--wm-text-dim, #888);
  font-size: 10px;
}

.cs-item__time {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  color: var(--wm-text-dim, #888);
}

.cs-item__category {
  font-family: 'SF Mono', monospace;
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--wm-text-dim, #888);
}

.threat-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-left: auto;
}

.threat-dot--red { background: #ff4444; }
.threat-dot--orange { background: #ff8800; }
.threat-dot--yellow { background: #ffaa00; }
.threat-dot--green { background: #44aa44; }

.cs-item__summary {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--wm-text-secondary, #ccc);
  line-height: 1.4;
  padding-left: 22px;
}

.cs-item__link {
  color: inherit;
  text-decoration: none;
}

.cs-item__link:hover {
  text-decoration: underline;
}

.cs-empty {
  padding: 24px;
  text-align: center;
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--wm-text-dim, #888);
}
</style>
