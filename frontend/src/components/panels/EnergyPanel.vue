<template>
  <BasePanel
    panelId="energy"
    title="ENERGY COMPLEX"
    infoTooltip="Energy commodity prices including crude oil, natural gas, and refined products. No free real-time API available."
    dataBadge="DEMO"
    @close="$emit('close')"
  >
    <div class="energy-body">
      <div class="energy-sub-header">LIVE TAPE</div>
      <div class="energy-grid">
        <div
          v-for="item in ENERGY"
          :key="item.name"
          class="energy-card"
        >
          <span class="energy-name">{{ item.name }}</span>
          <span class="energy-sparkline" v-html="generateSparkline(item.change, item.name)"></span>
          <span class="energy-price">{{ formatPrice(item.price) }}</span>
          <span
            class="energy-change"
            :class="item.change >= 0 ? 'positive' : 'negative'"
          >{{ formatChange(item.change) }}</span>
        </div>
      </div>
    </div>
  </BasePanel>
</template>

<script setup>
import { ref } from 'vue'
import BasePanel from '../BasePanel.vue'

const emit = defineEmits(['close'])

const ENERGY = [
  { name: 'OIL (WTI)', price: 68.92, change: 3.99 },
  { name: 'BRENT', price: 72.36, change: 4.22 },
  { name: 'NATURAL GAS', price: 3.42, change: -1.5 },
  { name: 'GASOLINE', price: 2.18, change: 0.8 },
  { name: 'HEATING OIL', price: 2.34, change: -0.6 },
  { name: 'URANIUM', price: 82.50, change: 2.1 },
]

function formatPrice(price) {
  return '$' + price.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  })
}

function formatChange(change) {
  const sign = change >= 0 ? '+' : ''
  return sign + change.toFixed(2) + '%'
}

function generateSparkline(change, seed) {
  const color = change >= 0 ? '#44ff88' : '#ff4444'
  const w = 100
  const h = 40
  const points = []
  const seedNum = seed.charCodeAt(0) * 7 + seed.charCodeAt(1) * 13
  for (let i = 0; i < 8; i++) {
    const x = (i / 7) * w
    const trend = change >= 0 ? (i / 7) * h * 0.4 : -(i / 7) * h * 0.4
    const noise = ((seedNum * (i + 1) * 17) % 20) / 20
    const y = h / 2 - trend + (noise - 0.5) * h * 0.3
    const clampedY = Math.max(2, Math.min(h - 2, y))
    points.push(`${x.toFixed(1)},${clampedY.toFixed(1)}`)
  }
  const pathD = 'M' + points.join(' L')
  return `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" style="display:block;"><path d="${pathD}" fill="none" stroke="${color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" opacity="0.8"/></svg>`
}
</script>

<style scoped>
.energy-body {
  padding: 8px 12px;
  font-family: 'SF Mono', monospace;
  font-size: 12px;
}

.energy-sub-header {
  font-size: 10px;
  font-weight: 600;
  color: var(--wm-text-dim, #888);
  text-transform: uppercase;
  letter-spacing: 1px;
  padding-bottom: 8px;
  margin-bottom: 8px;
  border-bottom: 1px solid var(--wm-border, #2a2a2a);
}

.energy-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.energy-card {
  background: var(--wm-surface-hover, #1e1e1e);
  border: 1px solid var(--wm-border, #2a2a2a);
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.energy-name {
  font-size: 10px;
  font-weight: 600;
  color: var(--wm-text-dim, #888);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.energy-sparkline {
  display: flex;
  align-items: center;
}

.energy-price {
  font-size: 20px;
  font-weight: 700;
  color: var(--wm-text, #e8e8e8);
  font-family: 'SF Mono', monospace;
  font-variant-numeric: tabular-nums;
}

.energy-change {
  font-size: 12px;
  font-weight: 600;
  font-family: 'SF Mono', monospace;
  font-variant-numeric: tabular-nums;
}

.energy-change.positive {
  color: #44ff88;
}

.energy-change.negative {
  color: #ff4444;
}

@media (max-width: 600px) {
  .energy-grid {
    grid-template-columns: 1fr;
  }
}
</style>
