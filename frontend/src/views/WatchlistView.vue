<template>
  <div class="watchlist-view">
    <div class="page-header">
      <h1 class="page-title">Your Watchlist</h1>
      <button class="btn-add" @click="showAddForm = !showAddForm">
        <PlusCircle :size="16" />
        <span>Add New</span>
      </button>
    </div>

    <!-- Add New Form (inline, expandable) -->
    <div v-if="showAddForm" class="add-form">
      <div class="add-form-header">Add Watchlist Item</div>
      <div class="add-form-grid">
        <div class="form-group">
          <label class="form-label">NAME *</label>
          <input
            v-model="newItem.name"
            type="text"
            class="form-input"
            placeholder="e.g. Jamaat-e-Islami"
            @input="autoGenerateKeywords"
          />
        </div>
        <div class="form-group">
          <label class="form-label">TYPE</label>
          <select v-model="newItem.item_type" class="form-select">
            <option value="organization">Organization</option>
            <option value="person">Person</option>
            <option value="topic">Topic</option>
            <option value="competitor">Competitor</option>
            <option value="location">Location</option>
          </select>
        </div>
        <div class="form-group">
          <label class="form-label">COUNTRY</label>
          <select v-model="newItem.country_code" class="form-select">
            <option value="">-- Optional --</option>
            <option v-for="c in countryOptions" :key="c.code" :value="c.code">{{ c.label }}</option>
          </select>
        </div>
        <div class="form-group form-group-wide">
          <label class="form-label">KEYWORDS</label>
          <input
            v-model="newItem.keywords"
            type="text"
            class="form-input"
            placeholder="Comma-separated keywords (auto-generated from name)"
          />
        </div>
      </div>
      <div class="add-form-actions">
        <button class="btn-submit" :disabled="!newItem.name.trim() || submitting" @click="submitItem">
          <span v-if="submitting">Creating...</span>
          <span v-else>Create Item</span>
        </button>
        <button class="btn-cancel" @click="showAddForm = false">Cancel</button>
      </div>
      <div v-if="addError" class="add-error">{{ addError }}</div>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="loading-text">Loading watchlist...</div>

    <!-- Error -->
    <div v-if="error" class="error-text">{{ error }}</div>

    <!-- Empty state -->
    <div v-if="!loading && !error && items.length === 0" class="empty-state">
      <div class="empty-icon">
        <Eye :size="48" />
      </div>
      <div class="empty-title">Add your first watchlist item to start monitoring</div>
      <div class="empty-subtitle">
        Track organizations, people, topics, and locations. OracleFlow will surface matching signals automatically.
      </div>
      <button class="btn-add btn-add-empty" @click="showAddForm = true">
        <PlusCircle :size="16" />
        <span>Add New Item</span>
      </button>
    </div>

    <!-- Watchlist cards -->
    <div v-if="!loading && items.length > 0" class="watchlist-feed">
      <div
        v-for="item in items"
        :key="item.id"
        class="watchlist-card"
        @click="goToDetail(item.id)"
      >
        <div class="card-top-row">
          <div class="card-name">{{ item.name }}</div>
          <div class="card-stats">
            <span class="signal-count">{{ item.signal_count ?? 0 }} signals</span>
            <span
              class="trend-arrow"
              :class="trendClass(item)"
            >{{ trendArrow(item) }}</span>
          </div>
        </div>
        <div class="card-badges">
          <span class="badge badge-type">{{ item.item_type || 'topic' }}</span>
          <span v-if="item.country_code" class="badge badge-country">
            {{ countryFlag(item.country_code) }} {{ item.country_code }}
          </span>
        </div>
        <div v-if="item.latest_signal_title" class="card-latest">
          <span class="latest-label">Latest:</span>
          <span class="latest-title">"{{ truncate(item.latest_signal_title, 60) }}"</span>
          <span v-if="item.latest_signal_time" class="latest-time">
            &mdash; {{ relativeTime(item.latest_signal_time) }}
          </span>
        </div>
        <div v-else class="card-latest card-latest-none">No signals yet</div>
        <div class="card-bottom-row">
          <div class="sentiment-row">
            <span class="sentiment-label">Sentiment:</span>
            <span
              class="sentiment-value"
              :class="sentimentClass(item.avg_sentiment)"
            >{{ formatSentiment(item.avg_sentiment) }} this week</span>
          </div>
          <span class="view-all-link">View All Signals &rarr;</span>
        </div>
      </div>
    </div>

    <!-- Quick Comparison -->
    <div v-if="!loading && items.length > 1" class="comparison-section">
      <div class="comparison-title">Quick Comparison</div>
      <div class="comparison-bars">
        <div v-for="item in sortedBySignals" :key="'cmp-' + item.id" class="comparison-row">
          <span class="comparison-name">{{ truncate(item.name, 16) }}</span>
          <div class="comparison-bar-track">
            <div
              class="comparison-bar-fill"
              :style="{ width: barWidth(item.signal_count) }"
            ></div>
          </div>
          <span class="comparison-count">{{ item.signal_count ?? 0 }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { getWatchlist, createWatchlistItem } from '../api/intelligence'
import { Eye, PlusCircle } from 'lucide-vue-next'

const router = useRouter()

const loading = ref(true)
const error = ref('')
const items = ref([])
const showAddForm = ref(false)
const submitting = ref(false)
const addError = ref('')

const newItem = ref({
  name: '',
  item_type: 'organization',
  country_code: '',
  keywords: '',
})

const countryOptions = [
  { code: 'BD', label: 'BD - Bangladesh' },
  { code: 'US', label: 'US - United States' },
  { code: 'GB', label: 'GB - United Kingdom' },
  { code: 'CN', label: 'CN - China' },
  { code: 'RU', label: 'RU - Russia' },
  { code: 'IN', label: 'IN - India' },
  { code: 'PK', label: 'PK - Pakistan' },
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
  { code: 'EG', label: 'EG - Egypt' },
  { code: 'ID', label: 'ID - Indonesia' },
  { code: 'MM', label: 'MM - Myanmar' },
]

const sortedBySignals = computed(() => {
  return [...items.value].sort((a, b) => (b.signal_count ?? 0) - (a.signal_count ?? 0))
})

const maxSignals = computed(() => {
  return Math.max(1, ...items.value.map(i => i.signal_count ?? 0))
})

const barWidth = (count) => {
  const pct = ((count ?? 0) / maxSignals.value) * 100
  return pct + '%'
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

const truncate = (str, len) => {
  if (!str) return ''
  return str.length > len ? str.slice(0, len) + '...' : str
}

const trendArrow = (item) => {
  const trend = item.trend ?? item.signal_trend ?? 0
  if (trend > 0) return '\u25B2'
  if (trend < 0) return '\u25BC'
  return '\u25AC'
}

const trendClass = (item) => {
  const trend = item.trend ?? item.signal_trend ?? 0
  if (trend > 0) return 'trend-up'
  if (trend < 0) return 'trend-down'
  return 'trend-flat'
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

const autoGenerateKeywords = () => {
  const name = newItem.value.name.trim()
  if (name) {
    // Auto-generate: full name + individual words longer than 2 chars
    const words = name.split(/\s+/).filter(w => w.length > 2)
    const kws = [name, ...words.filter(w => w.toLowerCase() !== name.toLowerCase())]
    newItem.value.keywords = [...new Set(kws)].join(', ')
  }
}

const goToDetail = (id) => {
  router.push(`/watchlist/${id}`)
}

const loadWatchlist = async () => {
  loading.value = true
  error.value = ''
  try {
    const res = await getWatchlist()
    const d = res.data || res
    items.value = Array.isArray(d) ? d : (d.items || d.results || [])
  } catch (e) {
    error.value = 'Failed to load watchlist: ' + (e.response?.data?.error || e.message)
  } finally {
    loading.value = false
  }
}

const submitItem = async () => {
  submitting.value = true
  addError.value = ''
  try {
    const payload = {
      name: newItem.value.name.trim(),
      item_type: newItem.value.item_type,
      keywords: newItem.value.keywords
        .split(',')
        .map(k => k.trim())
        .filter(Boolean),
    }
    if (newItem.value.country_code) {
      payload.country_code = newItem.value.country_code
    }
    await createWatchlistItem(payload)
    // Reset form
    newItem.value = { name: '', item_type: 'organization', country_code: '', keywords: '' }
    showAddForm.value = false
    await loadWatchlist()
  } catch (e) {
    addError.value = 'Failed to create item: ' + (e.response?.data?.error || e.message)
  } finally {
    submitting.value = false
  }
}

const onAddNewEvent = () => {
  showAddForm.value = true
}

onMounted(() => {
  loadWatchlist()
  window.addEventListener('watchlist-add-new', onAddNewEvent)
})

onBeforeUnmount(() => {
  window.removeEventListener('watchlist-add-new', onAddNewEvent)
})
</script>

<style scoped>
.watchlist-view {
  font-family: 'Space Grotesk', system-ui, sans-serif;
  max-width: 900px;
  background: #0a0a0a;
  color: #e8e8e8;
}

/* ── Page header ── */
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}

.page-title {
  font-size: 1.8rem;
  font-weight: 600;
  color: #FFFFFF;
  margin: 0;
}

.btn-add {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  padding: 8px 16px;
  background: transparent;
  border: 1px solid #FF4500;
  color: #FF4500;
  cursor: pointer;
  transition: all 0.15s;
  border-radius: 2px;
  letter-spacing: 0.3px;
}

.btn-add:hover {
  background: rgba(255, 69, 0, 0.12);
  color: #FF6A33;
  border-color: #FF6A33;
}

/* ── Add form ── */
.add-form {
  background: #141414;
  border: 1px solid #333;
  border-left: 3px solid #FF4500;
  padding: 20px;
  margin-bottom: 24px;
  border-radius: 2px;
}

.add-form-header {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: #FF4500;
  margin-bottom: 16px;
}

.add-form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.form-group-wide {
  grid-column: 1 / -1;
}

.form-label {
  display: block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  color: #666;
  letter-spacing: 1px;
  margin-bottom: 6px;
}

.form-input,
.form-select {
  width: 100%;
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

.form-input:focus,
.form-select:focus {
  border-color: #FF4500;
}

.form-select {
  cursor: pointer;
}

.add-form-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.btn-submit {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  padding: 8px 20px;
  background: #FF4500;
  border: none;
  color: #FFFFFF;
  cursor: pointer;
  transition: all 0.15s;
  border-radius: 2px;
  letter-spacing: 0.3px;
}

.btn-submit:hover:not(:disabled) {
  background: #FF6A33;
}

.btn-submit:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-cancel {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  padding: 8px 16px;
  background: transparent;
  border: 1px solid #333;
  color: #999;
  cursor: pointer;
  transition: all 0.15s;
  border-radius: 2px;
}

.btn-cancel:hover {
  border-color: #666;
  color: #ccc;
}

.add-error {
  margin-top: 12px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: #F44336;
}

/* ── Loading / Error / Empty ── */
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
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
}

.empty-icon {
  color: #333;
  margin-bottom: 20px;
}

.empty-title {
  font-size: 1.1rem;
  font-weight: 500;
  color: #888;
  margin-bottom: 10px;
}

.empty-subtitle {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.78rem;
  color: #555;
  max-width: 400px;
  line-height: 1.6;
  margin-bottom: 24px;
}

.btn-add-empty {
  margin-top: 0;
}

/* ── Watchlist cards ── */
.watchlist-feed {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.watchlist-card {
  background: #141414;
  border: 1px solid #222;
  border-left: 4px solid #333;
  padding: 18px 22px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
  border-radius: 2px;
}

.watchlist-card:hover {
  border-color: #444;
  border-left-color: #FF4500;
  background: #181818;
}

.card-top-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.card-name {
  font-size: 1.1rem;
  font-weight: 600;
  color: #FFFFFF;
}

.card-stats {
  display: flex;
  align-items: center;
  gap: 10px;
}

.signal-count {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #999;
}

.trend-arrow {
  font-size: 0.85rem;
}

.trend-up {
  color: #F44336;
}

.trend-down {
  color: #4CAF50;
}

.trend-flat {
  color: #666;
}

.card-badges {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

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

.card-latest {
  font-size: 0.85rem;
  color: #bbb;
  margin-bottom: 12px;
  line-height: 1.5;
}

.card-latest-none {
  color: #555;
  font-style: italic;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.78rem;
}

.latest-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #666;
  margin-right: 4px;
}

.latest-title {
  color: #ccc;
}

.latest-time {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #666;
}

.card-bottom-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.sentiment-row {
  display: flex;
  align-items: center;
  gap: 6px;
}

.sentiment-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  color: #666;
  letter-spacing: 0.5px;
}

.sentiment-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
}

.sentiment-positive {
  color: #4CAF50;
}

.sentiment-negative {
  color: #F44336;
}

.sentiment-neutral {
  color: #999;
}

.view-all-link {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.72rem;
  color: #FF4500;
  transition: opacity 0.15s;
}

.watchlist-card:hover .view-all-link {
  opacity: 0.8;
  text-decoration: underline;
}

/* ── Quick Comparison ── */
.comparison-section {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #222;
}

.comparison-title {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: #666;
  margin-bottom: 16px;
}

.comparison-bars {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.comparison-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.comparison-name {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #ccc;
  min-width: 130px;
  text-align: right;
}

.comparison-bar-track {
  flex: 1;
  max-width: 400px;
  height: 14px;
  background: #1a1a1a;
  border: 1px solid #2a2a2a;
  overflow: hidden;
  border-radius: 1px;
}

.comparison-bar-fill {
  height: 100%;
  background: #FF4500;
  transition: width 0.4s ease;
  border-radius: 1px;
}

.comparison-count {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #888;
  min-width: 32px;
}
</style>
