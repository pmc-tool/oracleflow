<template>
  <BasePanel
    panelId="cii"
    title="COUNTRY INSTABILITY"
    infoTooltip="Composite instability score derived from unrest, conflict, security, and information signals"
  >
    <template #default>
      <div class="cii-list">
        <div
          v-for="country in rankedCountries"
          :key="country.code"
          class="cii-row"
          @click="$emit('countrySelected', country.code)"
        >
          <div class="cii-row__main">
            <div class="cii-row__left">
              <span
                class="cii-dot"
                :style="{ background: getDotColor(country.score) }"
              ></span>
              <span class="cii-flag">{{ getFlagEmoji(country.code) }}</span>
              <span class="cii-name">{{ country.name }}</span>
              <span
                class="cii-score"
                :style="{ color: getDotColor(country.score) }"
              >{{ country.score }}</span>
            </div>
            <div class="cii-row__right">
              <span class="cii-trend">
                {{ country.trend === 'rising' ? '&#8593;' : country.trend === 'falling' ? '&#8595;' : '&#8594;' }}
              </span>
              <span
                class="cii-status"
                :style="{ color: getDotColor(country.score) }"
              >{{ getStatusLabel(country.score) }}</span>
            </div>
          </div>
          <!-- Score bar -->
          <div class="cii-row__bar-track">
            <div
              class="cii-row__bar-fill"
              :style="{ width: country.score + '%', background: getDotColor(country.score) }"
            ></div>
          </div>
          <!-- Sub-scores: U (Unrest), C (Conflict), S (Security), I (Information) -->
          <div class="cii-row__components">
            <span class="cii-component" :style="{ color: getComponentColor(country.components.U) }">U:{{ country.components.U }}</span>
            <span class="cii-component" :style="{ color: getComponentColor(country.components.C) }">C:{{ country.components.C }}</span>
            <span class="cii-component" :style="{ color: getComponentColor(country.components.S) }">S:{{ country.components.S }}</span>
            <span class="cii-component" :style="{ color: getComponentColor(country.components.I) }">I:{{ country.components.I }}</span>
          </div>
        </div>

        <div v-if="rankedCountries.length === 0 && !loading" class="cii-empty">
          No country data available
        </div>
        <div v-if="loading" class="cii-empty">
          Loading instability data...
        </div>
      </div>
    </template>
  </BasePanel>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import BasePanel from '../BasePanel.vue'
import { listCountries, getCountryRisk } from '../../api/intelligence'

defineEmits(['countrySelected'])

const countries = ref([])
const loading = ref(false)
let refreshInterval = null

function getDotColor(score) {
  if (score > 80) return 'var(--wm-critical, #ff4444)'
  if (score > 60) return 'var(--wm-high, #ff8800)'
  if (score > 40) return 'var(--wm-elevated, #ffaa00)'
  if (score > 20) return 'var(--wm-normal, #44aa44)'
  return '#3388ff'
}

function getStatusLabel(score) {
  if (score > 80) return 'CRISIS'
  if (score > 60) return 'HIGH'
  if (score > 40) return 'ELEVATED'
  return 'STABLE'
}

function getComponentColor(value) {
  if (value > 80) return 'var(--wm-critical, #ff4444)'
  if (value > 60) return 'var(--wm-high, #ff8800)'
  if (value > 40) return 'var(--wm-elevated, #ffaa00)'
  return 'var(--wm-text-dim, #888)'
}

function getFlagEmoji(code) {
  if (!code || code.length !== 2) return ''
  const codePoints = code
    .toUpperCase()
    .split('')
    .map(c => 0x1f1e6 + c.charCodeAt(0) - 65)
  return String.fromCodePoint(...codePoints)
}

function computeComponents(riskData) {
  // If the API returns pre-computed sub_scores, use them directly
  const sub = riskData?.sub_scores
  if (sub && typeof sub === 'object') {
    return {
      U: Math.round(sub.unrest ?? sub.U ?? 0),
      C: Math.round(sub.conflict ?? sub.C ?? 0),
      S: Math.round(sub.security ?? sub.S ?? 0),
      I: Math.round(sub.information ?? sub.I ?? 0),
    }
  }

  // Component mapping (API returns 0-1 floats in category_risk):
  // U (Unrest): politics + crime signals
  // C (Conflict): geopolitical signals
  // S (Security): cyber + technology signals
  // I (Information): other + economy + finance + healthcare + climate signals
  const categories = riskData?.category_risk || riskData || {}
  const polCount = (categories.politics != null ? 1 : 0) + (categories.crime != null ? 1 : 0)
  const U = polCount > 0
    ? Math.round(((categories.politics || 0) + (categories.crime || 0)) / polCount * 100)
    : 0
  const C = Math.round((categories.geopolitical || 0) * 100)
  const secCount = (categories.cyber != null ? 1 : 0) + (categories.technology != null ? 1 : 0)
  const S = secCount > 0
    ? Math.round(((categories.cyber || 0) + (categories.technology || 0)) / secCount * 100)
    : 0
  const infoFields = ['other', 'economy', 'finance', 'healthcare', 'climate']
  const infoVals = infoFields.filter(f => categories[f] != null)
  const I = infoVals.length > 0
    ? Math.round(infoVals.reduce((sum, f) => sum + (categories[f] || 0), 0) / infoVals.length * 100)
    : 0
  return { U, C, S, I }
}

function computeScore(components) {
  const { U, C, S, I } = components
  return Math.round((U + C + S + I) / 4)
}

const rankedCountries = computed(() => {
  return [...countries.value].sort((a, b) => b.score - a.score)
})

async function fetchData() {
  loading.value = true
  try {
    const res = await listCountries()
    const countryList = res.data?.results || res.data || []
    if (!Array.isArray(countryList)) {
      countries.value = []
      return
    }

    const enriched = await Promise.allSettled(
      countryList.map(async (c) => {
        const code = c.code || c.country_code || c.iso_code
        const name = c.country || c.name || c.country_name || code
        try {
          const riskRes = await getCountryRisk(code)
          const riskData = riskRes.data || {}
          const components = computeComponents(riskData)
          const rawScore = riskData.overall_risk ?? riskData.score ?? riskData.risk_score ?? null
          const score = rawScore != null ? Math.round(rawScore * 100) : computeScore(components)
          const trend = riskData.trend || 'stable'
          return { code, name, score: Math.round(score), trend, components }
        } catch {
          return { code, name, score: 0, trend: 'stable', components: { U: 0, C: 0, S: 0, I: 0 } }
        }
      })
    )

    countries.value = enriched
      .filter(r => r.status === 'fulfilled')
      .map(r => r.value)
  } catch (err) {
    console.error('[CIIPanel] fetch error:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
  refreshInterval = setInterval(fetchData, 120000)
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})
</script>

<style scoped>
.cii-list {
  overflow-y: auto;
  flex: 1;
}

.cii-row {
  padding: 8px 12px;
  border-bottom: 1px solid var(--wm-border, #2a2a2a);
  cursor: pointer;
  transition: background 0.15s ease;
}

.cii-row:hover {
  background: var(--wm-surface-hover, #1e1e1e);
}

.cii-row__main {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.cii-row__left {
  display: flex;
  align-items: center;
  gap: 6px;
}

.cii-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.cii-flag {
  font-size: 12px;
}

.cii-name {
  font-family: 'SF Mono', monospace;
  font-size: 12px;
  color: var(--wm-text, #e8e8e8);
}

.cii-row__right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.cii-score {
  font-family: 'SF Mono', monospace;
  font-size: 16px;
  font-weight: 700;
}

.cii-trend {
  font-family: 'SF Mono', monospace;
  font-size: 12px;
  color: var(--wm-text-dim, #888);
}

.cii-status {
  font-family: 'SF Mono', monospace;
  font-size: 9px;
  font-weight: 600;
  text-transform: uppercase;
  opacity: 0.8;
  min-width: 52px;
  text-align: right;
}

/* Score bar */
.cii-row__bar-track {
  height: 3px;
  background: var(--wm-border, #2a2a2a);
  border-radius: 2px;
  margin-top: 6px;
  overflow: hidden;
}

.cii-row__bar-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.4s ease;
}

.cii-row__components {
  display: flex;
  gap: 10px;
  margin-top: 4px;
  padding-left: 14px;
  font-family: 'SF Mono', monospace;
  font-size: 10px;
}

.cii-component {
  font-weight: 600;
}

.cii-empty {
  padding: 24px;
  text-align: center;
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--wm-text-dim, #888);
}
</style>
