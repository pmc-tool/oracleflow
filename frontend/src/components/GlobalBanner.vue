<template>
  <div class="global-banner">
    <span class="defcon-badge" :class="defcon.cls">
      &#9762; DEFCON {{ defcon.level }}
    </span>
    <span class="separator">|</span>
    <span class="live-dot"></span>
    <span class="live-text">LIVE</span>
    <span class="separator">|</span>
    <span class="chaos-label">Global Chaos:</span>
    <span class="chaos-value" :style="{ color: chaosColor }">{{ score }}</span>
    <span class="separator">|</span>
    <div class="category-pills">
      <span v-for="cat in categories" :key="cat.name" class="cat-pill">
        {{ cat.name }}: <strong>{{ cat.score }}</strong>
      </span>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { getChaos } from '../api/intelligence'

const chaosData = ref({})
let refreshTimer = null

const score = computed(() => {
  const s = chaosData.value.composite_score
  return s != null ? s.toFixed(1) : '--'
})

const delta = computed(() => {
  return chaosData.value.delta ?? 3.2
})

const chaosColor = computed(() => {
  const s = chaosData.value.composite_score
  if (s == null) return '#999'
  if (s < 30) return '#4CAF50'
  if (s < 60) return '#FFC107'
  if (s < 80) return '#FF9800'
  return '#F44336'
})

const defcon = computed(() => {
  const s = chaosData.value.composite_score
  if (s == null) return { level: '--', cls: 'defcon-unknown' }
  if (s > 80) return { level: 1, cls: 'defcon-1' }
  if (s > 60) return { level: 2, cls: 'defcon-2' }
  if (s > 40) return { level: 3, cls: 'defcon-3' }
  if (s > 20) return { level: 4, cls: 'defcon-4' }
  return { level: 5, cls: 'defcon-5' }
})

const categories = computed(() => {
  const cats = chaosData.value.categories || {}
  return [
    { name: 'Finance', score: cats.finance != null ? cats.finance.toFixed(0) : '--' },
    { name: 'Geo', score: cats.geopolitical != null ? cats.geopolitical.toFixed(0) : '--' },
    { name: 'Supply', score: cats.supply_chain != null ? cats.supply_chain.toFixed(0) : '--' },
    { name: 'Cyber', score: cats.cyber != null ? cats.cyber.toFixed(0) : '--' },
    { name: 'Climate', score: cats.climate != null ? cats.climate.toFixed(0) : '--' },
  ]
})

async function fetchChaos() {
  try {
    const res = await getChaos()
    chaosData.value = res.data || res || {}
  } catch {
    // silent
  }
}

onMounted(() => {
  fetchChaos()
  refreshTimer = setInterval(fetchChaos, 60000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
.global-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  height: 40px;
  padding: 0 16px;
  background: #0a0a0a;
  border: 1px solid #2a2a2a;
  flex-wrap: nowrap;
  overflow-x: auto;
}

.defcon-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 2px 10px;
  letter-spacing: 1px;
  white-space: nowrap;
  flex-shrink: 0;
  color: #fff;
}

.defcon-1 {
  background: #ff4444;
  animation: flash-defcon 1s ease-in-out infinite;
}

.defcon-2 {
  background: #ff8800;
}

.defcon-3 {
  background: #b8a800;
  color: #0a0a0a;
}

.defcon-4 {
  background: #4CAF50;
  color: #0a0a0a;
}

.defcon-5 {
  background: #2196F3;
}

.defcon-unknown {
  background: #333;
}

@keyframes flash-defcon {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.separator {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #333;
  flex-shrink: 0;
}

.live-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #4CAF50;
  flex-shrink: 0;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.6); }
  50% { opacity: 0.7; box-shadow: 0 0 0 6px rgba(76, 175, 80, 0); }
}

.live-text {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  font-weight: 700;
  color: #4CAF50;
  letter-spacing: 1px;
  flex-shrink: 0;
}

.chaos-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #777;
  flex-shrink: 0;
  white-space: nowrap;
}

.chaos-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1rem;
  font-weight: 700;
  flex-shrink: 0;
}

.category-pills {
  display: flex;
  gap: 8px;
  margin-left: auto;
  flex-shrink: 0;
}

.cat-pill {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  color: #666;
  white-space: nowrap;
}

.cat-pill strong {
  color: #aaa;
}
</style>
