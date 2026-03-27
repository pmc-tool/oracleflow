<template>
  <BasePanel
    panelId="intel-feed"
    title="INTEL FEED"
    :showCount="true"
    :count="items.length"
    :defaultRowSpan="2"
  >
    <template #tabs>
      <div class="feed-header-bar">
        <span v-if="newCount > 0" class="feed-new-badge">{{ newCount }} NEW</span>
        <span v-if="trendPct" class="feed-trend" :class="{ positive: trendPct > 0 }">
          {{ trendPct > 0 ? '+' : '' }}{{ trendPct }}%
        </span>
        <span class="feed-live-badge">LIVE</span>
        <div class="feed-actions">
          <button class="feed-action-btn" title="Download" @click="downloadFeed">&#8595;</button>
          <button class="feed-action-btn" title="Bookmark" @click="bookmarkFeed">&#10024;</button>
        </div>
      </div>
    </template>

    <template #default>
      <div class="feed-list">
        <div
          v-for="(item, idx) in items"
          :key="item.id || idx"
          class="feed-item"
          :class="{ 'feed-item--new': item._isNew }"
        >
          <div class="feed-item__top">
            <span class="feed-item__source">{{ item.sourceName }}</span>
            <div class="feed-item__tags">
              <span
                v-for="tag in item.tags"
                :key="tag"
                class="feed-tag"
                :class="'feed-tag--' + tag.toLowerCase()"
              >{{ tag }}</span>
            </div>
            <span class="feed-item__time">{{ item.timeAgo }}</span>
            <span class="threat-dot" :class="'threat-dot--' + item.threatDot"></span>
          </div>
          <div class="feed-item__headline">
            <a
              v-if="item.sourceUrl"
              :href="item.sourceUrl"
              target="_blank"
              rel="noopener noreferrer"
              class="feed-item__link"
            >{{ item.title }}</a>
            <span v-else>{{ item.title }}</span>
          </div>
          <div class="feed-item__bottom">
            <button class="feed-item__sim-btn" @click.stop="simulateItem(item)">Simulate &rarr;</button>
            <button class="feed-item__menu">&#8942;</button>
          </div>
        </div>

        <div v-if="items.length === 0" class="feed-empty">
          No intelligence items available
        </div>
      </div>
    </template>
  </BasePanel>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import BasePanel from '../BasePanel.vue'
import { listSignals } from '../../api/intelligence'

const router = useRouter()

const rawSignals = ref([])
const prevCount = ref(0)
let refreshInterval = null

const newCount = computed(() => {
  const now = Date.now()
  const oneHour = 3600000
  return rawSignals.value.filter(s => {
    const t = new Date(s.created_at).getTime()
    return (now - t) < oneHour
  }).length
})

const trendPct = computed(() => {
  if (prevCount.value === 0) return 20
  const diff = rawSignals.value.length - prevCount.value
  if (prevCount.value === 0) return 0
  return Math.round((diff / prevCount.value) * 100)
})

function getSourceName(item) {
  try {
    const raw = item.raw_data_json
    if (typeof raw === 'string') {
      return JSON.parse(raw).source_name || 'UNKNOWN'
    }
    return raw?.source_name || 'UNKNOWN'
  } catch {
    return 'UNKNOWN'
  }
}

function getTags(item) {
  const cat = (item.category || '').toLowerCase()
  const tags = ['ALERT']
  if (cat.includes('geopolit') || cat.includes('conflict')) tags.push('CONFLICT')
  else if (cat.includes('politic') || cat.includes('diplomati')) tags.push('DIPLOMATIC')
  else if (cat.includes('econom') || cat.includes('financ')) tags.push('ECONOMIC')
  else if (cat.includes('cyber')) tags.push('CYBER')
  else if (cat.includes('military') || cat.includes('defense')) tags.push('MILITARY')
  else if (cat.includes('climate') || cat.includes('environ')) { /* ALERT only */ }
  else {
    // Try to infer from title
    const title = (item.title || '').toLowerCase()
    if (title.includes('military') || title.includes('weapon') || title.includes('troop')) tags.push('MILITARY')
    else if (title.includes('trade') || title.includes('market') || title.includes('econom')) tags.push('ECONOMIC')
    else if (title.includes('cyber') || title.includes('hack')) tags.push('CYBER')
    else if (title.includes('diplomati') || title.includes('sanction') || title.includes('treaty')) tags.push('DIPLOMATIC')
    else tags.push('CONFLICT')
  }
  return tags
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

const items = computed(() => {
  const now = Date.now()
  const oneHour = 3600000
  return [...rawSignals.value]
    .sort((a, b) => (b.anomaly_score || 0) - (a.anomaly_score || 0))
    .slice(0, 16)
    .map(s => ({
      id: s.id,
      sourceName: getSourceName(s).toUpperCase(),
      title: s.title || 'Untitled signal',
      tags: getTags(s),
      timeAgo: formatTimeAgo(s.created_at || s.timestamp),
      sourceUrl: getSourceUrl(s),
      threatDot: getThreatDotClass(s),
      _isNew: (now - new Date(s.created_at || s.timestamp).getTime()) < oneHour,
    }))
})

function simulateItem(item) {
  router.push({
    path: '/simulate',
    query: {
      signal_id: item.id,
      title: item.title || '',
    }
  })
}

function downloadFeed() {
  const text = items.value.map(i => `[${i.sourceName}] ${i.title}`).join('\n')
  const blob = new Blob([text], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'intel-feed.txt'
  a.click()
  URL.revokeObjectURL(url)
}

function bookmarkFeed() {
  // Placeholder for bookmark functionality
}

async function fetchSignals() {
  try {
    prevCount.value = rawSignals.value.length
    const res = await listSignals({ limit: 100 })
    const data = res.data?.results || res.data || []
    rawSignals.value = Array.isArray(data) ? data : []
  } catch {
    // Use existing data
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
.feed-header-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  border-bottom: 1px solid var(--border, #2a2a2a);
}

.feed-new-badge {
  font-family: 'SF Mono', monospace;
  font-size: 9px;
  font-weight: 700;
  color: var(--green, #44ff88);
  border: 1px solid var(--green, #44ff88);
  padding: 1px 6px;
  letter-spacing: 0.5px;
}

.feed-trend {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  font-weight: 600;
  color: var(--text-dim, #888);
}

.feed-trend.positive {
  color: var(--green, #44ff88);
}

.feed-live-badge {
  font-family: 'SF Mono', monospace;
  font-size: 9px;
  font-weight: 700;
  color: var(--green, #44ff88);
  letter-spacing: 0.5px;
}

.feed-actions {
  display: flex;
  gap: 4px;
  margin-left: auto;
}

.feed-action-btn {
  background: transparent;
  border: none;
  color: var(--text-dim, #888);
  font-size: 13px;
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border-radius: 2px;
  transition: all 0.15s ease;
}

.feed-action-btn:hover {
  color: var(--text, #e8e8e8);
  background: var(--surface-hover, #1e1e1e);
}

/* Feed list */
.feed-list {
  display: flex;
  flex-direction: column;
}

.feed-item {
  padding: 10px 8px;
  border-bottom: 1px solid var(--border, #2a2a2a);
  transition: background 0.15s ease;
}

.feed-item:hover {
  background: var(--surface-hover, #1e1e1e);
}

.feed-item--new {
  border-left: 2px solid var(--green, #44ff88);
  animation: feedNewGlow 2s ease-out;
}

@keyframes feedNewGlow {
  0% { background: rgba(68, 255, 136, 0.1); }
  100% { background: transparent; }
}

.feed-item__top {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
  flex-wrap: wrap;
}

.feed-item__source {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  color: var(--text-dim, #888);
  letter-spacing: 0.5px;
  flex-shrink: 0;
}

.feed-item__tags {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.feed-tag {
  font-family: 'SF Mono', monospace;
  font-size: 8px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 1px 5px;
  border-radius: 1px;
  color: #fff;
}

.feed-tag--alert {
  background: var(--semantic-critical, #ff4444);
}

.feed-tag--conflict {
  background: var(--semantic-critical, #ff4444);
}

.feed-tag--diplomatic {
  background: var(--semantic-high, #ff8800);
}

.feed-tag--military {
  background: var(--semantic-high, #ff8800);
}

.feed-tag--economic {
  background: var(--semantic-normal, #44aa44);
}

.feed-tag--cyber {
  background: #9333ea;
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

.feed-item__headline {
  font-family: 'SF Mono', monospace;
  font-size: 13px;
  font-weight: 600;
  color: var(--text, #e8e8e8);
  line-height: 1.4;
  margin-bottom: 4px;
}

.feed-item__link {
  color: inherit;
  text-decoration: none;
}

.feed-item__link:hover {
  text-decoration: underline;
}

.feed-item__bottom {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.feed-item__time {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  color: var(--text-dim, #888);
  margin-left: auto;
}

.feed-item__sim-btn {
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
  white-space: nowrap;
  transition: all 0.15s ease;
}

.feed-item:hover .feed-item__sim-btn {
  display: inline-block;
}

.feed-item__sim-btn:hover {
  background: rgba(255, 69, 0, 0.15);
  color: #FF6A33;
  border-color: #FF6A33;
}

.feed-item__menu {
  background: transparent;
  border: none;
  color: var(--text-muted, #666);
  font-size: 14px;
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
  transition: color 0.15s ease;
}

.feed-item__menu:hover {
  color: var(--text, #e8e8e8);
}

.feed-empty {
  padding: 24px;
  text-align: center;
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--text-dim, #888);
}
</style>
