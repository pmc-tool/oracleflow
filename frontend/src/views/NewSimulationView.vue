<template>
  <div class="new-sim">
    <h1 class="page-title">New Simulation</h1>
    <p class="page-desc">Select intelligence signals and describe a scenario. OracleFlow will build a simulation document, generate AI agents, and predict outcomes.</p>

    <!-- Signal pre-fill banner -->
    <div v-if="signalBannerTitle" class="signal-prefill-banner">
      <span class="prefill-icon">&#9889;</span>
      <span class="prefill-text">Simulating impact of: <strong>{{ signalBannerTitle }}</strong></span>
    </div>

    <!-- Step 1: Select Signals -->
    <div class="section">
      <div class="section-header">
        <span class="step-num">01</span>
        <span class="step-label">Select Signals</span>
        <span class="step-hint">Choose signals to include as context for the simulation</span>
      </div>

      <!-- Filter controls -->
      <div class="signal-filters">
        <div class="filter-row">
          <input
            v-model="searchQuery"
            type="text"
            class="filter-input search-input"
            placeholder="Search signals by keyword..."
            @input="onSearchInput"
          />
          <select v-model="filterCategory" class="filter-input filter-select" @change="resetAndFetch">
            <option value="">All categories</option>
            <option value="finance">Finance</option>
            <option value="geopolitical">Geopolitical</option>
            <option value="supply_chain">Supply Chain</option>
            <option value="cyber">Cyber</option>
            <option value="climate">Climate</option>
            <option value="politics">Politics</option>
            <option value="healthcare">Healthcare</option>
            <option value="economy">Economy</option>
            <option value="crime">Crime</option>
            <option value="education">Education</option>
            <option value="technology">Technology</option>
            <option value="other">Other</option>
          </select>
          <select v-model="filterThreat" class="filter-input filter-select" @change="resetAndFetch">
            <option value="">All threat levels</option>
            <option value="0.7">High threat only (&gt;70%)</option>
            <option value="0.6">Elevated+ (&gt;60%)</option>
          </select>
          <select v-model="filterDateRange" class="filter-input filter-select" @change="resetAndFetch">
            <option value="">All time</option>
            <option value="24h">Last 24h</option>
            <option value="7d">Last 7 days</option>
            <option value="30d">Last 30 days</option>
          </select>
        </div>
        <div class="filter-actions">
          <button class="quick-filter-btn" :class="{ active: topThreatsActive }" @click="toggleTopThreats">
            Top Threats
          </button>
        </div>
      </div>

      <!-- Selection counter and clear -->
      <div class="selection-bar" v-if="selectedIds.size > 0 || signals.length > 0">
        <span class="selection-counter">
          <strong>{{ selectedIds.size }}</strong>/{{ MAX_SELECTION }} signals selected
        </span>
        <button v-if="selectedIds.size > 0" class="clear-btn" @click="clearSelection">Clear all</button>
      </div>

      <!-- Suggested signals from scenario text -->
      <div v-if="suggestedSignals.length > 0" class="suggested-section">
        <div class="suggested-header">Suggested signals (based on your scenario)</div>
        <div class="suggested-list">
          <label
            v-for="sig in suggestedSignals"
            :key="'sug-' + sig.id"
            class="signal-item suggested"
            :class="{ selected: selectedIds.has(sig.id) }"
          >
            <input type="checkbox" :value="sig.id" @change="toggleSignal(sig.id)" :checked="selectedIds.has(sig.id)" />
            <div class="signal-content">
              <div class="signal-top">
                <span class="signal-title">{{ sig.title }}</span>
                <span class="anomaly-badge" :style="{ background: anomalyColor(sig.anomaly_score) }">
                  {{ (sig.anomaly_score * 100).toFixed(0) }}%
                </span>
              </div>
              <div class="signal-meta">
                <span class="meta-badge source">{{ sig.source }}</span>
                <span class="meta-badge category">{{ sig.category?.replace(/_/g, ' ') }}</span>
                <span class="meta-time">{{ formatTime(sig.timestamp) }}</span>
              </div>
            </div>
          </label>
        </div>
      </div>

      <div v-if="loadingSignals && signals.length === 0" class="loading-text">Loading signals...</div>
      <div v-else-if="!loadingSignals && signals.length === 0" class="empty-text">
        No signals match your filters. Try broadening your search.
      </div>

      <div v-else class="signals-list">
        <label
          v-for="sig in signals"
          :key="sig.id"
          class="signal-item"
          :class="{ selected: selectedIds.has(sig.id), disabled: !selectedIds.has(sig.id) && selectedIds.size >= MAX_SELECTION }"
        >
          <input
            type="checkbox"
            :value="sig.id"
            @change="toggleSignal(sig.id)"
            :checked="selectedIds.has(sig.id)"
            :disabled="!selectedIds.has(sig.id) && selectedIds.size >= MAX_SELECTION"
          />
          <div class="signal-content">
            <div class="signal-top">
              <span class="signal-title">{{ sig.title }}</span>
              <span class="anomaly-badge" :style="{ background: anomalyColor(sig.anomaly_score) }">
                {{ (sig.anomaly_score * 100).toFixed(0) }}%
              </span>
            </div>
            <div class="signal-meta">
              <span class="meta-badge source">{{ sig.source }}</span>
              <span class="meta-badge category">{{ sig.category?.replace(/_/g, ' ') }}</span>
              <span class="meta-country" v-if="sig.country_code">{{ sig.country_code }}</span>
              <span class="meta-time">{{ formatTime(sig.timestamp) }}</span>
            </div>
            <div class="signal-summary" v-if="sig.summary">{{ sig.summary }}</div>
          </div>
        </label>
      </div>

      <!-- Load more / pagination -->
      <div class="load-more-bar" v-if="signals.length > 0 && hasMore">
        <button class="load-more-btn" @click="loadMore" :disabled="loadingMore">
          <span v-if="loadingMore">Loading...</span>
          <span v-else>Load more ({{ signalTotal - signals.length }} remaining)</span>
        </button>
      </div>
      <div class="load-more-bar" v-if="signals.length > 0 && !hasMore && signalTotal > 0">
        <span class="all-loaded-text">All {{ signalTotal }} matching signals loaded</span>
      </div>
    </div>

    <!-- Step 2: Scenario Prompt -->
    <div class="section">
      <div class="section-header">
        <span class="step-num">02</span>
        <span class="step-label">Scenario Prompt</span>
        <span class="step-hint">Describe what you want to predict</span>
      </div>

      <textarea
        v-model="scenario"
        class="scenario-input"
        placeholder="What happens if PNP wins the election and implements free healthcare?&#10;&#10;How will voters react to this policy change?&#10;Which demographic will be most affected?"
        rows="6"
        @input="onScenarioInput"
      ></textarea>
    </div>

    <!-- Step 3: Configuration -->
    <div class="section">
      <div class="section-header">
        <span class="step-num">03</span>
        <span class="step-label">Configuration</span>
      </div>

      <div class="config-row">
        <div class="config-item">
          <label>Platform</label>
          <select v-model="platform" class="config-select">
            <option value="twitter">Twitter (short-form debate)</option>
            <option value="reddit">Reddit (long-form discussion)</option>
          </select>
        </div>
        <div class="config-item">
          <label>Rounds</label>
          <select v-model="rounds" class="config-select">
            <option :value="1">1 round (quick test)</option>
            <option :value="3">3 rounds (fast)</option>
            <option :value="5">5 rounds (standard)</option>
            <option :value="10">10 rounds (balanced)</option>
            <option :value="20">20 rounds (deep)</option>
          </select>
        </div>
      </div>
    </div>

    <!-- Status / Progress -->
    <div class="section" v-if="status">
      <div class="status-box" :class="statusClass">
        <div class="status-icon">{{ statusIcon }}</div>
        <div class="status-text">
          <div class="status-title">{{ status }}</div>
          <div class="status-detail" v-if="statusDetail">{{ statusDetail }}</div>
        </div>
      </div>

      <!-- Progress steps -->
      <div class="progress-steps" v-if="running">
        <div v-for="(step, i) in progressSteps" :key="i" class="progress-step" :class="{ done: step.done, active: step.active }">
          <span class="progress-dot"></span>
          <span>{{ step.label }}</span>
        </div>
      </div>
    </div>

    <!-- Toast notification -->
    <Transition name="toast-fade">
      <div v-if="toastMessage" class="toast-notification">
        <span class="toast-text">{{ toastMessage }}</span>
        <button class="toast-close" @click="toastMessage = ''">&times;</button>
      </div>
    </Transition>

    <!-- Error -->
    <div class="error-box" v-if="error">{{ error }}</div>

    <!-- Action Button -->
    <button
      class="run-btn"
      @click="runSimulation"
      :disabled="running || (selectedIds.size === 0 && !scenario.trim())"
    >
      <span v-if="running">Simulation Running...</span>
      <span v-else>Run Simulation &rarr;</span>
    </button>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { listSignals } from '../api/intelligence'
import { generateOntology, buildGraph, getTaskStatus } from '../api/graph'
import { createSimulation, prepareSimulation, getPrepareStatus, startSimulation, getRunStatus } from '../api/simulation'
import { generateReport, getReportStatus, getReport } from '../api/report'

const router = useRouter()
const route = useRoute()

const PAGE_SIZE = 20
const MAX_SELECTION = 30

const signalBannerTitle = ref('')
const signals = ref([])
const signalTotal = ref(0)
const loadingSignals = ref(true)
const loadingMore = ref(false)
const selectedIds = reactive(new Set())
const scenario = ref('')
const platform = ref('twitter')
const rounds = ref(1)
const status = ref('')
const statusDetail = ref('')
const statusClass = ref('')
const statusIcon = ref('')
const running = ref(false)
const error = ref('')
const toastMessage = ref('')
const suggestedSignals = ref([])

// Filter state
const searchQuery = ref('')
const filterCategory = ref('')
const filterThreat = ref('')
const filterDateRange = ref('')
const topThreatsActive = ref(false)
const currentOffset = ref(0)

// Debounce timers
let searchTimer = null
let scenarioTimer = null

const hasMore = computed(() => signals.value.length < signalTotal.value)

const progressSteps = ref([
  { label: 'Building knowledge graph...', done: false, active: false },
  { label: 'Generating agent personas...', done: false, active: false },
  { label: 'Running simulation...', done: false, active: false },
  { label: 'Generating report...', done: false, active: false },
])

// Category-to-agent mapping for auto-selection
const CATEGORY_AGENT_MAP = {
  finance: ['economist', 'financial_analyst', 'market_strategist'],
  economy: ['economist', 'financial_analyst', 'policy_analyst'],
  politics: ['political_analyst', 'policy_analyst', 'diplomat'],
  geopolitical: ['geopolitical_analyst', 'diplomat', 'military_strategist'],
  healthcare: ['health_policy_analyst', 'epidemiologist', 'public_health'],
  climate: ['climate_scientist', 'environmental_analyst', 'policy_analyst'],
  cyber: ['cybersecurity_analyst', 'tech_strategist', 'intelligence_analyst'],
  crime: ['security_analyst', 'intelligence_analyst', 'law_enforcement'],
}

// Build query params from current filter state
function buildParams(offset = 0, limit = PAGE_SIZE) {
  const params = { limit, offset }
  if (searchQuery.value.trim()) params.search = searchQuery.value.trim()
  if (filterCategory.value) params.category = filterCategory.value
  if (filterDateRange.value) params.since = filterDateRange.value
  if (filterThreat.value) params.min_anomaly_score = parseFloat(filterThreat.value)
  else if (topThreatsActive.value) params.min_anomaly_score = 0.7
  return params
}

async function fetchSignals(append = false) {
  if (!append) {
    loadingSignals.value = true
    currentOffset.value = 0
  } else {
    loadingMore.value = true
  }

  try {
    const params = buildParams(currentOffset.value)
    const res = await listSignals(params)
    const data = res.data?.data || res.data || []
    const total = res.data?.total ?? data.length

    if (append) {
      signals.value = [...signals.value, ...data]
    } else {
      signals.value = data
    }
    signalTotal.value = total
  } catch (e) {
    console.error('Failed to load signals:', e)
  } finally {
    loadingSignals.value = false
    loadingMore.value = false
  }
}

function resetAndFetch() {
  currentOffset.value = 0
  fetchSignals(false)
}

function loadMore() {
  currentOffset.value = signals.value.length
  fetchSignals(true)
}

// Debounced search: 300ms
function onSearchInput() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    resetAndFetch()
  }, 300)
}

// Top threats quick-filter toggle
function toggleTopThreats() {
  topThreatsActive.value = !topThreatsActive.value
  // Clear the dropdown threat filter when using quick-filter
  if (topThreatsActive.value) filterThreat.value = ''
  resetAndFetch()
}

// Auto-suggest signals from scenario text (2s debounce)
function onScenarioInput() {
  clearTimeout(scenarioTimer)
  scenarioTimer = setTimeout(async () => {
    const text = scenario.value.trim()
    if (text.length < 10) {
      suggestedSignals.value = []
      return
    }
    // Extract keywords: take significant words (>3 chars), pick up to 3
    const words = text.split(/\s+/).filter(w => w.length > 3)
    const keywords = words.slice(0, 3).join(' ')
    if (!keywords) {
      suggestedSignals.value = []
      return
    }
    try {
      const res = await listSignals({ search: keywords, limit: 5, min_anomaly_score: 0.3 })
      const data = res.data?.data || res.data || []
      // Exclude signals already in the main list to avoid confusion
      suggestedSignals.value = data.filter(s => !signals.value.some(ms => ms.id === s.id))
    } catch {
      suggestedSignals.value = []
    }
  }, 2000)
}

function toggleSignal(id) {
  if (selectedIds.has(id)) {
    selectedIds.delete(id)
  } else if (selectedIds.size < MAX_SELECTION) {
    selectedIds.add(id)
  }
}

function clearSelection() {
  selectedIds.clear()
}

function anomalyColor(score) {
  if (score >= 0.8) return '#FF4500'
  if (score >= 0.6) return '#FF8C00'
  if (score >= 0.3) return '#FFD700'
  return '#444'
}

function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  const now = new Date()
  const diff = (now - d) / 1000 / 3600
  if (diff < 1) return `${Math.round(diff * 60)}m ago`
  if (diff < 24) return `${Math.round(diff)}h ago`
  return d.toLocaleDateString()
}

function setProgress(stepIndex) {
  progressSteps.value.forEach((s, i) => {
    s.done = i < stepIndex
    s.active = i === stepIndex
  })
}

function showToast(message, duration = 5000) {
  toastMessage.value = message
  setTimeout(() => {
    toastMessage.value = ''
  }, duration)
}

async function pollTask(taskId, maxWait = 600) {
  const start = Date.now()
  while ((Date.now() - start) / 1000 < maxWait) {
    await new Promise(r => setTimeout(r, 3000))
    try {
      const res = await getTaskStatus(taskId)
      const s = res.data?.status || res.status
      if (s === 'completed' || s === 'COMPLETED') return res.data || res
      if (s === 'failed' || s === 'FAILED') throw new Error(res.data?.error || 'Task failed')
      statusDetail.value = `Progress: ${res.data?.progress || 0}%`
    } catch (e) {
      throw e
    }
  }
  throw new Error('Timed out waiting for task')
}

async function runSimulation() {
  running.value = true
  error.value = ''
  status.value = 'Preparing simulation...'
  statusClass.value = 'info'
  statusIcon.value = '\u27F3'

  try {
    // Build document from selected signals (merge from both main list and suggestions)
    const allAvailable = [...signals.value, ...suggestedSignals.value]
    const seen = new Set()
    const deduped = allAvailable.filter(s => {
      if (seen.has(s.id)) return false
      seen.add(s.id)
      return true
    })
    const selectedSignals = deduped.filter(s => selectedIds.has(s.id))

    let docContent = `# Simulation Scenario\n\n`
    if (scenario.value.trim()) {
      docContent += `## Question\n${scenario.value.trim()}\n\n`
    }
    if (selectedSignals.length > 0) {
      docContent += `## Intelligence Signals\n\n`
      for (const sig of selectedSignals) {
        docContent += `### ${sig.title}\n`
        docContent += `- Source: ${sig.source} | Category: ${sig.category} | Country: ${sig.country_code || 'Global'}\n`
        docContent += `- Anomaly Score: ${(sig.anomaly_score * 100).toFixed(0)}% | Sentiment: ${(sig.sentiment_score * 100).toFixed(0)}%\n`
        if (sig.summary) docContent += `- ${sig.summary}\n`
        docContent += '\n'
      }
    }

    // Step 1: Generate ontology (upload document)
    setProgress(0)
    status.value = 'Building knowledge graph...'
    statusDetail.value = 'Extracting entities and relationships from signals'

    const blob = new Blob([docContent], { type: 'text/markdown' })
    const formData = new FormData()
    formData.append('files', blob, 'intelligence_report.md')
    formData.append('simulation_requirement', scenario.value.trim() || 'Analyze public reaction to these intelligence signals')
    formData.append('project_name', `OracleFlow Sim ${new Date().toISOString().slice(0, 16)}`)

    const ontRes = await generateOntology(formData)
    const projectId = ontRes.data?.project_id
    if (!projectId) throw new Error('Failed to create project')

    // Build graph
    const buildRes = await buildGraph({ project_id: projectId })
    const buildTaskId = buildRes.data?.task_id
    if (buildTaskId) {
      await pollTask(buildTaskId)
    }

    // Step 2: Create + prepare simulation
    setProgress(1)
    status.value = 'Generating agent personas...'
    statusDetail.value = 'Creating AI agents with unique personalities'

    const simRes = await createSimulation({ project_id: projectId })
    const simulationId = simRes.data?.simulation_id
    if (!simulationId) throw new Error('Failed to create simulation')

    const prepRes = await prepareSimulation({ simulation_id: simulationId })
    const prepTaskId = prepRes.data?.task_id
    if (prepTaskId) {
      // Poll prepare status
      const start = Date.now()
      while ((Date.now() - start) / 1000 < 600) {
        await new Promise(r => setTimeout(r, 3000))
        const ps = await getPrepareStatus({ task_id: prepTaskId })
        const pStatus = ps.data?.status || ps.status
        if (pStatus === 'completed' || pStatus === 'COMPLETED') break
        if (pStatus === 'failed' || pStatus === 'FAILED') throw new Error('Agent preparation failed')
        statusDetail.value = `Generating personas: ${ps.data?.progress || 0}%`
      }
    }

    // Step 3: Start simulation WITH our rounds
    setProgress(2)
    status.value = 'Starting simulation...'
    statusDetail.value = `${platform.value} debate \u2014 ${rounds.value} round${rounds.value > 1 ? 's' : ''}`

    await startSimulation({
      simulation_id: simulationId,
      platform: platform.value,
      max_rounds: rounds.value,
    })

    // Show toast and redirect to live simulation page
    setProgress(2)
    status.value = 'Simulation started! Opening live view...'
    statusClass.value = 'success'
    statusIcon.value = '\u2713'
    statusDetail.value = 'Watch agents debate in real-time with graph visualization'

    showToast('Simulation started! View progress \u2192')

    await new Promise(r => setTimeout(r, 1500))
    router.push(`/simulation/${simulationId}/start`)

  } catch (e) {
    status.value = 'Simulation failed'
    statusClass.value = 'error'
    statusIcon.value = '\u2717'
    error.value = e.message || 'Unknown error'
    console.error('Simulation error:', e)
  } finally {
    running.value = false
  }
}

onMounted(async () => {
  await fetchSignals(false)

  // Pre-fill from URL query params (signal_id, title, context)
  const qSignalId = route.query.signal_id
  const qTitle = route.query.title
  const qContext = route.query.context

  if (qTitle) {
    signalBannerTitle.value = qTitle
    scenario.value = qTitle
    if (qContext) {
      scenario.value += '\n\n' + qContext
    }
  }

  // If a signal_id was passed, auto-select it once signals load
  if (qSignalId) {
    const numericId = Number(qSignalId)
    if (!isNaN(numericId)) {
      selectedIds.add(numericId)
    } else {
      selectedIds.add(qSignalId)
    }

    // Auto-select agents based on the signal's category
    const matchedSignal = signals.value.find(s => String(s.id) === String(qSignalId))
    if (matchedSignal && matchedSignal.category) {
      const cat = matchedSignal.category.toLowerCase()
      const recommended = CATEGORY_AGENT_MAP[cat] || []
      if (recommended.length > 0) {
        // Auto-recommending agents for category
      }
    }
  }
})

onUnmounted(() => {
  clearTimeout(searchTimer)
  clearTimeout(scenarioTimer)
})
</script>

<style scoped>
.new-sim {
  max-width: 900px;
  margin: 0 auto;
}

.page-title {
  font-family: 'Space Grotesk', system-ui, sans-serif;
  font-size: 2rem;
  font-weight: 600;
  margin-bottom: 8px;
}

.page-desc {
  color: #999;
  font-size: 0.9rem;
  margin-bottom: 40px;
  line-height: 1.6;
}

/* -- Signal pre-fill banner -- */
.signal-prefill-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  margin-bottom: 30px;
  background: rgba(255, 69, 0, 0.06);
  border: 1px solid #FF4500;
  border-radius: 2px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  color: #e8e8e8;
  line-height: 1.5;
}

.prefill-icon {
  font-size: 1.1rem;
  flex-shrink: 0;
}

.prefill-text strong {
  color: #FF4500;
  font-weight: 600;
}

.section {
  margin-bottom: 35px;
}

.section-header {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 15px;
}

.step-num {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  color: #FF4500;
  font-size: 0.85rem;
}

.step-label {
  font-weight: 600;
  font-size: 1.1rem;
}

.step-hint {
  color: #666;
  font-size: 0.8rem;
}

/* -- Filter controls -- */
.signal-filters {
  margin-bottom: 12px;
}

.filter-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}

.filter-input {
  background: #111;
  border: 1px solid #333;
  color: #fff;
  padding: 8px 10px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  outline: none;
}

.filter-input:focus {
  border-color: #FF4500;
}

.search-input {
  flex: 2;
  min-width: 200px;
}

.filter-select {
  flex: 1;
  min-width: 130px;
}

.filter-actions {
  display: flex;
  gap: 8px;
}

.quick-filter-btn {
  background: #1a1a1a;
  border: 1px solid #444;
  color: #ccc;
  padding: 6px 14px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.15s;
}

.quick-filter-btn:hover {
  border-color: #FF4500;
  color: #FF4500;
}

.quick-filter-btn.active {
  background: rgba(255, 69, 0, 0.15);
  border-color: #FF4500;
  color: #FF4500;
  font-weight: 600;
}

/* -- Selection bar -- */
.selection-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  margin-bottom: 10px;
  background: #111;
  border: 1px solid #333;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
}

.selection-counter {
  color: #aaa;
}

.selection-counter strong {
  color: #FF4500;
}

.clear-btn {
  background: none;
  border: 1px solid #555;
  color: #999;
  padding: 3px 10px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  cursor: pointer;
  transition: all 0.15s;
}

.clear-btn:hover {
  border-color: #EF4444;
  color: #EF4444;
}

/* -- Suggested signals -- */
.suggested-section {
  margin-bottom: 12px;
}

.suggested-header {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #22C55E;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 6px;
  padding-left: 4px;
}

.suggested-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 8px;
  padding: 8px;
  border: 1px dashed rgba(34, 197, 94, 0.2);
  background: rgba(34, 197, 94, 0.03);
}

.signal-item.suggested {
  border-color: rgba(34, 197, 94, 0.2);
}

.signal-item.suggested.selected {
  border-color: #22C55E;
  background: rgba(34, 197, 94, 0.08);
}

/* -- Signal list -- */
.loading-text, .empty-text {
  color: #666;
  font-size: 0.9rem;
  padding: 20px;
  border: 1px solid #333;
  text-align: center;
}

.signals-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  max-height: 400px;
  overflow-y: auto;
}

.signal-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 15px;
  border: 1px solid #333;
  cursor: pointer;
  transition: all 0.15s;
}

.signal-item:hover {
  border-color: #555;
}

.signal-item.selected {
  border-color: #FF4500;
  background: rgba(255, 69, 0, 0.05);
}

.signal-item.disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.signal-item input[type="checkbox"] {
  margin-top: 4px;
  accent-color: #FF4500;
}

.signal-content {
  flex: 1;
  min-width: 0;
}

.signal-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.signal-title {
  font-weight: 500;
  font-size: 0.9rem;
}

.anomaly-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 2px 8px;
  color: #000;
}

.signal-meta {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
  margin-bottom: 4px;
}

.meta-badge {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  padding: 1px 6px;
  border: 1px solid #444;
  color: #aaa;
}

.meta-badge.source { color: #FF4500; border-color: #FF4500; }
.meta-country { font-size: 0.75rem; color: #888; }
.meta-time { font-size: 0.75rem; color: #666; }

.signal-summary {
  font-size: 0.8rem;
  color: #888;
  line-height: 1.4;
}

/* -- Load more -- */
.load-more-bar {
  display: flex;
  justify-content: center;
  padding: 12px 0;
}

.load-more-btn {
  background: #1a1a1a;
  border: 1px solid #444;
  color: #ccc;
  padding: 8px 24px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.15s;
}

.load-more-btn:hover:not(:disabled) {
  border-color: #FF4500;
  color: #FF4500;
}

.load-more-btn:disabled {
  color: #555;
  cursor: not-allowed;
}

.all-loaded-text {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #555;
}

/* -- Scenario -- */
.scenario-input {
  width: 100%;
  background: #111;
  border: 1px solid #333;
  color: #fff;
  padding: 15px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.9rem;
  line-height: 1.6;
  resize: vertical;
  outline: none;
}

.scenario-input:focus {
  border-color: #FF4500;
}

.scenario-input::placeholder {
  color: #555;
}

.config-row {
  display: flex;
  gap: 20px;
}

.config-item {
  flex: 1;
}

.config-item label {
  display: block;
  font-size: 0.8rem;
  color: #888;
  margin-bottom: 6px;
  font-family: 'JetBrains Mono', monospace;
}

.config-select {
  width: 100%;
  background: #111;
  border: 1px solid #333;
  color: #fff;
  padding: 10px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  outline: none;
}

.config-select:focus {
  border-color: #FF4500;
}

.status-box {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px;
  border: 1px solid #333;
}

.status-box.info { border-color: #FF4500; }
.status-box.success { border-color: #22C55E; }
.status-box.error { border-color: #EF4444; }

.status-icon {
  font-size: 1.3rem;
  width: 30px;
  text-align: center;
}

.status-title {
  font-weight: 600;
  font-size: 0.95rem;
}

.status-detail {
  font-size: 0.8rem;
  color: #888;
  margin-top: 2px;
}

.progress-steps {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-top: 15px;
  padding-left: 15px;
}

.progress-step {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.85rem;
  color: #555;
}

.progress-step.done { color: #22C55E; }
.progress-step.active { color: #FF4500; font-weight: 600; }

.progress-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #333;
}

.progress-step.done .progress-dot { background: #22C55E; }
.progress-step.active .progress-dot { background: #FF4500; animation: pulse 1.5s infinite; }

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* -- Toast notification -- */
.toast-notification {
  position: fixed;
  bottom: 30px;
  right: 30px;
  background: #1a1a1a;
  border: 1px solid #22C55E;
  color: #22C55E;
  padding: 14px 20px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  gap: 12px;
  z-index: 9999;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
}

.toast-close {
  background: none;
  border: none;
  color: #666;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0 4px;
}

.toast-close:hover {
  color: #fff;
}

.toast-fade-enter-active,
.toast-fade-leave-active {
  transition: all 0.3s ease;
}

.toast-fade-enter-from,
.toast-fade-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

.error-box {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid #EF4444;
  color: #EF4444;
  padding: 12px 15px;
  font-size: 0.85rem;
  margin-bottom: 20px;
}

.run-btn {
  width: 100%;
  padding: 18px;
  background: #FF4500;
  color: #fff;
  border: none;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  font-size: 1.1rem;
  cursor: pointer;
  transition: all 0.2s;
  letter-spacing: 1px;
}

.run-btn:hover:not(:disabled) {
  background: #E03E00;
  transform: translateY(-1px);
}

.run-btn:disabled {
  background: #333;
  color: #666;
  cursor: not-allowed;
  transform: none;
}
</style>
