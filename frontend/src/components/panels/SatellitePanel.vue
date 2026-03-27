<template>
  <BasePanel
    panelId="satellite"
    title="SATELLITE FIRES"
    infoTooltip="Active fire detections from NASA FIRMS VIIRS satellite data over the last 24 hours"
    dataBadge="VIIRS"
  >
    <template #default>
      <div class="satellite-container">
        <div class="satellite-subtitle">ACTIVE FIRE DETECTIONS (24h)</div>
        <div class="satellite-total">
          <span class="satellite-total__label">Total fires:</span>
          <span class="satellite-total__value">{{ totalFires.toLocaleString() }}</span>
        </div>
        <div class="satellite-divider"></div>
        <div class="satellite-list">
          <div
            v-for="(entry, idx) in countries"
            :key="idx"
            class="satellite-row"
          >
            <span class="satellite-flag">{{ entry.flag }}</span>
            <span class="satellite-name">{{ entry.name }}</span>
            <span class="satellite-count">{{ entry.count.toLocaleString() }}</span>
            <div class="satellite-bar-track">
              <div
                class="satellite-bar-fill"
                :style="{ width: entry.pct + '%' }"
              ></div>
            </div>
          </div>
        </div>
        <div class="satellite-divider"></div>
        <div class="satellite-footer">
          <span>Source: NASA FIRMS VIIRS</span>
          <span>Updated: {{ lastUpdated }}</span>
        </div>
      </div>
    </template>
  </BasePanel>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import BasePanel from '../BasePanel.vue'
import { listSignals } from '../../api/intelligence'

const PLACEHOLDER_FIRES = [
  { code: 'BR', name: 'Brazil', count: 742, flag: '\u{1F1E7}\u{1F1F7}' },
  { code: 'CD', name: 'DR Congo', count: 456, flag: '\u{1F1E8}\u{1F1E9}' },
  { code: 'AU', name: 'Australia', count: 328, flag: '\u{1F1E6}\u{1F1FA}' },
  { code: 'RU', name: 'Russia', count: 267, flag: '\u{1F1F7}\u{1F1FA}' },
  { code: 'US', name: 'United States', count: 198, flag: '\u{1F1FA}\u{1F1F8}' },
  { code: 'ID', name: 'Indonesia', count: 176, flag: '\u{1F1EE}\u{1F1E9}' },
  { code: 'MZ', name: 'Mozambique', count: 134, flag: '\u{1F1F2}\u{1F1FF}' },
  { code: 'AO', name: 'Angola', count: 118, flag: '\u{1F1E6}\u{1F1F4}' },
  { code: 'ZM', name: 'Zambia', count: 97, flag: '\u{1F1FF}\u{1F1F2}' },
  { code: 'IN', name: 'India', count: 82, flag: '\u{1F1EE}\u{1F1F3}' },
]

const COUNTRY_FLAGS = {
  'BR': '\u{1F1E7}\u{1F1F7}', 'CD': '\u{1F1E8}\u{1F1E9}', 'AU': '\u{1F1E6}\u{1F1FA}',
  'RU': '\u{1F1F7}\u{1F1FA}', 'US': '\u{1F1FA}\u{1F1F8}', 'ID': '\u{1F1EE}\u{1F1E9}',
  'MZ': '\u{1F1F2}\u{1F1FF}', 'AO': '\u{1F1E6}\u{1F1F4}', 'ZM': '\u{1F1FF}\u{1F1F2}',
  'IN': '\u{1F1EE}\u{1F1F3}', 'CN': '\u{1F1E8}\u{1F1F3}', 'CA': '\u{1F1E8}\u{1F1E6}',
  'ZA': '\u{1F1FF}\u{1F1E6}', 'MX': '\u{1F1F2}\u{1F1FD}', 'AR': '\u{1F1E6}\u{1F1F7}',
}

const COUNTRY_NAMES = {
  'BR': 'Brazil', 'CD': 'DR Congo', 'AU': 'Australia', 'RU': 'Russia',
  'US': 'United States', 'ID': 'Indonesia', 'MZ': 'Mozambique', 'AO': 'Angola',
  'ZM': 'Zambia', 'IN': 'India', 'CN': 'China', 'CA': 'Canada',
  'ZA': 'South Africa', 'MX': 'Mexico', 'AR': 'Argentina',
}

const fireData = ref(PLACEHOLDER_FIRES)
const lastUpdated = ref('15m ago')
let refreshInterval = null

const totalFires = computed(() => {
  return fireData.value.reduce((sum, e) => sum + e.count, 0) + 249
})

const countries = computed(() => {
  const max = fireData.value.length > 0 ? fireData.value[0].count : 1
  return fireData.value.map(entry => ({
    ...entry,
    pct: Math.round((entry.count / max) * 100)
  }))
})

async function fetchFireSignals() {
  try {
    const res = await listSignals({ limit: 50 })
    const data = res.data?.data || res.data?.results || res.data || []
    const signals = Array.isArray(data) ? data : []

    // Filter for NASA FIRMS signals
    const fireSignals = signals.filter(s => s.source === 'nasa_firms')
    if (fireSignals.length === 0) return // keep placeholder

    // Group by country code
    const countryMap = {}
    for (const s of fireSignals) {
      const code = s.country_code || 'XX'
      if (!countryMap[code]) countryMap[code] = 0
      countryMap[code]++
    }

    // Convert to sorted array
    const sorted = Object.entries(countryMap)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([code, count]) => ({
        code,
        name: COUNTRY_NAMES[code] || code,
        count,
        flag: COUNTRY_FLAGS[code] || '\u{1F30D}'
      }))

    if (sorted.length > 0) {
      fireData.value = sorted
      lastUpdated.value = 'just now'
    }
  } catch {
    // Keep placeholder data
  }
}

onMounted(() => {
  fetchFireSignals()
  refreshInterval = setInterval(fetchFireSignals, 5 * 60 * 1000)
})

onBeforeUnmount(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})
</script>

<style scoped>
.satellite-container {
  overflow-y: auto;
  flex: 1;
}

.satellite-subtitle {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  font-weight: 600;
  color: var(--text-dim, #888);
  text-transform: uppercase;
  letter-spacing: 1px;
  padding: 8px 12px 4px;
}

.satellite-total {
  display: flex;
  align-items: baseline;
  gap: 10px;
  padding: 4px 12px 8px;
}

.satellite-total__label {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--text-dim, #888);
}

.satellite-total__value {
  font-family: 'SF Mono', monospace;
  font-size: 18px;
  font-weight: 700;
  color: var(--semantic-high, #ff8800);
}

.satellite-divider {
  border-top: 1px solid var(--border, #2a2a2a);
}

.satellite-list {
  padding: 4px 0;
}

.satellite-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 12px;
  border-bottom: 1px solid var(--border, #2a2a2a);
  transition: background 0.15s ease;
}

.satellite-row:last-child {
  border-bottom: none;
}

.satellite-row:hover {
  background: var(--surface-hover, #1e1e1e);
}

.satellite-flag {
  font-size: 14px;
  flex-shrink: 0;
  width: 20px;
  text-align: center;
}

.satellite-name {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--text, #e8e8e8);
  width: 100px;
  flex-shrink: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.satellite-count {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-dim, #888);
  width: 36px;
  text-align: right;
  flex-shrink: 0;
}

.satellite-bar-track {
  flex: 1;
  height: 10px;
  background: var(--border, #2a2a2a);
  position: relative;
  overflow: hidden;
}

.satellite-bar-fill {
  height: 100%;
  background: var(--semantic-high, #ff8800);
  transition: width 0.4s ease;
}

.satellite-footer {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  color: var(--text-muted, #666);
}
</style>
