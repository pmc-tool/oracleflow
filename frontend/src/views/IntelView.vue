<template>
  <div class="intel-page">
    <!-- Critical Alert Ticker (like WorldMonitor's red bar) -->
    <div v-if="criticalAlert" class="alert-ticker" :class="criticalAlert.severity">
      <span class="alert-ticker__badge">{{ criticalAlert.severity.toUpperCase() }}</span>
      <span class="alert-ticker__text">{{ criticalAlert.title }}</span>
      <span class="alert-ticker__source">{{ criticalAlert.source }} · just now</span>
      <button class="alert-ticker__close" @click="criticalAlert = null">✕</button>
    </div>

    <!-- Header -->
    <IntelHeader
      :userCategories="userInterests"
      @projectionChange="mapProjection = $event"
      @searchToggle="showMapSearch = !showMapSearch"
    />

    <!-- Simulation CTA Banner -->
    <SimulationCTA :maxSimulations="planConfig.limits?.max_simulations || 0" />

    <!-- Main Content -->
    <div class="main-content">
      <!-- TOP SECTION: Map + Side Panels (like WorldMonitor) -->
      <div class="top-section" :style="{ height: mapHeight + 'px' }">
        <!-- Map (left) + CII below -->
        <div class="map-column">
          <div class="map-section">
            <div class="map-container">
              <LayerSidebar @layerToggle="onLayerToggle" />
              <WorldMap
                ref="worldMapRef"
                :riskData="riskMap"
                :selectedCountry="selectedCountry"
                :activeLayers="activeLayers"
                :signals="signals"
                :projection="mapProjection"
                @countrySelected="onCountrySelected"
              />
              <MapSearch
                :visible="showMapSearch"
                @close="showMapSearch = false"
                @countrySelected="onMapSearchSelect"
              />
              <div class="time-range">
                <button
                  v-for="t in timeRanges"
                  :key="t"
                  class="time-btn"
                  :class="{ active: activeTime === t }"
                  @click="activeTime = t"
                >{{ t }}</button>
              </div>
            </div>
          </div>
          <!-- CII Panel below map on left (like WorldMonitor) -->
          <CIIPanel class="cii-below-map" />
        </div>

        <!-- Side panels (right of map — News video + Posture + Insights) -->
        <div class="side-panels">
          <NewsPanel />
          <div class="side-panels__bottom">
            <StrategicPosturePanel />
            <InsightsPanel />
          </div>
        </div>

        <!-- Resize handle -->
        <div
          class="map-resize-handle"
          @mousedown="startResize"
        ></div>
      </div>

      <!-- BOTTOM: Panels Grid -->
      <PanelGrid :panels="unlockedPanels" :savedPanelOrder="savedPanelOrder" />

      <!-- Locked Panels (over plan limit) -->
      <div v-if="lockedPanels.length > 0" class="locked-panels-section">
        <div class="locked-panels-header">
          <span class="locked-panels-label">{{ lockedPanels.length }} panel{{ lockedPanels.length > 1 ? 's' : '' }} locked</span>
          <span class="locked-panels-hint">Upgrade your plan to unlock</span>
        </div>
        <div class="locked-panels-grid">
          <div
            v-for="panel in lockedPanels"
            :key="panel.panelId"
            class="locked-panel-card"
            @click="showUpgradePrompt = true"
          >
            <div class="locked-panel-overlay">
              <svg class="locked-panel-icon" viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="11" width="18" height="11" rx="2" />
                <path d="M7 11V7a5 5 0 0 1 10 0v4" />
              </svg>
              <span class="locked-panel-text">Upgrade to unlock</span>
            </div>
            <div class="locked-panel-name">{{ panel.panelId }}</div>
          </div>
        </div>
      </div>

      <!-- Upgrade Prompt Modal -->
      <div v-if="showUpgradePrompt" class="upgrade-modal-backdrop" @click="showUpgradePrompt = false">
        <div class="upgrade-modal" @click.stop>
          <button class="upgrade-modal-close" @click="showUpgradePrompt = false">&#10005;</button>
          <h3 class="upgrade-modal-title">Unlock More Panels</h3>
          <p class="upgrade-modal-desc">
            Your <strong>{{ planConfig.plan?.toUpperCase() || 'FREE' }}</strong> plan includes {{ planConfig.limits?.max_panels || 6 }} panels.
            Upgrade to access all {{ filteredPanelConfig.length }} panels available for your interests.
          </p>
          <div class="upgrade-modal-plans">
            <a href="/settings" class="upgrade-modal-btn">View Plans &amp; Upgrade</a>
          </div>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <footer class="site-footer">
      <div class="site-footer-brand">ORACLEFLOW</div>
      <span class="site-footer-copy">&copy; 2026 OracleFlow</span>
    </footer>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, onUnmounted, shallowRef, markRaw } from 'vue'
import { listCountries, listSignals, getCountryRisk, getUserPreferences } from '../api/intelligence'
import service from '../api/index'
import IntelHeader from '../components/IntelHeader.vue'
import SimulationCTA from '../components/SimulationCTA.vue'
import WorldMap from '../components/WorldMap.vue'
import MapSearch from '../components/MapSearch.vue'
import LayerSidebar from '../components/LayerSidebar.vue'
import PanelGrid from '../components/PanelGrid.vue'
import NewsPanel from '../components/panels/NewsPanel.vue'
import CIIPanel from '../components/panels/CIIPanel.vue'
import InsightsPanel from '../components/panels/InsightsPanel.vue'
import StrategicPosturePanel from '../components/panels/StrategicPosturePanel.vue'
import MarketsPanel from '../components/panels/MarketsPanel.vue'
import DisplacementPanel from '../components/panels/DisplacementPanel.vue'
import CrossSourcePanel from '../components/panels/CrossSourcePanel.vue'
import CascadePanel from '../components/panels/CascadePanel.vue'
import RegionalNewsPanel from '../components/panels/RegionalNewsPanel.vue'
import ForecastPanel from '../components/panels/ForecastPanel.vue'
import EscalationPanel from '../components/panels/EscalationPanel.vue'
import EconomicPanel from '../components/panels/EconomicPanel.vue'
import CyberPanel from '../components/panels/CyberPanel.vue'
import SupplyChainPanel from '../components/panels/SupplyChainPanel.vue'
import WeatherPanel from '../components/panels/WeatherPanel.vue'
import RadiationPanel from '../components/panels/RadiationPanel.vue'
import SanctionsPanel from '../components/panels/SanctionsPanel.vue'
import RiskOverviewPanel from '../components/panels/RiskOverviewPanel.vue'
import HeatmapPanel from '../components/panels/HeatmapPanel.vue'
import PredictionPanel from '../components/panels/PredictionPanel.vue'
import TechEventsPanel from '../components/panels/TechEventsPanel.vue'
import SatellitePanel from '../components/panels/SatellitePanel.vue'
import GPSJamPanel from '../components/panels/GPSJamPanel.vue'
import WebcamsPanel from '../components/panels/WebcamsPanel.vue'
import AIForecastPanel from '../components/panels/AIForecastPanel.vue'
import IntelFeedPanel from '../components/panels/IntelFeedPanel.vue'
import MetalsPanel from '../components/panels/MetalsPanel.vue'
import EnergyPanel from '../components/panels/EnergyPanel.vue'
import MacroStressPanel from '../components/panels/MacroStressPanel.vue'
import TradePolicyPanel from '../components/panels/TradePolicyPanel.vue'

// Plan config for panel gating
const planConfig = ref({ plan: 'free', limits: { max_panels: 6, max_categories: 3, max_simulations: 0 }, usage: {} })
const showUpgradePrompt = ref(false)
const savedPanelOrder = ref([])

const selectedCountry = ref('')
const selectedCountryName = ref('')
const mapProjection = ref('2d')
const showMapSearch = ref(false)
const worldMapRef = ref(null)

// Critical alert ticker — shows the highest anomaly signal
const criticalAlert = ref(null)
const countries = ref([])
const riskMap = ref({})
const signals = ref([])
const activeLayers = reactive(new Set(['conflicts', 'earthquakes', 'bases']))

// Panel configuration
// Panels that go in the GRID below the map (excludes News, Posture, Insights which are in side-panels)
// User interest categories for panel filtering
const userInterests = ref(null)

const gridPanelConfig = shallowRef([
  // CII is placed below map on left — not in grid
  { component: markRaw(MarketsPanel), props: {}, panelId: 'markets', categories: ['finance', 'economy'] },
  { component: markRaw(DisplacementPanel), props: {}, panelId: 'displacement', categories: ['geopolitical', 'climate', 'humanitarian'] },
  { component: markRaw(CrossSourcePanel), props: {}, panelId: 'cross-source', defaultRowSpan: 2, categories: ['geopolitical', 'finance'] },
  { component: markRaw(CascadePanel), props: {}, panelId: 'cascade', categories: ['geopolitical', 'supply_chain'] },
  { component: markRaw(RegionalNewsPanel), props: {}, panelId: 'regional-news', defaultColSpan: 2, defaultRowSpan: 2, categories: ['politics', 'geopolitical'] },
  { component: markRaw(ForecastPanel), props: {}, panelId: 'forecast', categories: ['geopolitical', 'politics'] },
  { component: markRaw(EscalationPanel), props: {}, panelId: 'escalation', categories: ['geopolitical', 'crime'] },
  { component: markRaw(EconomicPanel), props: {}, panelId: 'economic', categories: ['economy', 'finance'] },
  { component: markRaw(CyberPanel), props: {}, panelId: 'cyber', categories: ['cyber', 'technology'] },
  { component: markRaw(SupplyChainPanel), props: {}, panelId: 'supply-chain', categories: ['supply_chain', 'economy'] },
  { component: markRaw(WeatherPanel), props: {}, panelId: 'weather', categories: ['climate'] },
  { component: markRaw(RadiationPanel), props: {}, panelId: 'radiation', categories: ['climate', 'technology'] },
  { component: markRaw(SanctionsPanel), props: {}, panelId: 'sanctions', categories: ['politics', 'geopolitical'] },
  { component: markRaw(RiskOverviewPanel), props: {}, panelId: 'risk-overview', defaultRowSpan: 2, categories: ['geopolitical', 'economy'] },
  { component: markRaw(HeatmapPanel), props: {}, panelId: 'heatmap', categories: ['geopolitical', 'climate'] },
  { component: markRaw(PredictionPanel), props: {}, panelId: 'prediction', categories: ['geopolitical', 'finance'] },
  { component: markRaw(TechEventsPanel), props: {}, panelId: 'tech-events', categories: ['technology'] },
  { component: markRaw(SatellitePanel), props: {}, panelId: 'satellite', categories: ['climate', 'geopolitical'] },
  { component: markRaw(GPSJamPanel), props: {}, panelId: 'gps-jam', categories: ['cyber', 'geopolitical'] },
  { component: markRaw(WebcamsPanel), props: {}, panelId: 'webcams', defaultColSpan: 2, defaultRowSpan: 2, categories: ['geopolitical'] },
  { component: markRaw(AIForecastPanel), props: {}, panelId: 'ai-forecast', defaultRowSpan: 2, categories: ['finance', 'geopolitical', 'technology'] },
  { component: markRaw(IntelFeedPanel), props: {}, panelId: 'intel-feed', defaultRowSpan: 2, categories: ['geopolitical', 'politics', 'cyber'] },
  { component: markRaw(MetalsPanel), props: {}, panelId: 'metals', categories: ['finance', 'supply_chain'] },
  { component: markRaw(EnergyPanel), props: {}, panelId: 'energy', categories: ['finance', 'supply_chain'] },
  { component: markRaw(MacroStressPanel), props: {}, panelId: 'macro-stress', categories: ['economy', 'finance'] },
  { component: markRaw(TradePolicyPanel), props: {}, panelId: 'trade-policy', categories: ['economy', 'politics'] },
])

// Filter panels by user interests — show all panels if no preferences loaded
const filteredPanelConfig = computed(() => {
  if (!userInterests.value || userInterests.value.length === 0) {
    return gridPanelConfig.value
  }
  const interests = new Set(userInterests.value)
  return gridPanelConfig.value.filter(panel =>
    panel.categories.some(cat => interests.has(cat))
  )
})

// Panel gating: split filtered panels into unlocked and locked based on plan limits
const maxPanels = computed(() => planConfig.value.limits?.max_panels || 6)

const unlockedPanels = computed(() => {
  return filteredPanelConfig.value.slice(0, maxPanels.value)
})

const lockedPanels = computed(() => {
  return filteredPanelConfig.value.slice(maxPanels.value)
})

const lockedPanelCount = computed(() => lockedPanels.value.length)

function onLayerToggle(layerId, enabled) {
  if (enabled) activeLayers.add(layerId)
  else activeLayers.delete(layerId)
}

const timeRanges = ['1h', '6h', '24h', '48h', '7d', 'all']
const activeTime = ref('24h')

// Map resize logic
const STORAGE_KEY = 'oracleflow-map-height'
const MIN_HEIGHT = 350
const MAX_HEIGHT_RATIO = 0.9

function getDefaultHeight() {
  const stored = localStorage.getItem(STORAGE_KEY)
  if (stored) {
    const val = parseInt(stored, 10)
    if (!isNaN(val) && val >= MIN_HEIGHT) return val
  }
  return Math.round(window.innerHeight * 0.5)
}

const mapHeight = ref(getDefaultHeight())
let isResizing = false

function startResize(e) {
  e.preventDefault()
  isResizing = true
  const startY = e.clientY
  const startH = mapHeight.value

  function onMove(ev) {
    if (!isResizing) return
    const delta = ev.clientY - startY
    const maxH = Math.round(window.innerHeight * MAX_HEIGHT_RATIO)
    const newH = Math.min(maxH, Math.max(MIN_HEIGHT, startH + delta))
    mapHeight.value = newH
  }

  function onUp() {
    isResizing = false
    localStorage.setItem(STORAGE_KEY, String(mapHeight.value))
    document.removeEventListener('mousemove', onMove)
    document.removeEventListener('mouseup', onUp)
    document.body.style.cursor = ''
    document.body.style.userSelect = ''
  }

  document.body.style.cursor = 'ns-resize'
  document.body.style.userSelect = 'none'
  document.addEventListener('mousemove', onMove)
  document.addEventListener('mouseup', onUp)
}

function onMapSearchSelect({ code, coords, name }) {
  selectedCountry.value = code
  selectedCountryName.value = name || code
  if (worldMapRef.value && coords) {
    worldMapRef.value.flyTo(coords, 4)
  }
}

function onCountrySelected(code) {
  selectedCountry.value = code
  const found = countries.value.find(c => c.code === code || c.iso_a2 === code)
  selectedCountryName.value = found ? (found.name || found.code) : code
}

// Re-fetch signals when time range changes
const timeMap = { '1h': '1h', '6h': '6h', '24h': '24h', '48h': '48h', '7d': '7d', 'all': '' }
watch(activeTime, async (t) => {
  try {
    const params = { limit: 200 }
    const since = timeMap[t]
    if (since) params.since = since
    const sigRes = await listSignals(params)
    signals.value = sigRes.data || sigRes.items || []
  } catch {
    // silent
  }
})

onMounted(async () => {
  // Fetch plan config for panel gating
  try {
    const configRes = await service.get('/api/auth/plan-config')
    const configData = configRes.data || configRes
    if (configData && configData.plan) {
      planConfig.value = configData
    }
  } catch {
    // Fallback: use free plan defaults
  }

  // Fetch user preferences for panel filtering
  try {
    const prefRes = await getUserPreferences()
    const prefData = prefRes.data || prefRes
    if (prefData && Array.isArray(prefData.interest_categories)) {
      userInterests.value = prefData.interest_categories
    }
    // Load saved panel order from server preferences
    if (prefData?.dashboard_config?.panel_order && Array.isArray(prefData.dashboard_config.panel_order)) {
      savedPanelOrder.value = prefData.dashboard_config.panel_order
    }
  } catch {
    // Fallback: show all panels if preferences can't be loaded
  }

  try {
    const res = await listCountries()
    const d = res.data || res
    countries.value = Array.isArray(d) ? d : (d.items || d.results || [])

    // Build risk map from country list data (chaos_index / risk_score)
    // instead of making N+1 sequential getCountryRisk() calls
    const map = {}
    for (const c of countries.value) {
      const code = c.code || c.iso_a2
      if (code) {
        const score = c.chaos_index ?? c.risk_score ?? c.overall_risk ?? 0
        map[code] = Math.round((score > 1 ? score : score * 100)) // Normalize to 0-100
      }
    }
    riskMap.value = map
    // Fetch signals for map layers
    const sigRes = await listSignals({ limit: 200 })
    signals.value = sigRes.data || sigRes.items || []

    // Set critical alert from highest anomaly signal
    if (signals.value.length > 0) {
      const sorted = [...signals.value].sort((a, b) => (b.anomaly_score || 0) - (a.anomaly_score || 0))
      const top = sorted[0]
      if (top && top.anomaly_score > 0.7) {
        criticalAlert.value = {
          severity: top.anomaly_score > 0.85 ? 'critical' : 'high',
          title: top.title,
          source: top.raw_data_json?.source_name || top.source || 'OracleFlow',
        }
      }
    }
  } catch {
    // silent
  }
})
</script>

<style scoped>
/* ============================================================
   Scoped WorldMonitor CSS Variables — exact copy from WM :root
   ============================================================ */
.intel-page {
  /* Backgrounds */
  --bg: #0a0a0a;
  --bg-secondary: #111;
  --surface: #141414;
  --surface-hover: #1e1e1e;
  --surface-active: #1a1a2e;

  /* Borders */
  --border: #2a2a2a;
  --border-strong: #444;
  --border-subtle: #1a1a1a;

  /* Text */
  --text: #e8e8e8;
  --text-secondary: #ccc;
  --text-dim: #888;
  --text-muted: #666;
  --text-faint: #555;
  --text-ghost: #444;
  --accent: #fff;

  /* Overlays & shadows */
  --overlay-subtle: rgba(255, 255, 255, 0.03);
  --overlay-light: rgba(255, 255, 255, 0.05);
  --overlay-medium: rgba(255, 255, 255, 0.1);
  --overlay-heavy: rgba(255, 255, 255, 0.2);
  --shadow-color: rgba(0, 0, 0, 0.5);

  /* Scrollbar */
  --scrollbar-thumb: #333;
  --scrollbar-thumb-hover: #555;

  /* Input */
  --input-bg: #1a1a1a;

  /* Panels */
  --panel-bg: #141414;
  --panel-border: #2a2a2a;

  /* Map */
  --map-bg: #020a08;
  --map-grid: #0a2a20;
  --map-country: #0a2018;
  --map-stroke: #0f5040;

  /* Font stack */
  --font-mono: 'SF Mono', 'Monaco', 'Cascadia Code', 'Fira Code', 'DejaVu Sans Mono', 'Liberation Mono', monospace;

  /* Severity */
  --semantic-critical: #ff4444;
  --semantic-high: #ff8800;
  --semantic-elevated: #ffaa00;
  --semantic-normal: #44aa44;
  --semantic-low: #3388ff;
  --semantic-info: #3b82f6;
  --semantic-positive: #44ff88;

  /* Status */
  --status-live: #44ff88;
  --status-cached: #ffaa00;
  --status-unavailable: #ff4444;

  /* Legacy aliases */
  --red: #ff4444;
  --green: #44ff88;
  --yellow: #ffaa00;

  /* DEFCON */
  --defcon-1: #ff0040;
  --defcon-2: #ff4400;
  --defcon-3: #ffaa00;
  --defcon-4: #00aaff;
  --defcon-5: #2d8a6e;

  /* Layout */
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 100vh;
  background: var(--bg);
  color: var(--text);
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.5;
  overflow: hidden;
}

/* ============================================================
   Main Content — WM exact
   ============================================================ */
.intel-page .main-content {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  overflow-x: hidden;
  background: var(--bg);
  width: 100%;
}

/* ============================================================
   Critical Alert Ticker — red bar at top (WorldMonitor style)
   ============================================================ */
.intel-page .alert-ticker {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 16px;
  background: #1a0000;
  border-bottom: 1px solid #ff4444;
  font-size: 12px;
  flex-shrink: 0;
  animation: alert-flash 2s ease-in-out;
}
.intel-page .alert-ticker.critical {
  background: linear-gradient(90deg, #2a0000 0%, #1a0000 100%);
  border-bottom-color: #ff0000;
}
.intel-page .alert-ticker.high {
  background: linear-gradient(90deg, #2a1500 0%, #1a0a00 100%);
  border-bottom-color: #ff8800;
}
.alert-ticker__badge {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1px;
  padding: 2px 8px;
  background: #ff4444;
  color: #fff;
}
.alert-ticker.high .alert-ticker__badge { background: #ff8800; }
.alert-ticker__text {
  flex: 1;
  font-weight: 500;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.alert-ticker__source {
  color: var(--text-dim);
  font-size: 11px;
  white-space: nowrap;
}
.alert-ticker__close {
  background: none;
  border: none;
  color: var(--text-dim);
  cursor: pointer;
  font-size: 14px;
  padding: 0 4px;
}
.alert-ticker__close:hover { color: var(--text); }
@keyframes alert-flash {
  0% { background: rgba(255, 0, 0, 0.2); }
  100% { background: #1a0000; }
}

/* ============================================================
   Top Section — Map + Side Panels (WorldMonitor layout)
   ============================================================ */
.intel-page .top-section {
  display: flex;
  flex-direction: row;
  min-height: 350px;
  max-height: 90vh;
  flex-shrink: 0;
  position: relative;
}

/* Map column — map on top, CII below */
.intel-page .map-column {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.intel-page .map-section {
  flex: 3;
  min-height: 300px;
  border: 1px solid var(--border);
  background: var(--surface);
  display: flex;
  flex-direction: column;
  position: relative;
}

.intel-page .cii-below-map {
  flex: 1;
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid var(--border);
  border-top: none;
}

/* Side panels — right of map */
.intel-page .side-panels {
  width: 35%;
  min-width: 340px;
  max-width: 500px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--border);
  border-left: none;
}

.intel-page .side-panels > * {
  overflow: hidden;
}

.intel-page .side-panels > :first-child {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

/* Bottom pair: Posture + Insights side by side */
.intel-page .side-panels__bottom {
  display: flex;
  flex-direction: row;
  border-top: 1px solid var(--border);
  flex-shrink: 0;
  height: 250px;
}

.intel-page .side-panels__bottom > * {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
}

.intel-page .side-panels__bottom > *:first-child {
  border-right: 1px solid var(--border);
}

.intel-page .map-container {
  flex: 1;
  position: relative;
  overflow: hidden;
  min-height: 0;
}

.intel-page .map-container :deep(.world-map-wrapper) {
  width: 100%;
  height: 100%;
  position: absolute;
  top: 0;
  left: 0;
}

.intel-page .map-container :deep(.world-map-container) {
  width: 100%;
  height: 100%;
}

.intel-page .map-container :deep(.maplibregl-map),
.intel-page .map-container :deep(.maplibregl-canvas) {
  width: 100% !important;
  height: 100% !important;
}

/* ============================================================
   Time Range Buttons
   ============================================================ */
.intel-page .time-range {
  position: absolute;
  top: 8px;
  right: 8px;
  display: flex;
  gap: 0;
  z-index: 10;
}

.intel-page .time-btn {
  background: var(--surface);
  border: 1px solid var(--border);
  color: var(--text-dim);
  font-family: var(--font-mono);
  font-size: 11px;
  padding: 3px 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}

.intel-page .time-btn:first-child {
  border-radius: 2px 0 0 2px;
}

.intel-page .time-btn:last-child {
  border-radius: 0 2px 2px 0;
}

.intel-page .time-btn + .time-btn {
  border-left: none;
}

.intel-page .time-btn.active {
  background: var(--surface-hover);
  color: var(--text);
  border-color: var(--border-strong);
}

.intel-page .time-btn:hover:not(.active) {
  background: var(--surface-hover);
  color: var(--text-secondary);
}

/* ============================================================
   Map Resize Handle — WM exact
   ============================================================ */
.intel-page .map-resize-handle {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 8px;
  cursor: ns-resize;
  background: linear-gradient(to bottom, transparent, var(--border));
  z-index: 200;
  display: flex;
  align-items: center;
  justify-content: center;
}

.intel-page .map-resize-handle::after {
  content: '';
  width: 40px;
  height: 3px;
  background: var(--text-dim);
  border-radius: 2px;
  opacity: 0.5;
  transition: opacity 0.2s;
}

.intel-page .map-resize-handle:hover::after {
  opacity: 1;
}

/* ============================================================
   Site Footer — WM exact
   ============================================================ */
.intel-page .site-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 20px;
  font-size: 11px;
  color: var(--text-dim);
  border-top: 1px solid var(--border);
  flex-shrink: 0;
  background: var(--surface);
}

.intel-page .site-footer-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  color: var(--text);
  letter-spacing: 1px;
}

.intel-page .site-footer nav {
  display: flex;
  gap: 16px;
}

.intel-page .site-footer a {
  color: var(--text-dim);
  font-family: var(--font-mono);
  text-decoration: none;
  transition: color 0.15s;
}

.intel-page .site-footer a:hover {
  color: var(--accent);
}

.intel-page .site-footer-copy {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-dim);
  opacity: 0.6;
}

/* ============================================================
   Locked Panels Section
   ============================================================ */
.intel-page .locked-panels-section {
  padding: 12px 16px;
}

.intel-page .locked-panels-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding: 8px 12px;
  background: rgba(255, 69, 0, 0.08);
  border: 1px solid rgba(255, 69, 0, 0.2);
  border-radius: 3px;
}

.intel-page .locked-panels-label {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 700;
  color: #FF4500;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.intel-page .locked-panels-hint {
  font-size: 11px;
  color: var(--text-dim);
}

.intel-page .locked-panels-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 8px;
}

.intel-page .locked-panel-card {
  position: relative;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 3px;
  height: 100px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  opacity: 0.5;
  transition: opacity 0.2s, border-color 0.2s;
}

.intel-page .locked-panel-card:hover {
  opacity: 0.75;
  border-color: rgba(255, 69, 0, 0.4);
}

.intel-page .locked-panel-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.intel-page .locked-panel-icon {
  color: var(--text-dim);
}

.intel-page .locked-panel-text {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-dim);
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.intel-page .locked-panel-name {
  position: absolute;
  bottom: 6px;
  font-family: var(--font-mono);
  font-size: 9px;
  color: var(--text-ghost);
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

/* ============================================================
   Upgrade Prompt Modal
   ============================================================ */
.intel-page .upgrade-modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.intel-page .upgrade-modal {
  background: #141414;
  border: 1px solid #2a2a2a;
  border-radius: 6px;
  padding: 32px;
  max-width: 440px;
  width: 90%;
  position: relative;
  text-align: center;
}

.intel-page .upgrade-modal-close {
  position: absolute;
  top: 12px;
  right: 14px;
  background: none;
  border: none;
  color: var(--text-dim);
  font-size: 16px;
  cursor: pointer;
}

.intel-page .upgrade-modal-close:hover {
  color: var(--text);
}

.intel-page .upgrade-modal-title {
  font-family: var(--font-mono);
  font-size: 16px;
  font-weight: 700;
  color: var(--text);
  margin: 0 0 12px;
}

.intel-page .upgrade-modal-desc {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0 0 24px;
}

.intel-page .upgrade-modal-btn {
  display: inline-block;
  background: #FF4500;
  color: #fff;
  text-decoration: none;
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 700;
  padding: 10px 24px;
  border-radius: 3px;
  letter-spacing: 0.5px;
  transition: background 0.2s;
}

.intel-page .upgrade-modal-btn:hover {
  background: #e03e00;
}

@media (max-width: 768px) {
  .intel-page .site-footer {
    flex-direction: column;
    gap: 10px;
    text-align: center;
    padding: 12px 16px;
  }
  .intel-page .site-footer nav {
    flex-wrap: wrap;
    justify-content: center;
    gap: 12px;
  }
}
</style>
