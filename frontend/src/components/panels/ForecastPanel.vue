<template>
  <BasePanel panelId="forecast" title="AI FORECAST"
    infoTooltip="AI-generated scenario predictions based on completed simulations.">
    <template #default>
      <div v-if="loading" class="forecast-empty">
        Loading forecasts...
      </div>

      <div v-else-if="forecasts.length === 0" class="forecast-empty">
        No forecasts yet. Run a simulation to generate predictions.
      </div>

      <div v-else class="forecast-list">
        <div class="forecast-section-title">SCENARIO PREDICTIONS</div>

        <div
          v-for="fc in forecasts"
          :key="fc.id"
          class="forecast-card"
        >
          <div class="forecast-card__title">{{ fc.title }}</div>
          <div class="forecast-card__bar-row">
            <span class="forecast-card__bar-label">Probability:</span>
            <div class="forecast-card__bar">
              <div
                class="forecast-card__bar-fill"
                :style="{ width: fc.probability + '%' }"
                :class="barClass(fc.probability)"
              ></div>
            </div>
            <span class="forecast-card__bar-value">{{ fc.probability }}%</span>
          </div>
          <div class="forecast-card__meta">
            <span class="forecast-card__impact">
              Impact:
              <span :class="'impact--' + fc.impact.toLowerCase()">{{ fc.impact }}</span>
            </span>
          </div>
          <div class="forecast-card__signals">
            Based on {{ fc.signalCount }} signals
          </div>
        </div>
      </div>

      <button class="forecast-run-btn" @click="goSimulate">
        + Run New Simulation
      </button>
    </template>
  </BasePanel>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import BasePanel from '../BasePanel.vue'
import { listSimulations } from '../../api/intelligence'

const router = useRouter()
const simulations = ref([])
const loading = ref(true)

const forecasts = computed(() => {
  return simulations.value.map(sim => {
    let probability = 50
    let reportData = null

    // Parse report_json if available
    if (sim.report_json) {
      try {
        reportData = typeof sim.report_json === 'string'
          ? JSON.parse(sim.report_json)
          : sim.report_json
      } catch {
        reportData = null
      }
    }

    if (reportData && reportData.overall_sentiment != null) {
      probability = Math.round(Math.abs(reportData.overall_sentiment) * 100)
    }

    // Clamp
    probability = Math.max(0, Math.min(100, probability))

    // Impact level from probability
    let impact = 'LOW'
    if (probability >= 75) impact = 'CRITICAL'
    else if (probability >= 60) impact = 'HIGH'
    else if (probability >= 40) impact = 'MEDIUM'

    const signalCount = sim.signal_count || reportData?.signal_count || 0

    return {
      id: sim.id,
      title: sim.scenario || sim.title || sim.simulation_requirement || `Scenario #${sim.id}`,
      probability,
      impact,
      signalCount,
    }
  })
})

function barClass(prob) {
  if (prob >= 75) return 'bar--critical'
  if (prob >= 60) return 'bar--high'
  if (prob >= 40) return 'bar--elevated'
  return 'bar--normal'
}

function goSimulate() {
  router.push('/simulate')
}

async function fetchSimulations() {
  loading.value = true
  try {
    const res = await listSimulations()
    const data = res.data?.results || res.data || []
    simulations.value = Array.isArray(data) ? data : []
  } catch (err) {
    console.error('[ForecastPanel] fetch error:', err)
    simulations.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchSimulations()
})
</script>

<style scoped>
.forecast-empty {
  padding: 24px;
  text-align: center;
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--text-dim);
}

.forecast-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.forecast-section-title {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-dim);
  margin-bottom: 4px;
}

.forecast-card {
  border: 1px solid var(--border);
  padding: 10px;
  background: var(--surface);
}

.forecast-card__title {
  font-family: 'SF Mono', monospace;
  font-size: 12px;
  font-weight: 600;
  color: var(--text);
  margin-bottom: 8px;
  line-height: 1.4;
}

.forecast-card__bar-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.forecast-card__bar-label {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  color: var(--text-dim);
  white-space: nowrap;
}

.forecast-card__bar {
  flex: 1;
  height: 8px;
  background: var(--border);
  border-radius: 1px;
  overflow: hidden;
}

.forecast-card__bar-fill {
  height: 100%;
  border-radius: 1px;
  transition: width 0.5s ease;
}

.bar--critical {
  background: var(--semantic-critical);
}

.bar--high {
  background: var(--semantic-high);
}

.bar--elevated {
  background: var(--semantic-elevated);
}

.bar--normal {
  background: var(--semantic-normal);
}

.forecast-card__bar-value {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  font-weight: 600;
  color: var(--text);
  min-width: 32px;
  text-align: right;
}

.forecast-card__meta {
  margin-bottom: 4px;
}

.forecast-card__impact {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  color: var(--text-dim);
}

.impact--critical {
  color: var(--semantic-critical);
  font-weight: 700;
}

.impact--high {
  color: var(--semantic-high);
  font-weight: 700;
}

.impact--medium {
  color: var(--semantic-elevated);
  font-weight: 700;
}

.impact--low {
  color: var(--semantic-normal);
  font-weight: 700;
}

.forecast-card__signals {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  color: var(--text-muted);
}

.forecast-run-btn {
  display: block;
  width: 100%;
  margin-top: 8px;
  padding: 8px;
  background: transparent;
  border: 1px solid var(--border);
  color: var(--text-dim);
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.forecast-run-btn:hover {
  background: var(--surface-hover, #1e1e1e);
  color: var(--text);
  border-color: var(--text-dim);
}
</style>
