<template>
  <BasePanel panelId="displacement" title="UNHCR DISPLACEMENT" :showCount="true" :count="totalFormatted">
    <template #default>
      <div class="disp-stats">
        <div class="disp-stat">
          <span class="disp-stat__value">{{ formatNum(data.refugees) }}</span>
          <span class="disp-stat__label">REFUGEES</span>
        </div>
        <div class="disp-stat">
          <span class="disp-stat__value">{{ formatNum(data.asylum_seekers) }}</span>
          <span class="disp-stat__label">ASYLUM SEEKERS</span>
        </div>
        <div class="disp-stat">
          <span class="disp-stat__value">{{ formatNum(data.idps) }}</span>
          <span class="disp-stat__label">IDPS</span>
        </div>
      </div>

      <div class="disp-divider"></div>

      <div class="disp-tabs">
        <button
          class="disp-tab"
          :class="{ active: activeTab === 'origins' }"
          @click="activeTab = 'origins'"
        >Origins</button>
        <button
          class="disp-tab"
          :class="{ active: activeTab === 'hosts' }"
          @click="activeTab = 'hosts'"
        >Hosts</button>
      </div>

      <div class="disp-divider"></div>

      <div class="disp-table-header">
        <span class="disp-th-country">COUNTRY</span>
        <span class="disp-th-count">COUNT</span>
        <span v-if="activeTab === 'origins'" class="disp-th-status">STATUS</span>
      </div>

      <div class="disp-list">
        <div
          v-for="item in activeList"
          :key="item.code"
          class="disp-row"
        >
          <span class="disp-row__flag">{{ getFlagEmoji(item.code) }}</span>
          <span class="disp-row__country">{{ item.country }}</span>
          <span class="disp-row__count">{{ formatNum(item.count) }}</span>
          <span
            v-if="activeTab === 'origins'"
            class="disp-row__status"
            :class="'disp-status--' + (item.status || '').toLowerCase()"
          >{{ item.status }}</span>
        </div>
      </div>

      <div v-if="error" class="disp-empty">
        Failed to load displacement data
      </div>
    </template>
  </BasePanel>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import BasePanel from '../BasePanel.vue'
import { getDisplacement } from '../../api/intelligence'

const data = ref({
  refugees: 0,
  asylum_seekers: 0,
  idps: 0,
  total: 0,
  top_origins: [],
  top_hosts: [],
})
const activeTab = ref('origins')
const error = ref(false)

const totalFormatted = computed(() => {
  return formatNum(data.value.total)
})

const activeList = computed(() => {
  return activeTab.value === 'origins'
    ? data.value.top_origins
    : data.value.top_hosts
})

function formatNum(n) {
  if (!n) return '0'
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M'
  if (n >= 1_000) return (n / 1_000).toFixed(0) + 'K'
  return String(n)
}

function getFlagEmoji(code) {
  if (!code || code.length !== 2) return ''
  const codePoints = code
    .toUpperCase()
    .split('')
    .map(c => 0x1f1e6 + c.charCodeAt(0) - 65)
  return String.fromCodePoint(...codePoints)
}

async function fetchData() {
  try {
    const res = await getDisplacement()
    const d = res.data?.data || res.data || {}
    data.value = {
      refugees: d.refugees || 0,
      asylum_seekers: d.asylum_seekers || 0,
      idps: d.idps || 0,
      total: d.total || 0,
      top_origins: d.top_origins || [],
      top_hosts: d.top_hosts || [],
    }
  } catch (err) {
    console.error('[DisplacementPanel] fetch error:', err)
    error.value = true
  }
}

onMounted(fetchData)
</script>

<style scoped>
.disp-stats {
  display: flex;
  justify-content: space-around;
  padding: 12px 8px;
}

.disp-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.disp-stat__value {
  font-family: 'SF Mono', monospace;
  font-size: 18px;
  font-weight: 700;
  color: var(--wm-text, #e8e8e8);
}

.disp-stat__label {
  font-family: 'SF Mono', monospace;
  font-size: 9px;
  color: var(--wm-text-dim, #888);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.disp-divider {
  height: 1px;
  background: var(--wm-border, #2a2a2a);
  margin: 0 8px;
}

.disp-tabs {
  display: flex;
  gap: 2px;
  padding: 6px 8px;
}

.disp-tab {
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--wm-text-dim, #888);
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 1px;
  padding: 4px 10px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.disp-tab:hover {
  color: var(--wm-text, #e8e8e8);
}

.disp-tab.active {
  background: var(--wm-surface-hover, #1e1e1e);
  border-bottom: 2px solid var(--wm-live, #44ff88);
  color: var(--wm-text, #e8e8e8);
}

.disp-table-header {
  display: flex;
  align-items: center;
  padding: 6px 12px;
  border-bottom: 1px solid var(--wm-border, #2a2a2a);
  font-family: 'SF Mono', monospace;
  font-size: 9px;
  color: var(--wm-text-dim, #888);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.disp-th-country {
  flex: 1;
}

.disp-th-count {
  width: 60px;
  text-align: right;
}

.disp-th-status {
  width: 60px;
  text-align: right;
  margin-left: 8px;
}

.disp-list {
  overflow-y: auto;
  flex: 1;
}

.disp-row {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid var(--wm-border, #2a2a2a);
  transition: background 0.15s ease;
}

.disp-row:hover {
  background: var(--wm-surface-hover, #1e1e1e);
}

.disp-row__flag {
  font-size: 12px;
  margin-right: 6px;
}

.disp-row__country {
  flex: 1;
  font-family: 'SF Mono', monospace;
  font-size: 12px;
  color: var(--wm-text, #e8e8e8);
}

.disp-row__count {
  width: 60px;
  text-align: right;
  font-family: 'SF Mono', monospace;
  font-size: 12px;
  color: var(--wm-text-secondary, #ccc);
}

.disp-row__status {
  width: 60px;
  text-align: right;
  margin-left: 8px;
  font-family: 'SF Mono', monospace;
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  padding: 1px 6px;
  border-radius: 2px;
}

.disp-status--crisis {
  background: var(--wm-critical, #ff4444);
  color: #ffffff;
}

.disp-status--high {
  background: var(--wm-high, #ff8800);
  color: #ffffff;
}

.disp-empty {
  padding: 24px;
  text-align: center;
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--wm-text-dim, #888);
}
</style>
