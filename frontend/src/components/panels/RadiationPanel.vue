<template>
  <BasePanel
    panelId="radiation"
    title="RADIATION WATCH"
    infoTooltip="Representative radiation monitoring data. Live API integration planned."
    dataBadge="DEMO"
  >
    <template #default>
      <div class="radiation-content">
        <div class="radiation-section-label">MONITORING STATIONS</div>

        <div class="radiation-list">
          <div
            v-for="(station, idx) in stations"
            :key="idx"
            class="radiation-row"
          >
            <span class="radiation-name">{{ station.name }}</span>
            <span class="radiation-reading">{{ station.reading }} &mu;Sv/h</span>
            <span
              class="radiation-status"
              :style="{ color: getStatusColor(station.reading) }"
            >
              {{ getStatusIcon(station.reading) }} {{ getStatusLabel(station.reading) }}
            </span>
          </div>
        </div>

        <div class="radiation-divider"></div>

        <div class="radiation-footer">
          <span class="radiation-threshold">THRESHOLD: 0.30 &mu;Sv/h = Alert</span>
          <span class="radiation-updated">Last updated: 5m ago</span>
        </div>
      </div>
    </template>
  </BasePanel>
</template>

<script setup>
import { ref } from 'vue'
import BasePanel from '../BasePanel.vue'

function getStatusColor(reading) {
  if (reading > 0.30) return 'var(--semantic-critical, #ff4444)'
  if (reading >= 0.20) return 'var(--semantic-elevated, #ffaa00)'
  return 'var(--semantic-normal, #44aa44)'
}

function getStatusIcon(reading) {
  if (reading >= 0.20) return '\u26A0'
  return '\u25CF'
}

function getStatusLabel(reading) {
  if (reading > 0.30) return 'ALERT'
  if (reading >= 0.20) return 'ELEVATED'
  return 'NORMAL'
}

const stations = ref([
  { name: 'Chernobyl, UA', reading: 0.12 },
  { name: 'Fukushima, JP', reading: 0.08 },
  { name: 'Sellafield, GB', reading: 0.05 },
  { name: 'Zaporizhzhia, UA', reading: 0.15 },
  { name: 'La Hague, FR', reading: 0.04 }
])
</script>

<style scoped>
.radiation-content {
  display: flex;
  flex-direction: column;
  gap: 0;
  flex: 1;
}

.radiation-section-label {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  font-weight: 600;
  color: var(--wm-text-dim, #888);
  letter-spacing: 1px;
  text-transform: uppercase;
  padding: 4px 12px 8px;
}

.radiation-list {
  display: flex;
  flex-direction: column;
}

.radiation-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 12px;
  border-bottom: 1px solid var(--wm-border, #2a2a2a);
  transition: background 0.15s ease;
}

.radiation-row:hover {
  background: var(--wm-surface-hover, #1e1e1e);
}

.radiation-name {
  font-family: 'SF Mono', monospace;
  font-size: 12px;
  color: var(--wm-text, #e8e8e8);
  min-width: 130px;
}

.radiation-reading {
  font-family: 'SF Mono', monospace;
  font-size: 12px;
  color: var(--wm-text-dim, #888);
  min-width: 100px;
  text-align: right;
}

.radiation-status {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  font-weight: 600;
  min-width: 80px;
  text-align: right;
}

.radiation-divider {
  height: 1px;
  background: var(--wm-border, #2a2a2a);
  margin: 8px 0;
}

.radiation-footer {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 4px 12px;
}

.radiation-threshold {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  color: var(--wm-text-dim, #888);
}

.radiation-updated {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  color: var(--wm-text-muted, #666);
}
</style>
