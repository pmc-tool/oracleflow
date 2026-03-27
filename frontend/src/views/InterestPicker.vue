<template>
  <div class="interest-page">
    <div class="interest-container">
      <div class="header">
        <h1 class="heading">What matters to you?</h1>
        <p class="subtitle">Pick 3-5 categories to personalize your intelligence dashboard</p>
      </div>

      <div class="persona-row">
        <button
          v-for="persona in personas"
          :key="persona.id"
          class="persona-btn"
          :class="{ active: activePersona === persona.id }"
          @click="applyPersona(persona)"
        >
          {{ persona.label }}
        </button>
      </div>

      <div v-if="personaDescription" class="persona-description">
        {{ personaDescription }}
      </div>

      <div class="category-grid">
        <div
          v-for="cat in categories"
          :key="cat.id"
          class="category-card"
          :class="{ selected: selected.has(cat.id) }"
          @click="toggle(cat.id)"
        >
          <div class="card-top">
            <span class="card-icon">{{ cat.icon }}</span>
            <span class="card-check">{{ selected.has(cat.id) ? '\u2611' : '\u2610' }}</span>
          </div>
          <div class="card-title">{{ cat.title }}</div>
          <div class="card-desc">{{ cat.desc }}</div>
        </div>
      </div>

      <div class="bottom-bar">
        <span class="counter">{{ selected.size }}/5 selected</span>
        <button
          class="continue-btn"
          :disabled="selected.size < 3 || submitting"
          @click="handleSubmit"
        >
          <span v-if="submitting">Saving...</span>
          <span v-else>Continue to Dashboard <span class="arrow">&rarr;</span></span>
        </button>
      </div>

      <div v-if="error" class="error-msg">{{ error }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import service from '../api/index'

const router = useRouter()
const error = ref('')
const submitting = ref(false)
const activePersona = ref(null)
const selected = reactive(new Set())

const personas = [
  { id: 'trader', label: 'Trader', cats: ['finance', 'economy', 'technology', 'supply_chain'] },
  { id: 'policy_analyst', label: 'Policy Analyst', cats: ['politics', 'geopolitical', 'economy', 'climate'] },
  { id: 'security_analyst', label: 'Security Analyst', cats: ['cyber', 'crime', 'geopolitical', 'technology'] },
  { id: 'corporate_risk', label: 'Corporate Risk', cats: ['finance', 'supply_chain', 'cyber', 'economy'] },
  { id: 'humanitarian', label: 'Humanitarian', cats: ['climate', 'healthcare', 'geopolitical', 'education'] },
]

const categories = [
  { id: 'finance', icon: '\uD83D\uDCC8', title: 'Markets & Trading', desc: 'Equities, commodities, forex, and derivatives signals' },
  { id: 'geopolitical', icon: '\uD83C\uDF0D', title: 'Geopolitical & Conflict', desc: 'Wars, sanctions, territorial disputes, and diplomacy' },
  { id: 'supply_chain', icon: '\uD83D\uDE9A', title: 'Supply Chain', desc: 'Logistics disruptions, shipping routes, and trade flows' },
  { id: 'cyber', icon: '\uD83D\uDD12', title: 'Cyber Security', desc: 'Breaches, vulnerabilities, threat actors, and APTs' },
  { id: 'climate', icon: '\u26C8\uFE0F', title: 'Climate & Weather', desc: 'Extreme weather events, climate policy, and resources' },
  { id: 'politics', icon: '\uD83C\uDFDB\uFE0F', title: 'Politics & Policy', desc: 'Elections, legislation, regulatory changes worldwide' },
  { id: 'healthcare', icon: '\uD83C\uDFE5', title: 'Health & Pandemic', desc: 'Disease outbreaks, pharma developments, health policy' },
  { id: 'economy', icon: '\uD83D\uDCB1', title: 'Economy & Macro', desc: 'GDP, inflation, central banks, and employment data' },
  { id: 'crime', icon: '\uD83D\uDEA8', title: 'Crime & Security', desc: 'Organized crime, terrorism, law enforcement operations' },
  { id: 'education', icon: '\uD83C\uDF93', title: 'Education & Research', desc: 'Academic research, think-tank publications, and R&D' },
  { id: 'technology', icon: '\uD83E\uDD16', title: 'Technology & AI', desc: 'AI advances, semiconductors, big tech, and startups' },
  { id: 'other', icon: '\uD83D\uDCCC', title: 'Other / General', desc: 'Broad intelligence not covered by specific verticals' },
]

const personaDescriptions = {
  trader: "You'll see Markets, Crypto, Commodities, Macro Stress panels. 50+ finance feeds. Ticker-tagged signals.",
  policy_analyst: "You'll get Policy, Geopolitical, Economy, and Climate panels. Legislative tracking. Sanctions monitoring. Think-tank feeds.",
  security_analyst: "Cyber threat feeds from CISA, NVD, Krebs. MITRE ATT&CK tagging. IOC extraction. APT tracking dashboards.",
  corporate_risk: "Finance, Supply Chain, Cyber, and Economy panels. Earnings alerts. Vendor risk signals. Regulatory change tracking.",
  humanitarian: "Climate, Healthcare, Geopolitical, and Education panels. Disaster alerts. Epidemic tracking. UN/NGO feed aggregation.",
}

const personaDescription = computed(() => {
  if (!activePersona.value) return null
  return personaDescriptions[activePersona.value] || null
})

function toggle(id) {
  if (selected.has(id)) {
    selected.delete(id)
    activePersona.value = null
  } else if (selected.size < 5) {
    selected.add(id)
  }
}

function applyPersona(persona) {
  selected.clear()
  persona.cats.forEach(c => selected.add(c))
  activePersona.value = persona.id
}

async function handleSubmit() {
  if (selected.size < 3) return
  error.value = ''
  submitting.value = true

  try {
    await service.put('/api/auth/preferences', {
      interest_categories: Array.from(selected),
      persona_shortcut: activePersona.value || null,
    })
    router.push('/intel')
  } catch (err) {
    error.value = err?.response?.data?.message || err?.message || 'Failed to save preferences'
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

.interest-page {
  min-height: 100vh;
  background: #0a0a0a;
  color: #e8e8e8;
  display: flex;
  justify-content: center;
  padding: 48px 24px 80px;
  font-family: 'Space Grotesk', sans-serif;
}

.interest-container {
  width: 100%;
  max-width: 960px;
}

.header {
  text-align: center;
  margin-bottom: 36px;
}

.heading {
  font-family: 'JetBrains Mono', monospace;
  font-size: 2rem;
  font-weight: 700;
  letter-spacing: 1px;
  margin: 0 0 10px 0;
  color: #e8e8e8;
}

.subtitle {
  font-size: 1rem;
  color: #777;
  margin: 0;
}

.persona-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
  margin-bottom: 32px;
}

.persona-btn {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.5px;
  padding: 10px 20px;
  background: #141414;
  border: 1px solid #2a2a2a;
  border-radius: 4px;
  color: #aaa;
  cursor: pointer;
  transition: border-color 0.2s, color 0.2s, background 0.2s;
}

.persona-btn:hover {
  border-color: #555;
  color: #e8e8e8;
}

.persona-btn.active {
  border-color: #FF4500;
  color: #FF4500;
  background: rgba(255, 69, 0, 0.08);
}

.persona-description {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.78rem;
  color: #FF4500;
  background: rgba(255, 69, 0, 0.06);
  border: 1px solid rgba(255, 69, 0, 0.2);
  border-radius: 4px;
  padding: 12px 16px;
  margin-bottom: 20px;
  line-height: 1.5;
  letter-spacing: 0.2px;
  text-align: center;
}

.category-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  margin-bottom: 32px;
}

@media (max-width: 820px) {
  .category-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 520px) {
  .category-grid {
    grid-template-columns: 1fr;
  }
}

.category-card {
  background: #141414;
  border: 1px solid #2a2a2a;
  border-radius: 4px;
  padding: 18px;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
  user-select: none;
}

.category-card:hover {
  border-color: #444;
}

.category-card.selected {
  border-color: #FF4500;
  background: rgba(255, 69, 0, 0.1);
}

.card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.card-icon {
  font-size: 1.5rem;
}

.card-check {
  font-size: 1.2rem;
  color: #555;
}

.category-card.selected .card-check {
  color: #FF4500;
}

.card-title {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.88rem;
  font-weight: 700;
  letter-spacing: 0.3px;
  color: #e8e8e8;
  margin-bottom: 4px;
}

.card-desc {
  font-size: 0.78rem;
  color: #666;
  line-height: 1.4;
}

.bottom-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.counter {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  color: #777;
  letter-spacing: 0.5px;
}

.continue-btn {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 0.95rem;
  font-weight: 700;
  padding: 14px 32px;
  background: #FF4500;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  letter-spacing: 0.3px;
  transition: background 0.2s, opacity 0.2s;
}

.continue-btn:hover:not(:disabled) {
  background: #e03e00;
}

.continue-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.continue-btn .arrow {
  font-family: sans-serif;
}

.error-msg {
  margin-top: 16px;
  background: rgba(255, 69, 0, 0.1);
  border: 1px solid rgba(255, 69, 0, 0.3);
  border-radius: 3px;
  padding: 10px 14px;
  font-size: 0.8rem;
  color: #FF4500;
  text-align: center;
}
</style>
