<template>
  <BasePanel
    panelId="trade-policy"
    title="TRADE POLICY"
    infoTooltip="Active trade disputes, tariff rates, and non-tariff barriers between major economies."
    @close="$emit('close')"
  >
    <template #tabs>
      <div class="trade-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="trade-tab"
          :class="{ active: activeTab === tab.key }"
          @click="activeTab = tab.key"
        >{{ tab.label }}</button>
      </div>
    </template>

    <div class="trade-body">
      <!-- Overview Tab -->
      <div v-if="activeTab === 'overview'">
        <div class="trade-section-header">ACTIVE TRADE DISPUTES</div>
        <div
          v-for="dispute in DISPUTES"
          :key="dispute.id"
          class="trade-dispute"
        >
          <div class="dispute-header">
            <span class="dispute-flags">{{ dispute.flagA }} &#8596; {{ dispute.flagB }}</span>
            <span class="dispute-name">{{ dispute.name }}</span>
          </div>
          <div class="dispute-detail">
            <span class="dispute-label">Status:</span>
            <span
              class="dispute-status-badge"
              :class="'status-' + dispute.status.toLowerCase()"
            >{{ dispute.status }}</span>
          </div>
          <div class="dispute-detail">
            <span class="dispute-label">Tariff rate:</span>
            <span class="dispute-value">{{ dispute.tariffRate }}</span>
          </div>
          <div class="dispute-detail">
            <span class="dispute-label">Sectors:</span>
            <span class="dispute-value">{{ dispute.sectors }}</span>
          </div>
        </div>
      </div>

      <!-- Tariffs Tab -->
      <div v-if="activeTab === 'tariffs'">
        <div class="trade-section-header">TARIFF RATES BY PAIR</div>
        <div
          v-for="tariff in TARIFFS"
          :key="tariff.pair"
          class="trade-row"
        >
          <span class="trade-pair">{{ tariff.pair }}</span>
          <span class="trade-rate">{{ tariff.rate }}</span>
          <span
            class="trade-trend"
            :class="tariff.trend === 'up' ? 'trend-up' : (tariff.trend === 'down' ? 'trend-down' : 'trend-neutral')"
          >{{ tariff.trend === 'up' ? '\u25B2' : (tariff.trend === 'down' ? '\u25BC' : '\u2192') }}</span>
        </div>
      </div>

      <!-- Barriers Tab -->
      <div v-if="activeTab === 'barriers'">
        <div class="trade-section-header">NON-TARIFF BARRIERS</div>
        <div
          v-for="barrier in BARRIERS"
          :key="barrier.name"
          class="trade-barrier"
        >
          <div class="barrier-header">
            <span class="barrier-country">{{ barrier.country }}</span>
            <span
              class="barrier-severity"
              :class="'severity-' + barrier.severity"
            >{{ barrier.severity.toUpperCase() }}</span>
          </div>
          <div class="barrier-desc">{{ barrier.description }}</div>
          <div class="barrier-sectors">Sectors: {{ barrier.sectors }}</div>
        </div>
      </div>
    </div>
  </BasePanel>
</template>

<script setup>
import { ref } from 'vue'
import BasePanel from '../BasePanel.vue'

const emit = defineEmits(['close'])

const activeTab = ref('overview')

const tabs = [
  { key: 'overview', label: 'Overview' },
  { key: 'tariffs', label: 'Tariffs' },
  { key: 'barriers', label: 'Barriers' },
]

const DISPUTES = [
  {
    id: 1,
    flagA: '\uD83C\uDDFA\uD83C\uDDF8',
    flagB: '\uD83C\uDDE8\uD83C\uDDF3',
    name: 'US-China Tech War',
    status: 'ESCALATING',
    tariffRate: '25-100%',
    sectors: 'Semiconductors, AI, EVs',
  },
  {
    id: 2,
    flagA: '\uD83C\uDDEA\uD83C\uDDFA',
    flagB: '\uD83C\uDDE8\uD83C\uDDF3',
    name: 'EU-China EV Tariffs',
    status: 'ACTIVE',
    tariffRate: '45%',
    sectors: 'Electric vehicles',
  },
  {
    id: 3,
    flagA: '\uD83C\uDDFA\uD83C\uDDF8',
    flagB: '\uD83C\uDDEA\uD83C\uDDFA',
    name: 'Steel/Aluminum',
    status: 'MONITORING',
    tariffRate: '10-25%',
    sectors: 'Steel, Aluminum',
  },
]

const TARIFFS = [
  { pair: 'US \u2192 China', rate: '25-100%', trend: 'up' },
  { pair: 'China \u2192 US', rate: '15-125%', trend: 'up' },
  { pair: 'EU \u2192 China', rate: '45%', trend: 'up' },
  { pair: 'US \u2192 EU', rate: '10-25%', trend: 'neutral' },
  { pair: 'India \u2192 China', rate: '30-70%', trend: 'up' },
  { pair: 'US \u2192 Canada', rate: '0-25%', trend: 'neutral' },
]

const BARRIERS = [
  {
    country: 'China',
    severity: 'high',
    description: 'Export controls on rare earth minerals and gallium/germanium',
    sectors: 'Mining, Electronics',
  },
  {
    country: 'EU',
    severity: 'medium',
    description: 'Carbon border adjustment mechanism (CBAM) increasing import costs',
    sectors: 'Steel, Cement, Fertilizer',
  },
  {
    country: 'India',
    severity: 'medium',
    description: 'Import licensing and quality control requirements on electronics',
    sectors: 'Electronics, Telecom',
  },
  {
    country: 'US',
    severity: 'high',
    description: 'Entity list restrictions and CHIPS Act domestic preference',
    sectors: 'Semiconductors, AI',
  },
]
</script>

<style scoped>
.trade-tabs {
  display: flex;
  gap: 0;
  padding: 0 12px;
  border-bottom: 1px solid var(--wm-border, #2a2a2a);
}

.trade-tab {
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

.trade-tab:hover {
  color: var(--wm-text, #e8e8e8);
}

.trade-tab.active {
  color: var(--wm-text, #e8e8e8);
  border-bottom-color: var(--wm-text, #e8e8e8);
}

.trade-body {
  padding: 8px 12px;
  font-family: 'SF Mono', monospace;
  font-size: 12px;
}

.trade-section-header {
  font-size: 10px;
  font-weight: 600;
  color: var(--wm-text-dim, #888);
  text-transform: uppercase;
  letter-spacing: 1px;
  padding-bottom: 8px;
  margin-bottom: 8px;
  border-bottom: 1px solid var(--wm-border, #2a2a2a);
}

/* Disputes */
.trade-dispute {
  padding: 10px 0;
  border-bottom: 1px solid var(--wm-border, #2a2a2a);
}

.trade-dispute:last-child {
  border-bottom: none;
}

.dispute-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.dispute-flags {
  font-size: 14px;
  flex-shrink: 0;
}

.dispute-name {
  font-weight: 700;
  color: var(--wm-text, #e8e8e8);
  font-size: 12px;
}

.dispute-detail {
  display: flex;
  gap: 8px;
  padding: 2px 0 2px 32px;
  font-size: 11px;
}

.dispute-label {
  color: var(--wm-text-dim, #888);
  flex-shrink: 0;
}

.dispute-value {
  color: var(--wm-text, #e8e8e8);
}

.dispute-status-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  letter-spacing: 0.5px;
}

.dispute-status-badge.status-escalating {
  background: rgba(255, 68, 68, 0.15);
  color: #ff4444;
  border: 1px solid rgba(255, 68, 68, 0.3);
}

.dispute-status-badge.status-active {
  background: rgba(255, 136, 0, 0.15);
  color: #ff8800;
  border: 1px solid rgba(255, 136, 0, 0.3);
}

.dispute-status-badge.status-monitoring {
  background: rgba(255, 170, 0, 0.15);
  color: #ffaa00;
  border: 1px solid rgba(255, 170, 0, 0.3);
}

/* Tariffs rows */
.trade-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 0;
  border-bottom: 1px solid var(--wm-border, #2a2a2a);
}

.trade-row:last-child {
  border-bottom: none;
}

.trade-pair {
  flex: 1;
  color: var(--wm-text, #e8e8e8);
  font-size: 12px;
}

.trade-rate {
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  color: var(--wm-text, #e8e8e8);
  width: 80px;
  text-align: right;
  flex-shrink: 0;
}

.trade-trend {
  font-size: 10px;
  width: 20px;
  text-align: center;
  flex-shrink: 0;
}

.trade-trend.trend-up {
  color: #ff4444;
}

.trade-trend.trend-down {
  color: #44ff88;
}

.trade-trend.trend-neutral {
  color: var(--wm-text-muted, #666);
}

/* Barriers */
.trade-barrier {
  padding: 10px 0;
  border-bottom: 1px solid var(--wm-border, #2a2a2a);
}

.trade-barrier:last-child {
  border-bottom: none;
}

.barrier-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 4px;
}

.barrier-country {
  font-weight: 700;
  color: var(--wm-text, #e8e8e8);
  font-size: 12px;
}

.barrier-severity {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  letter-spacing: 0.5px;
}

.barrier-severity.severity-high {
  background: rgba(255, 68, 68, 0.15);
  color: #ff4444;
  border: 1px solid rgba(255, 68, 68, 0.3);
}

.barrier-severity.severity-medium {
  background: rgba(255, 170, 0, 0.15);
  color: #ffaa00;
  border: 1px solid rgba(255, 170, 0, 0.3);
}

.barrier-severity.severity-low {
  background: rgba(68, 170, 68, 0.15);
  color: #44aa44;
  border: 1px solid rgba(68, 170, 68, 0.3);
}

.barrier-desc {
  font-size: 11px;
  color: var(--wm-text-dim, #888);
  line-height: 1.4;
  margin-bottom: 4px;
}

.barrier-sectors {
  font-size: 10px;
  color: var(--wm-text-muted, #666);
}
</style>
