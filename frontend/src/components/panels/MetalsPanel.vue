<template>
  <BasePanel
    panelId="metals"
    title="METALS & MATERIALS"
    infoTooltip="Commodity prices for precious and industrial metals. No free real-time API available."
    dataBadge="DEMO"
    @close="$emit('close')"
  >
    <div class="metals-body">
      <div class="metals-grid">
        <div
          v-for="metal in METALS"
          :key="metal.name"
          class="metal-card"
        >
          <span class="metal-name">{{ metal.name }}</span>
          <span class="metal-sparkline" v-html="generateSparkline(metal.change, metal.name)"></span>
          <span class="metal-price">{{ formatPrice(metal.price) }}</span>
          <span
            class="metal-change"
            :class="metal.change >= 0 ? 'positive' : 'negative'"
          >{{ formatChange(metal.change) }}</span>
        </div>
      </div>
    </div>
  </BasePanel>
</template>

<script setup>
import { ref } from 'vue'
import BasePanel from '../BasePanel.vue'

const emit = defineEmits(['close'])

const METALS = [
  { name: 'GOLD', price: 2432, change: -2.65 },
  { name: 'SILVER', price: 30.62, change: -5.54 },
  { name: 'COPPER', price: 4.51, change: -0.90 },
  { name: 'PLATINUM', price: 1854, change: 1.2 },
  { name: 'PALLADIUM', price: 1378, change: -3.1 },
  { name: 'ALUMINUM', price: 2672, change: 0.8 },
]

function formatPrice(price) {
  return '$' + price.toLocaleString('en-US', {
    minimumFractionDigits: price >= 1000 ? 0 : 2,
    maximumFractionDigits: 2
  })
}

function formatChange(change) {
  const sign = change >= 0 ? '+' : ''
  return sign + change.toFixed(2) + '%'
}

function generateSparkline(change, seed) {
  const color = change >= 0 ? '#44ff88' : '#ff4444'
  const w = 80
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
.metals-body {
  padding: 8px 12px;
  font-family: 'SF Mono', monospace;
  font-size: 12px;
}

.metals-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.metal-card {
  background: var(--wm-surface-hover, #1e1e1e);
  border: 1px solid var(--wm-border, #2a2a2a);
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metal-name {
  font-size: 10px;
  font-weight: 600;
  color: var(--wm-text-dim, #888);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.metal-sparkline {
  display: flex;
  align-items: center;
}

.metal-price {
  font-size: 20px;
  font-weight: 700;
  color: var(--wm-text, #e8e8e8);
  font-family: 'SF Mono', monospace;
  font-variant-numeric: tabular-nums;
}

.metal-change {
  font-size: 12px;
  font-weight: 600;
  font-family: 'SF Mono', monospace;
  font-variant-numeric: tabular-nums;
}

.metal-change.positive {
  color: #44ff88;
}

.metal-change.negative {
  color: #ff4444;
}

@media (max-width: 600px) {
  .metals-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
