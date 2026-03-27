<template>
  <BasePanel panelId="regional-news" title="WORLD NEWS"
    dataBadge="LIVE"
    :showCount="true" :count="totalSignals"
    :defaultColSpan="2" :defaultRowSpan="2">
    <template #default>
      <div class="region-grid">
        <div
          v-for="region in regionData"
          :key="region.name"
          class="region-card"
        >
          <div class="region-card__header">
            <span class="region-card__name">{{ region.name }}</span>
            <span class="region-card__live">LIVE</span>
            <span class="region-card__count">&darr; {{ region.signals.length }}</span>
          </div>
          <div class="region-card__articles">
            <div
              v-for="article in region.articles"
              :key="article.id"
              class="region-article"
            >
              <div class="region-article__header">
                <span class="region-article__source">{{ article.source }}</span>
                <span
                  v-if="article.tag"
                  class="region-article__tag"
                  :class="'tag--' + article.tagClass"
                >{{ article.tag }}</span>
                <span class="region-article__time">{{ article.timeAgo }}</span>
                <span class="threat-dot" :class="'threat-dot--' + article.threatDot"></span>
              </div>
              <div class="region-article__headline">
                <a
                  v-if="article.sourceUrl"
                  :href="article.sourceUrl"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="region-article__link"
                >{{ article.title }}</a>
                <span v-else>{{ article.title }}</span>
              </div>
            </div>
            <div v-if="region.signals.length === 0" class="region-article__empty">
              No signals
            </div>
          </div>
        </div>
      </div>
    </template>
  </BasePanel>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import BasePanel from '../BasePanel.vue'
import { listSignals } from '../../api/intelligence'

const signals = ref([])
let refreshInterval = null

const REGIONS = {
  'UNITED STATES': ['US'],
  'EUROPE': ['GB', 'DE', 'FR', 'IT', 'ES', 'PL', 'UA', 'NL', 'SE', 'NO', 'DK', 'FI', 'AT', 'CH', 'BE', 'IE', 'CZ', 'PT', 'GR', 'RO', 'HU'],
  'MIDDLE EAST': ['IL', 'IR', 'IQ', 'SY', 'SA', 'AE', 'QA', 'KW', 'YE', 'PS', 'JO', 'LB', 'OM', 'BH'],
  'AFRICA': ['NG', 'ZA', 'KE', 'ET', 'EG', 'GH', 'TZ', 'CD', 'SD', 'SS', 'SO', 'ML', 'NE', 'BF', 'CM', 'SN'],
  'LATIN AMERICA': ['BR', 'MX', 'AR', 'CO', 'VE', 'CL', 'PE', 'EC', 'CU', 'JM', 'TT', 'BB', 'HT', 'DO', 'GT', 'HN'],
  'ASIA-PACIFIC': ['CN', 'JP', 'KR', 'KP', 'IN', 'PK', 'AU', 'NZ', 'ID', 'TH', 'VN', 'PH', 'MY', 'SG', 'MM', 'TW', 'BD', 'LK'],
}

// Build reverse lookup: country_code -> region name
const CODE_TO_REGION = {}
for (const [region, codes] of Object.entries(REGIONS)) {
  for (const code of codes) {
    CODE_TO_REGION[code] = region
  }
}

const TAG_MAP = {
  geopolitical: { tag: 'CONFLICT', cls: 'red' },
  politics: { tag: 'ALERT', cls: 'red' },
  economy: { tag: 'ECONOMIC', cls: 'green' },
  cyber: { tag: 'ALERT', cls: 'red' },
  military: { tag: 'MILITARY', cls: 'orange' },
}

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

function getTag(item) {
  const cat = (item.category || '').toLowerCase()
  const mapped = TAG_MAP[cat]
  if (!mapped) return null
  return mapped
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

const regionData = computed(() => {
  const buckets = {}
  for (const name of Object.keys(REGIONS)) {
    buckets[name] = []
  }
  buckets['GLOBAL'] = []

  signals.value.forEach(s => {
    const cc = s.country_code
    const region = cc ? (CODE_TO_REGION[cc] || 'GLOBAL') : 'GLOBAL'
    if (!buckets[region]) buckets[region] = []
    buckets[region].push(s)
  })

  const regionOrder = [...Object.keys(REGIONS)]
  if (buckets['GLOBAL'] && buckets['GLOBAL'].length > 0) {
    regionOrder.push('GLOBAL')
  }

  return regionOrder
    .filter(name => buckets[name])
    .map(name => {
      const regionSignals = buckets[name]
      const articles = regionSignals.slice(0, 3).map(s => {
        const tagInfo = getTag(s)
        return {
          id: s.id,
          source: getSourceName(s).toUpperCase(),
          title: s.title || 'Untitled',
          timeAgo: formatTimeAgo(s.created_at || s.timestamp),
          tag: tagInfo ? tagInfo.tag : null,
          tagClass: tagInfo ? tagInfo.cls : '',
          sourceUrl: getSourceUrl(s),
          threatDot: getThreatDotClass(s),
        }
      })
      return {
        name,
        signals: regionSignals,
        articles,
      }
    })
})

const totalSignals = computed(() => signals.value.length)

async function fetchSignals() {
  try {
    const res = await listSignals({ limit: 200 })
    const data = res.data?.results || res.data || []
    signals.value = Array.isArray(data) ? data : []
  } catch (err) {
    console.error('[RegionalNewsPanel] fetch error:', err)
  }
}

onMounted(() => {
  fetchSignals()
  refreshInterval = setInterval(fetchSignals, 120000)
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})
</script>

<style scoped>
.region-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4px;
}

.region-card {
  border: 1px solid var(--border);
  padding: 10px;
  background: var(--surface);
  overflow-y: auto;
  max-height: 280px;
}

.region-card__header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  padding-bottom: 4px;
  border-bottom: 1px solid var(--border);
}

.region-card__name {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text);
  flex: 1;
}

.region-card__live {
  font-family: 'SF Mono', monospace;
  font-size: 9px;
  font-weight: 700;
  color: var(--green);
  letter-spacing: 0.5px;
}

.region-card__live::before {
  content: '\25CF ';
  font-size: 8px;
}

.region-card__count {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  color: var(--text-dim);
}

.region-card__articles {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.region-article {
  border-bottom: 1px solid var(--border);
  padding-bottom: 6px;
}

.region-article:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.region-article__header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 2px;
}

.region-article__source {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  color: var(--text-dim);
  letter-spacing: 0.5px;
}

.region-article__tag {
  font-family: 'SF Mono', monospace;
  font-size: 8px;
  font-weight: 700;
  text-transform: uppercase;
  padding: 1px 4px;
  border-radius: 2px;
  letter-spacing: 0.5px;
}

.tag--red {
  background: var(--semantic-critical);
  color: #fff;
}

.tag--orange {
  background: var(--semantic-high);
  color: #fff;
}

.tag--blue {
  background: var(--semantic-low, #3388ff);
  color: #fff;
}

.tag--green {
  background: var(--semantic-normal);
  color: #fff;
}

.region-article__time {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  color: var(--text-muted);
  margin-left: auto;
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

.region-article__headline {
  font-family: 'SF Mono', monospace;
  font-size: 12px;
  font-weight: 500;
  color: var(--text);
  line-height: 1.4;
  margin-bottom: 2px;
}

.region-article__link {
  color: inherit;
  text-decoration: none;
}

.region-article__link:hover {
  text-decoration: underline;
}

.region-article__empty {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  color: var(--text-muted);
  padding: 8px 0;
}
</style>
