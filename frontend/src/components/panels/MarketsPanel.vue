<template>
  <BasePanel
    panelId="markets"
    title="MARKETS"
    infoTooltip="Live market data for stocks, crypto, and commodities. Data may be delayed."
    @close="$emit('close')"
  >
    <template #tabs>
      <div class="market-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="market-tab"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >{{ tab.label }}</button>
      </div>
    </template>

    <div class="markets-body">
      <div
        v-for="item in activeData"
        :key="item.symbol"
        class="market-row"
      >
        <span class="market-symbol">{{ item.symbol }}</span>
        <span class="market-price">{{ formatPrice(item.price) }}</span>
        <span
          class="market-change"
          :class="item.change >= 0 ? 'positive' : 'negative'"
        >{{ formatChange(item.change) }}</span>
        <span
          class="market-arrow"
          :class="item.change >= 0 ? 'positive' : 'negative'"
        >{{ item.change >= 0 ? '\u25B2' : '\u25BC' }}</span>
        <span class="market-sparkline" v-html="generateSparkline(item.change)"></span>
      </div>
    </div>
  </BasePanel>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import BasePanel from '../BasePanel.vue'
import { getQuotes } from '../../api/intelligence'

const emit = defineEmits(['close'])

const activeTab = ref('stocks')
let refreshInterval = null

const tabs = [
  { key: 'stocks', label: 'Stocks' },
  { key: 'crypto', label: 'Crypto' },
  { key: 'commodities', label: 'Commodities' }
]

const PLACEHOLDER_STOCKS = [
  { symbol: 'AAPL', price: 178.23, change: 1.2 },
  { symbol: 'TSLA', price: 242.50, change: -0.8 },
  { symbol: 'MSFT', price: 412.10, change: 0.3 },
  { symbol: 'AMZN', price: 185.67, change: 0.5 },
  { symbol: 'GOOGL', price: 155.89, change: -0.2 },
  { symbol: 'NVDA', price: 875.30, change: 3.1 },
]

const PLACEHOLDER_CRYPTO = [
  { symbol: 'BTC', price: 67234, change: 2.3 },
  { symbol: 'ETH', price: 3456, change: -0.5 },
  { symbol: 'SOL', price: 142.30, change: 4.1 },
  { symbol: 'BNB', price: 598.40, change: 0.7 },
]

const PLACEHOLDER_COMMODITIES = [
  { symbol: 'GOLD', price: 2234.50, change: 0.4 },
  { symbol: 'OIL', price: 78.23, change: -1.2 },
  { symbol: 'SILVER', price: 28.45, change: 1.1 },
]

const liveStocks = ref([])
const liveCrypto = ref([])

const dataMap = computed(() => ({
  stocks: liveStocks.value.length > 0 ? liveStocks.value : PLACEHOLDER_STOCKS,
  crypto: liveCrypto.value.length > 0 ? liveCrypto.value : PLACEHOLDER_CRYPTO,
  commodities: PLACEHOLDER_COMMODITIES
}))

const activeData = computed(() => dataMap.value[activeTab.value] || [])

async function fetchQuotes() {
  try {
    const res = await getQuotes()
    const data = res.data?.data || res.data || {}
    if (Array.isArray(data.stocks) && data.stocks.length > 0) {
      liveStocks.value = data.stocks
    }
    if (Array.isArray(data.crypto) && data.crypto.length > 0) {
      liveCrypto.value = data.crypto
    }
  } catch {
    // Fall back to placeholder data
  }
}

onMounted(() => {
  fetchQuotes()
  refreshInterval = setInterval(fetchQuotes, 5 * 60 * 1000)
})

onBeforeUnmount(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})

function formatPrice(price) {
  return '$' + price.toLocaleString('en-US', {
    minimumFractionDigits: price >= 1000 ? 0 : 2,
    maximumFractionDigits: 2
  })
}

function formatChange(change) {
  const sign = change >= 0 ? '+' : ''
  return sign + change.toFixed(1) + '%'
}

function generateSparkline(change) {
  const color = change >= 0 ? '#44ff88' : '#ff4444'
  // Generate a simple 5-point sparkline using a seeded pseudo-random approach
  const seed = Math.abs(change * 1000) % 100
  const points = []
  const w = 40
  const h = 14
  for (let i = 0; i < 5; i++) {
    const x = (i / 4) * w
    // Create a slight upward or downward trend based on change direction
    const base = change >= 0 ? h * 0.6 : h * 0.4
    const variance = ((seed * (i + 1) * 7) % 10) / 10
    const y = base + (variance - 0.5) * h * 0.6 + (change >= 0 ? -i * 1.2 : i * 1.2)
    const clampedY = Math.max(1, Math.min(h - 1, y))
    points.push(`${x.toFixed(1)},${clampedY.toFixed(1)}`)
  }
  const pathD = 'M' + points.join(' L')
  return `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" style="display:block;"><path d="${pathD}" fill="none" stroke="${color}" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`
}
</script>

<style scoped>
.market-tabs {
  display: flex;
  gap: 0;
  padding: 0 12px;
  border-bottom: 1px solid var(--wm-border, #2a2a2a);
}
.market-tab {
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--wm-text-dim, #888);
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  font-weight: 600;
  padding: 6px 12px;
  cursor: pointer;
  letter-spacing: 0.5px;
  transition: color 0.15s, border-color 0.15s;
}
.market-tab:hover {
  color: var(--wm-text, #e8e8e8);
}
.market-tab.active {
  color: var(--wm-text, #e8e8e8);
  border-bottom-color: var(--wm-text, #e8e8e8);
}

.markets-body {
  padding: 8px 12px;
  font-family: 'SF Mono', monospace;
  font-size: 12px;
}

.market-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 0;
  border-bottom: 1px solid var(--wm-border, #2a2a2a);
}
.market-row:last-child {
  border-bottom: none;
}

.market-symbol {
  font-weight: 700;
  color: var(--wm-text, #e8e8e8);
  width: 56px;
  flex-shrink: 0;
  letter-spacing: 0.5px;
}

.market-price {
  color: var(--wm-text, #e8e8e8);
  font-variant-numeric: tabular-nums;
  width: 80px;
  text-align: right;
  flex-shrink: 0;
}

.market-change {
  font-variant-numeric: tabular-nums;
  width: 56px;
  text-align: right;
  flex-shrink: 0;
  font-weight: 600;
}
.market-change.positive {
  color: #44ff88;
}
.market-change.negative {
  color: #ff4444;
}

.market-arrow {
  font-size: 10px;
  width: 14px;
  text-align: center;
  flex-shrink: 0;
}
.market-arrow.positive {
  color: #44ff88;
}
.market-arrow.negative {
  color: #ff4444;
}

.market-sparkline {
  display: flex;
  align-items: center;
  margin-left: auto;
  flex-shrink: 0;
}
</style>
