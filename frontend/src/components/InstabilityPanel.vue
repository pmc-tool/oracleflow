<template>
  <div class="instability-panel">
    <div class="panel-header">
      <div class="header-title">
        <span class="title-text">COUNTRY INSTABILITY</span>
        <span class="info-icon" title="Countries ranked by composite instability score">&#9432;</span>
      </div>
      <div class="header-updated">
        Updated {{ lastUpdated }}
      </div>
    </div>

    <div v-if="loading" class="panel-loading">
      <span class="loading-dot"></span>
      Loading data...
    </div>

    <div v-else class="country-list">
      <div
        v-for="country in rankedCountries"
        :key="country.code"
        class="country-row"
        :class="{ selected: country.code === selectedCode }"
        @click="selectCountry(country)"
      >
        <div class="row-main">
          <span class="status-dot" :style="{ background: dotColor(country.score) }"></span>
          <span class="country-flag">{{ flagEmoji(country.code) }}</span>
          <span class="country-name">{{ country.name }}</span>
          <span class="country-score" :style="{ color: scoreColor(country.score) }">
            {{ Math.round(country.score) }}
          </span>
          <span class="trend-arrow">
            {{ country.trend }}
          </span>
        </div>
        <div class="row-components">
          <span class="comp">U:{{ country.unrest }}</span>
          <span class="comp">C:{{ country.conflict }}</span>
          <span class="comp">S:{{ country.security }}</span>
          <span class="comp">I:{{ country.information }}</span>
        </div>
        <div class="status-tag" :class="statusClass(country.score)">
          {{ statusLabel(country.score) }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { listCountries, getCountryRisk } from '../api/intelligence'

const emit = defineEmits(['countrySelected'])

const props = defineProps({
  selectedCountry: { type: String, default: '' }
})

const countries = ref([])
const riskDetails = ref({})
const loading = ref(true)
const lastUpdated = ref('')
const selectedCode = ref('')

function flagEmoji(code) {
  if (!code || code.length !== 2) return ''
  const offset = 127397
  return String.fromCodePoint(
    code.toUpperCase().charCodeAt(0) + offset,
    code.toUpperCase().charCodeAt(1) + offset
  )
}

function dotColor(score) {
  if (score > 70) return '#ff4444'
  if (score > 50) return '#ff8800'
  if (score > 30) return '#ffaa00'
  return '#44aa44'
}

function scoreColor(score) {
  if (score > 70) return '#ff4444'
  if (score > 50) return '#ff8800'
  if (score > 30) return '#ffaa00'
  return '#44aa44'
}

function statusLabel(score) {
  if (score > 80) return 'CRISIS'
  if (score > 60) return 'HIGH'
  if (score > 40) return 'ELEVATED'
  return 'STABLE'
}

function statusClass(score) {
  if (score > 80) return 'tag-crisis'
  if (score > 60) return 'tag-high'
  if (score > 40) return 'tag-elevated'
  return 'tag-stable'
}

function mapCategoriesToComponents(categories) {
  if (!categories) return { unrest: 0, conflict: 0, security: 0, information: 0 }
  const politics = categories.politics || categories.finance || 0
  const crime = categories.crime || categories.supply_chain || 0
  const geopolitical = categories.geopolitical || 0
  const cyber = categories.cyber || 0
  const climate = categories.climate || 0
  const other = categories.other || categories.information || 0

  return {
    unrest: Math.round(((politics + crime) / 2)),
    conflict: Math.round(geopolitical),
    security: Math.round(cyber),
    information: Math.round((climate + other) / 2 || other || climate)
  }
}

const rankedCountries = computed(() => {
  const list = countries.value
    .map(c => {
      const code = c.code || c.iso_a2
      const risk = riskDetails.value[code] || {}
      const cats = risk.categories || {}
      const catValues = Object.values(cats).filter(v => v != null)
      const score = catValues.length > 0
        ? (catValues.reduce((a, b) => a + b, 0) / catValues.length)
        : (c.risk_score != null ? c.risk_score : 0)
      const components = mapCategoriesToComponents(cats)

      return {
        code,
        name: c.name || code,
        score,
        trend: '\u2192 stable',
        ...components
      }
    })
    .filter(c => c.code && c.code !== '-99')
    .sort((a, b) => b.score - a.score)

  return list
})

function selectCountry(country) {
  selectedCode.value = country.code
  emit('countrySelected', country.code)
}

onMounted(async () => {
  loading.value = true
  const now = new Date()
  lastUpdated.value = now.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })

  try {
    const res = await listCountries()
    const d = res.data || res
    countries.value = Array.isArray(d) ? d : (d.items || d.results || [])

    // Fetch risk details for each country (in parallel, batched)
    const codes = countries.value
      .map(c => c.code || c.iso_a2)
      .filter(Boolean)

    const batchSize = 10
    for (let i = 0; i < codes.length; i += batchSize) {
      const batch = codes.slice(i, i + batchSize)
      const results = await Promise.allSettled(
        batch.map(code => getCountryRisk(code))
      )
      results.forEach((result, idx) => {
        if (result.status === 'fulfilled') {
          const data = result.value?.data || result.value || {}
          riskDetails.value[batch[idx]] = data
        }
      })
    }
  } catch {
    // silent
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.instability-panel {
  width: 280px;
  min-width: 280px;
  max-width: 280px;
  height: 100%;
  background: #141414;
  border-right: 1px solid #2a2a2a;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  font-family: 'Space Grotesk', system-ui, sans-serif;
}

.panel-header {
  padding: 14px 16px 10px;
  border-bottom: 1px solid #2a2a2a;
  flex-shrink: 0;
}

.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.title-text {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  font-weight: 700;
  color: #e8e8e8;
  letter-spacing: 0.08em;
}

.info-icon {
  font-size: 0.85rem;
  color: #666;
  cursor: help;
}

.header-updated {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  color: #666;
  margin-top: 4px;
}

.panel-loading {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 20px 16px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #666;
}

.loading-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #ff8800;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}

.country-list {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

.country-list::-webkit-scrollbar {
  width: 4px;
}

.country-list::-webkit-scrollbar-track {
  background: #0a0a0a;
}

.country-list::-webkit-scrollbar-thumb {
  background: #2a2a2a;
  border-radius: 2px;
}

.country-row {
  padding: 10px 16px 8px;
  border-bottom: 1px solid #1a1a1a;
  cursor: pointer;
  transition: background 0.15s;
  border-left: 3px solid transparent;
}

.country-row:hover {
  background: #1a1a1a;
}

.country-row.selected {
  background: #1a1a1a;
  border-left-color: #ff4444;
}

.row-main {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.country-flag {
  font-size: 0.9rem;
  flex-shrink: 0;
}

.country-name {
  font-size: 0.8rem;
  font-weight: 600;
  color: #e8e8e8;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  flex: 1;
  min-width: 0;
}

.country-score {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.05rem;
  font-weight: 700;
  flex-shrink: 0;
  min-width: 30px;
  text-align: right;
}

.trend-arrow {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  color: #666;
  flex-shrink: 0;
  white-space: nowrap;
}

.row-components {
  display: flex;
  gap: 6px;
  margin-top: 4px;
  padding-left: 20px;
}

.comp {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6rem;
  color: #555;
}

.status-tag {
  display: inline-block;
  margin-top: 4px;
  margin-left: 20px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.55rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  padding: 1px 6px;
  border-radius: 2px;
}

.tag-crisis {
  color: #ff4444;
  background: rgba(255, 68, 68, 0.12);
  border: 1px solid rgba(255, 68, 68, 0.25);
}

.tag-high {
  color: #ff8800;
  background: rgba(255, 136, 0, 0.12);
  border: 1px solid rgba(255, 136, 0, 0.25);
}

.tag-elevated {
  color: #ffaa00;
  background: rgba(255, 170, 0, 0.12);
  border: 1px solid rgba(255, 170, 0, 0.25);
}

.tag-stable {
  color: #44aa44;
  background: rgba(68, 170, 68, 0.12);
  border: 1px solid rgba(68, 170, 68, 0.25);
}
</style>
