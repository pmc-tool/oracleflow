<template>
  <BasePanel
    panelId="prediction"
    title="PREDICTION MARKETS"
    infoTooltip="Representative prediction market data. Live API integration planned."
    dataBadge="DEMO"
  >
    <template #default>
      <div class="prediction-container">
        <div
          v-for="(market, idx) in markets"
          :key="idx"
          class="prediction-market"
        >
          <div class="prediction-question">{{ market.question }}</div>
          <div
            v-for="(outcome, oidx) in market.outcomes"
            :key="oidx"
            class="prediction-outcome"
          >
            <span class="prediction-label">{{ outcome.label }}</span>
            <div class="prediction-bar-track">
              <div
                class="prediction-bar-fill"
                :style="{ width: outcome.pct + '%', background: outcomeColor(outcome.pct) }"
              ></div>
            </div>
            <span class="prediction-pct">{{ outcome.pct }}%</span>
          </div>
        </div>
      </div>
    </template>
  </BasePanel>
</template>

<script setup>
import { ref } from 'vue'
import BasePanel from '../BasePanel.vue'

function outcomeColor(pct) {
  if (pct > 50) return 'var(--semantic-normal, #44aa44)'
  if (pct >= 25) return 'var(--semantic-elevated, #ffaa00)'
  return 'var(--semantic-critical, #ff4444)'
}

const markets = ref([
  {
    question: 'US Presidential Election 2028',
    outcomes: [
      { label: 'Trump wins', pct: 62 },
      { label: 'Harris wins', pct: 35 },
      { label: 'Other', pct: 3 },
    ]
  },
  {
    question: 'Iran Nuclear Deal',
    outcomes: [
      { label: 'Deal reached', pct: 18 },
      { label: 'No deal 2026', pct: 72 },
      { label: 'Conflict', pct: 10 },
    ]
  },
  {
    question: 'Taiwan Conflict by 2027',
    outcomes: [
      { label: 'Yes', pct: 12 },
      { label: 'No', pct: 88 },
    ]
  },
  {
    question: 'Fed Rate Cut Before Q3 2026',
    outcomes: [
      { label: 'Yes', pct: 41 },
      { label: 'No', pct: 59 },
    ]
  },
  {
    question: 'Ukraine Ceasefire 2026',
    outcomes: [
      { label: 'Ceasefire', pct: 22 },
      { label: 'Continued conflict', pct: 68 },
      { label: 'Full peace deal', pct: 10 },
    ]
  }
])
</script>

<style scoped>
.prediction-container {
  overflow-y: auto;
  flex: 1;
}

.prediction-market {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border, #2a2a2a);
}

.prediction-market:last-child {
  border-bottom: none;
}

.prediction-question {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  font-weight: 700;
  color: var(--text, #e8e8e8);
  margin-bottom: 6px;
}

.prediction-outcome {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 2px 0;
}

.prediction-label {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--text-dim, #888);
  width: 120px;
  flex-shrink: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.prediction-bar-track {
  flex: 1;
  height: 10px;
  background: var(--border, #2a2a2a);
  position: relative;
  overflow: hidden;
}

.prediction-bar-fill {
  height: 100%;
  transition: width 0.4s ease;
}

.prediction-pct {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-dim, #888);
  width: 32px;
  text-align: right;
  flex-shrink: 0;
}
</style>
