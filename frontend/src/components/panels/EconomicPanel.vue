<template>
  <BasePanel panelId="economic" title="ECONOMIC INDICATORS" dataBadge="DEMO" infoTooltip="Representative economic data. FRED API key not configured. Data as of Mar 2026.">
    <template #default>
      <div class="econ-container">
        <div class="econ-tabs">
          <button
            class="econ-tab"
            :class="{ 'econ-tab--active': activeTab === 'calendar' }"
            @click="activeTab = 'calendar'"
          >Calendar</button>
          <button
            class="econ-tab"
            :class="{ 'econ-tab--active': activeTab === 'indicators' }"
            @click="activeTab = 'indicators'"
          >Indicators</button>
        </div>

        <div v-if="activeTab === 'calendar'" class="econ-section">
          <div class="econ-section__title">UPCOMING EVENTS</div>
          <div
            v-for="(evt, idx) in calendarEvents"
            :key="idx"
            class="econ-event"
          >
            <span class="econ-event__date">{{ evt.date }}</span>
            <span class="econ-event__name">{{ evt.name }}</span>
            <span class="econ-event__flag">{{ evt.flag }}</span>
          </div>
        </div>

        <div v-if="activeTab === 'indicators'" class="econ-section">
          <div class="econ-section__title">RECENT INDICATORS</div>
          <div
            v-for="(ind, idx) in indicators"
            :key="idx"
            class="econ-indicator"
          >
            <span class="econ-indicator__name">{{ ind.name }}</span>
            <span
              class="econ-indicator__value"
              :class="ind.positive ? 'val-positive' : 'val-negative'"
            >{{ ind.value }}</span>
            <span
              class="econ-indicator__trend"
              :class="ind.positive ? 'val-positive' : 'val-negative'"
            >{{ ind.trend }}</span>
            <span class="econ-indicator__period">{{ ind.period }}</span>
          </div>
        </div>
      </div>
    </template>
  </BasePanel>
</template>

<script setup>
import { ref } from 'vue'
import BasePanel from '../BasePanel.vue'

const activeTab = ref('calendar')

const calendarEvents = ref([
  { date: 'Mar 27', name: 'Fed Interest Rate Decision', flag: '\u{1F1FA}\u{1F1F8}' },
  { date: 'Mar 28', name: 'UK GDP Q4 Final', flag: '\u{1F1EC}\u{1F1E7}' },
  { date: 'Mar 29', name: 'EU CPI Flash Estimate', flag: '\u{1F1EA}\u{1F1FA}' },
  { date: 'Apr 01', name: 'US ISM Manufacturing', flag: '\u{1F1FA}\u{1F1F8}' },
  { date: 'Apr 02', name: 'OPEC+ Meeting', flag: '\u{1F30D}' },
  { date: 'Apr 04', name: 'US Non-Farm Payrolls', flag: '\u{1F1FA}\u{1F1F8}' },
  { date: 'Apr 10', name: 'ECB Interest Rate Decision', flag: '\u{1F1EA}\u{1F1FA}' },
  { date: 'Apr 15', name: 'China GDP Q1', flag: '\u{1F1E8}\u{1F1F3}' },
])

const indicators = ref([
  { name: 'US GDP Growth', value: '+2.8%', trend: '\u25B2', positive: true, period: 'Q4' },
  { name: 'US Inflation', value: '3.1%', trend: '\u25BC', positive: true, period: 'Feb' },
  { name: 'UK Interest Rate', value: '5.25%', trend: '\u2192', positive: false, period: 'Mar' },
  { name: 'EU Unemployment', value: '6.4%', trend: '\u25BC', positive: true, period: 'Jan' },
  { name: 'China PMI', value: '50.2', trend: '\u25B2', positive: true, period: 'Mar' },
  { name: 'Japan CPI', value: '2.8%', trend: '\u25B2', positive: false, period: 'Feb' },
  { name: 'US 10Y Yield', value: '4.32%', trend: '\u25B2', positive: false, period: 'Mar' },
  { name: 'Oil (Brent)', value: '$82.40', trend: '\u25BC', positive: true, period: 'Mar' },
])
</script>

<style scoped>
.econ-container {
  overflow-y: auto;
  flex: 1;
}

.econ-tabs {
  display: flex;
  border-bottom: 1px solid var(--wm-border, #2a2a2a);
}

.econ-tab {
  flex: 1;
  padding: 8px 12px;
  background: none;
  border: none;
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  font-weight: 600;
  color: var(--wm-text-dim, #888);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  cursor: pointer;
  transition: color 0.15s ease, border-color 0.15s ease;
  border-bottom: 2px solid transparent;
}

.econ-tab:hover {
  color: var(--wm-text, #e8e8e8);
}

.econ-tab--active {
  color: var(--wm-accent, #fff);
  border-bottom-color: var(--wm-accent, #fff);
}

.econ-section {
  padding: 0;
}

.econ-section__title {
  padding: 8px 12px;
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  font-weight: 700;
  color: var(--wm-text-dim, #888);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--wm-border, #2a2a2a);
}

.econ-event {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 12px;
  border-bottom: 1px solid var(--wm-border, #2a2a2a);
  transition: background 0.15s ease;
}

.econ-event:hover {
  background: var(--wm-surface-hover, #1e1e1e);
}

.econ-event__date {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--wm-text-dim, #888);
  min-width: 48px;
}

.econ-event__name {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--wm-text, #e8e8e8);
  flex: 1;
}

.econ-event__flag {
  font-size: 13px;
}

.econ-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 12px;
  border-bottom: 1px solid var(--wm-border, #2a2a2a);
  transition: background 0.15s ease;
}

.econ-indicator:hover {
  background: var(--wm-surface-hover, #1e1e1e);
}

.econ-indicator__name {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--wm-text-dim, #888);
  flex: 1;
  min-width: 100px;
}

.econ-indicator__value {
  font-family: 'SF Mono', monospace;
  font-size: 12px;
  font-weight: 700;
  min-width: 56px;
  text-align: right;
}

.econ-indicator__trend {
  font-family: 'SF Mono', monospace;
  font-size: 12px;
  min-width: 14px;
  text-align: center;
}

.econ-indicator__period {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--wm-text-muted, #666);
  min-width: 28px;
  text-align: right;
}

.val-positive {
  color: #44ff88;
}

.val-negative {
  color: #ff4444;
}

.econ-empty {
  padding: 24px;
  text-align: center;
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--wm-text-dim, #888);
}
</style>
