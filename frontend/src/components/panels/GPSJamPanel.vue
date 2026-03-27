<template>
  <BasePanel
    panelId="gps-jam"
    title="GPS JAMMING"
    infoTooltip="Representative GPS jamming data. Live ADS-B anomaly API integration planned."
    dataBadge="DEMO"
    :showCount="true"
    :count="zones.length"
  >
    <template #default>
      <div class="gpsjam-container">
        <div class="gpsjam-subtitle">ACTIVE JAMMING ZONES</div>
        <div class="gpsjam-list">
          <div
            v-for="(zone, idx) in zones"
            :key="idx"
            class="gpsjam-zone"
          >
            <div class="gpsjam-zone__header">
              <span class="gpsjam-zone__dot" :style="{ color: severityColor(zone.severity) }">&#x25CF;</span>
              <span class="gpsjam-zone__name">{{ zone.name }}</span>
            </div>
            <div class="gpsjam-zone__details">
              <div class="gpsjam-zone__detail">
                <span class="gpsjam-zone__label">Hexes affected:</span>
                <span class="gpsjam-zone__val">{{ zone.hexes }}</span>
              </div>
              <div class="gpsjam-zone__detail">
                <span class="gpsjam-zone__label">Source:</span>
                <span class="gpsjam-zone__val">{{ zone.source }}</span>
              </div>
              <div v-if="zone.impact" class="gpsjam-zone__detail">
                <span class="gpsjam-zone__label">Impact:</span>
                <span class="gpsjam-zone__val">{{ zone.impact }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="gpsjam-divider"></div>
        <div class="gpsjam-summary">
          <span>Total zones: {{ zones.length }}</span>
          <span>Hexes: {{ totalHexes }}</span>
        </div>
      </div>
    </template>
  </BasePanel>
</template>

<script setup>
import { ref, computed } from 'vue'
import BasePanel from '../BasePanel.vue'

function severityColor(level) {
  if (level === 'critical') return '#ff4444'
  if (level === 'high') return '#ff8800'
  if (level === 'elevated') return '#ffaa00'
  return '#44aa44'
}

const zones = ref([
  {
    severity: 'critical',
    name: 'Eastern Mediterranean',
    hexes: 28,
    source: 'State-sponsored',
    impact: 'Commercial aviation rerouted'
  },
  {
    severity: 'high',
    name: 'Black Sea Region',
    hexes: 15,
    source: 'Military',
    impact: 'Ship navigation affected'
  },
  {
    severity: 'elevated',
    name: 'Baltic States',
    hexes: 8,
    source: 'Unknown',
    impact: 'Intermittent disruption'
  },
  {
    severity: 'high',
    name: 'Northern Syria / Iraq',
    hexes: 12,
    source: 'Military operations',
    impact: 'Drone operations disrupted'
  },
  {
    severity: 'elevated',
    name: 'Korean Peninsula DMZ',
    hexes: 5,
    source: 'State-sponsored',
    impact: null
  }
])

const totalHexes = computed(() => {
  return zones.value.reduce((sum, z) => sum + z.hexes, 0)
})
</script>

<style scoped>
.gpsjam-container {
  overflow-y: auto;
  flex: 1;
}

.gpsjam-subtitle {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  font-weight: 600;
  color: var(--text-dim, #888);
  text-transform: uppercase;
  letter-spacing: 1px;
  padding: 8px 12px 6px;
}

.gpsjam-list {
  padding: 0;
}

.gpsjam-zone {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border, #2a2a2a);
  transition: background 0.15s ease;
}

.gpsjam-zone:hover {
  background: var(--surface-hover, #1e1e1e);
}

.gpsjam-zone__header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.gpsjam-zone__dot {
  font-size: 10px;
  flex-shrink: 0;
}

.gpsjam-zone__name {
  font-family: 'SF Mono', monospace;
  font-size: 12px;
  font-weight: 700;
  color: var(--text, #e8e8e8);
}

.gpsjam-zone__details {
  padding-left: 18px;
}

.gpsjam-zone__detail {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 2px;
}

.gpsjam-zone__label {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--text-dim, #888);
  min-width: 100px;
}

.gpsjam-zone__val {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--text-secondary, #ccc);
}

.gpsjam-divider {
  border-top: 1px solid var(--border, #2a2a2a);
}

.gpsjam-summary {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  color: var(--text-muted, #666);
  font-weight: 600;
}
</style>
