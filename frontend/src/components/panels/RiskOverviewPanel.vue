<template>
  <BasePanel
    panelId="risk-overview"
    title="STRATEGIC RISK OVERVIEW"
    infoTooltip="Composite global risk score derived from conflict, economic, supply chain, cyber, and climate indicators"
    dataBadge="LIVE"
    :defaultRowSpan="2"
  >
    <template #default>
      <div class="risk-content">
        <!-- Circular Gauge -->
        <div class="risk-gauge-container">
          <svg class="risk-gauge" viewBox="0 0 140 140">
            <!-- Background circle -->
            <circle
              cx="70" cy="70" r="58"
              fill="none"
              :stroke="'var(--wm-border, #2a2a2a)'"
              stroke-width="8"
            />
            <!-- Score arc -->
            <circle
              cx="70" cy="70" r="58"
              fill="none"
              :stroke="getLevelColor(riskScore)"
              stroke-width="8"
              stroke-linecap="round"
              :stroke-dasharray="arcDash"
              stroke-dashoffset="0"
              transform="rotate(-90 70 70)"
              class="risk-gauge-arc"
            />
          </svg>
          <div class="risk-gauge-label">
            <span
              class="risk-gauge-score"
              :style="{ color: getLevelColor(riskScore) }"
            >{{ riskScore }}</span>
            <span
              class="risk-gauge-level"
              :style="{ color: getLevelColor(riskScore) }"
            >{{ levelLabel }}</span>
          </div>
        </div>

        <!-- Trend -->
        <div class="risk-trend">
          <span class="risk-trend-label">TREND:</span>
          <span class="risk-trend-icon">{{ trendIcon }}</span>
          <span class="risk-trend-text">{{ trendLabel }}</span>
        </div>

        <!-- Divider -->
        <div class="risk-divider"></div>

        <!-- Risk Factors -->
        <div class="risk-factors-label">RISK FACTORS</div>
        <div class="risk-factors">
          <div
            v-for="(factor, idx) in riskFactors"
            :key="idx"
            class="risk-factor-row"
          >
            <span class="risk-factor-name">{{ factor.name }}</span>
            <div class="risk-factor-bar-wrapper">
              <div
                class="risk-factor-bar"
                :style="{
                  width: factor.value + '%',
                  background: getFactorColor(factor.value)
                }"
              ></div>
              <div class="risk-factor-bar-bg"></div>
            </div>
            <span
              class="risk-factor-value"
              :style="{ color: getFactorColor(factor.value) }"
            >{{ factor.value }}</span>
          </div>
        </div>
      </div>
    </template>
  </BasePanel>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import BasePanel from '../BasePanel.vue'
import { getChaos, getChaosHistory } from '../../api/intelligence'

const riskScore = ref(79)
const chaosHistory = ref([])

const riskFactors = ref([
  { name: 'Conflict Intensity', value: 82 },
  { name: 'Economic Instability', value: 63 },
  { name: 'Supply Chain Risk', value: 52 },
  { name: 'Cyber Threat Level', value: 34 },
  { name: 'Climate Disruption', value: 45 }
])

let refreshInterval = null

function getLevelColor(score) {
  if (score > 70) return 'var(--semantic-critical, #ff4444)'
  if (score > 50) return 'var(--semantic-high, #ff8800)'
  if (score > 30) return 'var(--semantic-elevated, #ffaa00)'
  return 'var(--semantic-normal, #44aa44)'
}

function getFactorColor(value) {
  if (value > 70) return 'var(--semantic-critical, #ff4444)'
  if (value > 50) return 'var(--semantic-high, #ff8800)'
  if (value > 30) return 'var(--semantic-elevated, #ffaa00)'
  return 'var(--semantic-normal, #44aa44)'
}

const levelLabel = computed(() => {
  if (riskScore.value > 70) return 'CRITICAL'
  if (riskScore.value > 50) return 'HIGH'
  if (riskScore.value > 30) return 'ELEVATED'
  return 'NORMAL'
})

const trendLabel = computed(() => {
  if (chaosHistory.value.length < 2) return 'Stable'
  const recent = chaosHistory.value.slice(-3)
  const first = recent[0]
  const last = recent[recent.length - 1]
  const diff = last - first
  if (diff > 2) return 'Escalating'
  if (diff < -2) return 'De-escalating'
  return 'Stable'
})

const trendIcon = computed(() => {
  if (trendLabel.value === 'Escalating') return '\u{1F4C8}'
  if (trendLabel.value === 'De-escalating') return '\u{1F4C9}'
  return '\u{2194}\uFE0F'
})

const circumference = 2 * Math.PI * 58

const arcDash = computed(() => {
  const filled = (riskScore.value / 100) * circumference
  return `${filled} ${circumference - filled}`
})

async function fetchData() {
  try {
    const res = await getChaos()
    const data = res.data || res
    if (data.score != null) {
      riskScore.value = Math.round(data.score)
    } else if (data.chaos_index != null) {
      riskScore.value = Math.round(data.chaos_index)
    }

    // Map chaos categories to risk factors if available
    const cats = data.categories || {}
    if (Object.keys(cats).length > 0) {
      riskFactors.value = [
        { name: 'Conflict Intensity', value: Math.round(cats.geopolitical || cats.conflict || 82) },
        { name: 'Economic Instability', value: Math.round(cats.economy || cats.finance || 63) },
        { name: 'Supply Chain Risk', value: Math.round(cats.trade || cats.supply || 52) },
        { name: 'Cyber Threat Level', value: Math.round(cats.cyber || cats.technology || 34) },
        { name: 'Climate Disruption', value: Math.round(cats.climate || cats.environment || 45) }
      ]
    }
  } catch {
    // Use placeholder data on error
  }

  try {
    const histRes = await getChaosHistory(7)
    const histData = histRes.data || histRes
    if (Array.isArray(histData)) {
      chaosHistory.value = histData.map(d => d.score ?? d.chaos_index ?? d.value ?? 0)
    } else if (histData.history) {
      chaosHistory.value = histData.history.map(d => d.score ?? d.value ?? 0)
    }
  } catch {
    // Use default trend
  }
}

onMounted(() => {
  fetchData()
  refreshInterval = setInterval(fetchData, 60000)
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})
</script>

<style scoped>
.risk-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0;
  flex: 1;
  padding: 8px 0;
}

/* Circular Gauge */
.risk-gauge-container {
  position: relative;
  width: 140px;
  height: 140px;
  margin: 8px 0 12px;
}

.risk-gauge {
  width: 100%;
  height: 100%;
}

.risk-gauge-arc {
  transition: stroke-dasharray 0.6s ease, stroke 0.3s ease;
}

.risk-gauge-label {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}

.risk-gauge-score {
  font-family: 'SF Mono', monospace;
  font-size: 36px;
  font-weight: 700;
  line-height: 1;
}

.risk-gauge-level {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 1px;
}

/* Trend */
.risk-trend {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 12px;
}

.risk-trend-label {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  font-weight: 600;
  color: var(--wm-text-dim, #888);
  letter-spacing: 0.5px;
}

.risk-trend-icon {
  font-size: 14px;
}

.risk-trend-text {
  font-family: 'SF Mono', monospace;
  font-size: 12px;
  color: var(--wm-text, #e8e8e8);
  font-weight: 600;
}

/* Divider */
.risk-divider {
  width: 100%;
  height: 1px;
  background: var(--wm-border, #2a2a2a);
}

/* Risk Factors */
.risk-factors-label {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  font-weight: 600;
  color: var(--wm-text-dim, #888);
  letter-spacing: 1px;
  text-transform: uppercase;
  padding: 10px 12px 6px;
  align-self: flex-start;
}

.risk-factors {
  width: 100%;
  display: flex;
  flex-direction: column;
}

.risk-factor-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 5px 12px;
}

.risk-factor-name {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--wm-text, #e8e8e8);
  min-width: 140px;
}

.risk-factor-bar-wrapper {
  flex: 1;
  height: 8px;
  position: relative;
  min-width: 60px;
}

.risk-factor-bar-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--wm-border, #2a2a2a);
  border-radius: 2px;
}

.risk-factor-bar {
  position: absolute;
  top: 0;
  left: 0;
  bottom: 0;
  border-radius: 2px;
  z-index: 1;
  transition: width 0.3s ease;
}

.risk-factor-value {
  font-family: 'SF Mono', monospace;
  font-size: 12px;
  font-weight: 700;
  min-width: 24px;
  text-align: right;
}
</style>
