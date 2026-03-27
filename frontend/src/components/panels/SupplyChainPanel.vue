<template>
  <BasePanel panelId="supply-chain" title="SUPPLY CHAIN">
    <template #default>
      <div class="sc-container">
        <div class="sc-section__title">CHOKEPOINT STATUS</div>

        <div
          v-for="(cp, idx) in chokepoints"
          :key="idx"
          class="sc-chokepoint"
        >
          <div class="sc-chokepoint__header">
            <span class="sc-chokepoint__name">{{ cp.name }}</span>
            <span class="sc-chokepoint__status" :style="{ color: statusColor(cp.status) }">
              &#x25CF; {{ cp.status }}
            </span>
          </div>
          <div class="sc-chokepoint__detail">
            {{ cp.detail }}
          </div>
        </div>

        <div class="sc-divider"></div>
        <div class="sc-section__title">SHIPPING INDEX</div>

        <div
          v-for="(idx_item, idx) in shippingIndices"
          :key="idx"
          class="sc-index"
        >
          <span class="sc-index__name">{{ idx_item.name }}</span>
          <span class="sc-index__value">{{ idx_item.value }}</span>
          <span
            class="sc-index__change"
            :class="idx_item.positive ? 'change-positive' : 'change-negative'"
          >{{ idx_item.change }}</span>
        </div>
      </div>
    </template>
  </BasePanel>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import BasePanel from '../BasePanel.vue'
import { listSignals } from '../../api/intelligence'

const CHOKEPOINT_KEYWORDS = [
  { name: 'Strait of Hormuz', keywords: ['hormuz', 'persian gulf'] },
  { name: 'Suez Canal', keywords: ['suez'] },
  { name: 'Bab el-Mandeb', keywords: ['bab el-mandeb', 'bab al-mandab', 'red sea', 'houthi'] },
  { name: 'Panama Canal', keywords: ['panama canal'] },
  { name: 'Strait of Malacca', keywords: ['malacca'] },
  { name: 'Taiwan Strait', keywords: ['taiwan strait', 'taiwan blockade'] },
]

const chokepoints = ref([])
const shippingIndices = ref([
  { name: 'Baltic Dry Index', value: '--', change: '--', positive: true },
  { name: 'Container Freight', value: '--', change: '--', positive: false },
])

function statusFromCount(count, maxAnomaly) {
  if (count >= 10 || maxAnomaly >= 0.8) return 'CRITICAL'
  if (count >= 5 || maxAnomaly >= 0.5) return 'ELEVATED'
  if (count >= 1) return 'MONITORING'
  return 'NORMAL'
}

onMounted(async () => {
  try {
    const res = await listSignals({ limit: 200, categories: 'supply_chain,geopolitical' })
    const signals = res.data || res
    const allSignals = Array.isArray(signals) ? signals : (signals.data || signals.items || [])

    chokepoints.value = CHOKEPOINT_KEYWORDS.map(cp => {
      const matching = allSignals.filter(s => {
        const text = ((s.title || '') + ' ' + (s.summary || '')).toLowerCase()
        return cp.keywords.some(kw => text.includes(kw))
      })
      const maxAnomaly = matching.length > 0 ? Math.max(...matching.map(s => s.anomaly_score || 0)) : 0
      const status = statusFromCount(matching.length, maxAnomaly)
      return {
        name: cp.name,
        status,
        detail: `${matching.length} signal${matching.length !== 1 ? 's' : ''} | Max anomaly: ${(maxAnomaly * 100).toFixed(0)}%`,
      }
    })
  } catch {
    // Fallback to static
    chokepoints.value = CHOKEPOINT_KEYWORDS.map(cp => ({
      name: cp.name, status: 'UNKNOWN', detail: 'Data unavailable'
    }))
  }
})

function statusColor(status) {
  if (status === 'CRITICAL') return '#ff4444'
  if (status === 'ELEVATED') return '#ffaa00'
  return '#44aa44'
}
</script>

<style scoped>
.sc-container {
  overflow-y: auto;
  flex: 1;
}

.sc-section__title {
  padding: 8px 12px;
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  font-weight: 700;
  color: var(--wm-text-dim, #888);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--wm-border, #2a2a2a);
}

.sc-chokepoint {
  padding: 8px 12px;
  border-bottom: 1px solid var(--wm-border, #2a2a2a);
  transition: background 0.15s ease;
}

.sc-chokepoint:hover {
  background: var(--wm-surface-hover, #1e1e1e);
}

.sc-chokepoint__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.sc-chokepoint__name {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  font-weight: 600;
  color: var(--wm-text, #e8e8e8);
}

.sc-chokepoint__status {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.sc-chokepoint__detail {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--wm-text-dim, #888);
  padding-left: 2px;
}

.sc-divider {
  height: 1px;
  background: var(--wm-border, #2a2a2a);
}

.sc-index {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 12px;
  border-bottom: 1px solid var(--wm-border, #2a2a2a);
  transition: background 0.15s ease;
}

.sc-index:hover {
  background: var(--wm-surface-hover, #1e1e1e);
}

.sc-index__name {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--wm-text-dim, #888);
  flex: 1;
}

.sc-index__value {
  font-family: 'SF Mono', monospace;
  font-size: 12px;
  font-weight: 700;
  color: var(--wm-text, #e8e8e8);
  min-width: 48px;
  text-align: right;
}

.sc-index__change {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  font-weight: 600;
  min-width: 48px;
  text-align: right;
}

.change-positive {
  color: #44ff88;
}

.change-negative {
  color: #ff4444;
}
</style>
