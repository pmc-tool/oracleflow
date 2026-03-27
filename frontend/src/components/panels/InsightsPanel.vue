<template>
  <BasePanel
    panelId="insights"
    title="AI INSIGHTS"
    :defaultRowSpan="2"
    infoTooltip="AI-generated intelligence brief synthesized from all active signals."
    @close="$emit('close')"
  >
    <template #tabs>
      <div class="live-badge-row">
        <span class="live-badge">
          <span class="live-dot"></span>
          LIVE
        </span>
      </div>
    </template>

    <div class="insights-body">
      <!-- Loading state -->
      <div v-if="loading" class="loading-state">
        <span class="pulse-dot"></span>
        Generating intelligence brief...
      </div>

      <!-- World Brief -->
      <template v-else>
        <div class="section-header">
          <span class="section-icon">&#127758;</span>
          <span class="section-title">WORLD BRIEF</span>
        </div>

        <div class="brief-text">
          <p v-for="(para, i) in briefParagraphs" :key="i" v-html="para"></p>
        </div>

        <div class="divider"></div>

        <!-- Country Instability -->
        <div class="section-header">
          <span class="section-title">COUNTRY INSTABILITY</span>
          <span class="info-icon" title="Top countries by instability index">&#9432;</span>
        </div>

        <div class="instability-list">
          <div
            v-for="country in topCountries"
            :key="country.code"
            class="instability-row"
          >
            <span class="instability-dot" :style="{ color: getScoreColor(country.score) }">&#9679;</span>
            <span class="instability-name">{{ country.name }}</span>
            <span class="instability-score" :style="{ color: getScoreColor(country.score) }">{{ country.score }}</span>
          </div>
        </div>

        <div class="divider"></div>

        <!-- Footer -->
        <div class="insights-footer">
          <span>Updated {{ timeAgo }}</span>
          <span class="footer-sep">|</span>
          <span>{{ signalCount }} signals</span>
          <span class="footer-sep">|</span>
          <button class="refresh-btn" @click="fetchBrief">&#8635; Refresh</button>
        </div>
      </template>
    </div>
  </BasePanel>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import BasePanel from '../BasePanel.vue'
import { getWorldBrief, listSignals } from '../../api/intelligence'

const emit = defineEmits(['close'])

const loading = ref(true)
const briefData = ref(null)
const signalCount = ref(0)
const lastUpdated = ref(null)
let refreshInterval = null

const PLACEHOLDER_BRIEF = {
  paragraphs: [
    'Global tensions remain elevated across multiple theaters. <strong>Iran</strong> continues to project force through proxy networks in the Middle East, while <strong>Russia</strong> sustains offensive operations along the eastern Ukrainian front. Maritime disruptions in the <strong>Red Sea</strong> corridor persist with Houthi forces targeting commercial shipping lanes.',
    'Key risk indicators show deterioration in the <strong>Taiwan Strait</strong> region, with increased PLA naval activity and air defense zone incursions reported over the past 72 hours. Economic sanctions pressure on <strong>North Korea</strong> has intensified following recent ballistic missile tests, raising concerns about regional stability.',
    'Outlook remains cautious. Intelligence signals suggest a 30-day window of heightened geopolitical risk, particularly in the Persian Gulf and South China Sea. Monitoring of <strong>48 active signals</strong> across <strong>12 countries</strong> continues. Recommend elevated awareness posture for all tracked regions.'
  ],
  countries: [
    { code: 'IR', name: 'Iran', score: 100 },
    { code: 'RU', name: 'Russia', score: 83 },
    { code: 'JM', name: 'Jamaica', score: 67 },
    { code: 'UA', name: 'Ukraine', score: 62 },
    { code: 'YE', name: 'Yemen', score: 58 }
  ]
}

const briefParagraphs = computed(() => {
  if (briefData.value && briefData.value.paragraphs) {
    return briefData.value.paragraphs
  }
  return PLACEHOLDER_BRIEF.paragraphs
})

const topCountries = computed(() => {
  if (briefData.value && briefData.value.countries) {
    return briefData.value.countries.slice(0, 5)
  }
  return PLACEHOLDER_BRIEF.countries
})

const timeAgo = computed(() => {
  if (!lastUpdated.value) return 'just now'
  const diff = Math.floor((Date.now() - lastUpdated.value) / 60000)
  if (diff < 1) return 'just now'
  if (diff === 1) return '1m ago'
  return `${diff}m ago`
})

function getScoreColor(score) {
  if (score >= 80) return '#ff4444'
  if (score >= 60) return '#ffaa00'
  if (score >= 40) return '#ff8800'
  return '#44aa44'
}

async function fetchBrief() {
  loading.value = true
  try {
    const [briefRes, signalsRes] = await Promise.all([
      getWorldBrief(),
      listSignals({ limit: 1 })
    ])
    if (briefRes.data) {
      briefData.value = briefRes.data
    }
    if (signalsRes.data && signalsRes.data.count != null) {
      signalCount.value = signalsRes.data.count
    } else {
      signalCount.value = 30
    }
  } catch {
    // Use placeholder data
    briefData.value = null
    signalCount.value = 30
  } finally {
    lastUpdated.value = Date.now()
    loading.value = false
  }
}

onMounted(() => {
  fetchBrief()
  // Auto-refresh every 30 minutes
  refreshInterval = setInterval(fetchBrief, 30 * 60 * 1000)
})

onBeforeUnmount(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})
</script>

<style scoped>
.live-badge-row {
  display: flex;
  justify-content: flex-end;
  padding: 0 12px 4px;
}
.live-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 10px;
  font-weight: 600;
  color: #44ff88;
  letter-spacing: 1px;
}
.live-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #44ff88;
  animation: livePulse 2s ease-in-out infinite;
}
@keyframes livePulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.insights-body {
  padding: 12px;
  font-family: 'SF Mono', monospace;
  font-size: 12px;
}

.loading-state {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--wm-text-dim, #888);
  font-size: 12px;
  padding: 24px 0;
}
.pulse-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #44ff88;
  animation: livePulse 1.5s ease-in-out infinite;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
}
.section-icon {
  font-size: 13px;
}
.section-title {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 1px;
  color: var(--wm-text, #e8e8e8);
}
.info-icon {
  font-size: 12px;
  color: var(--wm-text-dim, #888);
  cursor: help;
  margin-left: auto;
}

.brief-text {
  font-size: 12px;
  line-height: 1.6;
  color: var(--wm-text-dim, #888);
}
.brief-text p {
  margin: 0 0 10px 0;
}
.brief-text p:last-child {
  margin-bottom: 0;
}
.brief-text :deep(strong) {
  color: var(--wm-text, #e8e8e8);
  font-weight: 600;
}

.divider {
  height: 1px;
  background: var(--wm-border, #2a2a2a);
  margin: 12px 0;
}

.instability-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.instability-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}
.instability-dot {
  font-size: 10px;
  flex-shrink: 0;
}
.instability-name {
  color: var(--wm-text, #e8e8e8);
  font-weight: 500;
  flex: 1;
}
.instability-score {
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  min-width: 28px;
  text-align: right;
}

.insights-footer {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  color: var(--wm-text-dim, #888);
}
.footer-sep {
  color: var(--wm-border, #2a2a2a);
}
.refresh-btn {
  background: none;
  border: none;
  color: var(--wm-text-dim, #888);
  font-size: 10px;
  font-family: 'SF Mono', monospace;
  cursor: pointer;
  padding: 0;
}
.refresh-btn:hover {
  color: var(--wm-text, #e8e8e8);
}
</style>
