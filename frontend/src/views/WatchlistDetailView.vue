<template>
  <div class="watchlist-detail">
    <!-- Header -->
    <div class="detail-header">
      <button class="btn-back" @click="$router.push('/watchlist')">
        <ArrowLeft :size="16" />
        <span>Back</span>
      </button>
      <div class="header-info">
        <h1 class="detail-name">{{ item.name || 'Loading...' }}</h1>
        <div class="header-badges" v-if="item.name">
          <span class="badge badge-type">{{ item.item_type || 'topic' }}</span>
          <span v-if="item.country_code" class="badge badge-country">
            {{ countryFlag(item.country_code) }} {{ item.country_code }}
          </span>
        </div>
      </div>
      <div class="header-actions" v-if="item.name">
        <button class="btn-action btn-danger" @click="confirmDelete">Delete</button>
      </div>
    </div>

    <!-- Stats row -->
    <div v-if="item.name" class="stats-row">
      <div class="stat-box">
        <span class="stat-value">{{ item.signal_count ?? signals.length }}</span>
        <span class="stat-label">SIGNALS TODAY</span>
      </div>
      <div class="stat-box">
        <span class="stat-value" :class="sentimentClass(item.avg_sentiment)">
          {{ formatSentiment(item.avg_sentiment) }}
        </span>
        <span class="stat-label">SENTIMENT</span>
      </div>
      <div class="stat-box">
        <span class="stat-value" :class="trendTextClass(item)">
          {{ trendArrow(item) }} {{ trendLabel(item) }}
        </span>
        <span class="stat-label">TREND</span>
      </div>
      <div class="stat-box" v-if="item.keywords && item.keywords.length">
        <span class="stat-value stat-keywords">{{ item.keywords.join(', ') }}</span>
        <span class="stat-label">KEYWORDS</span>
      </div>
    </div>

    <!-- Sentiment Over Time -->
    <div class="section-box" v-if="sentimentData.length > 0">
      <h2 class="section-heading">Sentiment Over Time</h2>
      <div class="sentiment-chart">
        <div v-for="day in sentimentData" :key="day.date" class="sentiment-row">
          <span class="sentiment-date">{{ formatShortDate(day.date) }}</span>
          <div class="sentiment-bar-track">
            <div class="sentiment-bar-neg" :style="{ width: negWidth(day.avg_sentiment) + '%' }"></div>
            <div class="sentiment-bar-pos" :style="{ width: posWidth(day.avg_sentiment) + '%' }"></div>
          </div>
          <span class="sentiment-value" :style="{ color: day.avg_sentiment >= 0 ? '#22c55e' : '#ef4444' }">
            {{ day.avg_sentiment > 0 ? '+' : '' }}{{ day.avg_sentiment.toFixed(2) }}
          </span>
          <span class="sentiment-count">{{ day.signal_count }} signals</span>
        </div>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-text">Loading details...</div>

    <!-- Error -->
    <div v-if="error" class="error-text">{{ error }}</div>

    <!-- Signals section -->
    <div v-if="!loading && signals.length > 0" class="signals-section">
      <div class="section-title">SIGNALS (filtered by keywords)</div>
      <div class="signal-feed">
        <div
          v-for="sig in signals"
          :key="sig.id"
          class="signal-card"
          :class="{ 'card-expanded': expandedId === sig.id }"
          @click="toggleExpand(sig.id)"
        >
          <div class="card-header">
            <div class="badge-row">
              <span class="badge badge-source">{{ sig.source }}</span>
              <span class="badge badge-category">{{ sig.category }}</span>
              <span
                class="badge badge-threat"
                :class="threatClass(sig.anomaly_score)"
              >{{ threatLabel(sig.anomaly_score) }}</span>
              <span v-if="sig.country_code" class="badge badge-country-sig">
                {{ countryFlag(sig.country_code) }} {{ sig.country_code }}
              </span>
            </div>
            <span class="card-timestamp">{{ relativeTime(sig.timestamp) }}</span>
          </div>

          <h3 class="card-title">
            <a
              v-if="sig.source_url"
              :href="sig.source_url"
              target="_blank"
              rel="noopener noreferrer"
              class="title-link"
              @click.stop
            >{{ sig.title }}</a>
            <span v-else class="title-text">{{ sig.title }}</span>
          </h3>

          <!-- Entity tags -->
          <div class="entity-tags" v-if="sig.entities">
            <span v-for="o in (sig.entities.organizations || [])" :key="'org-'+o" class="tag tag-org">{{ o }}</span>
            <span v-for="cn in (sig.entities.countries || [])" :key="'co-'+cn" class="tag tag-country-tag">{{ cn }}</span>
          </div>

          <!-- Anomaly bar -->
          <div class="anomaly-row">
            <span class="anomaly-label">ANOMALY</span>
            <div class="anomaly-bar-track">
              <div
                class="anomaly-bar-fill"
                :class="threatClass(sig.anomaly_score)"
                :style="{ width: ((sig.anomaly_score || 0) * 100) + '%' }"
              ></div>
            </div>
            <span class="anomaly-value">{{ ((sig.anomaly_score || 0) * 100).toFixed(0) }}%</span>
          </div>

          <!-- Expanded detail -->
          <div v-if="expandedId === sig.id" class="card-detail">
            <div v-if="sig.summary" class="detail-summary">{{ sig.summary }}</div>
            <div v-else class="detail-no-summary">No summary available.</div>
            <div class="detail-meta">
              <span class="meta-item">
                <span class="meta-label">SENTIMENT</span>
                <span class="meta-value">{{ sig.sentiment_score != null ? sig.sentiment_score.toFixed(2) : '--' }}</span>
              </span>
              <span class="meta-item">
                <span class="meta-label">IMPORTANCE</span>
                <span class="meta-value">{{ sig.importance != null ? sig.importance.toFixed(2) : '--' }}</span>
              </span>
              <span class="meta-item">
                <span class="meta-label">TIMESTAMP</span>
                <span class="meta-value">{{ formatFull(sig.timestamp) }}</span>
              </span>
            </div>
            <div class="detail-actions">
              <a
                v-if="sig.source_url"
                :href="sig.source_url"
                target="_blank"
                rel="noopener noreferrer"
                class="detail-source-link"
                @click.stop
              >Open original source &#8599;</a>
              <button
                class="btn-simulate"
                @click.stop="goToSimulation(sig)"
              >Simulate Impact &rarr;</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="!loading && signals.length === 0 && item.name" class="empty-signals">
      No matching signals found for this watchlist item yet.
    </div>

    <!-- Add Website to Monitor -->
    <div v-if="item.name && !loading" class="section-box monitor-section">
      <h2 class="section-heading">Add Website to Monitor</h2>
      <div class="monitor-form">
        <input
          v-model="newSiteUrl"
          type="url"
          class="form-input"
          placeholder="https://example.com"
          @keyup.enter="addMonitoredSite"
        />
        <button
          class="btn-action-primary btn-monitor-add"
          :disabled="!newSiteUrl.trim() || addingSite"
          @click="addMonitoredSite"
        >
          <span v-if="addingSite">Adding...</span>
          <span v-else>Add Site</span>
        </button>
      </div>
      <div v-if="siteError" class="add-error">{{ siteError }}</div>
      <div v-if="siteSuccess" class="add-success">{{ siteSuccess }}</div>
    </div>

    <!-- Monitored websites -->
    <div v-if="monitoredWebsites.length > 0" class="monitored-section">
      <div class="section-title">MONITORED WEBSITES</div>
      <div class="monitored-list">
        <div v-for="site in monitoredWebsites" :key="site.id || site.url" class="monitored-item">
          <span class="monitored-url">{{ site.url || site.domain }}</span>
          <span class="monitored-meta">
            <span v-if="site.last_checked">last checked {{ relativeTime(site.last_checked) }}</span>
            <span v-if="site.change_count">, {{ site.change_count }} changes</span>
            <span v-if="!site.last_checked && !site.change_count">pending first check</span>
          </span>
        </div>
      </div>
    </div>

    <!-- Alerts Section -->
    <div v-if="item.name && !loading" class="section-box alerts-section">
      <h2 class="section-heading">Alerts</h2>
      <div v-if="alertRule" class="alert-rule-display">
        <div class="alert-rule-row">
          <span class="alert-check">&#10003;</span>
          <span class="alert-rule-text">
            Keyword alert: "{{ (alertRule.keywords || []).join('", "') }}"
            (anomaly > {{ alertRule.threshold }})
          </span>
        </div>
        <div class="alert-controls">
          <div class="alert-threshold-control">
            <label class="form-label">THRESHOLD</label>
            <input
              v-model.number="editThreshold"
              type="number"
              class="form-input form-input-sm"
              min="0"
              max="1"
              step="0.05"
            />
            <button
              class="btn-action-sm"
              :disabled="editThreshold === alertRule.threshold || updatingAlert"
              @click="updateThreshold"
            >Update</button>
          </div>
          <div class="alert-keyword-control">
            <label class="form-label">ADD KEYWORD</label>
            <div class="keyword-add-row">
              <input
                v-model="newAlertKeyword"
                type="text"
                class="form-input form-input-sm"
                placeholder="e.g. coalition"
                @keyup.enter="addAlertKeyword"
              />
              <button
                class="btn-action-sm"
                :disabled="!newAlertKeyword.trim() || updatingAlert"
                @click="addAlertKeyword"
              >Add</button>
            </div>
          </div>
        </div>
        <div class="alert-keywords-list">
          <span v-for="kw in (alertRule.keywords || [])" :key="kw" class="alert-keyword-tag">
            {{ kw }}
            <button class="keyword-remove" @click="removeAlertKeyword(kw)">&times;</button>
          </span>
        </div>
        <div v-if="alertError" class="add-error">{{ alertError }}</div>
        <div v-if="alertSuccess" class="add-success">{{ alertSuccess }}</div>
      </div>
      <div v-else class="alert-rule-none">No alert rule configured for this item.</div>
    </div>

    <!-- Bottom actions -->
    <div v-if="item.name && !loading" class="bottom-actions">
      <button class="btn-action-primary" @click="goToSimulationGeneral">
        Simulate Impact &rarr;
      </button>
      <button class="btn-action-secondary" @click="exportCSV">
        Export CSV &rarr;
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  getWatchlistItem, getWatchlistSignals, getWatchlistSentiment,
  deleteWatchlistItem, updateWatchlistItem,
  discoverSite, listAlertRules, updateAlertRule,
} from '../api/intelligence'
import { ArrowLeft } from 'lucide-vue-next'

const props = defineProps({
  id: { type: [String, Number], required: true }
})

const router = useRouter()
const route = useRoute()

const loading = ref(true)
const error = ref('')
const item = ref({})
const signals = ref([])
const sentimentData = ref([])
const expandedId = ref(null)

// Monitor website state
const newSiteUrl = ref('')
const addingSite = ref(false)
const siteError = ref('')
const siteSuccess = ref('')

// Alert rule state
const alertRule = ref(null)
const editThreshold = ref(0.7)
const newAlertKeyword = ref('')
const updatingAlert = ref(false)
const alertError = ref('')
const alertSuccess = ref('')

const monitoredWebsites = computed(() => {
  const sites = item.value.monitored_sites || []
  const webUrls = item.value.websites || []
  // Merge: show monitored_sites objects plus any plain URL strings from websites array
  const seen = new Set(sites.map(s => s.url || s.domain))
  const extra = webUrls
    .filter(u => typeof u === 'string' && !seen.has(u))
    .map(u => ({ url: u }))
  return [...sites, ...extra]
})

const itemId = props.id || route.params.id

const toggleExpand = (id) => {
  expandedId.value = expandedId.value === id ? null : id
}

const countryFlag = (code) => {
  if (!code || code.length !== 2) return ''
  const offset = 0x1F1E6
  return String.fromCodePoint(
    code.charCodeAt(0) - 65 + offset,
    code.charCodeAt(1) - 65 + offset
  )
}

const relativeTime = (ts) => {
  if (!ts) return '--'
  const now = Date.now()
  const then = new Date(ts).getTime()
  const diff = Math.max(0, now - then)
  const seconds = Math.floor(diff / 1000)
  if (seconds < 60) return `${seconds}s ago`
  const minutes = Math.floor(seconds / 60)
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days}d ago`
  return new Date(ts).toLocaleDateString()
}

const formatFull = (ts) => {
  if (!ts) return '--'
  return new Date(ts).toLocaleString()
}

const threatLabel = (score) => {
  if (score > 0.8) return 'CRITICAL'
  if (score > 0.6) return 'HIGH'
  if (score > 0.4) return 'ELEVATED'
  return 'LOW'
}

const threatClass = (score) => {
  if (score > 0.8) return 'threat-critical'
  if (score > 0.6) return 'threat-high'
  if (score > 0.4) return 'threat-elevated'
  return 'threat-low'
}

const formatSentiment = (val) => {
  if (val == null) return '--'
  const num = parseFloat(val)
  if (isNaN(num)) return '--'
  return (num >= 0 ? '+' : '') + num.toFixed(1)
}

const sentimentClass = (val) => {
  if (val == null) return ''
  const num = parseFloat(val)
  if (isNaN(num)) return ''
  if (num > 0.1) return 'sentiment-positive'
  if (num < -0.1) return 'sentiment-negative'
  return 'sentiment-neutral'
}

const trendArrow = (item) => {
  const trend = item.trend ?? item.signal_trend ?? 0
  if (trend > 0) return '\u25B2'
  if (trend < 0) return '\u25BC'
  return '\u25AC'
}

const trendLabel = (item) => {
  const trend = item.trend ?? item.signal_trend ?? 0
  if (trend > 0) return 'Rising'
  if (trend < 0) return 'Declining'
  return 'Stable'
}

const trendTextClass = (item) => {
  const trend = item.trend ?? item.signal_trend ?? 0
  if (trend > 0) return 'trend-up'
  if (trend < 0) return 'trend-down'
  return 'trend-flat'
}

const formatShortDate = (dateStr) => {
  if (!dateStr) return '--'
  const d = new Date(dateStr)
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

const negWidth = (val) => val < 0 ? Math.abs(val) * 50 : 0
const posWidth = (val) => val > 0 ? val * 50 : 0

const goToSimulation = (sig) => {
  router.push({
    path: '/simulate',
    query: {
      signal_id: sig.id,
      title: sig.title || '',
      context: sig.summary || '',
    }
  })
}

const goToSimulationGeneral = () => {
  router.push({
    path: '/simulate',
    query: {
      title: `Impact analysis: ${item.value.name}`,
      context: `Watchlist item: ${item.value.name} (${item.value.item_type}). Keywords: ${(item.value.keywords || []).join(', ')}`,
    }
  })
}

const exportCSV = () => {
  const params = new URLSearchParams()
  params.set('limit', '500')
  if (item.value.keywords && item.value.keywords.length) {
    params.set('keywords', item.value.keywords.join(','))
  }
  window.open(`/api/watchlist/${itemId}/signals/export?${params.toString()}`, '_blank')
}

const confirmDelete = async () => {
  if (!confirm(`Delete "${item.value.name}" from your watchlist?`)) return
  try {
    await deleteWatchlistItem(itemId)
    router.push('/watchlist')
  } catch (e) {
    error.value = 'Failed to delete: ' + (e.response?.data?.error || e.message)
  }
}

const addMonitoredSite = async () => {
  const url = newSiteUrl.value.trim()
  if (!url) return
  addingSite.value = true
  siteError.value = ''
  siteSuccess.value = ''
  try {
    // 1. Create the monitored site via POST /api/sites/
    await discoverSite(url, 50)
    // 2. Add URL to watchlist item's websites array
    const currentWebsites = item.value.websites || []
    if (!currentWebsites.includes(url)) {
      const updatedWebsites = [...currentWebsites, url]
      await updateWatchlistItem(itemId, { websites: updatedWebsites })
      item.value.websites = updatedWebsites
    }
    siteSuccess.value = `Added ${url} to monitoring`
    newSiteUrl.value = ''
    // Refresh data to get updated monitored_sites
    setTimeout(() => { siteSuccess.value = '' }, 3000)
  } catch (e) {
    siteError.value = 'Failed to add site: ' + (e.response?.data?.error || e.message)
  } finally {
    addingSite.value = false
  }
}

const loadAlertRule = async () => {
  try {
    const res = await listAlertRules()
    const d = res.data || res
    const rules = Array.isArray(d) ? d : (d.data || d.rules || [])
    // Find the alert rule for this watchlist item by name pattern
    const itemName = item.value.name
    const match = rules.find(r =>
      r.name === `Watchlist: ${itemName}` ||
      (r.keywords && r.keywords.includes(itemName))
    )
    if (match) {
      alertRule.value = match
      editThreshold.value = match.threshold ?? 0.7
    }
  } catch (e) {
    // Non-critical, silently fail
    alertRule.value = null
  }
}

const updateThreshold = async () => {
  if (!alertRule.value) return
  updatingAlert.value = true
  alertError.value = ''
  alertSuccess.value = ''
  try {
    const res = await updateAlertRule(alertRule.value.id, {
      threshold: editThreshold.value,
    })
    const d = res.data || res
    alertRule.value = d.data || d
    alertSuccess.value = 'Threshold updated'
    setTimeout(() => { alertSuccess.value = '' }, 3000)
  } catch (e) {
    alertError.value = 'Failed to update threshold: ' + (e.response?.data?.error || e.message)
  } finally {
    updatingAlert.value = false
  }
}

const addAlertKeyword = async () => {
  const kw = newAlertKeyword.value.trim()
  if (!kw || !alertRule.value) return
  updatingAlert.value = true
  alertError.value = ''
  alertSuccess.value = ''
  try {
    const currentKeywords = alertRule.value.keywords || []
    if (currentKeywords.includes(kw)) {
      alertError.value = 'Keyword already exists'
      updatingAlert.value = false
      return
    }
    const updatedKeywords = [...currentKeywords, kw]
    const res = await updateAlertRule(alertRule.value.id, {
      keywords: updatedKeywords,
    })
    const d = res.data || res
    alertRule.value = d.data || d
    newAlertKeyword.value = ''
    alertSuccess.value = `Added keyword "${kw}"`
    setTimeout(() => { alertSuccess.value = '' }, 3000)
  } catch (e) {
    alertError.value = 'Failed to add keyword: ' + (e.response?.data?.error || e.message)
  } finally {
    updatingAlert.value = false
  }
}

const removeAlertKeyword = async (kw) => {
  if (!alertRule.value) return
  updatingAlert.value = true
  alertError.value = ''
  alertSuccess.value = ''
  try {
    const updatedKeywords = (alertRule.value.keywords || []).filter(k => k !== kw)
    const res = await updateAlertRule(alertRule.value.id, {
      keywords: updatedKeywords,
    })
    const d = res.data || res
    alertRule.value = d.data || d
    alertSuccess.value = `Removed keyword "${kw}"`
    setTimeout(() => { alertSuccess.value = '' }, 3000)
  } catch (e) {
    alertError.value = 'Failed to remove keyword: ' + (e.response?.data?.error || e.message)
  } finally {
    updatingAlert.value = false
  }
}

const loadData = async () => {
  loading.value = true
  error.value = ''
  try {
    const [itemRes, signalsRes, sentimentRes] = await Promise.all([
      getWatchlistItem(itemId),
      getWatchlistSignals(itemId, { limit: 20 }),
      getWatchlistSentiment(itemId).catch(() => ({ data: [] })),
    ])
    const d = itemRes.data || itemRes
    item.value = d.data || d
    const s = signalsRes.data || signalsRes
    signals.value = Array.isArray(s) ? s : (s.items || s.results || [])
    const sd = sentimentRes.data || sentimentRes
    sentimentData.value = Array.isArray(sd) ? sd : (sd.data || [])
    // Load alert rule after item is loaded
    await loadAlertRule()
  } catch (e) {
    error.value = 'Failed to load watchlist item: ' + (e.response?.data?.error || e.message)
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.watchlist-detail {
  font-family: 'Space Grotesk', system-ui, sans-serif;
  max-width: 900px;
  background: #0a0a0a;
  color: #e8e8e8;
}

/* ── Header ── */
.detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.btn-back {
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  padding: 6px 12px;
  background: transparent;
  border: 1px solid #333;
  color: #999;
  cursor: pointer;
  transition: all 0.15s;
  border-radius: 2px;
  flex-shrink: 0;
}

.btn-back:hover {
  border-color: #FF4500;
  color: #FF4500;
}

.header-info {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.detail-name {
  font-size: 1.5rem;
  font-weight: 600;
  color: #FFFFFF;
  margin: 0;
}

.header-badges {
  display: flex;
  gap: 8px;
}

.header-actions {
  flex-shrink: 0;
}

.btn-action {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  padding: 6px 14px;
  background: transparent;
  border: 1px solid #333;
  color: #999;
  cursor: pointer;
  transition: all 0.15s;
  border-radius: 2px;
}

.btn-danger {
  border-color: #F44336;
  color: #F44336;
}

.btn-danger:hover {
  background: rgba(244, 67, 54, 0.12);
  color: #EF5350;
}

/* ── Stats row ── */
.stats-row {
  display: flex;
  gap: 24px;
  margin-bottom: 28px;
  padding: 16px 20px;
  background: #141414;
  border: 1px solid #222;
  border-radius: 2px;
  flex-wrap: wrap;
}

.stat-box {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.1rem;
  font-weight: 600;
  color: #FFFFFF;
}

.stat-keywords {
  font-size: 0.75rem;
  font-weight: 400;
  color: #888;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stat-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  color: #666;
  letter-spacing: 1px;
}

.sentiment-positive { color: #4CAF50; }
.sentiment-negative { color: #F44336; }
.sentiment-neutral { color: #999; }
.trend-up { color: #F44336; }
.trend-down { color: #4CAF50; }
.trend-flat { color: #666; }

/* ── Sentiment Over Time ── */
.section-box {
  margin-bottom: 28px;
  padding: 20px;
  background: #141414;
  border: 1px solid #222;
  border-radius: 2px;
}

.section-heading {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: #666;
  margin: 0 0 16px 0;
  font-weight: 400;
}

.sentiment-chart {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sentiment-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.sentiment-date {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.72rem;
  color: #888;
  min-width: 56px;
  text-align: right;
}

.sentiment-bar-track {
  flex: 1;
  max-width: 400px;
  height: 14px;
  background: #1a1a1a;
  border: 1px solid #2a2a2a;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  border-radius: 1px;
}

.sentiment-bar-neg {
  position: absolute;
  right: 50%;
  height: 100%;
  background: #ef4444;
  opacity: 0.7;
  transition: width 0.4s ease;
  border-radius: 1px 0 0 1px;
}

.sentiment-bar-pos {
  position: absolute;
  left: 50%;
  height: 100%;
  background: #22c55e;
  opacity: 0.7;
  transition: width 0.4s ease;
  border-radius: 0 1px 1px 0;
}

.sentiment-bar-track::after {
  content: '';
  position: absolute;
  left: 50%;
  top: 0;
  bottom: 0;
  width: 1px;
  background: #444;
  z-index: 1;
}

.sentiment-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  min-width: 48px;
  text-align: right;
}

.sentiment-count {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  color: #555;
  min-width: 70px;
}

/* ── Badges ── */
.badge {
  display: inline-block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  padding: 2px 8px;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  border-radius: 2px;
}

.badge-type {
  border: 1px solid #FF4500;
  color: #FF4500;
  background: rgba(255, 69, 0, 0.08);
}

.badge-country {
  border: 1px solid #555;
  color: #ccc;
  background: #1a1a1a;
}

/* ── Sections ── */
.section-title {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: #666;
  margin-bottom: 16px;
}

/* ── Signal cards (reuses SignalsView styling) ── */
.signals-section {
  margin-bottom: 28px;
}

.signal-feed {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.signal-card {
  background: #111;
  border: 1px solid #222;
  border-left: 4px solid #333;
  padding: 16px 20px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
  border-radius: 2px;
}

.signal-card:hover {
  border-color: #444;
  border-left-color: #FF4500;
  background: #141414;
}

.signal-card.card-expanded {
  border-left-color: #FF4500;
  background: #0f0f0f;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  flex-wrap: wrap;
  gap: 8px;
}

.badge-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}

.badge-source {
  border: 1px solid #444;
  color: #aaa;
  background: #1a1a1a;
}

.badge-category {
  border: 1px solid #FF4500;
  color: #FF4500;
  background: rgba(255, 69, 0, 0.08);
}

.badge-country-sig {
  border: 1px solid #555;
  color: #ccc;
  background: #1a1a1a;
}

.badge-threat {
  font-weight: 700;
  border: 1px solid;
}

.badge-threat.threat-critical {
  border-color: #F44336;
  color: #F44336;
  background: rgba(244, 67, 54, 0.12);
}

.badge-threat.threat-high {
  border-color: #FF9800;
  color: #FF9800;
  background: rgba(255, 152, 0, 0.10);
}

.badge-threat.threat-elevated {
  border-color: #FFC107;
  color: #FFC107;
  background: rgba(255, 193, 7, 0.08);
}

.badge-threat.threat-low {
  border-color: #4CAF50;
  color: #4CAF50;
  background: rgba(76, 175, 80, 0.08);
}

.card-timestamp {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #666;
  white-space: nowrap;
}

.card-title {
  font-size: 1rem;
  font-weight: 500;
  line-height: 1.45;
  margin: 0 0 12px 0;
}

.title-link {
  color: #e8e8e8;
  text-decoration: none;
  transition: color 0.15s;
}

.title-link:hover {
  color: #FF4500;
  text-decoration: underline;
}

.title-text {
  color: #e8e8e8;
}

.entity-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}

.tag {
  display: inline-block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  padding: 2px 7px;
  border-radius: 10px;
  letter-spacing: 0.3px;
}

.tag-org {
  background: rgba(158, 158, 158, 0.12);
  border: 1px solid rgba(158, 158, 158, 0.35);
  color: #BDBDBD;
}

.tag-country-tag {
  background: rgba(76, 175, 80, 0.12);
  border: 1px solid rgba(76, 175, 80, 0.35);
  color: #66BB6A;
}

.anomaly-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.anomaly-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  color: #666;
  letter-spacing: 1px;
  min-width: 56px;
}

.anomaly-bar-track {
  flex: 1;
  max-width: 200px;
  height: 6px;
  background: #1a1a1a;
  border: 1px solid #2a2a2a;
  overflow: hidden;
  border-radius: 1px;
}

.anomaly-bar-fill {
  height: 100%;
  transition: width 0.3s ease;
  border-radius: 1px;
}

.anomaly-bar-fill.threat-critical { background: #F44336; }
.anomaly-bar-fill.threat-high { background: #FF9800; }
.anomaly-bar-fill.threat-elevated { background: #FFC107; }
.anomaly-bar-fill.threat-low { background: #4CAF50; }

.anomaly-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #888;
  min-width: 32px;
  text-align: right;
}

.card-detail {
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px solid #222;
}

.detail-summary {
  font-size: 0.9rem;
  line-height: 1.6;
  color: #bbb;
  margin-bottom: 14px;
}

.detail-no-summary {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: #555;
  font-style: italic;
  margin-bottom: 14px;
}

.detail-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  margin-bottom: 14px;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.meta-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  color: #555;
  letter-spacing: 1px;
}

.meta-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: #ccc;
}

.detail-actions {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.detail-source-link {
  display: inline-block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #FF4500;
  text-decoration: none;
  padding: 4px 0;
  transition: opacity 0.15s;
}

.detail-source-link:hover {
  opacity: 0.8;
  text-decoration: underline;
}

.btn-simulate {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  padding: 5px 14px;
  background: transparent;
  border: 1px solid #FF4500;
  color: #FF4500;
  cursor: pointer;
  transition: all 0.15s;
  border-radius: 2px;
  letter-spacing: 0.3px;
  white-space: nowrap;
}

.btn-simulate:hover {
  background: rgba(255, 69, 0, 0.12);
  color: #FF6A33;
  border-color: #FF6A33;
}

/* ── Empty signals ── */
.empty-signals {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  color: #555;
  padding: 30px 0;
  font-style: italic;
}

/* ── Monitored websites ── */
.monitored-section {
  margin-top: 28px;
  padding-top: 20px;
  border-top: 1px solid #222;
}

.monitored-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.monitored-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: #141414;
  border: 1px solid #222;
  border-radius: 2px;
}

.monitored-item::before {
  content: '\2022';
  color: #FF4500;
  font-size: 1.2rem;
  flex-shrink: 0;
}

.monitored-url {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: #ccc;
}

.monitored-meta {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #666;
}

/* ── Bottom actions ── */
.bottom-actions {
  display: flex;
  gap: 16px;
  margin-top: 32px;
  padding-top: 20px;
  border-top: 1px solid #222;
}

.btn-action-primary {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  padding: 10px 20px;
  background: transparent;
  border: 1px solid #FF4500;
  color: #FF4500;
  cursor: pointer;
  transition: all 0.15s;
  border-radius: 2px;
  letter-spacing: 0.3px;
}

.btn-action-primary:hover {
  background: rgba(255, 69, 0, 0.12);
  color: #FF6A33;
  border-color: #FF6A33;
}

.btn-action-secondary {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  padding: 10px 20px;
  background: transparent;
  border: 1px solid #4CAF50;
  color: #4CAF50;
  cursor: pointer;
  transition: all 0.15s;
  border-radius: 2px;
}

.btn-action-secondary:hover {
  background: rgba(76, 175, 80, 0.12);
  color: #66BB6A;
  border-color: #66BB6A;
}

/* ── Status states ── */
.loading-text {
  font-family: 'JetBrains Mono', monospace;
  color: #999;
  font-size: 0.9rem;
}

.error-text {
  font-family: 'JetBrains Mono', monospace;
  color: #F44336;
  font-size: 0.85rem;
  margin-top: 15px;
}

/* ── Monitor Website ── */
.monitor-section {
  margin-bottom: 28px;
}

.monitor-form {
  display: flex;
  gap: 10px;
  align-items: center;
}

.monitor-form .form-input {
  flex: 1;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  padding: 8px 12px;
  background: #0a0a0a;
  border: 1px solid #333;
  color: #e8e8e8;
  outline: none;
  border-radius: 2px;
  box-sizing: border-box;
}

.monitor-form .form-input:focus {
  border-color: #FF4500;
}

.btn-monitor-add {
  white-space: nowrap;
  padding: 8px 16px !important;
  font-size: 0.78rem !important;
}

.btn-monitor-add:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.add-error {
  margin-top: 8px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.78rem;
  color: #F44336;
}

.add-success {
  margin-top: 8px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.78rem;
  color: #4CAF50;
}

/* ── Alerts Section ── */
.alerts-section {
  margin-bottom: 28px;
}

.alert-rule-display {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.alert-rule-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.alert-check {
  color: #4CAF50;
  font-size: 1rem;
  font-weight: 700;
}

.alert-rule-text {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: #ccc;
}

.alert-controls {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.alert-threshold-control,
.alert-keyword-control {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  color: #666;
  letter-spacing: 1px;
}

.form-input-sm {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.78rem;
  padding: 6px 10px;
  background: #0a0a0a;
  border: 1px solid #333;
  color: #e8e8e8;
  outline: none;
  border-radius: 2px;
  width: 140px;
  box-sizing: border-box;
}

.form-input-sm:focus {
  border-color: #FF4500;
}

.keyword-add-row {
  display: flex;
  gap: 8px;
  align-items: center;
}

.btn-action-sm {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.72rem;
  padding: 5px 12px;
  background: transparent;
  border: 1px solid #FF4500;
  color: #FF4500;
  cursor: pointer;
  transition: all 0.15s;
  border-radius: 2px;
  white-space: nowrap;
}

.btn-action-sm:hover:not(:disabled) {
  background: rgba(255, 69, 0, 0.12);
  color: #FF6A33;
  border-color: #FF6A33;
}

.btn-action-sm:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.alert-keywords-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.alert-keyword-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  padding: 3px 10px;
  background: rgba(255, 69, 0, 0.08);
  border: 1px solid #FF4500;
  color: #FF4500;
  border-radius: 12px;
}

.keyword-remove {
  background: none;
  border: none;
  color: #FF4500;
  cursor: pointer;
  font-size: 0.9rem;
  padding: 0 2px;
  line-height: 1;
  opacity: 0.6;
  transition: opacity 0.15s;
}

.keyword-remove:hover {
  opacity: 1;
}

.alert-rule-none {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: #555;
  font-style: italic;
}
</style>
