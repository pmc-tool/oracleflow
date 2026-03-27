<template>
  <header class="header">
    <div class="header-left">
      <div class="defcon-badge" :style="{ background: defconColor }">
        &#9762; DEFCON {{ defconLevel }}
      </div>
      <span class="pipe-sep"></span>
      <span class="logo">ORACLEFLOW</span>
      <span class="version">v0.1</span>
      <span class="pipe-sep"></span>
      <span class="status-indicator">
        <span class="status-dot"></span>
        LIVE
      </span>
      <span v-if="signalCount > 0" class="signal-badge">
        <span class="signal-badge__count">{{ formattedSignalCount }}</span> signal{{ signalCount !== 1 ? 's' : '' }} in your categories today
      </span>
      <span class="pipe-sep"></span>
      <div class="region-dropdown">
        Global <span class="dropdown-arrow">&#9660;</span>
      </div>
    </div>
    <div class="header-right">
      <div class="map-dimension-toggle">
        <button
          class="map-dim-btn"
          :class="{ active: viewMode === '2D' }"
          @click="setProjection('2D')"
        >2D</button>
        <button
          class="map-dim-btn"
          :class="{ active: viewMode === '3D' }"
          @click="setProjection('3D')"
        >3D</button>
      </div>
      <button class="search-toggle-btn" @click="emit('searchToggle')" title="Search map">
        &#128269;
      </button>
      <span class="pipe-sep"></span>
      <span class="header-clock">{{ utcTime }}</span>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { getChaos, listSignals } from '../api/intelligence'

const props = defineProps({
  userCategories: {
    type: Array,
    default: null
  }
})

const emit = defineEmits(['projectionChange', 'searchToggle'])

const signalCount = ref(0)

const formattedSignalCount = computed(() => {
  const n = signalCount.value
  if (n >= 1000) return (n / 1000).toFixed(1).replace(/\.0$/, '') + 'k'
  return n.toLocaleString()
})

const viewMode = ref('2D')
const chaosScore = ref(30)
const now = ref(new Date())
let timer = null

function setProjection(mode) {
  viewMode.value = mode
  emit('projectionChange', mode.toLowerCase())
}

const defconLevel = computed(() => {
  const s = chaosScore.value
  if (s > 80) return 1
  if (s > 60) return 2
  if (s > 40) return 3
  if (s > 20) return 4
  return 5
})

const defconColor = computed(() => {
  switch (defconLevel.value) {
    case 1: return '#ff0040'
    case 2: return '#ff4400'
    case 3: return '#ffaa00'
    case 4: return '#00aaff'
    case 5: return '#2d8a6e'
    default: return '#ffaa00'
  }
})

const utcTime = computed(() => {
  const d = now.value
  const days = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']
  const months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
  const day = days[d.getUTCDay()]
  const date = String(d.getUTCDate()).padStart(2, '0')
  const month = months[d.getUTCMonth()]
  const year = d.getUTCFullYear()
  const hours = String(d.getUTCHours()).padStart(2, '0')
  const minutes = String(d.getUTCMinutes()).padStart(2, '0')
  return `${day}, ${date} ${month} ${year} ${hours}:${minutes} UTC`
})

onMounted(async () => {
  timer = setInterval(() => {
    now.value = new Date()
  }, 1000)

  try {
    const res = await getChaos()
    const data = res.data || res
    if (data && data.score != null) {
      chaosScore.value = data.score
    } else if (data && data.chaos_score != null) {
      chaosScore.value = data.chaos_score
    }
  } catch {
    // fallback to default
  }

  // Fetch signal count for user's categories
  try {
    const params = { limit: 1 }
    if (props.userCategories && props.userCategories.length > 0) {
      params.categories = props.userCategories.join(',')
    }
    const sigRes = await listSignals(params)
    const sigData = sigRes.data || sigRes
    signalCount.value = sigData.total || sigData.count || (Array.isArray(sigData) ? sigData.length : 0)
  } catch {
    // silent
  }
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
/* ============================================================
   Header — WM exact: .header from main.css
   ============================================================ */
.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  height: 40px;
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

/* DEFCON badge */
.defcon-badge {
  color: #fff;
  font-weight: 700;
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 2px;
  letter-spacing: 0.5px;
  white-space: nowrap;
  font-family: var(--font-mono);
}

/* Pipe separator */
.pipe-sep {
  display: inline-block;
  width: 1px;
  height: 20px;
  background: var(--border);
  flex-shrink: 0;
}

/* Logo — WM exact: .logo */
.logo {
  font-weight: bold;
  font-size: 14px;
  letter-spacing: 2px;
  color: var(--accent);
}

/* Version — WM exact: .version */
.version {
  font-size: 9px;
  color: var(--text-muted);
  opacity: 0.5;
  margin-left: 6px;
  font-weight: normal;
  letter-spacing: 0.5px;
  vertical-align: middle;
}

/* Status indicator — WM exact */
.status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  color: var(--status-live, #44ff88);
  font-weight: 600;
  white-space: nowrap;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--green, #44ff88);
  animation: pulse-dot 2s infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Signal badge */
.signal-badge {
  font-size: 10px;
  font-weight: 500;
  color: #FF4500;
  background: rgba(255, 69, 0, 0.1);
  border: 1px solid rgba(255, 69, 0, 0.25);
  padding: 2px 8px;
  border-radius: 3px;
  white-space: nowrap;
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 0.3px;
}

.signal-badge__count {
  font-weight: 700;
  color: #FF6A33;
}

/* Region dropdown */
.region-dropdown {
  color: var(--text-secondary);
  cursor: pointer;
  padding: 2px 8px;
  border: 1px solid var(--border);
  border-radius: 2px;
  white-space: nowrap;
  font-size: 11px;
}

.region-dropdown:hover {
  border-color: var(--border-strong);
  background: var(--surface-hover);
}

.dropdown-arrow {
  font-size: 8px;
  margin-left: 4px;
  color: var(--text-dim);
}

/* 2D/3D Toggle — WM exact: .map-dimension-toggle, .map-dim-btn */
.map-dimension-toggle {
  display: flex;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  overflow: hidden;
  margin-right: 2px;
}

.map-dim-btn {
  background: transparent;
  border: none;
  color: var(--text-dim);
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  cursor: pointer;
  transition: all 0.2s;
  letter-spacing: 0.5px;
  font-family: var(--font-mono);
}

.map-dim-btn:hover {
  color: var(--text);
  background: var(--surface-hover);
}

.map-dim-btn.active {
  background: var(--green, #44ff88);
  color: var(--bg);
}

/* Search toggle button */
.search-toggle-btn {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-dim);
  font-size: 13px;
  padding: 2px 7px;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
  line-height: 1;
}

.search-toggle-btn:hover {
  color: var(--text);
  border-color: var(--border-strong);
  background: var(--surface-hover);
}

/* Header clock — WM exact: .header-clock */
.header-clock {
  font-size: 10px;
  color: var(--text-dim);
  letter-spacing: 0.5px;
  pointer-events: none;
  text-transform: uppercase;
  white-space: nowrap;
}
</style>
