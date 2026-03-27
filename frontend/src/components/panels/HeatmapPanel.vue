<template>
  <BasePanel
    panelId="heatmap"
    title="SIGNAL HEATMAP"
    infoTooltip="Signal density by country over the last 24 hours"
    :showCount="true"
    :count="totalSignals"
  >
    <template #default>
      <div class="heatmap-container">
        <div class="heatmap-subtitle">SIGNAL DENSITY (24h)</div>
        <div class="heatmap-list">
          <div
            v-for="(entry, idx) in topCountries"
            :key="idx"
            class="heatmap-row"
          >
            <span class="heatmap-flag">{{ entry.flag }}</span>
            <span class="heatmap-code">{{ entry.code }}</span>
            <div class="heatmap-bar-track">
              <div
                class="heatmap-bar-fill"
                :style="{ width: entry.pct + '%', background: barColor(entry.pct) }"
              ></div>
            </div>
            <span class="heatmap-count">{{ entry.count }}</span>
          </div>
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
let refreshInterval = null

const flagMap = {
  US: '\u{1F1FA}\u{1F1F8}', JM: '\u{1F1EF}\u{1F1F2}', GB: '\u{1F1EC}\u{1F1E7}',
  UA: '\u{1F1FA}\u{1F1E6}', IR: '\u{1F1EE}\u{1F1F7}', RU: '\u{1F1F7}\u{1F1FA}',
  TT: '\u{1F1F9}\u{1F1F9}', BB: '\u{1F1E7}\u{1F1E7}', IN: '\u{1F1EE}\u{1F1F3}',
  BR: '\u{1F1E7}\u{1F1F7}', CN: '\u{1F1E8}\u{1F1F3}', DE: '\u{1F1E9}\u{1F1EA}',
  FR: '\u{1F1EB}\u{1F1F7}', IL: '\u{1F1EE}\u{1F1F1}', KR: '\u{1F1F0}\u{1F1F7}',
  AU: '\u{1F1E6}\u{1F1FA}', JP: '\u{1F1EF}\u{1F1F5}', CD: '\u{1F1E8}\u{1F1E9}',
  ID: '\u{1F1EE}\u{1F1E9}', MZ: '\u{1F1F2}\u{1F1FF}'
}

const placeholderData = [
  { code: 'US', count: 124 },
  { code: 'JM', count: 85 },
  { code: 'GB', count: 63 },
  { code: 'UA', count: 58 },
  { code: 'IR', count: 45 },
  { code: 'RU', count: 38 },
  { code: 'TT', count: 32 },
  { code: 'BB', count: 24 },
  { code: 'IN', count: 18 },
  { code: 'BR', count: 15 },
]

const countryCounts = computed(() => {
  if (signals.value.length === 0) return placeholderData
  const counts = {}
  for (const s of signals.value) {
    const cc = s.country_code || s.country || ''
    if (cc) {
      counts[cc] = (counts[cc] || 0) + 1
    }
  }
  return Object.entries(counts)
    .map(([code, count]) => ({ code, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 10)
})

const topCountries = computed(() => {
  const data = countryCounts.value
  const max = data.length > 0 ? data[0].count : 1
  return data.map(entry => ({
    ...entry,
    flag: flagMap[entry.code] || '\u{1F3F3}\u{FE0F}',
    pct: Math.round((entry.count / max) * 100)
  }))
})

const totalSignals = computed(() => {
  return countryCounts.value.reduce((sum, e) => sum + e.count, 0)
})

function barColor(pct) {
  if (pct >= 70) return '#ff4444'
  if (pct >= 40) return '#ffaa00'
  return '#3388ff'
}

async function fetchSignals() {
  try {
    const res = await listSignals({ limit: 200 })
    const data = res.data?.data || res.data?.results || res.data || []
    signals.value = Array.isArray(data) ? data : []
  } catch {
    // use placeholder
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
.heatmap-container {
  overflow-y: auto;
  flex: 1;
}

.heatmap-subtitle {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  font-weight: 600;
  color: var(--text-dim, #888);
  text-transform: uppercase;
  letter-spacing: 1px;
  padding: 8px 12px 6px;
}

.heatmap-list {
  padding: 0;
}

.heatmap-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 12px;
  border-bottom: 1px solid var(--border, #2a2a2a);
  transition: background 0.15s ease;
}

.heatmap-row:hover {
  background: var(--surface-hover, #1e1e1e);
}

.heatmap-flag {
  font-size: 14px;
  flex-shrink: 0;
  width: 20px;
  text-align: center;
}

.heatmap-code {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  font-weight: 600;
  color: var(--text, #e8e8e8);
  width: 24px;
  flex-shrink: 0;
}

.heatmap-bar-track {
  flex: 1;
  height: 10px;
  background: var(--border, #2a2a2a);
  position: relative;
  overflow: hidden;
}

.heatmap-bar-fill {
  height: 100%;
  transition: width 0.4s ease;
}

.heatmap-count {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-dim, #888);
  width: 36px;
  text-align: right;
  flex-shrink: 0;
}
</style>
