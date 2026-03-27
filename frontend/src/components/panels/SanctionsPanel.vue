<template>
  <BasePanel
    panelId="sanctions"
    title="SANCTIONS PRESSURE"
    infoTooltip="Global sanctions pressure index based on designation counts and enforcement actions"
  >
    <template #default>
      <div class="sanctions-content">
        <div class="sanctions-section-label">MOST SANCTIONED</div>

        <div class="sanctions-list">
          <div
            v-for="(entry, idx) in entries"
            :key="idx"
            class="sanctions-row"
          >
            <div class="sanctions-row__header">
              <span class="sanctions-flag">{{ entry.flag }}</span>
              <span class="sanctions-name">{{ entry.name }}</span>
              <div class="sanctions-bar-wrapper">
                <div
                  class="sanctions-bar"
                  :style="{
                    width: (entry.score / 100 * 100) + '%',
                    background: getBarColor(entry.score)
                  }"
                ></div>
                <div class="sanctions-bar-bg"></div>
              </div>
              <span
                class="sanctions-score"
                :style="{ color: getBarColor(entry.score) }"
              >{{ entry.score }}</span>
            </div>
            <div class="sanctions-row__sub">
              {{ entry.designations }} designations
            </div>
          </div>
        </div>
      </div>
    </template>
  </BasePanel>
</template>

<script setup>
import { ref } from 'vue'
import BasePanel from '../BasePanel.vue'

function getBarColor(score) {
  if (score > 80) return 'var(--semantic-critical, #ff4444)'
  if (score > 60) return 'var(--semantic-high, #ff8800)'
  if (score > 40) return 'var(--semantic-elevated, #ffaa00)'
  return 'var(--semantic-normal, #44aa44)'
}

const entries = ref([
  { flag: '\uD83C\uDDF7\uD83C\uDDFA', name: 'Russia', score: 98, designations: '12,400+' },
  { flag: '\uD83C\uDDEE\uD83C\uDDF7', name: 'Iran', score: 85, designations: '4,200+' },
  { flag: '\uD83C\uDDF0\uD83C\uDDF5', name: 'North Korea', score: 78, designations: '2,100+' },
  { flag: '\uD83C\uDDF8\uD83C\uDDFE', name: 'Syria', score: 72, designations: '1,800+' },
  { flag: '\uD83C\uDDFB\uD83C\uDDEA', name: 'Venezuela', score: 55, designations: '900+' },
  { flag: '\uD83C\uDDF2\uD83C\uDDF2', name: 'Myanmar', score: 48, designations: '600+' }
])
</script>

<style scoped>
.sanctions-content {
  display: flex;
  flex-direction: column;
  flex: 1;
}

.sanctions-section-label {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  font-weight: 600;
  color: var(--wm-text-dim, #888);
  letter-spacing: 1px;
  text-transform: uppercase;
  padding: 4px 12px 8px;
}

.sanctions-list {
  display: flex;
  flex-direction: column;
}

.sanctions-row {
  padding: 8px 12px;
  border-bottom: 1px solid var(--wm-border, #2a2a2a);
  transition: background 0.15s ease;
}

.sanctions-row:hover {
  background: var(--wm-surface-hover, #1e1e1e);
}

.sanctions-row__header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.sanctions-flag {
  font-size: 14px;
  flex-shrink: 0;
}

.sanctions-name {
  font-family: 'SF Mono', monospace;
  font-size: 12px;
  font-weight: 600;
  color: var(--wm-text, #e8e8e8);
  min-width: 90px;
}

.sanctions-bar-wrapper {
  flex: 1;
  height: 8px;
  position: relative;
  min-width: 60px;
}

.sanctions-bar-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--wm-border, #2a2a2a);
  border-radius: 2px;
}

.sanctions-bar {
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  border-radius: 2px;
  z-index: 1;
  transition: width 0.3s ease;
}

.sanctions-score {
  font-family: 'SF Mono', monospace;
  font-size: 14px;
  font-weight: 700;
  min-width: 28px;
  text-align: right;
}

.sanctions-row__sub {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  color: var(--wm-text-muted, #666);
  padding-left: 22px;
  margin-top: 2px;
}
</style>
