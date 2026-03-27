<template>
  <div class="signals-view">
    <h1 class="page-title">Signals</h1>

    <!-- Filter bar -->
    <div class="filter-bar">
      <select v-model="filters.source" class="filter-select">
        <option value="">All Sources</option>
        <option v-for="s in sourceOptions" :key="s" :value="s">{{ s }}</option>
      </select>
      <select v-model="filters.category" class="filter-select">
        <option value="">All Categories</option>
        <option v-for="c in categoryOptions" :key="c" :value="c">{{ c }}</option>
      </select>
      <select v-model="filters.country" class="filter-select">
        <option value="">All Countries</option>
        <option v-for="c in countryOptions" :key="c.code" :value="c.code">{{ c.label }}</option>
      </select>
      <select v-model="sortBy" class="filter-select">
        <option value="timestamp">Latest</option>
        <option value="anomaly">Highest Threat</option>
        <option value="importance">Most Important</option>
      </select>
      <button class="btn-clear" @click="clearFilters">Clear</button>
      <button class="btn-export" @click="exportCSV">Export CSV</button>
    </div>

    <div v-if="loading" class="loading-text">Loading signals...</div>

    <div v-else-if="signals.length === 0" class="empty-state">No signals detected</div>

    <template v-else>
      <!-- Card feed -->
      <div class="signal-feed">
        <div
          v-for="sig in signals"
          :key="sig.id"
          class="signal-card-wrapper"
        >
          <!-- Site monitor alert banner -->
          <div v-if="isSiteMonitorAlert(sig)" class="site-monitor-banner">
            <span class="site-monitor-banner__icon">&#9888;</span>
            <span class="site-monitor-banner__text">
              Major change detected on <strong>{{ extractDomain(sig.source_url) || 'monitored site' }}</strong>. Simulate the impact?
            </span>
            <button class="btn-simulate btn-simulate--small" @click.stop="simulateImpact(sig)">
              Simulate &rarr;
            </button>
          </div>
          <div
            class="signal-card"
            :class="{ 'card-expanded': expandedId === sig.id, 'card-site-monitor': isSiteMonitorAlert(sig) }"
            @click="toggleExpand(sig.id)"
          >
          <!-- Card header: badges row -->
          <div class="card-header">
            <div class="badge-row">
              <span class="badge badge-source">{{ sig.source }}</span>
              <span class="badge badge-category">{{ sig.category }}</span>
              <span
                class="badge badge-threat"
                :class="threatClass(sig.anomaly_score)"
              >{{ threatLabel(sig.anomaly_score) }}</span>
              <span v-if="sig.country_code" class="badge badge-country">
                {{ countryFlag(sig.country_code) }} {{ sig.country_code }}
              </span>
            </div>
            <div class="timestamp-group">
              <span v-if="detectionSpeed(sig) != null" class="badge badge-detection" :class="detectionSpeedClass(sig)">&#9889; {{ detectionSpeed(sig) }}m</span>
              <span class="card-timestamp">{{ relativeTime(sig.timestamp) }}</span>
            </div>
          </div>

          <!-- Title: clickable link to source -->
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
            <span v-for="t in (sig.entities.tickers || [])" :key="'tk-'+t" class="tag tag-ticker">{{ t }}</span>
            <span v-for="c in (sig.entities.cves || [])" :key="'cve-'+c" class="tag tag-cve">{{ c }}</span>
            <span v-for="o in (sig.entities.organizations || [])" :key="'org-'+o" class="tag tag-org">{{ o }}</span>
            <span v-for="cn in (sig.entities.countries || [])" :key="'co-'+cn" class="tag tag-country">{{ cn }}</span>
          </div>

          <!-- Anomaly score bar -->
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
                <span class="meta-label">SIGNAL TYPE</span>
                <span class="meta-value">{{ sig.signal_type || '--' }}</span>
              </span>
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
                :disabled="analysisLoading === sig.id"
                @click.stop="simulateImpact(sig)"
              >
                <span v-if="analysisLoading === sig.id">Analyzing...</span>
                <span v-else-if="analysisResults[sig.id]">Hide Analysis</span>
                <span v-else>Simulate Impact &rarr;</span>
              </button>
              <button
                class="btn-simulate btn-simulate--secondary"
                @click.stop="goToFullSimulation(sig)"
              >Run Full Simulation &rarr;</button>
            </div>

            <!-- AI Impact Analysis panel -->
            <div v-if="analysisLoading === sig.id" class="analysis-panel" @click.stop>
              <div class="analysis-loading">
                <span class="analysis-spinner"></span>
                Generating impact analysis...
              </div>
            </div>

            <div v-if="analysisError[sig.id]" class="analysis-panel analysis-error" @click.stop>
              {{ analysisError[sig.id] }}
            </div>

            <div v-if="analysisResults[sig.id]" class="analysis-panel" @click.stop>
              <h4 class="analysis-heading">AI Impact Analysis</h4>
              <div class="analysis-body" v-html="formatAnalysis(analysisResults[sig.id])"></div>
            </div>
          </div>
        </div>
        </div>
      </div>

      <!-- Pagination -->
      <div class="pagination">
        <button class="btn-page" :disabled="page <= 1" @click="page--; loadSignals()">
          &larr; Prev
        </button>
        <span class="page-info">Page {{ page }} of {{ totalPages }}</span>
        <button class="btn-page" :disabled="page >= totalPages" @click="page++; loadSignals()">
          Next &rarr;
        </button>
      </div>
    </template>

    <div v-if="error" class="error-text">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listSignals, analyzeSignal } from '../api/intelligence'

const router = useRouter()

const loading = ref(true)
const error = ref('')
const signals = ref([])
const page = ref(1)
const totalPages = ref(1)
const perPage = 20
const expandedId = ref(null)
const sortBy = ref('timestamp')
const analysisLoading = ref(null)   // signal id currently being analyzed
const analysisResults = ref({})     // { [signalId]: analysisText }
const analysisError = ref({})

const sourceOptions = ['rss', 'scrapling', 'usgs', 'acled', 'nasa_firms', 'finnhub']
const categoryOptions = ['politics', 'economy', 'finance', 'healthcare', 'climate', 'crime', 'cyber', 'geopolitical', 'other']
const countryOptions = [
  { code: 'US', label: 'US - United States' },
  { code: 'GB', label: 'GB - United Kingdom' },
  { code: 'CN', label: 'CN - China' },
  { code: 'RU', label: 'RU - Russia' },
  { code: 'IN', label: 'IN - India' },
  { code: 'JP', label: 'JP - Japan' },
  { code: 'DE', label: 'DE - Germany' },
  { code: 'FR', label: 'FR - France' },
  { code: 'BR', label: 'BR - Brazil' },
  { code: 'AU', label: 'AU - Australia' },
  { code: 'CA', label: 'CA - Canada' },
  { code: 'KR', label: 'KR - South Korea' },
  { code: 'IL', label: 'IL - Israel' },
  { code: 'IR', label: 'IR - Iran' },
  { code: 'SA', label: 'SA - Saudi Arabia' },
  { code: 'UA', label: 'UA - Ukraine' },
  { code: 'TW', label: 'TW - Taiwan' },
  { code: 'TR', label: 'TR - Turkey' },
  { code: 'NG', label: 'NG - Nigeria' },
  { code: 'ZA', label: 'ZA - South Africa' },
  { code: 'MX', label: 'MX - Mexico' },
  { code: 'PK', label: 'PK - Pakistan' },
  { code: 'EG', label: 'EG - Egypt' },
  { code: 'ID', label: 'ID - Indonesia' },
  { code: 'PL', label: 'PL - Poland' },
]

const filters = reactive({
  source: '',
  category: '',
  country: '',
})

const toggleExpand = (id) => {
  expandedId.value = expandedId.value === id ? null : id
}

// Threat level helpers
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

// Country code to flag emoji
const countryFlag = (code) => {
  if (!code || code.length !== 2) return ''
  const offset = 0x1F1E6
  return String.fromCodePoint(
    code.charCodeAt(0) - 65 + offset,
    code.charCodeAt(1) - 65 + offset
  )
}

// Relative time formatter ("2h ago", "5m ago")
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

const simulateImpact = async (sig) => {
  // If already analyzed, toggle visibility by clearing the result
  if (analysisResults.value[sig.id]) {
    delete analysisResults.value[sig.id]
    return
  }

  analysisLoading.value = sig.id
  analysisError.value[sig.id] = ''
  try {
    const res = await analyzeSignal(sig.id)
    const d = res.data || res
    analysisResults.value[sig.id] = d.analysis || d.data?.analysis || 'No analysis returned.'
  } catch (e) {
    analysisError.value[sig.id] = 'Analysis failed: ' + (e.response?.data?.error || e.message)
  } finally {
    analysisLoading.value = null
  }
}

const goToFullSimulation = (sig) => {
  const query = {
    signal_id: sig.id,
    title: sig.title || '',
  }
  if (sig.summary) {
    query.context = `${sig.summary} | Category: ${sig.category || 'unknown'} | Source: ${sig.source || 'unknown'}`
  }
  router.push({ path: '/simulate', query })
}

const extractDomain = (url) => {
  if (!url) return null
  try {
    return new URL(url).hostname.replace('www.', '')
  } catch {
    return null
  }
}

const formatAnalysis = (text) => {
  if (!text) return ''
  // Convert markdown-ish numbered sections into styled HTML
  return text
    .replace(/\n/g, '<br>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/(\d+)\.\s+(IMPACT ASSESSMENT|PROBABILITY|TIMELINE|AFFECTED SECTORS|RECOMMENDED ACTIONS):/gi,
      '<br><span class="analysis-section-label">$1. $2:</span>')
}

// Detection speed: time between source publication and our ingestion
const detectionSpeed = (sig) => {
  const pub = sig.raw_data_json?.published || sig.raw_data_json?.published_at
  if (!pub) return null
  const pubTime = new Date(pub).getTime()
  const ingestTime = new Date(sig.timestamp).getTime()
  const diffMin = Math.round((ingestTime - pubTime) / 60000)
  if (diffMin < 0 || diffMin > 1440) return null // ignore bad data
  return diffMin
}

const detectionSpeedClass = (sig) => {
  const mins = detectionSpeed(sig)
  if (mins == null) return ''
  if (mins <= 5) return 'detection-fast'
  if (mins <= 30) return 'detection-medium'
  return 'detection-slow'
}

const isSiteMonitorAlert = (sig) => {
  return sig.source === 'site_monitor' && (sig.anomaly_score || 0) > 0.6
}

const exportCSV = () => {
  const params = new URLSearchParams()
  params.set('limit', '500')
  if (filters.source) params.set('source', filters.source)
  if (filters.category) params.set('categories', filters.category)
  if (filters.country) params.set('country_code', filters.country)
  window.open('/api/signals/export?' + params.toString(), '_blank')
}

const clearFilters = () => {
  filters.source = ''
  filters.category = ''
  filters.country = ''
  page.value = 1
}

const loadSignals = async () => {
  loading.value = true
  error.value = ''
  try {
    const params = { limit: perPage, offset: (page.value - 1) * perPage }
    if (filters.source) params.source = filters.source
    if (filters.category) params.category = filters.category
    if (filters.country) params.country = filters.country
    if (sortBy.value) params.sort = sortBy.value

    const res = await listSignals(params)
    const d = res.data || res
    signals.value = Array.isArray(d) ? d : (d.items || d.results || [])
    const total = d.total ?? signals.value.length
    totalPages.value = Math.max(1, Math.ceil(total / perPage))
  } catch (e) {
    error.value = 'Failed to load signals: ' + e.message
  } finally {
    loading.value = false
  }
}

watch(filters, () => {
  page.value = 1
  loadSignals()
})

watch(sortBy, () => {
  page.value = 1
  loadSignals()
})

onMounted(loadSignals)
</script>

<style scoped>
.signals-view {
  font-family: 'Space Grotesk', system-ui, sans-serif;
  max-width: 900px;
  background: #0a0a0a;
  color: #e8e8e8;
}

.page-title {
  font-size: 1.8rem;
  font-weight: 600;
  margin-bottom: 24px;
  color: #FFFFFF;
}

/* ── Filter bar ── */
.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.filter-select {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  padding: 6px 12px;
  background: #111;
  border: 1px solid #333;
  color: #CCC;
  outline: none;
  cursor: pointer;
  min-width: 140px;
  border-radius: 2px;
}

.filter-select:focus {
  border-color: #FF4500;
}

.btn-clear {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  padding: 6px 14px;
  background: transparent;
  border: 1px solid #333;
  color: #999;
  cursor: pointer;
  transition: all 0.15s;
  border-radius: 2px;
}

.btn-clear:hover {
  border-color: #FF4500;
  color: #FF4500;
}

.btn-export {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  padding: 6px 14px;
  background: transparent;
  border: 1px solid #4CAF50;
  color: #4CAF50;
  cursor: pointer;
  transition: all 0.15s;
  border-radius: 2px;
  margin-left: auto;
}

.btn-export:hover {
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

.empty-state {
  color: #666;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  padding: 30px 0;
}

/* ── Card feed ── */
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

/* ── Card header ── */
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

.badge {
  display: inline-block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  padding: 2px 8px;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  border-radius: 2px;
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

.badge-country {
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

.timestamp-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.card-timestamp {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #666;
  white-space: nowrap;
}

/* ── Detection speed badge ── */
.badge-detection {
  font-size: 0.6rem;
  padding: 1px 6px;
  border-radius: 2px;
  font-weight: 700;
  white-space: nowrap;
}

.badge-detection.detection-fast {
  border: 1px solid #4CAF50;
  color: #4CAF50;
  background: rgba(76, 175, 80, 0.1);
}

.badge-detection.detection-medium {
  border: 1px solid #FFC107;
  color: #FFC107;
  background: rgba(255, 193, 7, 0.08);
}

.badge-detection.detection-slow {
  border: 1px solid #FF9800;
  color: #FF9800;
  background: rgba(255, 152, 0, 0.08);
}

/* ── Entity tags ── */
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
  cursor: pointer;
  transition: opacity 0.15s;
}

.tag:hover {
  opacity: 0.8;
}

.tag-ticker {
  background: rgba(33, 150, 243, 0.12);
  border: 1px solid rgba(33, 150, 243, 0.35);
  color: #42A5F5;
}

.tag-cve {
  background: rgba(244, 67, 54, 0.12);
  border: 1px solid rgba(244, 67, 54, 0.35);
  color: #EF5350;
}

.tag-org {
  background: rgba(158, 158, 158, 0.12);
  border: 1px solid rgba(158, 158, 158, 0.35);
  color: #BDBDBD;
}

.tag-country {
  background: rgba(76, 175, 80, 0.12);
  border: 1px solid rgba(76, 175, 80, 0.35);
  color: #66BB6A;
}

/* ── Title ── */
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

/* ── Anomaly bar ── */
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

.anomaly-bar-fill.threat-critical {
  background: #F44336;
}

.anomaly-bar-fill.threat-high {
  background: #FF9800;
}

.anomaly-bar-fill.threat-elevated {
  background: #FFC107;
}

.anomaly-bar-fill.threat-low {
  background: #4CAF50;
}

.anomaly-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #888;
  min-width: 32px;
  text-align: right;
}

/* ── Expanded detail ── */
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

/* ── Simulate Impact button ── */
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

.btn-simulate:hover:not(:disabled) {
  background: rgba(255, 69, 0, 0.12);
  color: #FF6A33;
  border-color: #FF6A33;
}

.btn-simulate:disabled {
  opacity: 0.5;
  cursor: wait;
}

.btn-simulate--secondary {
  border-color: #555;
  color: #999;
}

.btn-simulate--secondary:hover {
  border-color: #888;
  color: #ccc;
  background: rgba(255, 255, 255, 0.04);
}

.btn-simulate--small {
  font-size: 0.7rem;
  padding: 3px 10px;
}

/* ── Analysis panel ── */
.analysis-panel {
  margin-top: 16px;
  padding: 16px;
  background: #0c0c0c;
  border: 1px solid #2a2a2a;
  border-left: 3px solid #FF4500;
  border-radius: 2px;
}

.analysis-heading {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: #FF4500;
  margin: 0 0 12px 0;
}

.analysis-body {
  font-size: 0.85rem;
  line-height: 1.7;
  color: #bbb;
}

.analysis-body :deep(.analysis-section-label) {
  display: inline-block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.72rem;
  font-weight: 700;
  color: #FF4500;
  letter-spacing: 0.5px;
  margin-top: 8px;
}

.analysis-loading {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: #888;
}

.analysis-spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid #333;
  border-top-color: #FF4500;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.analysis-error {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: #F44336;
  border-left-color: #F44336;
}

/* ── Site monitor alert banner ── */
.signal-card-wrapper {
  display: flex;
  flex-direction: column;
}

.site-monitor-banner {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  background: rgba(255, 69, 0, 0.06);
  border: 1px solid #FF4500;
  border-bottom: none;
  border-radius: 2px 2px 0 0;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.78rem;
  color: #FF4500;
}

.site-monitor-banner__icon {
  font-size: 1rem;
  flex-shrink: 0;
}

.site-monitor-banner__text {
  flex: 1;
  line-height: 1.4;
}

.site-monitor-banner__text strong {
  color: #FF6A33;
}

.signal-card.card-site-monitor {
  border-color: #FF4500;
  border-top-left-radius: 0;
  border-top-right-radius: 0;
  box-shadow: 0 2px 12px rgba(255, 69, 0, 0.08);
}

/* ── Pagination ── */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
  margin-top: 24px;
  padding: 16px 0;
}

.btn-page {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  padding: 6px 14px;
  background: transparent;
  border: 1px solid #333;
  color: #CCC;
  cursor: pointer;
  transition: all 0.15s;
  border-radius: 2px;
}

.btn-page:hover:not(:disabled) {
  border-color: #FF4500;
  color: #FF4500;
}

.btn-page:disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.page-info {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: #999;
}
</style>
