<template>
  <Transition name="slide-up">
    <div v-if="visible" class="onboarding-card">
      <div class="onboarding-header">
        <span class="onboarding-title">OracleFlow Setup</span>
        <span class="step-indicator">{{ currentStep }}/2</span>
      </div>

      <!-- Step 1: Dashboard overview -->
      <div v-if="currentStep === 1" class="step-content">
        <p class="step-heading">Your intelligence dashboard is live</p>
        <p class="step-desc">
          We've configured your dashboard for
          <strong class="accent">{{ personaLabel }}</strong> intelligence.
          You're seeing <strong class="accent">{{ panelCount }}</strong> panels
          filtered from 30.
        </p>
        <div class="step-actions">
          <button class="action-btn primary-btn" @click="advanceToStep2">Continue</button>
          <button class="action-btn skip-btn" @click="dismiss">Skip</button>
        </div>
      </div>

      <!-- Step 2: Monitor first website -->
      <div v-if="currentStep === 2" class="step-content">
        <p class="step-heading">Monitor your first website</p>

        <div v-if="monitorState === 'idle'" class="monitor-form">
          <input
            v-model="siteUrl"
            type="url"
            class="url-input"
            placeholder="https://example.com"
            @keydown.enter="startMonitoring"
          />
          <button
            class="action-btn primary-btn"
            :disabled="!siteUrl.trim()"
            @click="startMonitoring"
          >Start Monitoring</button>
        </div>

        <div v-if="monitorState === 'discovering'" class="monitor-progress">
          <span class="progress-dot"></span>
          <span class="progress-text">Discovering pages...</span>
        </div>

        <div v-if="monitorState === 'done'" class="monitor-progress">
          <span class="progress-check">&#10003;</span>
          <span class="progress-text">Done! {{ pagesFound }} pages found.</span>
        </div>

        <div v-if="monitorState === 'error'" class="monitor-progress">
          <span class="progress-error">&#10007;</span>
          <span class="progress-text error-text">{{ monitorError }}</span>
          <button class="action-btn skip-btn" style="margin-left:auto" @click="monitorState = 'idle'">Retry</button>
        </div>

        <div v-if="monitorState === 'idle'" class="step-actions">
          <button class="action-btn skip-btn" @click="dismiss">Skip</button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getUserPreferences, updateUserPreferences, discoverSite } from '../api/intelligence'

const STORAGE_KEY = 'of_onboarding_complete'

const visible = ref(false)
const currentStep = ref(1)
const personaLabel = ref('General')
const panelCount = ref(0)
const siteUrl = ref('')
const monitorState = ref('idle') // idle | discovering | done | error
const pagesFound = ref(0)
const monitorError = ref('')

const props = defineProps({
  filteredPanelCount: {
    type: Number,
    default: 0
  }
})

const PERSONA_MAP = {
  finance: 'Trader',
  economy: 'Economic',
  cyber: 'Security',
  technology: 'Technology',
  geopolitical: 'Geopolitical',
  politics: 'Political',
  climate: 'Climate',
  supply_chain: 'Supply Chain',
  crime: 'Crime',
  humanitarian: 'Humanitarian'
}

function advanceToStep2() {
  currentStep.value = 2
}

async function startMonitoring() {
  if (!siteUrl.value.trim()) return
  monitorState.value = 'discovering'
  monitorError.value = ''
  try {
    const res = await discoverSite(siteUrl.value.trim())
    const data = res.data || res
    pagesFound.value = data.page_count || data.pages_found || data.pages?.length || 0
    monitorState.value = 'done'
    // Auto-complete after showing result
    setTimeout(() => completeOnboarding(), 1500)
  } catch (err) {
    monitorState.value = 'error'
    monitorError.value = err?.response?.data?.detail || err.message || 'Failed to discover site'
  }
}

async function completeOnboarding() {
  visible.value = false
  localStorage.setItem(STORAGE_KEY, 'true')
  try {
    await updateUserPreferences({ onboarding_completed: true })
  } catch {
    // localStorage fallback already set
  }
}

function dismiss() {
  completeOnboarding()
}

onMounted(async () => {
  if (localStorage.getItem(STORAGE_KEY)) return

  // Fetch user preferences to determine persona and categories
  try {
    const res = await getUserPreferences()
    const data = res.data || res
    const categories = data?.interest_categories || []

    // Determine persona from first/primary category
    if (categories.length > 0) {
      personaLabel.value = PERSONA_MAP[categories[0]] || categories[0]
    }

    // Panel count from prop or calculate
    panelCount.value = props.filteredPanelCount || categories.length * 4 || 6
  } catch {
    // Use defaults
    panelCount.value = props.filteredPanelCount || 6
  }

  visible.value = true
})
</script>

<style scoped>
.onboarding-card {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 320px;
  background: #141414;
  border: 1px solid #2a2a2a;
  border-radius: 10px;
  padding: 16px 18px;
  z-index: 9999;
  font-family: 'JetBrains Mono', monospace;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
}

.onboarding-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.onboarding-title {
  font-size: 0.8rem;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 0.5px;
}

.step-indicator {
  font-size: 0.7rem;
  color: #555;
  letter-spacing: 1px;
}

.step-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.step-heading {
  font-size: 0.8rem;
  font-weight: 600;
  color: #FF4500;
  margin: 0;
}

.step-desc {
  font-size: 0.72rem;
  color: #999;
  line-height: 1.6;
  margin: 0;
}

.accent {
  color: #FF4500;
  font-weight: 600;
}

.monitor-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.url-input {
  width: 100%;
  background: #1a1a1a;
  border: 1px solid #2a2a2a;
  border-radius: 4px;
  padding: 8px 10px;
  color: #e8e8e8;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.72rem;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}

.url-input:focus {
  border-color: #FF4500;
}

.url-input::placeholder {
  color: #555;
}

.monitor-progress {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 0;
}

.progress-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #FF4500;
  animation: pulse-progress 1s infinite;
}

@keyframes pulse-progress {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.8); }
}

.progress-check {
  color: #44ff88;
  font-size: 1rem;
  font-weight: 700;
}

.progress-error {
  color: #ff4444;
  font-size: 1rem;
  font-weight: 700;
}

.progress-text {
  font-size: 0.72rem;
  color: #ccc;
}

.error-text {
  color: #ff6666;
}

.step-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 4px;
}

.action-btn {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.72rem;
  font-weight: 600;
  padding: 6px 14px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
  border: none;
}

.action-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.primary-btn {
  background: #FF4500;
  color: #ffffff;
}

.primary-btn:hover:not(:disabled) {
  background: #e63e00;
}

.skip-btn {
  background: transparent;
  color: #555;
  border: 1px solid #2a2a2a;
}

.skip-btn:hover {
  color: #999;
  border-color: #444;
}

/* Transition */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  opacity: 0;
  transform: translateY(20px);
}
</style>
