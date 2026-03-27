<template>
  <transition name="slide-up">
    <div v-if="countryCode" class="country-risk-panel">
      <!-- Header -->
      <div class="panel-header">
        <div class="country-info">
          <span class="country-flag">{{ isGlobal ? '🌐' : flagEmoji(countryCode) }}</span>
          <span class="country-name">{{ countryName || countryCode }}</span>
        </div>
        <button class="close-btn" @click="$emit('close')">&times;</button>
      </div>

      <!-- Loading state -->
      <div v-if="loading" class="panel-loading">Loading risk data...</div>

      <template v-else>
        <!-- Instability Index -->
        <div class="instability-section">
          <div class="instability-header">
            <span class="instability-label">Instability Index</span>
            <span class="instability-updated">Updated {{ updatedAt }}</span>
          </div>
          <div class="instability-score-row">
            <span class="instability-score" :style="{ color: scoreColor(instabilityIndex) }">
              {{ instabilityIndex }}/100
            </span>
            <span class="instability-trend">{{ trendLabel }}</span>
          </div>
          <div class="instability-bar-track">
            <div
              class="instability-bar-fill"
              :style="{ width: instabilityIndex + '%', background: scoreColor(instabilityIndex) }"
            ></div>
          </div>
        </div>

        <!-- 4-Component Breakdown -->
        <div class="breakdown-grid">
          <div v-for="comp in breakdownComponents" :key="comp.key" class="breakdown-card">
            <span class="breakdown-label">{{ comp.label }}</span>
            <div class="breakdown-bar-track">
              <div
                class="breakdown-bar-fill"
                :style="{ width: comp.score + '%', background: scoreColor(comp.score) }"
              ></div>
            </div>
            <span class="breakdown-score" :style="{ color: scoreColor(comp.score) }">
              {{ comp.score }}
            </span>
          </div>
        </div>

        <!-- Intelligence Brief -->
        <div class="brief-section">
          <div class="section-title">INTELLIGENCE BRIEF</div>
          <div v-if="briefLoading" class="brief-loading">Generating AI brief...</div>
          <div v-else-if="briefText" class="brief-text">{{ briefText }}</div>
          <button v-else class="generate-btn" @click="fetchBrief">Generate AI Brief</button>
        </div>

        <!-- Active Signals badges -->
        <div v-if="signalBadges.length" class="signals-badges-section">
          <div class="section-title">ACTIVE SIGNALS</div>
          <div class="badges-row">
            <span v-for="badge in signalBadges" :key="badge.category" class="signal-badge">
              {{ badge.count }} {{ badge.category }}
            </span>
          </div>
        </div>

        <!-- Cross-source Signals -->
        <div v-if="crossSourceSignals.length" class="cross-source-section">
          <div class="section-title">CROSS-SOURCE SIGNALS</div>
          <div class="signal-list">
            <div v-for="(sig, idx) in crossSourceSignals" :key="sig.id || idx" class="signal-row">
              <span class="signal-index">{{ idx + 1 }}</span>
              <span class="signal-source">{{ sig.source_type || 'NEWS' }}</span>
              <span class="severity-badge" :class="severityClass(sig.anomaly_score)">
                {{ severityLabel(sig.anomaly_score) }}
              </span>
              <span class="signal-meta">{{ sig.country_code || 'Global' }} · {{ timeAgo(sig.timestamp) }}</span>
              <div class="signal-title">{{ sig.title }}</div>
            </div>
          </div>
        </div>

        <!-- Footer link -->
        <div class="panel-footer">
          <router-link :to="profileRoute" class="profile-link">
            View Full Country Profile &rarr;
          </router-link>
        </div>
      </template>
    </div>
  </transition>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { getCountryRisk, getCountryBrief, listSignals } from '../api/intelligence'

const props = defineProps({
  countryCode: { type: String, default: '' },
  countryName: { type: String, default: '' }
})

defineEmits(['close'])

const riskData = ref({})
const loading = ref(false)
const briefText = ref('')
const briefLoading = ref(false)
const signals = ref([])

const isGlobal = computed(() => props.countryCode?.toUpperCase() === 'GLOBAL')

const profileRoute = computed(() =>
  isGlobal.value ? '/intel' : `/countries/${props.countryCode}`
)

// Instability index: overall risk scaled to 0-100
const instabilityIndex = computed(() => {
  const score = riskData.value.overall_risk
  if (score == null) return 0
  return Math.round(score * 100)
})

const trendLabel = computed(() => {
  const idx = instabilityIndex.value
  if (idx < 25) return 'stable'
  if (idx < 50) return 'watch'
  if (idx < 75) return 'elevated'
  return 'critical'
})

const updatedAt = computed(() => {
  const now = new Date()
  const day = now.getDate()
  const months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
  const h = String(now.getHours()).padStart(2, '0')
  const m = String(now.getMinutes()).padStart(2, '0')
  return `${day} ${months[now.getMonth()]}, ${h}:${m}`
})

// Map categories to 4 components
const breakdownComponents = computed(() => {
  const cats = riskData.value.category_risk || {}
  function avg(...keys) {
    const vals = keys.map(k => cats[k]).filter(v => v != null)
    if (!vals.length) return 0
    return Math.round((vals.reduce((a, b) => a + b, 0) / vals.length) * 100)
  }
  return [
    { key: 'unrest', label: 'Unrest', score: avg('politics', 'crime') },
    { key: 'conflict', label: 'Conflict', score: avg('geopolitical') },
    { key: 'security', label: 'Security', score: avg('cyber', 'technology') },
    { key: 'information', label: 'Info', score: avg('other', 'economy', 'finance') },
  ]
})

// Signal category badges
const signalBadges = computed(() => {
  const counts = {}
  for (const s of signals.value) {
    const cat = s.category || 'other'
    counts[cat] = (counts[cat] || 0) + 1
  }
  return Object.entries(counts)
    .map(([category, count]) => ({ category, count }))
    .sort((a, b) => b.count - a.count)
})

// Cross-source signals (top 5 by anomaly)
const crossSourceSignals = computed(() => {
  return [...signals.value]
    .sort((a, b) => (b.anomaly_score || 0) - (a.anomaly_score || 0))
    .slice(0, 5)
})

function scoreColor(score) {
  if (score == null) return '#666'
  if (score < 25) return '#44aa44'
  if (score < 50) return '#ffaa00'
  if (score < 75) return '#ff8800'
  return '#ff4444'
}

function flagEmoji(code) {
  if (!code || code.length !== 2) return ''
  const offset = 127397
  return String.fromCodePoint(
    code.charCodeAt(0) + offset,
    code.charCodeAt(1) + offset
  )
}

function severityClass(score) {
  if (score == null) return 'sev-normal'
  if (score >= 0.75) return 'sev-critical'
  if (score >= 0.5) return 'sev-high'
  if (score >= 0.25) return 'sev-elevated'
  return 'sev-normal'
}

function severityLabel(score) {
  if (score == null) return 'NORMAL'
  if (score >= 0.75) return 'CRITICAL'
  if (score >= 0.5) return 'HIGH'
  if (score >= 0.25) return 'ELEVATED'
  return 'NORMAL'
}

function timeAgo(ts) {
  if (!ts) return ''
  const diff = Date.now() - new Date(ts).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  return `${Math.floor(hours / 24)}d ago`
}

async function fetchRisk(code) {
  if (!code) return
  loading.value = true
  try {
    const res = await getCountryRisk(code)
    riskData.value = res.data?.data || res.data || res || {}
  } catch {
    riskData.value = {}
  } finally {
    loading.value = false
  }
}

async function fetchSignals(code) {
  try {
    const params = code.toUpperCase() === 'GLOBAL' ? { limit: 30 } : { country_code: code, limit: 30 }
    const res = await listSignals(params)
    signals.value = res.data?.data || res.data || []
  } catch {
    signals.value = []
  }
}

async function fetchBrief() {
  if (!props.countryCode) return
  briefLoading.value = true
  try {
    const res = await getCountryBrief(props.countryCode)
    briefText.value = res.data?.data?.brief || res.data?.brief || 'Brief unavailable.'
  } catch {
    briefText.value = 'Failed to generate intelligence brief.'
  } finally {
    briefLoading.value = false
  }
}

watch(() => props.countryCode, (code) => {
  briefText.value = ''
  if (code) {
    fetchRisk(code)
    fetchSignals(code)
    fetchBrief()
  } else {
    riskData.value = {}
    signals.value = []
  }
}, { immediate: true })
</script>

<style scoped>
.country-risk-panel {
  background: #0a0a0a;
  border: 1px solid #2a2a2a;
  border-top: 2px solid #ff4444;
  padding: 20px 24px;
  width: 100%;
}

.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(30px);
  opacity: 0;
}

/* Header */
.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.country-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.country-flag {
  font-size: 1.6rem;
}

.country-name {
  font-family: 'Space Grotesk', system-ui, sans-serif;
  font-size: 1.2rem;
  font-weight: 600;
  color: #ffffff;
}

.close-btn {
  background: none;
  border: 1px solid #2a2a2a;
  color: #666;
  font-size: 1.3rem;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s;
}

.close-btn:hover {
  border-color: #555;
  color: #fff;
}

.panel-loading {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: #666;
  padding: 20px 0;
}

/* Instability Index */
.instability-section {
  margin-bottom: 20px;
}

.instability-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.instability-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.instability-updated {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  color: #555;
}

.instability-score-row {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 8px;
}

.instability-score {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.6rem;
  font-weight: 700;
}

.instability-trend {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #666;
}

.instability-bar-track {
  width: 100%;
  height: 6px;
  background: #141414;
  border-radius: 3px;
  overflow: hidden;
}

.instability-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.6s ease;
}

/* Breakdown Grid */
.breakdown-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 24px;
}

.breakdown-card {
  background: #141414;
  border: 1px solid #2a2a2a;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.breakdown-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.breakdown-bar-track {
  width: 100%;
  height: 4px;
  background: #0a0a0a;
  border-radius: 2px;
  overflow: hidden;
}

.breakdown-bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.5s ease;
}

.breakdown-score {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.1rem;
  font-weight: 700;
}

/* Section titles */
.section-title {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  color: #555;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 10px;
  border-bottom: 1px solid #1a1a1a;
  padding-bottom: 6px;
}

/* Intelligence Brief */
.brief-section {
  margin-bottom: 20px;
}

.brief-loading {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #666;
  padding: 12px 0;
}

.brief-text {
  font-family: 'Space Grotesk', system-ui, sans-serif;
  font-size: 0.85rem;
  color: #ccc;
  line-height: 1.6;
  white-space: pre-wrap;
}

.generate-btn {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #ff4444;
  background: #141414;
  border: 1px solid #2a2a2a;
  padding: 8px 16px;
  cursor: pointer;
  transition: all 0.15s;
}

.generate-btn:hover {
  border-color: #ff4444;
  background: #1a1010;
}

/* Active Signal Badges */
.signals-badges-section {
  margin-bottom: 20px;
}

.badges-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.signal-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #ccc;
  background: #141414;
  border: 1px solid #2a2a2a;
  padding: 4px 10px;
}

/* Cross-source Signals */
.cross-source-section {
  margin-bottom: 20px;
}

.signal-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.signal-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  background: #141414;
  border: 1px solid #1a1a1a;
}

.signal-index {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #555;
  width: 16px;
  flex-shrink: 0;
}

.signal-source {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  color: #888;
  background: #0a0a0a;
  border: 1px solid #2a2a2a;
  padding: 2px 6px;
  text-transform: uppercase;
}

.severity-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  font-weight: 700;
  padding: 2px 8px;
  letter-spacing: 0.05em;
}

.sev-critical {
  color: #ff4444;
  border: 1px solid #ff4444;
}

.sev-high {
  color: #ff8800;
  border: 1px solid #ff8800;
}

.sev-elevated {
  color: #ffaa00;
  border: 1px solid #ffaa00;
}

.sev-normal {
  color: #44aa44;
  border: 1px solid #44aa44;
}

.signal-meta {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  color: #555;
}

.signal-title {
  width: 100%;
  font-family: 'Space Grotesk', system-ui, sans-serif;
  font-size: 0.8rem;
  color: #bbb;
  margin-top: 2px;
}

/* Footer */
.panel-footer {
  padding-top: 16px;
  border-top: 1px solid #1a1a1a;
  text-align: center;
}

.profile-link {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #ff4444;
  text-decoration: none;
  transition: color 0.15s;
}

.profile-link:hover {
  color: #ff6a33;
}

/* Responsive */
@media (max-width: 640px) {
  .breakdown-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
