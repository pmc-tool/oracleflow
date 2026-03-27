<template>
  <div class="country-detail">
    <router-link to="/countries" class="back-link">&larr; Back to Countries</router-link>

    <div v-if="loading" class="loading-text">Loading...</div>

    <template v-else-if="country">
      <div class="country-header">
        <span class="country-flag">{{ getFlag(country.code || code) }}</span>
        <div>
          <h1 class="page-title">{{ country.name }}</h1>
          <div class="header-meta">
            <span v-if="country.region" class="meta-tag">{{ country.region }}</span>
            <span v-if="country.timezone" class="meta-tag">{{ country.timezone }}</span>
          </div>
        </div>
      </div>

      <!-- Risk Section -->
      <div v-if="risk" class="section-box">
        <h2 class="section-heading">Risk Assessment</h2>
        <div class="risk-top">
          <div class="risk-score-box">
            <div class="risk-label">Overall Risk</div>
            <div class="risk-score" :style="{ color: riskColor(risk.overall_score) }">
              {{ risk.overall_score != null ? risk.overall_score.toFixed(1) : '--' }}
            </div>
          </div>
          <div class="risk-categories">
            <div v-for="(val, key) in risk.categories || {}" :key="key" class="risk-cat-row">
              <span class="risk-cat-label">{{ key }}</span>
              <div class="risk-bar-track">
                <div
                  class="risk-bar-fill"
                  :style="{ width: (val || 0) + '%', background: riskColor(val) }"
                ></div>
              </div>
              <span class="risk-cat-score">{{ val != null ? val.toFixed(1) : '--' }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- AI Intelligence Brief -->
      <div class="section-box brief-section">
        <div class="brief-header">
          <h2 class="section-heading">Intelligence Brief</h2>
          <button v-if="!briefLoading && !brief" class="gen-brief-btn" @click="generateBrief">
            Generate AI Brief
          </button>
          <button v-if="brief" class="gen-brief-btn refresh" @click="generateBrief">
            Refresh
          </button>
        </div>
        <div v-if="briefLoading" class="brief-loading">
          <span class="loading-dot"></span> Generating intelligence brief...
        </div>
        <div v-else-if="brief" class="brief-content" v-html="formatBrief(brief)"></div>
        <div v-else class="brief-placeholder">
          Click "Generate AI Brief" to create an AI-powered intelligence analysis from {{ country?.name || code }}'s recent signals.
        </div>
      </div>

      <!-- Sources -->
      <div class="section-box" v-if="hasSources">
        <h2 class="section-heading">Sources</h2>

        <div v-if="country.news_sites && country.news_sites.length" class="source-group">
          <h3 class="source-group-title" @click="toggleSection('news')">
            {{ expandedSections.news ? '[-]' : '[+]' }} News Sites ({{ country.news_sites.length }})
          </h3>
          <ul v-if="expandedSections.news" class="source-list">
            <li v-for="(s, i) in country.news_sites" :key="'n'+i">
              <a :href="s.url || s" target="_blank" class="source-link">{{ s.name || s.url || s }}</a>
            </li>
          </ul>
        </div>

        <div v-if="country.reddit_subs && country.reddit_subs.length" class="source-group">
          <h3 class="source-group-title" @click="toggleSection('reddit')">
            {{ expandedSections.reddit ? '[-]' : '[+]' }} Reddit Subs ({{ country.reddit_subs.length }})
          </h3>
          <ul v-if="expandedSections.reddit" class="source-list">
            <li v-for="(s, i) in country.reddit_subs" :key="'r'+i" class="mono-item">
              {{ typeof s === 'string' ? s : s.name || s.subreddit }}
            </li>
          </ul>
        </div>

        <div v-if="country.government_sites && country.government_sites.length" class="source-group">
          <h3 class="source-group-title" @click="toggleSection('gov')">
            {{ expandedSections.gov ? '[-]' : '[+]' }} Government Sites ({{ country.government_sites.length }})
          </h3>
          <ul v-if="expandedSections.gov" class="source-list">
            <li v-for="(s, i) in country.government_sites" :key="'g'+i">
              <a :href="s.url || s" target="_blank" class="source-link">{{ s.name || s.url || s }}</a>
            </li>
          </ul>
        </div>

        <div v-if="country.political_entities && country.political_entities.length" class="source-group">
          <h3 class="source-group-title" @click="toggleSection('political')">
            {{ expandedSections.political ? '[-]' : '[+]' }} Political Entities ({{ country.political_entities.length }})
          </h3>
          <ul v-if="expandedSections.political" class="source-list">
            <li v-for="(s, i) in country.political_entities" :key="'p'+i" class="mono-item">
              {{ typeof s === 'string' ? s : s.name }}
            </li>
          </ul>
        </div>
      </div>
    </template>

    <div v-if="error" class="error-text">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { getCountry, getCountryRisk, getCountryBrief } from '../api/intelligence'

const props = defineProps({
  code: { type: String, required: true }
})

const loading = ref(true)
const error = ref('')
const country = ref(null)
const risk = ref(null)
const brief = ref('')
const briefLoading = ref(false)

async function generateBrief() {
  briefLoading.value = true
  try {
    const res = await getCountryBrief(props.code)
    brief.value = res.data?.brief || res.brief || ''
  } catch (e) {
    console.error('Brief generation failed:', e)
    brief.value = 'Failed to generate brief. Check that the LLM service is configured.'
  } finally {
    briefLoading.value = false
  }
}

function formatBrief(text) {
  if (!text) return ''
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n- /g, '<br>• ')
    .replace(/\n(\d+)\. /g, '<br>$1. ')
    .replace(/^/, '<p>')
    .replace(/$/, '</p>')
}

const expandedSections = reactive({
  news: false,
  reddit: false,
  gov: false,
  political: false,
})

const toggleSection = (key) => {
  expandedSections[key] = !expandedSections[key]
}

const hasSources = computed(() => {
  if (!country.value) return false
  const c = country.value
  return (c.news_sites && c.news_sites.length) ||
    (c.reddit_subs && c.reddit_subs.length) ||
    (c.government_sites && c.government_sites.length) ||
    (c.political_entities && c.political_entities.length)
})

const getFlag = (code) => {
  if (!code || code.length < 2) return ''
  return String.fromCodePoint(
    ...code.toUpperCase().split('').map(c => 127397 + c.charCodeAt(0))
  )
}

const riskColor = (score) => {
  if (score == null) return '#999'
  if (score < 30) return '#4CAF50'
  if (score < 60) return '#FFC107'
  if (score < 80) return '#FF9800'
  return '#F44336'
}

onMounted(async () => {
  try {
    const [countryRes, riskRes] = await Promise.allSettled([
      getCountry(props.code),
      getCountryRisk(props.code),
    ])

    if (countryRes.status === 'fulfilled') {
      country.value = countryRes.value.data || countryRes.value
    }
    if (riskRes.status === 'fulfilled') {
      risk.value = riskRes.value.data || riskRes.value
    }
  } catch (e) {
    error.value = 'Failed to load country: ' + e.message
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.brief-section { position: relative; }
.brief-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
.gen-brief-btn {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  padding: 6px 14px;
  background: #FF4500;
  color: #fff;
  border: none;
  cursor: pointer;
  font-weight: 600;
  letter-spacing: 0.5px;
}
.gen-brief-btn:hover { background: #E03E00; }
.gen-brief-btn.refresh { background: #333; }
.gen-brief-btn.refresh:hover { background: #555; }
.brief-loading {
  color: #FF4500;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  padding: 20px 0;
}
.loading-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  background: #FF4500;
  border-radius: 50%;
  animation: pulse 1s infinite;
  margin-right: 8px;
}
@keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.3; } }
.brief-content {
  font-size: 0.9rem;
  line-height: 1.8;
  color: #ddd;
  border-left: 3px solid #FF4500;
  padding-left: 20px;
}
.brief-content :deep(strong) { color: #fff; }
.brief-content :deep(p) { margin-bottom: 15px; }
.brief-placeholder {
  color: #666;
  font-size: 0.85rem;
  padding: 20px 0;
  font-style: italic;
}
.country-detail {
  font-family: 'Space Grotesk', system-ui, sans-serif;
  max-width: 1000px;
}

.back-link {
  display: inline-block;
  color: #999;
  text-decoration: none;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  margin-bottom: 20px;
  transition: color 0.15s;
}

.back-link:hover {
  color: #FF4500;
}

.country-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 30px;
}

.country-flag {
  font-size: 3rem;
  line-height: 1;
}

.page-title {
  font-size: 1.8rem;
  font-weight: 600;
  color: #FFFFFF;
  margin: 0;
}

.header-meta {
  display: flex;
  gap: 10px;
  margin-top: 6px;
}

.meta-tag {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #999;
  border: 1px solid #333;
  padding: 2px 8px;
}

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

.section-box {
  border: 1px solid #333;
  padding: 20px;
  margin-bottom: 24px;
  background: #000;
}

.section-heading {
  font-size: 1rem;
  font-weight: 600;
  color: #FFFFFF;
  margin-bottom: 20px;
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 0.5px;
}

.risk-top {
  display: flex;
  gap: 30px;
  align-items: flex-start;
}

.risk-score-box {
  min-width: 120px;
  text-align: center;
}

.risk-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #999;
  margin-bottom: 8px;
  letter-spacing: 0.5px;
}

.risk-score {
  font-family: 'JetBrains Mono', monospace;
  font-size: 3rem;
  font-weight: 700;
  line-height: 1;
}

.risk-categories {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.risk-cat-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.risk-cat-label {
  width: 100px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #CCC;
  text-align: right;
}

.risk-bar-track {
  flex: 1;
  height: 12px;
  background: #1a1a1a;
  border: 1px solid #333;
  overflow: hidden;
}

.risk-bar-fill {
  height: 100%;
  transition: width 0.5s ease;
}

.risk-cat-score {
  width: 40px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: #FFFFFF;
  text-align: right;
}

.source-group {
  margin-bottom: 16px;
}

.source-group:last-child {
  margin-bottom: 0;
}

.source-group-title {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: #CCC;
  cursor: pointer;
  padding: 6px 0;
  margin: 0;
  font-weight: 500;
  transition: color 0.15s;
}

.source-group-title:hover {
  color: #FF4500;
}

.source-list {
  list-style: none;
  padding: 8px 0 0 16px;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.source-link {
  color: #FF4500;
  text-decoration: none;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  word-break: break-all;
}

.source-link:hover {
  text-decoration: underline;
}

.mono-item {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: #CCC;
}
</style>
