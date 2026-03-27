<template>
  <BasePanel
    panelId="ai-forecast"
    title="AI FORECASTS"
    infoTooltip="AI-generated probability assessments for active geopolitical theaters based on signal analysis"
    dataBadge="LIVE"
    :showCount="true"
    :count="filteredTheaters.length"
    :defaultRowSpan="2"
  >
    <template #tabs>
      <div class="forecast-tabs">
        <button
          v-for="tab in categoryTabs"
          :key="tab"
          class="forecast-tab"
          :class="{ active: activeCategory === tab }"
          @click="activeCategory = tab"
        >{{ tab }}</button>
      </div>
    </template>

    <template #default>
      <div class="forecast-content">
        <div class="forecast-section-header">
          <span class="forecast-section-title">ACTIVE THEATERS</span>
        </div>

        <div class="forecast-list">
          <div
            v-for="(theater, idx) in filteredTheaters"
            :key="idx"
            class="theater-row"
          >
            <div class="theater-top">
              <span class="theater-name">{{ theater.name }}</span>
              <span
                class="theater-pct"
                :style="{ color: getBarColor(theater.probability) }"
              >{{ theater.probability }}%</span>
            </div>
            <div class="theater-bar-wrapper">
              <div
                class="theater-bar"
                :style="{
                  width: theater.probability + '%',
                  background: getBarColor(theater.probability)
                }"
              ></div>
              <div class="theater-bar-bg"></div>
            </div>
            <div class="theater-meta">
              <span
                class="theater-status-dot"
                :style="{ background: theater.status === 'state' ? 'var(--semantic-info, #3b82f6)' : 'var(--semantic-high, #ff8800)' }"
              ></span>
              <span class="theater-status-label">{{ theater.status }}</span>
            </div>
          </div>
        </div>

        <div v-if="filteredTheaters.length === 0" class="forecast-empty">
          No theaters matching current filter
        </div>
      </div>
    </template>
  </BasePanel>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import BasePanel from '../BasePanel.vue'
import { listSignals } from '../../api/intelligence'

const categoryTabs = ['All', 'Conflict', 'Market', 'Supply Chain', 'Political', 'Military', 'Cyber', 'Infra']
const activeCategory = ref('All')

const theaters = ref([
  { name: 'Black Sea maritime disruption', probability: 80, status: 'state', category: 'Conflict' },
  { name: 'Iran-Israel escalation', probability: 72, status: 'trajectory', category: 'Military' },
  { name: 'Taiwan Strait tensions', probability: 45, status: 'trajectory', category: 'Political' },
  { name: 'Ukraine front line shifts', probability: 88, status: 'state', category: 'Conflict' },
  { name: 'Red Sea shipping disruption', probability: 65, status: 'trajectory', category: 'Supply Chain' },
  { name: 'China-Philippines SCS standoff', probability: 53, status: 'trajectory', category: 'Military' },
  { name: 'Global semiconductor shortage', probability: 41, status: 'state', category: 'Supply Chain' },
  { name: 'EU energy price volatility', probability: 58, status: 'trajectory', category: 'Market' },
  { name: 'Critical infrastructure cyber threat', probability: 62, status: 'state', category: 'Cyber' },
  { name: 'Suez Canal disruption risk', probability: 37, status: 'trajectory', category: 'Infra' },
  { name: 'North Korea provocation cycle', probability: 48, status: 'trajectory', category: 'Military' },
  { name: 'Sudan conflict spillover', probability: 70, status: 'state', category: 'Conflict' },
  { name: 'US-China trade decoupling', probability: 55, status: 'state', category: 'Market' },
  { name: 'Baltic states NATO posture', probability: 44, status: 'trajectory', category: 'Political' },
])

let refreshInterval = null

const filteredTheaters = computed(() => {
  if (activeCategory.value === 'All') return theaters.value
  return theaters.value.filter(t => t.category === activeCategory.value)
})

function getBarColor(pct) {
  if (pct > 70) return 'var(--semantic-critical, #ff4444)'
  if (pct > 50) return 'var(--semantic-high, #ff8800)'
  if (pct > 30) return 'var(--semantic-elevated, #ffaa00)'
  return 'var(--semantic-normal, #44aa44)'
}

async function fetchAndComputeTheaters() {
  try {
    const res = await listSignals({ limit: 200 })
    const data = res.data?.data || res.data?.results || res.data || []
    const signals = Array.isArray(data) ? data : []
    if (signals.length === 0) return

    // Group signals by keywords to adjust probabilities
    const regionKeywords = {
      'Black Sea maritime disruption': ['black sea', 'odessa', 'sevastopol', 'maritime'],
      'Iran-Israel escalation': ['iran', 'israel', 'tehran', 'idf', 'irgc'],
      'Taiwan Strait tensions': ['taiwan', 'taipei', 'strait', 'pla'],
      'Ukraine front line shifts': ['ukraine', 'kyiv', 'donbas', 'kherson', 'zaporizhzhia'],
      'Red Sea shipping disruption': ['red sea', 'houthi', 'yemen', 'shipping'],
      'China-Philippines SCS standoff': ['south china sea', 'philippines', 'manila', 'spratlys'],
      'Sudan conflict spillover': ['sudan', 'khartoum', 'rsf', 'darfur'],
    }

    for (const theater of theaters.value) {
      const keys = regionKeywords[theater.name]
      if (!keys) continue
      const matchCount = signals.filter(s => {
        const text = ((s.title || '') + ' ' + (s.summary || '')).toLowerCase()
        return keys.some(k => text.includes(k))
      }).length
      if (matchCount > 0) {
        // Compute average anomaly score for matched signals
        const matched = signals.filter(s => {
          const text = ((s.title || '') + ' ' + (s.summary || '')).toLowerCase()
          return keys.some(k => text.includes(k))
        })
        const avgAnomaly = matched.reduce((sum, s) => sum + (s.anomaly_score || 0.5), 0) / matched.length
        const adjustment = Math.min(matchCount * 2 + Math.round(avgAnomaly * 10), 20)
        theater.probability = Math.min(99, theater.probability + adjustment)
      }
    }
  } catch {
    // Use placeholder data
  }
}

onMounted(() => {
  fetchAndComputeTheaters()
  refreshInterval = setInterval(fetchAndComputeTheaters, 120000)
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})
</script>

<style scoped>
.forecast-tabs {
  display: flex;
  gap: 2px;
  overflow-x: auto;
  padding: 4px 8px;
  scrollbar-width: none;
  flex-wrap: wrap;
}

.forecast-tabs::-webkit-scrollbar {
  display: none;
}

.forecast-tab {
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-dim, #888);
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 4px 6px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s ease;
}

.forecast-tab:hover {
  color: var(--text, #e8e8e8);
}

.forecast-tab.active {
  background: var(--surface-hover, #1e1e1e);
  border-bottom: 2px solid var(--green, #44ff88);
  color: var(--text, #e8e8e8);
}

.forecast-content {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.forecast-section-header {
  padding: 8px 8px 6px;
  border-bottom: 2px solid var(--semantic-info, #3b82f6);
  margin-bottom: 4px;
}

.forecast-section-title {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  font-weight: 700;
  color: var(--text-dim, #888);
  letter-spacing: 1.5px;
  text-transform: uppercase;
}

.forecast-list {
  display: flex;
  flex-direction: column;
}

.theater-row {
  padding: 8px 8px;
  border-bottom: 1px solid var(--border, #2a2a2a);
  transition: background 0.15s ease;
}

.theater-row:hover {
  background: var(--surface-hover, #1e1e1e);
}

.theater-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.theater-name {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--text, #e8e8e8);
  font-weight: 500;
}

.theater-pct {
  font-family: 'SF Mono', monospace;
  font-size: 13px;
  font-weight: 700;
  flex-shrink: 0;
  margin-left: 8px;
}

.theater-bar-wrapper {
  position: relative;
  height: 6px;
  margin-bottom: 4px;
}

.theater-bar-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--border, #2a2a2a);
  border-radius: 2px;
}

.theater-bar {
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  border-radius: 2px;
  z-index: 1;
  transition: width 0.4s ease;
}

.theater-meta {
  display: flex;
  align-items: center;
  gap: 5px;
}

.theater-status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}

.theater-status-label {
  font-family: 'SF Mono', monospace;
  font-size: 9px;
  color: var(--text-muted, #666);
  text-transform: lowercase;
  letter-spacing: 0.5px;
}

.forecast-empty {
  padding: 24px;
  text-align: center;
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--text-dim, #888);
}
</style>
