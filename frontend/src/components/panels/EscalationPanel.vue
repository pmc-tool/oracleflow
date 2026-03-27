<template>
  <BasePanel panelId="escalation" title="ESCALATION CORRELATION">
    <template #default>
      <div class="esc-container">
        <div v-if="escalations.length > 0" class="esc-alert">
          &#x26A0; ACTIVE ESCALATION DETECTED
        </div>
        <div v-if="escalations.length === 0 && !loading" class="esc-empty">
          No escalation correlations detected
        </div>
        <div v-if="loading" class="esc-empty">
          Analyzing signal correlations...
        </div>

        <div
          v-for="esc in escalations"
          :key="esc.country"
          class="esc-item"
        >
          <div class="esc-item__header">
            <span class="esc-item__flag">{{ esc.flag }}</span>
            <span class="esc-item__name">{{ esc.country }}</span>
          </div>
          <div class="esc-item__row">
            <span class="esc-item__label">Military:</span>
            <span class="esc-item__val">{{ esc.military }} signals</span>
            <span class="esc-item__trend" :class="trendClass(esc.militaryTrend)">{{ esc.militaryTrend }}</span>
          </div>
          <div class="esc-item__row">
            <span class="esc-item__label">Political:</span>
            <span class="esc-item__val">{{ esc.political }} signals</span>
            <span class="esc-item__trend" :class="trendClass(esc.politicalTrend)">{{ esc.politicalTrend }}</span>
          </div>
          <div class="esc-item__row">
            <span class="esc-item__label">Combined risk:</span>
            <div class="esc-bar">
              <div
                class="esc-bar__fill"
                :style="{ width: esc.risk + '%', background: riskColor(esc.risk) }"
              ></div>
            </div>
            <span class="esc-item__pct" :style="{ color: riskColor(esc.risk) }">{{ esc.risk }}%</span>
          </div>
        </div>

        <div v-if="escalations.length > 0 && escalations.length < 5" class="esc-footer">
          No other escalations detected
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

const countryFlags = {
  Ukraine: '\u{1F1FA}\u{1F1E6}', Iran: '\u{1F1EE}\u{1F1F7}', China: '\u{1F1E8}\u{1F1F3}',
  Russia: '\u{1F1F7}\u{1F1FA}', Israel: '\u{1F1EE}\u{1F1F1}', Taiwan: '\u{1F1F9}\u{1F1FC}',
  'North Korea': '\u{1F1F0}\u{1F1F5}', Syria: '\u{1F1F8}\u{1F1FE}', Yemen: '\u{1F1FE}\u{1F1EA}',
  Myanmar: '\u{1F1F2}\u{1F1F2}', Sudan: '\u{1F1F8}\u{1F1E9}', Libya: '\u{1F1F1}\u{1F1FE}',
}

const militaryKeywords = ['military', 'troops', 'airstrike', 'army', 'weapons', 'missile', 'drone', 'combat', 'war', 'attack', 'defense', 'naval']

const MAX_POSSIBLE = 20

const escalations = computed(() => {
  const grouped = {}

  signals.value.forEach(s => {
    const country = s.country || s.country_code || ''
    if (!country) return

    if (!grouped[country]) {
      grouped[country] = { military: 0, political: 0 }
    }

    const cat = (s.category || '').toLowerCase()
    const title = (s.title || '').toLowerCase()
    const type = (s.signal_type || '').toLowerCase()

    const isMilitary = cat === 'geopolitical' && militaryKeywords.some(kw => title.includes(kw) || type.includes(kw))
    const isPolitical = cat === 'politics' || cat === 'political'

    if (isMilitary) grouped[country].military++
    if (isPolitical) grouped[country].political++
  })

  return Object.entries(grouped)
    .filter(([, v]) => v.military > 1 && v.political > 1)
    .map(([country, v]) => ({
      country,
      flag: countryFlags[country] || '\u{1F3F3}',
      military: v.military,
      political: v.political,
      militaryTrend: v.military >= 3 ? '\u25B2' : '\u2192',
      politicalTrend: v.political >= 3 ? '\u25B2' : '\u2192',
      risk: Math.min(100, Math.round((v.military + v.political) / MAX_POSSIBLE * 100)),
    }))
    .sort((a, b) => b.risk - a.risk)
    .slice(0, 5)
})

function riskColor(risk) {
  if (risk >= 75) return '#ff4444'
  if (risk >= 50) return '#ff8800'
  if (risk >= 30) return '#ffaa00'
  return '#44aa44'
}

function trendClass(trend) {
  if (trend === '\u25B2') return 'trend-up'
  return 'trend-flat'
}

async function fetchSignals() {
  loading.value = true
  try {
    const res = await listSignals({ limit: 200 })
    const data = res.data?.data || res.data?.results || res.data || []
    signals.value = Array.isArray(data) ? data : []
  } catch (err) {
    console.error('[EscalationPanel] fetch error:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchSignals()
  refreshInterval = setInterval(fetchSignals, 120000)
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})
</script>

<style scoped>
.esc-container {
  overflow-y: auto;
  flex: 1;
}

.esc-alert {
  padding: 8px 12px;
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  font-weight: 700;
  color: #ff4444;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--wm-border, #2a2a2a);
}

.esc-item {
  padding: 10px 12px;
  border-bottom: 1px solid var(--wm-border, #2a2a2a);
  transition: background 0.15s ease;
}

.esc-item:hover {
  background: var(--wm-surface-hover, #1e1e1e);
}

.esc-item__header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.esc-item__flag {
  font-size: 14px;
}

.esc-item__name {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  font-weight: 700;
  color: var(--wm-text, #e8e8e8);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.esc-item__row {
  display: flex;
  align-items: center;
  gap: 6px;
  padding-left: 22px;
  margin-bottom: 3px;
}

.esc-item__label {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--wm-text-dim, #888);
  min-width: 70px;
}

.esc-item__val {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--wm-text, #e8e8e8);
}

.esc-item__trend {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  margin-left: 4px;
}

.trend-up {
  color: #ff4444;
}

.trend-flat {
  color: var(--wm-text-dim, #888);
}

.esc-bar {
  flex: 1;
  height: 8px;
  background: var(--wm-border, #2a2a2a);
  border-radius: 2px;
  overflow: hidden;
  max-width: 100px;
}

.esc-bar__fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s ease;
}

.esc-item__pct {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  font-weight: 700;
  min-width: 32px;
  text-align: right;
}

.esc-empty {
  padding: 24px;
  text-align: center;
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--wm-text-dim, #888);
}

.esc-footer {
  padding: 10px 12px;
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--wm-text-dim, #888);
}
</style>
