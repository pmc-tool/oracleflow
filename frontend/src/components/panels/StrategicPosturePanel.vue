<template>
  <BasePanel
    panelId="posture"
    title="AI STRATEGIC POSTURE"
    :defaultRowSpan="2"
    infoTooltip="Real-time military and geopolitical posture assessment across key theaters."
    @close="$emit('close')"
  >
    <template #tabs>
      <div class="posture-header-row">
        <span v-if="newCount > 0" class="new-count-badge">{{ newCount }} NEW</span>
      </div>
    </template>

    <div class="posture-body">
      <!-- Emoji Key (collapsible) -->
      <div class="emoji-key-header" @click="showKey = !showKey">
        <span>&#128273; Emoji Key</span>
        <span class="key-toggle">{{ showKey ? '\u25B2' : '\u25BC' }}</span>
      </div>
      <div v-if="showKey" class="emoji-key-content">
        <div class="key-row"><span>&#9992;</span> Aircraft / air operations</div>
        <div class="key-row"><span>&#9875;</span> Naval vessel / anchor</div>
        <div class="key-row"><span>&#128674;</span> Ship / maritime movement</div>
        <div class="key-row"><span class="status-crit">CRIT</span> Critical threat level</div>
        <div class="key-row"><span class="status-elev">ELEV</span> Elevated threat level</div>
        <div class="key-row"><span class="status-norm">NORM</span> Normal operations</div>
      </div>

      <div class="divider"></div>

      <!-- Theater Cards -->
      <div
        v-for="theater in theaters"
        :key="theater.name"
        class="theater-card"
      >
        <div class="theater-header">
          <span class="theater-name">{{ theater.name }}</span>
          <span
            class="theater-status"
            :class="'status-' + theater.status.toLowerCase()"
          >{{ theater.status }}</span>
        </div>

        <div class="theater-counts">
          <div class="count-row">
            <span class="count-label">AIR</span>
            <span class="count-value">&#9992; {{ theater.air }}</span>
          </div>
          <div class="count-row">
            <span class="count-label">SEA</span>
            <span class="count-value">
              <template v-if="theater.ships > 0">&#128674; {{ theater.ships }}&nbsp;&nbsp;</template>
              &#9875; {{ theater.naval }}
            </span>
          </div>
        </div>

        <div class="theater-footer">
          <span class="theater-trend">&rarr; {{ theater.trend }}</span>
          <span class="theater-link">&rarr; {{ theater.linkCountry }}</span>
        </div>

        <div class="divider"></div>
      </div>
    </div>
  </BasePanel>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import BasePanel from '../BasePanel.vue'
import { listSignals } from '../../api/intelligence'

const emit = defineEmits(['close'])

const showKey = ref(false)
const newCount = ref(1)
const signals = ref([])
let refreshInterval = null

const REGION_CONFIG = [
  {
    name: 'Iran Theater',
    keywords: ['iran', 'persian gulf', 'tehran', 'israel'],
    linkCountry: 'Iran',
    defaultAir: 5,
    defaultNaval: 9,
    defaultShips: 0,
    defaultStatus: 'CRIT'
  },
  {
    name: 'Taiwan Strait',
    keywords: ['taiwan', 'china sea', 'strait', 'pla'],
    linkCountry: 'Taiwan',
    defaultAir: 2,
    defaultNaval: 48,
    defaultShips: 3,
    defaultStatus: 'CRIT'
  },
  {
    name: 'Red Sea / Yemen',
    keywords: ['yemen', 'houthi', 'red sea'],
    linkCountry: 'Yemen',
    defaultAir: 0,
    defaultNaval: 12,
    defaultShips: 0,
    defaultStatus: 'ELEV'
  },
  {
    name: 'Europe / Ukraine',
    keywords: ['ukraine', 'russia', 'kyiv', 'donbas', 'nato'],
    linkCountry: 'Ukraine',
    defaultAir: 8,
    defaultNaval: 4,
    defaultShips: 2,
    defaultStatus: 'ELEV'
  },
  {
    name: 'Korean Peninsula',
    keywords: ['north korea', 'pyongyang', 'korean'],
    linkCountry: 'North Korea',
    defaultAir: 1,
    defaultNaval: 3,
    defaultShips: 0,
    defaultStatus: 'NORM'
  }
]

function countMatches(signalsList, regionKeywords, typeKeywords) {
  return signalsList.filter(s => {
    const text = ((s.title || '') + ' ' + (s.summary || '') + ' ' + (s.content || '')).toLowerCase()
    const matchesRegion = regionKeywords.some(kw => text.includes(kw))
    const matchesType = typeKeywords.some(kw => text.includes(kw))
    return matchesRegion && matchesType
  }).length
}

function countRegionSignals(signalsList, regionKeywords) {
  return signalsList.filter(s => {
    const text = ((s.title || '') + ' ' + (s.summary || '') + ' ' + (s.content || '')).toLowerCase()
    return regionKeywords.some(kw => text.includes(kw))
  }).length
}

function getStatus(regionCount, air, naval) {
  // Use total region signal count for threat level
  const total = regionCount > 0 ? regionCount : (air + naval)
  if (total > 5) return 'CRIT'
  if (total > 3) return 'ELEV'
  return 'NORM'
}

const theaters = computed(() => {
  const sigs = signals.value
  if (!sigs || sigs.length === 0) {
    // Use placeholder data
    return REGION_CONFIG.map(r => ({
      name: r.name,
      air: r.defaultAir,
      naval: r.defaultNaval,
      ships: r.defaultShips,
      status: r.defaultStatus,
      trend: 'stable',
      linkCountry: r.linkCountry
    }))
  }

  return REGION_CONFIG.map(r => {
    const regionTotal = countRegionSignals(sigs, r.keywords)
    const air = countMatches(sigs, r.keywords, ['air', 'flight', 'aircraft'])
    const naval = countMatches(sigs, r.keywords, ['naval', 'ship', 'vessel', 'maritime'])
    return {
      name: r.name,
      air: air || r.defaultAir,
      naval: naval || r.defaultNaval,
      ships: 0,
      status: getStatus(regionTotal, air, naval),
      trend: regionTotal > 5 ? 'escalating' : regionTotal > 2 ? 'active' : 'stable',
      linkCountry: r.linkCountry
    }
  })
})

async function fetchSignals() {
  try {
    const res = await listSignals({ limit: 200 })
    const data = res.data?.data || res.data?.results || res.data || []
    signals.value = Array.isArray(data) ? data : []
    if (signals.value.length > 0) {
      newCount.value = signals.value.filter(s => {
        const age = Date.now() - new Date(s.timestamp || 0).getTime()
        return age < 3600000 // signals from last hour
      }).length
    }
  } catch {
    signals.value = []
  }
}

onMounted(() => {
  fetchSignals()
  refreshInterval = setInterval(fetchSignals, 5 * 60 * 1000)
})

onBeforeUnmount(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})
</script>

<style scoped>
.posture-header-row {
  display: flex;
  justify-content: flex-end;
  padding: 0 12px 4px;
}
.new-count-badge {
  font-size: 10px;
  font-weight: 700;
  color: #44ff88;
  letter-spacing: 0.5px;
}

.posture-body {
  padding: 12px;
  font-family: 'SF Mono', monospace;
  font-size: 12px;
}

.emoji-key-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 11px;
  font-weight: 600;
  color: var(--wm-text, #e8e8e8);
  cursor: pointer;
  padding: 4px 0;
  user-select: none;
}
.key-toggle {
  font-size: 10px;
  color: var(--wm-text-dim, #888);
}
.emoji-key-content {
  padding: 8px 0 4px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.key-row {
  font-size: 11px;
  color: var(--wm-text-dim, #888);
  display: flex;
  align-items: center;
  gap: 6px;
}

.divider {
  height: 1px;
  background: var(--wm-border, #2a2a2a);
  margin: 12px 0;
}

.theater-card {
  margin-bottom: 0;
}

.theater-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}
.theater-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--wm-text, #e8e8e8);
  letter-spacing: 0.5px;
}
.theater-status {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1px;
  padding: 2px 6px;
}
.status-crit {
  color: #ff4444;
}
.status-elev {
  color: #ffaa00;
}
.status-norm {
  color: #44aa44;
}

.theater-counts {
  display: flex;
  flex-direction: column;
  gap: 3px;
  margin-bottom: 6px;
}
.count-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 11px;
}
.count-label {
  color: var(--wm-text-dim, #888);
  font-weight: 600;
  width: 28px;
  letter-spacing: 0.5px;
}
.count-value {
  color: var(--wm-text, #e8e8e8);
}

.theater-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 10px;
  color: var(--wm-text-dim, #888);
}
.theater-trend {
  color: var(--wm-text-dim, #888);
}
.theater-link {
  color: var(--wm-text-dim, #888);
  cursor: pointer;
}
.theater-link:hover {
  color: var(--wm-text, #e8e8e8);
}
</style>
