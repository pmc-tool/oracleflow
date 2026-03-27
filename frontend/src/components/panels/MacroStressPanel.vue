<template>
  <BasePanel
    panelId="macro-stress"
    title="MACRO STRESS"
    infoTooltip="Economic stress indicators including yields, volatility, inflation, and central bank rates."
    @close="$emit('close')"
  >
    <template #tabs>
      <div class="macro-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="macro-tab"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >{{ tab.label }}</button>
      </div>
    </template>

    <div class="macro-body">
      <!-- Indicators Tab -->
      <div v-if="activeTab === 'indicators'">
        <div class="macro-section-header">STRESS INDICATORS</div>
        <div
          v-for="item in INDICATORS"
          :key="item.name"
          class="macro-row"
        >
          <span class="macro-label">{{ item.name }}</span>
          <span class="macro-value">{{ item.value }}</span>
          <span
            class="macro-trend"
            :class="getTrendClass(item)"
          >{{ getTrendArrow(item.delta) }} {{ formatDelta(item.delta) }}</span>
        </div>
      </div>

      <!-- Gov Tab -->
      <div v-if="activeTab === 'gov'">
        <div class="macro-section-header">GOVERNMENT POLICY</div>
        <div
          v-for="item in GOV_DATA"
          :key="item.name"
          class="macro-row"
        >
          <span class="macro-label">{{ item.name }}</span>
          <span class="macro-value">{{ item.value }}</span>
          <span
            class="macro-trend"
            :class="item.delta >= 0 ? 'trend-up' : 'trend-down'"
          >{{ getTrendArrow(item.delta) }} {{ formatDelta(item.delta) }}</span>
        </div>
      </div>

      <!-- Central Banks Tab -->
      <div v-if="activeTab === 'banks'">
        <div class="macro-section-header">CENTRAL BANK RATES</div>
        <div
          v-for="item in BANK_DATA"
          :key="item.name"
          class="macro-row"
        >
          <span class="macro-label">{{ item.name }}</span>
          <span class="macro-value">{{ item.value }}</span>
          <span
            class="macro-trend"
            :class="item.delta === 0 ? 'trend-neutral' : (item.delta > 0 ? 'trend-up' : 'trend-down')"
          >{{ getTrendArrow(item.delta) }} {{ formatDelta(item.delta) }}</span>
        </div>
      </div>
    </div>
  </BasePanel>
</template>

<script setup>
import { ref } from 'vue'
import BasePanel from '../BasePanel.vue'

const emit = defineEmits(['close'])

const activeTab = ref('indicators')

const tabs = [
  { key: 'indicators', label: 'Indicators' },
  { key: 'gov', label: 'Gov' },
  { key: 'banks', label: 'Central Banks' },
]

const INDICATORS = [
  { name: 'US 10Y Yield', value: '4.28%', delta: 0.05, type: 'yield' },
  { name: 'VIX (Fear Index)', value: '18.2', delta: -2.1, type: 'vix', vixValue: 18.2 },
  { name: 'USD Index (DXY)', value: '104.3', delta: 0.4, type: 'neutral' },
  { name: 'US CPI (YoY)', value: '3.1%', delta: -0.2, type: 'inflation' },
  { name: 'Fed Funds Rate', value: '5.25%', delta: 0.0, type: 'rate' },
  { name: 'EU Inflation', value: '2.4%', delta: -0.3, type: 'inflation' },
  { name: 'China GDP (YoY)', value: '5.2%', delta: 0.1, type: 'gdp' },
  { name: 'Japan 10Y Yield', value: '0.85%', delta: 0.02, type: 'yield' },
]

const GOV_DATA = [
  { name: 'US Debt/GDP', value: '123.4%', delta: 1.2 },
  { name: 'US Budget Deficit', value: '-$1.7T', delta: -0.3 },
  { name: 'EU Debt/GDP', value: '88.6%', delta: -0.5 },
  { name: 'China Debt/GDP', value: '77.1%', delta: 2.1 },
  { name: 'Japan Debt/GDP', value: '263%', delta: 0.8 },
]

const BANK_DATA = [
  { name: 'Federal Reserve', value: '5.25-5.50%', delta: 0.0 },
  { name: 'ECB (Main Refi)', value: '4.50%', delta: -0.25 },
  { name: 'Bank of England', value: '5.25%', delta: 0.0 },
  { name: 'Bank of Japan', value: '0.10%', delta: 0.10 },
  { name: 'PBoC (1Y LPR)', value: '3.45%', delta: -0.10 },
]

function getTrendArrow(delta) {
  if (delta === 0) return '\u2192'
  return delta > 0 ? '\u25B2' : '\u25BC'
}

function formatDelta(delta) {
  if (delta === 0) return '0.0'
  const sign = delta > 0 ? '+' : ''
  return sign + delta.toFixed(2)
}

function getTrendClass(item) {
  if (item.type === 'vix') {
    if (item.vixValue > 20) return 'trend-critical'
    if (item.vixValue > 15) return 'trend-warning'
    return 'trend-normal'
  }
  if (item.type === 'gdp') {
    return item.delta >= 0 ? 'trend-normal' : 'trend-critical'
  }
  if (item.type === 'yield' || item.type === 'inflation') {
    return item.delta > 0 ? 'trend-critical' : (item.delta < 0 ? 'trend-normal' : 'trend-neutral')
  }
  if (item.delta === 0) return 'trend-neutral'
  return item.delta > 0 ? 'trend-up' : 'trend-down'
}
</script>

<style scoped>
.macro-tabs {
  display: flex;
  gap: 0;
  padding: 0 12px;
  border-bottom: 1px solid var(--wm-border, #2a2a2a);
}

.macro-tab {
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

.macro-tab:hover {
  color: var(--wm-text, #e8e8e8);
}

.macro-tab.active {
  color: var(--wm-text, #e8e8e8);
  border-bottom-color: var(--wm-text, #e8e8e8);
}

.macro-body {
  padding: 8px 12px;
  font-family: 'SF Mono', monospace;
  font-size: 12px;
}

.macro-section-header {
  font-size: 10px;
  font-weight: 600;
  color: var(--wm-text-dim, #888);
  text-transform: uppercase;
  letter-spacing: 1px;
  padding-bottom: 8px;
  margin-bottom: 4px;
  border-bottom: 1px solid var(--wm-border, #2a2a2a);
}

.macro-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 0;
  border-bottom: 1px solid var(--wm-border, #2a2a2a);
}

.macro-row:last-child {
  border-bottom: none;
}

.macro-label {
  flex: 1;
  color: var(--wm-text, #e8e8e8);
  font-size: 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.macro-value {
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  color: var(--wm-text, #e8e8e8);
  width: 80px;
  text-align: right;
  flex-shrink: 0;
}

.macro-trend {
  font-variant-numeric: tabular-nums;
  font-size: 11px;
  font-weight: 600;
  width: 70px;
  text-align: right;
  flex-shrink: 0;
}

.macro-trend.trend-critical {
  color: #ff4444;
}

.macro-trend.trend-warning {
  color: #ffaa00;
}

.macro-trend.trend-normal {
  color: #44aa44;
}

.macro-trend.trend-neutral {
  color: var(--wm-text-muted, #666);
}

.macro-trend.trend-up {
  color: #44ff88;
}

.macro-trend.trend-down {
  color: #ff4444;
}
</style>
