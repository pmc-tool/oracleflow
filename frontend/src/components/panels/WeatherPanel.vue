<template>
  <BasePanel
    panelId="weather"
    title="WEATHER ALERTS"
    infoTooltip="Simulated severe weather alerts. Real-time alert API integration planned."
    dataBadge="SIMULATED"
    :showCount="true"
    :count="alerts.length"
  >
    <template #default>
      <div class="weather-list">
        <div
          v-for="(alert, idx) in alerts"
          :key="idx"
          class="weather-row"
        >
          <div class="weather-row__header">
            <span
              class="weather-dot"
              :style="{ background: getSeverityColor(alert.severity) }"
            ></span>
            <span class="weather-type">{{ alert.type }}</span>
          </div>
          <div class="weather-row__details">
            <span class="weather-detail">{{ alert.detail }}</span>
            <span v-if="alert.detail2" class="weather-detail">{{ alert.detail2 }}</span>
            <span class="weather-time">Updated: {{ alert.updated }}</span>
          </div>
        </div>
      </div>
    </template>
  </BasePanel>
</template>

<script setup>
import { ref } from 'vue'
import BasePanel from '../BasePanel.vue'

function getSeverityColor(severity) {
  if (severity === 'critical') return 'var(--semantic-critical, #ff4444)'
  if (severity === 'high') return 'var(--semantic-high, #ff8800)'
  if (severity === 'elevated') return 'var(--semantic-elevated, #ffaa00)'
  return 'var(--semantic-normal, #44aa44)'
}

const alerts = ref([
  {
    severity: 'critical',
    type: 'Hurricane Warning',
    detail: 'Category 3 | Caribbean Basin',
    detail2: 'Sustained winds: 120 mph',
    updated: '1h ago'
  },
  {
    severity: 'high',
    type: 'Severe Thunderstorm',
    detail: 'Central US | Tornado possible',
    detail2: null,
    updated: '3h ago'
  },
  {
    severity: 'elevated',
    type: 'Heat Wave Advisory',
    detail: 'Southern Europe | 42\u00B0C expected',
    detail2: null,
    updated: '6h ago'
  },
  {
    severity: 'normal',
    type: 'Winter Storm Watch',
    detail: 'Northern Japan | Heavy snowfall',
    detail2: null,
    updated: '12h ago'
  }
])
</script>

<style scoped>
.weather-list {
  overflow-y: auto;
  flex: 1;
}

.weather-row {
  padding: 8px 12px;
  border-bottom: 1px solid var(--wm-border, #2a2a2a);
  transition: background 0.15s ease;
}

.weather-row:hover {
  background: var(--wm-surface-hover, #1e1e1e);
}

.weather-row__header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.weather-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.weather-type {
  font-family: 'SF Mono', monospace;
  font-size: 12px;
  font-weight: 700;
  color: var(--wm-text, #e8e8e8);
}

.weather-row__details {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin-top: 4px;
  padding-left: 16px;
}

.weather-detail {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--wm-text-dim, #888);
}

.weather-time {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  color: var(--wm-text-muted, #666);
  margin-top: 2px;
}
</style>
