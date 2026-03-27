<template>
  <BasePanel panelId="cascade" title="DISASTER CASCADE"
    infoTooltip="Detects when multiple signal types converge on the same region within 24 hours."
    :showCount="true" :count="totalConvergences">
    <template #default>
      <div v-if="convergences.length === 0" class="cascade-empty">
        No active convergence detected
      </div>

      <div v-else class="cascade-list">
        <div
          v-for="conv in convergences"
          :key="conv.country"
          class="cascade-item"
        >
          <div class="cascade-item__header">
            <span class="cascade-item__warning">&#9888;</span>
            <span class="cascade-item__label">CONVERGENCE DETECTED</span>
            <span
              class="cascade-item__severity"
              :class="'severity--' + conv.severity.toLowerCase()"
            >{{ conv.severity }}</span>
          </div>
          <div class="cascade-item__country">
            {{ conv.countryName }} &mdash; {{ conv.categoryCount }} signal types
          </div>
          <div class="cascade-item__tree">
            <div
              v-for="(cat, idx) in conv.categories"
              :key="cat.name"
              class="cascade-item__branch"
            >
              <span class="cascade-item__connector">{{ idx < conv.categories.length - 1 ? '\u251C\u2500\u2500' : '\u2514\u2500\u2500' }}</span>
              <span class="cascade-item__icon">{{ cat.icon }}</span>
              <span class="cascade-item__cat-name">{{ cat.name }}</span>
              <span class="cascade-item__cat-count">({{ cat.count }} signals)</span>
            </div>
          </div>
          <div class="cascade-item__timeframe">Timeframe: last 24h</div>
        </div>
      </div>
    </template>
  </BasePanel>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import BasePanel from '../BasePanel.vue'
import { listSignals } from '../../api/intelligence'

const signals = ref([])
let refreshInterval = null

const CATEGORY_ICONS = {
  politics: '\uD83D\uDCF0',
  economy: '\uD83D\uDCB0',
  healthcare: '\uD83C\uDFE5',
  climate: '\uD83C\uDF0D',
  cyber: '\uD83D\uDEE1',
  crime: '\uD83D\uDD2B',
  finance: '\uD83D\uDCC8',
  geopolitical: '\u2694',
}

const CATEGORY_LABELS = {
  politics: 'POLITICAL',
  economy: 'ECONOMIC',
  healthcare: 'HEALTHCARE',
  climate: 'CLIMATE',
  cyber: 'CYBER',
  crime: 'CRIME',
  finance: 'FINANCE',
  geopolitical: 'GEOPOLITICAL',
}

const COUNTRY_NAMES = {
  US: 'United States', GB: 'United Kingdom', DE: 'Germany', FR: 'France',
  IT: 'Italy', ES: 'Spain', JP: 'Japan', CN: 'China', RU: 'Russia',
  BR: 'Brazil', IN: 'India', AU: 'Australia', CA: 'Canada', MX: 'Mexico',
  ZA: 'South Africa', NG: 'Nigeria', KE: 'Kenya', IL: 'Israel', IR: 'Iran',
  IQ: 'Iraq', SY: 'Syria', SA: 'Saudi Arabia', AE: 'UAE', UA: 'Ukraine',
  PL: 'Poland', KR: 'South Korea', KP: 'North Korea', PK: 'Pakistan',
  JM: 'Jamaica', TT: 'Trinidad & Tobago', BB: 'Barbados', HT: 'Haiti',
  DO: 'Dominican Republic', GT: 'Guatemala', HN: 'Honduras', AR: 'Argentina',
  CO: 'Colombia', VE: 'Venezuela', CL: 'Chile', PE: 'Peru', EC: 'Ecuador',
  CU: 'Cuba', EG: 'Egypt', ET: 'Ethiopia', GH: 'Ghana', TZ: 'Tanzania',
  CD: 'DR Congo', SD: 'Sudan', SS: 'South Sudan', SO: 'Somalia',
  PH: 'Philippines', TH: 'Thailand', VN: 'Vietnam', MY: 'Malaysia',
  SG: 'Singapore', ID: 'Indonesia', MM: 'Myanmar', TW: 'Taiwan',
  NZ: 'New Zealand', BD: 'Bangladesh', LK: 'Sri Lanka',
  QA: 'Qatar', KW: 'Kuwait', YE: 'Yemen', PS: 'Palestine',
  JO: 'Jordan', LB: 'Lebanon', OM: 'Oman', BH: 'Bahrain',
  NL: 'Netherlands', SE: 'Sweden', NO: 'Norway', DK: 'Denmark',
  FI: 'Finland', AT: 'Austria', CH: 'Switzerland', BE: 'Belgium',
  IE: 'Ireland', CZ: 'Czech Republic', PT: 'Portugal', GR: 'Greece',
  RO: 'Romania', HU: 'Hungary', ML: 'Mali', NE: 'Niger',
  BF: 'Burkina Faso', CM: 'Cameroon', SN: 'Senegal',
}

const convergences = computed(() => {
  const now = Date.now()
  const cutoff = now - 24 * 60 * 60 * 1000

  // Filter to last 24h signals with country_code
  const recent = signals.value.filter(s => {
    if (!s.country_code) return false
    const t = new Date(s.created_at).getTime()
    return t >= cutoff
  })

  // Group by country_code, then by category
  const byCountry = {}
  recent.forEach(s => {
    const cc = s.country_code
    if (!byCountry[cc]) byCountry[cc] = {}
    const cat = (s.category || 'unknown').toLowerCase()
    if (!byCountry[cc][cat]) byCountry[cc][cat] = []
    byCountry[cc][cat].push(s)
  })

  // Build convergence list (3+ categories)
  const results = []
  for (const [cc, cats] of Object.entries(byCountry)) {
    const catKeys = Object.keys(cats)
    if (catKeys.length >= 2) {
      const totalSignals = Object.values(cats).reduce((sum, arr) => sum + arr.length, 0)
      const severity = catKeys.length >= 4 ? 'CRITICAL' : catKeys.length >= 3 ? 'HIGH' : 'ELEVATED'
      const categories = catKeys
        .map(k => ({
          name: CATEGORY_LABELS[k] || k.toUpperCase(),
          icon: CATEGORY_ICONS[k] || '\uD83D\uDCCB',
          count: cats[k].length,
        }))
        .sort((a, b) => b.count - a.count)

      results.push({
        country: cc,
        countryName: COUNTRY_NAMES[cc] || cc,
        categoryCount: catKeys.length,
        totalSignals,
        severity,
        categories,
      })
    }
  }

  // Sort: CRITICAL first, then by total signals
  const severityOrder = { CRITICAL: 0, HIGH: 1, ELEVATED: 2 }
  results.sort((a, b) => {
    const so = (severityOrder[a.severity] ?? 9) - (severityOrder[b.severity] ?? 9)
    if (so !== 0) return so
    return b.totalSignals - a.totalSignals
  })

  return results
})

const totalConvergences = computed(() => convergences.value.length)

async function fetchSignals() {
  try {
    const res = await listSignals({ limit: 200 })
    const data = res.data?.results || res.data || []
    signals.value = Array.isArray(data) ? data : []
  } catch (err) {
    console.error('[CascadePanel] fetch error:', err)
  }
}

onMounted(() => {
  fetchSignals()
  refreshInterval = setInterval(fetchSignals, 120000)
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})
</script>

<style scoped>
.cascade-empty {
  padding: 24px;
  text-align: center;
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--text-dim);
}

.cascade-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.cascade-item {
  border: 1px solid var(--border);
  padding: 10px;
  background: var(--surface);
}

.cascade-item__header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.cascade-item__warning {
  font-size: 12px;
  color: var(--semantic-high);
}

.cascade-item__label {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text);
  flex: 1;
}

.cascade-item__severity {
  font-family: 'SF Mono', monospace;
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  padding: 1px 6px;
  border-radius: 2px;
}

.severity--critical {
  background: var(--semantic-critical);
  color: #fff;
}

.severity--high {
  background: var(--semantic-high);
  color: #fff;
}

.severity--elevated {
  background: var(--semantic-elevated);
  color: #1a1a1a;
}

.cascade-item__country {
  font-family: 'SF Mono', monospace;
  font-size: 12px;
  font-weight: 500;
  color: var(--text);
  margin-bottom: 6px;
}

.cascade-item__tree {
  margin-bottom: 6px;
  padding-left: 4px;
}

.cascade-item__branch {
  display: flex;
  align-items: center;
  gap: 4px;
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  line-height: 1.6;
}

.cascade-item__connector {
  color: var(--text-muted);
  font-size: 12px;
}

.cascade-item__icon {
  font-size: 11px;
}

.cascade-item__cat-name {
  color: var(--text-dim);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  font-size: 10px;
  font-weight: 600;
}

.cascade-item__cat-count {
  color: var(--text-muted);
  font-size: 10px;
}

.cascade-item__timeframe {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  color: var(--text-muted);
}
</style>
