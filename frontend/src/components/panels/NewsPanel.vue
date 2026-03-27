<template>
  <BasePanel panelId="news" title="LIVE NEWS" :showCount="true" :count="filteredSignals.length">
    <template #tabs>
      <div class="news-tabs">
        <button
          v-for="tab in sourceTabs"
          :key="tab"
          class="news-tab"
          :class="{ active: activeTab === tab }"
          @click="activeTab = tab"
        >
          {{ tab }}
        </button>
      </div>
    </template>

    <template #default>
      <!-- Live video stream for selected source -->
      <div v-if="activeStreamUrl && !embedFailed" class="news-stream">
        <div class="stream-header">
          <span class="stream-live-dot"></span>
          <span class="stream-label">LIVE</span>
          <span class="stream-channel">{{ activeTab }}</span>
          <button class="stream-close" @click="showStream = false">✕</button>
        </div>
        <!-- HLS: native video element (no YouTube issues) -->
        <video
          v-if="isHLS"
          :src="activeStreamUrl"
          class="stream-iframe"
          autoplay
          muted
          playsinline
          controls
        ></video>
        <!-- YouTube: iframe embed -->
        <iframe
          v-else
          :src="activeStreamUrl"
          class="stream-iframe"
          allow="autoplay; encrypted-media; picture-in-picture"
          allowfullscreen
          frameborder="0"
          referrerpolicy="strict-origin-when-cross-origin"
          @load="onIframeLoad"
        ></iframe>
      </div>

      <!-- YouTube fallback when embed fails (Error 153 from localhost) -->
      <div v-if="showStream && embedFailed && getStreamInfo(activeTab)" class="news-stream-fallback">
        <div class="stream-header">
          <span class="stream-live-dot"></span>
          <span class="stream-label">LIVE</span>
          <span class="stream-channel">{{ activeTab }}</span>
          <button class="stream-close" @click="showStream = false">✕</button>
        </div>
        <div class="fallback-body">
          <span class="fallback-icon">&#9654;</span>
          <span class="fallback-msg">Embed blocked (Error 153). Open stream directly:</span>
          <a
            :href="getYouTubeWatchUrl(activeTab)"
            target="_blank"
            rel="noopener"
            class="fallback-link"
          >Watch {{ activeTab }} on YouTube &#8599;</a>
        </div>
      </div>

      <div class="news-toolbar">
        <button class="sort-toggle" @click="toggleSort">
          {{ sortMode === 'importance' ? '▼ IMPORTANCE' : '▼ NEWEST' }}
        </button>
        <button v-if="getStreamInfo(activeTab)" class="stream-toggle" @click="toggleStream">
          {{ showStream ? 'Headlines' : 'Live Video' }}
        </button>
      </div>

      <div class="news-list" v-show="!showStream || !getStreamInfo(activeTab)">
        <div
          v-for="item in sortedSignals"
          :key="item.id"
          class="news-item"
          :class="{ 'news-item--new': item._isNew }"
        >
          <div class="news-item__header">
            <span class="news-item__source">{{ getSourceName(item) }}</span>
            <span v-if="item.category" class="news-item__category">{{ item.category }}</span>
            <span class="news-item__time">{{ formatTimeAgo(item.created_at || item.timestamp) }}</span>
            <span class="threat-dot" :class="'threat-dot--' + getThreatDotClass(item)"></span>
          </div>
          <div class="news-item__headline">
            <a
              v-if="getSourceUrl(item)"
              :href="getSourceUrl(item)"
              target="_blank"
              rel="noopener noreferrer"
              class="news-item__link"
            >{{ item.title }}</a>
            <span v-else>{{ item.title }}</span>
          </div>
          <div class="news-item__footer">
            <span
              v-if="getThreatLevel(item) !== 'NORMAL'"
              class="threat-badge"
              :class="'threat-badge--' + getThreatLevel(item).toLowerCase()"
            >
              {{ getThreatLevel(item) }}
            </span>
            <span v-if="item.country_code" class="news-item__country">
              {{ getFlagEmoji(item.country_code) }} {{ item.country_code }}
            </span>
            <span class="news-item__sources">{{ getSourceCount(item) }} sources</span>
            <button class="news-item__simulate" @click.stop="simulateSignal(item)">Simulate &rarr;</button>
          </div>
        </div>

        <div v-if="sortedSignals.length === 0" class="news-empty">
          No signals matching current filter
        </div>
      </div>
    </template>
  </BasePanel>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import BasePanel from '../BasePanel.vue'
import { listSignals } from '../../api/intelligence'

const router = useRouter()

const signals = ref([])
const activeTab = ref('BLOOMBERG')
const sortMode = ref('importance')
const newItemIds = ref(new Set())
const showStream = ref(true)

const embedFailed = ref(false)

// Live stream sources — mix of HLS (direct) and YouTube fallbacks
// HLS streams work without YouTube embed issues (no Error 153)
const SOURCE_STREAMS = {
  'BLOOMBERG': { type: 'youtube', id: 'dp8PhLsUcFE' },
  'SKYNEWS': { type: 'youtube', id: '9Auq9mYxFEE' },
  'DW': { type: 'hls', url: 'https://dwamdstream103.akamaized.net/hls/live/2015526/dwstream103/master.m3u8' },
  'EURONEWS': { type: 'youtube', id: 'pykpO5kQJ98' },
  'CNN': { type: 'youtube', id: 'w_Ma8oQLmSM' },
  'CNBC': { type: 'youtube', id: '9NyxcX3rhQs' },
  'FRANCE24': { type: 'youtube', id: 'u9foWyMSETk' },
  'ALJAZEERA': { type: 'youtube', id: 'gCNeDWCI0vo' },
  'ALARABIYA': { type: 'youtube', id: 'n7eQejkXbnM' },
}

function getStreamInfo(tab) {
  return SOURCE_STREAMS[tab] || null
}

const activeStreamUrl = computed(() => {
  if (!showStream.value) return null
  const info = getStreamInfo(activeTab.value)
  if (!info) return null
  if (info.type === 'hls') return info.url
  const origin = typeof window !== 'undefined' ? window.location.origin : ''
  return `https://www.youtube.com/embed/${info.id}?autoplay=1&mute=1&controls=1&modestbranding=1&playsinline=1&rel=0&enablejsapi=1&origin=${origin}`
})

const isHLS = computed(() => {
  const info = getStreamInfo(activeTab.value)
  return info?.type === 'hls'
})
let refreshInterval = null

function scoreHeadline(title) {
  let score = 0
  const t = title.toLowerCase()
  const violence = ['killed', 'dead', 'casualties', 'attack', 'bombing']
  const military = ['war', 'airstrike', 'missile', 'troops', 'military']
  const unrest = ['protest', 'uprising', 'coup', 'riot', 'revolution']
  const urgent = ['breaking', 'urgent', 'emergency', 'crisis']

  if (violence.some(w => t.includes(w))) score += 100
  if (military.some(w => t.includes(w))) score += 80
  if (unrest.some(w => t.includes(w))) score += 60
  if (urgent.some(w => t.includes(w))) score += 50
  return score
}

function extractDomain(url) {
  if (!url) return null
  try {
    const hostname = new URL(url).hostname
    return hostname.replace('www.', '').split('.')[0].toUpperCase()
  } catch {
    return null
  }
}

function getSourceName(item) {
  try {
    const raw = item.raw_data_json
    if (typeof raw === 'string') {
      try {
        const parsed = JSON.parse(raw)
        return parsed.source_name || parsed.source || extractDomain(parsed.feed) || item.source || 'Unknown'
      } catch {
        return item.source || 'Unknown'
      }
    }
    if (raw && typeof raw === 'object') {
      return raw.source_name || raw.source || extractDomain(raw.feed) || item.source || 'Unknown'
    }
    return item.source || 'Unknown'
  } catch {
    return item.source || 'Unknown'
  }
}

function getSourceCount(item) {
  try {
    const raw = item.raw_data_json
    if (typeof raw === 'string') {
      return JSON.parse(raw).source_count || 1
    }
    return raw?.source_count || 1
  } catch {
    return 1
  }
}

function getSourceUrl(item) {
  if (item.source_url) return item.source_url
  try {
    const raw = item.raw_data_json
    if (typeof raw === 'string') {
      const parsed = JSON.parse(raw)
      return parsed.link || parsed.url || parsed.source_url || null
    }
    if (raw && typeof raw === 'object') {
      return raw.link || raw.url || raw.source_url || null
    }
  } catch { /* ignore */ }
  return null
}

function getThreatDotClass(item) {
  const score = item.anomaly_score || 0
  if (score > 0.8) return 'red'
  if (score > 0.6) return 'orange'
  if (score > 0.4) return 'yellow'
  return 'green'
}

function getThreatLevel(item) {
  const score = scoreHeadline(item.title || '')
  if (score >= 100) return 'CRITICAL'
  if (score >= 60) return 'HIGH'
  if (score >= 40) return 'ELEVATED'
  return 'NORMAL'
}

function formatTimeAgo(dateStr) {
  if (!dateStr) return ''
  const now = Date.now()
  const then = new Date(dateStr).getTime()
  const diff = Math.floor((now - then) / 1000)
  if (diff < 60) return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

function getFlagEmoji(code) {
  if (!code || code.length !== 2) return ''
  const codePoints = code
    .toUpperCase()
    .split('')
    .map(c => 0x1f1e6 + c.charCodeAt(0) - 65)
  return String.fromCodePoint(...codePoints)
}

// Hardcoded channel tabs matching SOURCE_STREAMS keys
const CHANNEL_TABS = ['BLOOMBERG', 'SKYNEWS', 'EURONEWS', 'DW', 'CNBC', 'CNN', 'FRANCE24', 'ALJAZEERA', 'ALARABIYA']

const sourceTabs = computed(() => {
  return [...CHANNEL_TABS, 'ALL']
})

function getYouTubeWatchUrl(tab) {
  const info = getStreamInfo(tab)
  if (!info || info.type !== 'youtube') return '#'
  return `https://www.youtube.com/watch?v=${info.id}`
}

function onIframeLoad(event) {
  // Detect if YouTube embed was blocked -- iframe loads but with error page
  // We can't inspect cross-origin iframe content, so we use a timeout heuristic
  // and also watch for the activeTab change to reset
}

function simulateSignal(item) {
  router.push({
    path: '/simulate',
    query: {
      signal_id: item.id,
      title: item.title || '',
    }
  })
}

function toggleStream() {
  showStream.value = !showStream.value
  embedFailed.value = false
}

// Reset embed failure state when switching tabs
watch(activeTab, () => {
  embedFailed.value = false
})

// Detect YouTube embed failures via message events (Error 153)
if (typeof window !== 'undefined') {
  window.addEventListener('message', (event) => {
    try {
      if (event.origin.includes('youtube.com')) {
        const data = typeof event.data === 'string' ? JSON.parse(event.data) : event.data
        if (data?.event === 'onError' || data?.info?.errorCode === 150 || data?.info?.errorCode === 153) {
          embedFailed.value = true
        }
      }
    } catch {
      // ignore non-JSON messages
    }
  })
}

const filteredSignals = computed(() => {
  if (activeTab.value === 'ALL') return signals.value
  // Match tab name loosely against source name (case-insensitive, partial match)
  const tab = activeTab.value.toLowerCase()
  return signals.value.filter(s => {
    const src = getSourceName(s).toLowerCase()
    return src === tab || src.includes(tab) || tab.includes(src)
  })
})

const sortedSignals = computed(() => {
  const items = [...filteredSignals.value].map(item => ({
    ...item,
    _isNew: newItemIds.value.has(item.id),
    _score: scoreHeadline(item.title || '')
  }))

  if (sortMode.value === 'importance') {
    items.sort((a, b) => b._score - a._score)
  } else {
    items.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
  }
  return items
})

function toggleSort() {
  sortMode.value = sortMode.value === 'importance' ? 'newest' : 'importance'
}

async function fetchSignals() {
  try {
    const res = await listSignals({ limit: 100 })
    const data = res.data?.results || res.data || []
    const existingIds = new Set(signals.value.map(s => s.id))
    const incoming = Array.isArray(data) ? data : []

    // Mark new items
    const freshIds = new Set()
    incoming.forEach(s => {
      if (!existingIds.has(s.id)) {
        freshIds.add(s.id)
      }
    })
    newItemIds.value = freshIds

    signals.value = incoming

    // Clear new markers after animation
    if (freshIds.size > 0) {
      setTimeout(() => {
        newItemIds.value = new Set()
      }, 2000)
    }
  } catch (err) {
    console.error('[NewsPanel] fetch error:', err)
  }
}

onMounted(() => {
  fetchSignals()
  refreshInterval = setInterval(fetchSignals, 60000)
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})
</script>

<style scoped>
/* Live video stream */
.news-stream {
  display: flex;
  flex-direction: column;
  background: #000;
}
.stream-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: var(--surface, #141414);
  border-bottom: 1px solid var(--border, #2a2a2a);
}
.stream-live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ff4444;
  animation: pulse-stream 1.5s infinite;
}
@keyframes pulse-stream { 0%,100%{opacity:1} 50%{opacity:0.4} }
.stream-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 1px;
  color: var(--text, #e8e8e8);
}
.stream-close {
  margin-left: auto;
  background: none;
  border: none;
  color: var(--text-dim, #888);
  cursor: pointer;
  font-size: 14px;
}
.stream-channel {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1px;
  color: var(--text, #e8e8e8);
}
.stream-iframe {
  width: 100%;
  aspect-ratio: 16 / 9;
  border: none;
  background: #000;
}
/* Fallback when YouTube embed fails */
.news-stream-fallback {
  display: flex;
  flex-direction: column;
  background: #000;
}
.fallback-body {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px 16px;
  gap: 8px;
  aspect-ratio: 16 / 9;
  background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
}
.fallback-icon {
  font-size: 32px;
  color: #ff4444;
}
.fallback-msg {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  color: var(--text-dim, #888);
  text-align: center;
}
.fallback-link {
  font-family: 'SF Mono', monospace;
  font-size: 12px;
  font-weight: 600;
  color: #44aaff;
  text-decoration: none;
  padding: 6px 16px;
  border: 1px solid #44aaff;
  border-radius: 3px;
  transition: all 0.15s ease;
}
.fallback-link:hover {
  background: rgba(68, 170, 255, 0.15);
  color: #66ccff;
}
.news-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 10px;
  border-bottom: 1px solid var(--border, #2a2a2a);
}
.stream-toggle {
  background: none;
  border: 1px solid var(--border, #2a2a2a);
  color: var(--text-dim, #888);
  font-family: inherit;
  font-size: 10px;
  padding: 2px 8px;
  cursor: pointer;
  border-radius: 2px;
}
.stream-toggle:hover {
  color: var(--text, #e8e8e8);
  border-color: var(--border-strong, #444);
}

.news-tabs {
  display: flex;
  gap: 2px;
  overflow-x: auto;
  padding: 4px 8px;
  scrollbar-width: none;
}

.news-tabs::-webkit-scrollbar {
  display: none;
}

.news-tab {
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--wm-text-dim, #888);
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 1px;
  padding: 4px 8px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s ease;
}

.news-tab:hover {
  color: var(--wm-text, #e8e8e8);
}

.news-tab.active {
  background: var(--wm-surface-hover, #1e1e1e);
  border-bottom: 2px solid var(--wm-live, #44ff88);
  color: var(--wm-text, #e8e8e8);
}

.news-toolbar {
  display: flex;
  justify-content: flex-end;
  padding: 4px 8px;
  border-bottom: 1px solid var(--wm-border, #2a2a2a);
}

.sort-toggle {
  background: transparent;
  border: 1px solid var(--wm-border, #2a2a2a);
  color: var(--wm-text-dim, #888);
  font-family: 'SF Mono', monospace;
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 2px 8px;
  cursor: pointer;
  border-radius: 2px;
}

.sort-toggle:hover {
  color: var(--wm-text, #e8e8e8);
  border-color: var(--wm-text-dim, #888);
}

.news-list {
  overflow-y: auto;
  flex: 1;
}

.news-item {
  padding: 10px 12px;
  border-bottom: 1px solid var(--wm-border, #2a2a2a);
  transition: background 0.15s ease;
}

.news-item:hover {
  background: var(--wm-surface-hover, #1e1e1e);
}

.news-item--new {
  animation: newGlow 2s ease-out;
}

@keyframes newGlow {
  0% {
    background: rgba(68, 255, 136, 0.15);
  }
  100% {
    background: transparent;
  }
}

.news-item__header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.news-item__source {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  color: var(--wm-text-dim, #888);
}

.news-item__time {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  color: var(--wm-text-dim, #888);
  margin-left: auto;
}

.news-item__category {
  font-family: 'SF Mono', monospace;
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 1px 5px;
  border-radius: 1px;
  background: var(--wm-border, #2a2a2a);
  color: var(--wm-text-dim, #888);
}

.threat-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.threat-dot--red { background: #ff4444; }
.threat-dot--orange { background: #ff8800; }
.threat-dot--yellow { background: #ffaa00; }
.threat-dot--green { background: #44aa44; }

.news-item__headline {
  font-family: 'SF Mono', monospace;
  font-size: 12px;
  font-weight: 500;
  color: var(--wm-text, #e8e8e8);
  line-height: 1.4;
  margin-bottom: 6px;
}

.news-item__link {
  color: inherit;
  text-decoration: none;
}

.news-item__link:hover {
  text-decoration: underline;
}

.news-item__footer {
  display: flex;
  align-items: center;
  gap: 8px;
}

.threat-badge {
  font-family: 'SF Mono', monospace;
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  padding: 1px 6px;
  border-radius: 2px;
}

.threat-badge--critical {
  background: var(--wm-critical, #ff4444);
  color: #ffffff;
}

.threat-badge--high {
  background: var(--wm-high, #ff8800);
  color: #ffffff;
}

.threat-badge--elevated {
  background: var(--wm-elevated, #ffaa00);
  color: #1a1a1a;
}

.news-item__country {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  color: var(--wm-text-dim, #888);
}

.news-item__sources {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  color: var(--wm-text-dim, #888);
}

.news-item__simulate {
  display: none;
  font-family: 'SF Mono', monospace;
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 0.5px;
  padding: 2px 8px;
  background: transparent;
  border: 1px solid #FF4500;
  color: #FF4500;
  cursor: pointer;
  border-radius: 2px;
  margin-left: auto;
  white-space: nowrap;
  transition: all 0.15s ease;
}

.news-item:hover .news-item__simulate {
  display: inline-block;
}

.news-item__simulate:hover {
  background: rgba(255, 69, 0, 0.15);
  color: #FF6A33;
  border-color: #FF6A33;
}

.news-empty {
  padding: 24px;
  text-align: center;
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--wm-text-dim, #888);
}
</style>
