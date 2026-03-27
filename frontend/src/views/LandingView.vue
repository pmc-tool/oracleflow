<template>
  <div class="landing-page">
    <!-- Live Intelligence Ribbon -->
    <div class="live-ribbon">
      <div class="ribbon-inner">
        <span class="ribbon-dot"></span>
        <span class="ribbon-text">LIVE: {{ liveFeedText }}</span>
      </div>
    </div>

    <!-- Fixed Navbar -->
    <nav class="landing-nav">
      <div class="nav-inner">
        <span class="nav-brand">ORACLEFLOW</span>
        <div class="nav-links">
          <a href="#how" @click.prevent="scrollTo('how')">How It Works</a>
          <a href="#use-cases" @click.prevent="scrollTo('use-cases')">Use Cases</a>
          <a href="#pricing" @click.prevent="scrollTo('pricing')">Pricing</a>
          <a href="#faq" @click.prevent="scrollTo('faq')">FAQ</a>
          <router-link v-if="isLoggedIn" to="/intel" class="nav-login-btn">Dashboard</router-link>
          <router-link v-else to="/login" class="nav-login-btn">Sign In</router-link>
          <router-link v-if="isLoggedIn" to="/intel" class="nav-cta-btn">Open Dashboard</router-link>
          <router-link v-else to="/register" class="nav-cta-btn">Start Free</router-link>
        </div>
        <button class="mobile-menu-btn" @click="mobileMenuOpen = !mobileMenuOpen">
          <span></span><span></span><span></span>
        </button>
      </div>
      <div v-if="mobileMenuOpen" class="mobile-menu">
        <a href="#how" @click.prevent="scrollTo('how'); mobileMenuOpen = false">How It Works</a>
        <a href="#use-cases" @click.prevent="scrollTo('use-cases'); mobileMenuOpen = false">Use Cases</a>
        <a href="#pricing" @click.prevent="scrollTo('pricing'); mobileMenuOpen = false">Pricing</a>
        <a href="#faq" @click.prevent="scrollTo('faq'); mobileMenuOpen = false">FAQ</a>
        <router-link v-if="isLoggedIn" to="/intel" @click="mobileMenuOpen = false">Dashboard</router-link>
        <router-link v-else to="/login" @click="mobileMenuOpen = false">Sign In</router-link>
        <router-link v-if="isLoggedIn" to="/intel" @click="mobileMenuOpen = false" class="nav-cta-btn">Open Dashboard</router-link>
        <router-link v-else to="/register" @click="mobileMenuOpen = false" class="nav-cta-btn">Start Free</router-link>
      </div>
    </nav>

    <!-- ===== HERO ===== -->
    <section class="hero-section">
      <div class="hero-grid">
        <!-- LEFT: Copy + CTAs -->
        <div class="hero-left">
          <div class="hero-tag">
            <span class="hero-tag-dot"></span>
            INTELLIGENCE PLATFORM
          </div>
          <h1 class="hero-title">
            Know What Happens
            <span class="hero-accent">Before It Happens</span>
          </h1>
          <p class="hero-subtitle">
            OracleFlow monitors 214 global intelligence feeds, detects anomalies in real-time,
            and runs AI simulations to predict outcomes &mdash; so you act first, not last.
          </p>
          <div class="hero-ctas">
            <router-link v-if="isLoggedIn" to="/intel" class="cta-primary">
              Go to Dashboard
              <span class="cta-arrow">&rarr;</span>
            </router-link>
            <router-link v-else to="/register" class="cta-primary">
              Start Free &mdash; No Credit Card
              <span class="cta-arrow">&rarr;</span>
            </router-link>
            <router-link to="/intel" class="cta-secondary">
              See Live Dashboard
              <span class="cta-arrow">&rarr;</span>
            </router-link>
          </div>
          <p class="hero-trust-line">Trusted by intelligence analysts, hedge funds, and government agencies</p>
        </div>

        <!-- RIGHT: Live Chaos Widget + Counters -->
        <div class="hero-right">
          <div class="chaos-card-live">
            <div class="chaos-header">
              <span class="chaos-label">GLOBAL CHAOS INDEX</span>
              <span class="chaos-live-dot"></span>
              <span class="chaos-live-text">LIVE</span>
            </div>
            <div class="chaos-score" :style="{ color: chaosColor }">{{ chaosScore }}</div>
            <div class="chaos-bar-track">
              <div class="chaos-bar-fill" :style="{ width: chaosScore + '%', background: chaosColor }"></div>
            </div>
            <div class="chaos-categories">
              <div v-for="cat in chaosCats" :key="cat.key" class="chaos-cat">
                <span class="chaos-cat-label">{{ cat.label }}</span>
                <span class="chaos-cat-score" :style="{ color: cat.color }">{{ cat.score }}</span>
              </div>
            </div>
          </div>
          <div class="live-counters">
            <div class="counter-item">
              <span class="counter-value">{{ animatedSignals.toLocaleString() }}</span>
              <span class="counter-label">signals processed</span>
            </div>
            <div class="counter-item">
              <span class="counter-value">{{ feedCount }}</span>
              <span class="counter-label">live feeds</span>
            </div>
            <div class="counter-item">
              <span class="counter-value">30</span>
              <span class="counter-label">intel panels</span>
            </div>
            <div class="counter-item">
              <span class="counter-value">&lt;2s</span>
              <span class="counter-label">signal latency</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== PROBLEM ===== -->
    <section class="problem-section">
      <div class="section-inner">
        <div class="section-label">THE PROBLEM</div>
        <h2 class="section-title">By the Time You See It on the News, It's Already Too Late</h2>
        <div class="problem-grid">
          <div class="problem-card">
            <div class="problem-icon">!</div>
            <h3>Information Lag</h3>
            <p>Traditional intelligence tools deliver reports hours or days after events unfold. Markets move, policies shift, and crises escalate while you wait.</p>
          </div>
          <div class="problem-card">
            <div class="problem-icon">&times;</div>
            <h3>Signal Overload</h3>
            <p>Thousands of sources, millions of data points. Analysts drown in noise and miss the 3 signals that actually matter.</p>
          </div>
          <div class="problem-card">
            <div class="problem-icon">?</div>
            <h3>No Predictive Power</h3>
            <p>Dashboards show what happened. They can't tell you what happens next. You need simulation, not just aggregation.</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== HOW IT WORKS ===== -->
    <section id="how" class="how-section">
      <div class="section-inner">
        <div class="section-label">HOW ORACLEFLOW WORKS</div>
        <h2 class="section-title">From Raw Data to Actionable Prediction in 4 Steps</h2>
        <div class="pipeline">
          <div class="pipeline-step" v-for="step in steps" :key="step.num">
            <div class="pipeline-num">{{ step.num }}</div>
            <div class="pipeline-line"></div>
            <div class="pipeline-content">
              <div class="pipeline-icon">{{ step.icon }}</div>
              <h3>{{ step.title }}</h3>
              <p>{{ step.desc }}</p>
              <div class="pipeline-detail">{{ step.detail }}</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== LIVE INTEL PREVIEW ===== -->
    <section class="intel-preview-section">
      <div class="section-inner">
        <div class="section-label">LIVE INTELLIGENCE</div>
        <h2 class="section-title">30 Intelligence Panels. One Unified View.</h2>
        <div class="intel-showcase">
          <div class="intel-panels-grid">
            <div v-for="panel in showcasePanels" :key="panel.name" class="intel-panel-card">
              <div class="panel-card-header">
                <span class="panel-card-dot" :style="{ background: panel.color }"></span>
                {{ panel.name }}
              </div>
              <div class="panel-card-body">{{ panel.desc }}</div>
            </div>
          </div>
          <div class="intel-cta-overlay">
            <router-link to="/intel" class="cta-primary">
              Open Live Dashboard
              <span class="cta-arrow">&rarr;</span>
            </router-link>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== USE CASES ===== -->
    <section id="use-cases" class="usecases-section">
      <div class="section-inner">
        <div class="section-label">WHO IT'S FOR</div>
        <h2 class="section-title">Built for People Who Can't Afford to Be Surprised</h2>
        <div class="usecase-grid">
          <div v-for="uc in useCases" :key="uc.role" class="usecase-card">
            <div class="usecase-icon">{{ uc.icon }}</div>
            <h3 class="usecase-role">{{ uc.role }}</h3>
            <p class="usecase-problem"><strong>The pain:</strong> {{ uc.pain }}</p>
            <p class="usecase-solution"><strong>With OracleFlow:</strong> {{ uc.solution }}</p>
            <div class="usecase-quote">"{{ uc.quote }}"</div>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== COMPARISON ===== -->
    <section class="compare-section">
      <div class="section-inner">
        <div class="section-label">COMPARISON</div>
        <h2 class="section-title">Why OracleFlow vs. Everything Else</h2>
        <div class="compare-table-wrapper">
          <table class="compare-table">
            <thead>
              <tr>
                <th>Feature</th>
                <th>Bloomberg Terminal</th>
                <th>Recorded Future</th>
                <th>Palantir</th>
                <th class="compare-highlight">OracleFlow</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in compareRows" :key="row.feature">
                <td class="compare-feature">{{ row.feature }}</td>
                <td>{{ row.bloomberg }}</td>
                <td>{{ row.recorded }}</td>
                <td>{{ row.palantir }}</td>
                <td class="compare-highlight">{{ row.oracle }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- ===== PRICING ===== -->
    <section id="pricing" class="pricing-section">
      <div class="section-inner">
        <div class="section-label">PRICING</div>
        <h2 class="section-title">Intelligence Shouldn't Cost a Fortune</h2>
        <p class="pricing-sub">Start free. Upgrade when you need more power.</p>
        <div class="pricing-grid">
          <div
            v-for="plan in plans"
            :key="plan.name"
            class="pricing-card"
            :class="{ 'pricing-card-popular': plan.popular }"
          >
            <div v-if="plan.popular" class="popular-badge">MOST POPULAR</div>
            <h3 class="plan-name">{{ plan.name }}</h3>
            <div class="plan-tagline">{{ plan.tagline }}</div>
            <div class="plan-price">
              <span class="price-amount">{{ plan.price }}</span>
              <span v-if="plan.period" class="price-period">{{ plan.period }}</span>
            </div>
            <ul class="plan-features">
              <li v-for="(feature, i) in plan.features" :key="i">{{ feature }}</li>
            </ul>
            <router-link
              :to="plan.cta.to"
              class="plan-cta"
              :class="{ 'plan-cta-primary': plan.popular, 'plan-cta-enterprise': plan.enterprise }"
            >
              {{ plan.cta.label }}
            </router-link>
          </div>
        </div>
        <p class="pricing-guarantee">30-day money-back guarantee. Cancel anytime. No contracts.</p>
      </div>
    </section>

    <!-- ===== TRUST ===== -->
    <section class="trust-section">
      <div class="section-inner">
        <div class="trust-grid">
          <div class="trust-item">
            <div class="trust-icon">&#x1F512;</div>
            <div class="trust-text">
              <strong>End-to-End Encryption</strong>
              <span>AES-256 at rest, TLS 1.3 in transit</span>
            </div>
          </div>
          <div class="trust-item">
            <div class="trust-icon">&#x1F3E2;</div>
            <div class="trust-text">
              <strong>On-Premise Deployment</strong>
              <span>Air-gapped option for sovereign clients</span>
            </div>
          </div>
          <div class="trust-item">
            <div class="trust-icon">&#x1F6E1;</div>
            <div class="trust-text">
              <strong>SOC 2 Compliant</strong>
              <span>Enterprise-grade security controls</span>
            </div>
          </div>
          <div class="trust-item">
            <div class="trust-icon">&#x1F310;</div>
            <div class="trust-text">
              <strong>GDPR Ready</strong>
              <span>Data export & deletion on demand</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== FAQ ===== -->
    <section id="faq" class="faq-section">
      <div class="section-inner">
        <div class="section-label">FAQ</div>
        <h2 class="section-title">Common Questions</h2>
        <div class="faq-list">
          <div
            v-for="(faq, i) in faqs"
            :key="i"
            class="faq-item"
            :class="{ 'faq-open': faqOpen === i }"
            @click="faqOpen = faqOpen === i ? -1 : i"
          >
            <div class="faq-question">
              <span>{{ faq.q }}</span>
              <span class="faq-toggle">{{ faqOpen === i ? '&minus;' : '+' }}</span>
            </div>
            <div v-if="faqOpen === i" class="faq-answer">{{ faq.a }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- ===== FINAL CTA ===== -->
    <section class="final-cta-section">
      <div class="section-inner final-cta-inner">
        <h2 class="final-cta-title">Stop Reacting. Start Predicting.</h2>
        <p class="final-cta-desc">
          Join the intelligence professionals who know what's coming before it arrives.
        </p>
        <div class="final-cta-btns">
          <router-link to="/register" class="cta-primary cta-large">
            Get Started Free
            <span class="cta-arrow">&rarr;</span>
          </router-link>
          <router-link to="/intel" class="cta-secondary cta-large">
            View Live Demo
            <span class="cta-arrow">&rarr;</span>
          </router-link>
        </div>
      </div>
    </section>

    <!-- ===== FOOTER ===== -->
    <footer class="landing-footer">
      <div class="footer-inner">
        <div class="footer-left">
          <span class="footer-brand">ORACLEFLOW</span>
          <span class="footer-copy">&copy; 2026 OracleFlow Intelligence Systems</span>
        </div>
        <div class="footer-links">
          <router-link to="/terms">Terms</router-link>
          <router-link to="/privacy">Privacy</router-link>
          <a href="mailto:contact@oracleflow.io">Contact</a>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const mobileMenuOpen = ref(false)
const faqOpen = ref(-1)
const isLoggedIn = ref(false)

// Live data
const signalCount = ref(1020)
const feedCount = ref(214)
const animatedSignals = ref(0)
const chaosScore = ref('--')
const chaosCats = ref([
  { key: 'finance', label: 'FIN', score: '--', color: '#3b82f6' },
  { key: 'geopolitical', label: 'GEO', score: '--', color: '#ef4444' },
  { key: 'supply_chain', label: 'SCM', score: '--', color: '#f59e0b' },
  { key: 'cyber', label: 'CYB', score: '--', color: '#a855f7' },
  { key: 'climate', label: 'CLI', score: '--', color: '#22c55e' },
])

const chaosColor = computed(() => {
  const s = parseFloat(chaosScore.value)
  if (isNaN(s)) return '#888'
  if (s < 30) return '#22c55e'
  if (s < 60) return '#f59e0b'
  if (s < 80) return '#f97316'
  return '#ef4444'
})

// Live feed ribbon
const liveFeedItems = ref([
  'Monitoring 214 intelligence feeds across 42 countries',
  'AI simulation engine online — 500 agents ready',
  'Chaos Index computing in real-time',
])
const liveFeedIndex = ref(0)
const liveFeedText = computed(() => liveFeedItems.value[liveFeedIndex.value % liveFeedItems.value.length])
let ribbonInterval = null

// Animated counter
let counterInterval = null

const steps = [
  {
    num: '01',
    icon: '\u25CE',
    title: 'INGEST',
    desc: 'We pull from 214 feeds: Reuters, AP, ACLED, USGS, NASA, Finnhub, government sources.',
    detail: 'RSS, APIs, web scraping — every 5 minutes'
  },
  {
    num: '02',
    icon: '\u25C8',
    title: 'DETECT',
    desc: 'AI classifies every signal by category, anomaly score, and geographic impact.',
    detail: 'NLP + anomaly scoring in <2 seconds'
  },
  {
    num: '03',
    icon: '\u25A3',
    title: 'SIMULATE',
    desc: '500 AI agents debate the scenario: politicians, economists, military analysts, civilians.',
    detail: 'Multi-agent simulation with GPT-4o'
  },
  {
    num: '04',
    icon: '\u2666',
    title: 'PREDICT',
    desc: 'Get probability-weighted outcomes, tipping points, and recommended actions.',
    detail: 'Delivered to your dashboard in real-time'
  },
]

const showcasePanels = [
  { name: 'Global News', desc: 'Real-time feed from 214 sources', color: '#FF4500' },
  { name: 'Chaos Index', desc: 'Composite global instability score', color: '#ef4444' },
  { name: 'Markets', desc: 'Live stocks, crypto, commodities', color: '#22c55e' },
  { name: 'Geopolitical', desc: 'Conflict, sanctions, diplomacy', color: '#3b82f6' },
  { name: 'Cyber Threats', desc: 'Zero-days, breaches, ransomware', color: '#a855f7' },
  { name: 'Supply Chain', desc: 'Disruptions, port delays, shortages', color: '#f59e0b' },
  { name: 'Climate Events', desc: 'Earthquakes, fires, hurricanes', color: '#14b8a6' },
  { name: 'AI Simulation', desc: 'Predictive multi-agent debate', color: '#ec4899' },
]

const useCases = [
  {
    icon: '\u{1F3DB}',
    role: 'Political Intelligence',
    pain: 'Policy changes blindside your strategy. You learn about regulatory shifts from news headlines.',
    solution: 'Monitor government sites, detect policy changes in minutes, simulate public reaction before the press conference.',
    quote: 'We knew about the trade restriction 4 hours before Bloomberg reported it.'
  },
  {
    icon: '\u{1F4C8}',
    role: 'Hedge Fund / Trading Desk',
    pain: 'By the time your analyst reads the report, the market has already priced it in.',
    solution: 'Real-time anomaly detection on 214 feeds. Chaos Index spikes trigger alerts. AI simulates market impact.',
    quote: 'The Chaos Index spike at 3AM gave us a 40-minute head start on the energy trade.'
  },
  {
    icon: '\u{1F3E2}',
    role: 'Corporate Risk & Security',
    pain: 'Supply chain disruptions, cyber threats, and geopolitical risks appear without warning.',
    solution: 'Track supplier regions, monitor cyber feeds, get AI-predicted cascading effects across your supply network.',
    quote: 'We rerouted shipments 6 hours before the port closure was announced.'
  },
  {
    icon: '\u{1F30D}',
    role: 'NGO / Humanitarian',
    pain: 'Crisis response is always reactive. By the time funding is mobilized, the damage is done.',
    solution: 'Early warning from displacement data, conflict feeds, and climate monitoring. Predict refugee flows before they start.',
    quote: 'The displacement forecast gave us 48 hours to pre-position supplies.'
  },
]

const compareRows = [
  { feature: 'Real-time global signals', bloomberg: 'Financial only', recorded: 'Cyber focus', palantir: 'Custom build', oracle: '214 feeds, all domains' },
  { feature: 'AI predictive simulation', bloomberg: 'No', recorded: 'No', palantir: 'Custom', oracle: '500-agent sim engine' },
  { feature: 'Chaos/Risk index', bloomberg: 'No', recorded: 'Partial', palantir: 'Custom', oracle: 'Built-in, real-time' },
  { feature: 'Setup time', bloomberg: 'Weeks', recorded: 'Weeks', palantir: 'Months', oracle: '5 minutes' },
  { feature: 'Starting price', bloomberg: '$24K/yr', recorded: '$50K+/yr', palantir: '$1M+/yr', oracle: '$0 (free tier)' },
  { feature: 'On-premise option', bloomberg: 'No', recorded: 'Yes', palantir: 'Yes', oracle: 'Yes' },
]

const plans = [
  {
    name: 'ANALYST',
    tagline: 'For individuals getting started',
    price: '$0',
    period: '/mo',
    features: ['1 monitored site', '100 signals/day', '1 simulation', '6 intel panels', '3 categories'],
    cta: { label: 'Start Free', to: '/register' },
    popular: false,
    enterprise: false,
  },
  {
    name: 'SCOUT',
    tagline: 'For solo analysts who need more',
    price: '$49',
    period: '/mo',
    features: ['2 monitored sites', 'Unlimited signals', '3 simulations/mo', '10 intel panels', '5 categories'],
    cta: { label: 'Start 14-Day Trial', to: '/register' },
    popular: false,
    enterprise: false,
  },
  {
    name: 'STRATEGIST',
    tagline: 'For teams that need an edge',
    price: '$199',
    period: '/mo',
    features: ['5 monitored sites', 'Unlimited signals', '10 simulations/mo', '15 intel panels', '8 categories', '3 team members'],
    cta: { label: 'Start 14-Day Trial', to: '/register' },
    popular: false,
    enterprise: false,
  },
  {
    name: 'COMMANDER',
    tagline: 'For serious intelligence operations',
    price: '$999',
    period: '/mo',
    features: ['25 monitored sites', 'Unlimited signals', '50 simulations/mo', 'All 30 panels', 'All categories', '10 team members'],
    cta: { label: 'Start 14-Day Trial', to: '/register' },
    popular: true,
    enterprise: false,
  },
  {
    name: 'SOVEREIGN',
    tagline: 'Full platform. Your infrastructure.',
    price: '$5,000',
    period: '/mo',
    features: ['Unlimited everything', 'On-premise deployment', 'Air-gapped option', 'Dedicated support', 'Custom integrations', 'SLA guarantee'],
    cta: { label: 'Contact Sales', to: '/register' },
    popular: false,
    enterprise: true,
  },
]

const faqs = [
  {
    q: 'Where does OracleFlow get its intelligence data?',
    a: 'We aggregate from 214 open-source intelligence feeds including Reuters, AP, ACLED (conflict), USGS (earthquakes), NASA FIRMS (fires), Finnhub (markets), government RSS feeds, and more. All sources are legal, open-source intelligence (OSINT). You can also add custom sites to monitor.'
  },
  {
    q: 'How accurate are the AI simulations?',
    a: 'Our multi-agent simulation uses 500 AI personas (politicians, economists, military analysts, civilians) powered by GPT-4o to debate scenarios. While no prediction is 100% accurate, our system identifies probable outcomes and tipping points that human analysts consistently miss. The value is in exploring scenarios before they unfold.'
  },
  {
    q: 'Can I deploy OracleFlow on my own servers?',
    a: 'Yes. The Sovereign plan includes full on-premise deployment with Docker. We support air-gapped installations for government and military clients. Your data never leaves your infrastructure.'
  },
  {
    q: 'How is this different from a Bloomberg Terminal?',
    a: 'Bloomberg focuses on financial data. OracleFlow covers ALL intelligence domains — geopolitical, cyber, supply chain, climate, and financial — in one unified view. Plus, Bloomberg shows what happened. OracleFlow simulates what happens next. And we start at $0, not $24,000/year.'
  },
  {
    q: 'Is there a free tier? What are the limits?',
    a: 'Yes. The Analyst plan is completely free, forever. You get 1 monitored site, 100 signals per day, access to the Global Chaos Index, and all 30 intelligence panels. No credit card required. Upgrade only when you need AI simulations or more monitoring capacity.'
  },
]

const scrollTo = (id) => {
  const el = document.getElementById(id)
  if (el) el.scrollIntoView({ behavior: 'smooth' })
}

onMounted(async () => {
  // Check auth state
  isLoggedIn.value = !!localStorage.getItem('of_token')

  // Animate signal counter
  const target = signalCount.value
  const duration = 2000
  const start = performance.now()
  const tick = () => {
    const elapsed = performance.now() - start
    const progress = Math.min(elapsed / duration, 1)
    animatedSignals.value = Math.floor(progress * target)
    if (progress < 1) requestAnimationFrame(tick)
  }
  requestAnimationFrame(tick)

  // Rotate ribbon
  ribbonInterval = setInterval(() => {
    liveFeedIndex.value++
  }, 4000)

  // Fetch real chaos data
  try {
    const res = await fetch('/api/chaos/')
    if (res.ok) {
      const data = await res.json()
      const d = data.data || data
      const score = d.global_score ?? d.composite_score
      if (score != null) chaosScore.value = score.toFixed(1)
      const cats = d.category_scores || d.categories || {}
      const catMap = { finance: 'FIN', geopolitical: 'GEO', supply_chain: 'SCM', cyber: 'CYB', climate: 'CLI' }
      const colors = { finance: '#3b82f6', geopolitical: '#ef4444', supply_chain: '#f59e0b', cyber: '#a855f7', climate: '#22c55e' }
      chaosCats.value = Object.entries(catMap).map(([key, label]) => ({
        key,
        label,
        score: cats[key] != null ? cats[key].toFixed(1) : '--',
        color: colors[key]
      }))
    }
  } catch { /* use defaults */ }

  // Fetch signal count
  try {
    const res = await fetch('/api/signals/?limit=1')
    if (res.ok) {
      const data = await res.json()
      const d = data.data || data
      const total = d.total ?? signalCount.value
      signalCount.value = total
      animatedSignals.value = total
    }
  } catch { /* use defaults */ }
})

onUnmounted(() => {
  if (ribbonInterval) clearInterval(ribbonInterval)
  if (counterInterval) clearInterval(counterInterval)
})
</script>

<style scoped>
/* ===== TOKENS ===== */
.landing-page {
  --bg: #0a0a0a;
  --surface: #111111;
  --surface2: #1a1a1a;
  --text: #e8e8e8;
  --text-dim: #888;
  --text-muted: #555;
  --accent: #FF4500;
  --accent-hover: #e63e00;
  --border: #222;
  --mono: 'JetBrains Mono', 'Fira Code', monospace;
  --sans: 'Space Grotesk', 'Inter', system-ui, sans-serif;
}

/* ===== RESET ===== */
.landing-page {
  min-height: 100vh;
  background: var(--bg);
  color: var(--text);
  font-family: var(--sans);
  overflow-x: hidden;
}

.landing-page *,
.landing-page *::before,
.landing-page *::after {
  box-sizing: border-box;
}

.landing-page a {
  text-decoration: none;
  color: inherit;
}

/* ===== LIVE RIBBON ===== */
.live-ribbon {
  background: var(--accent);
  padding: 8px 0;
  text-align: center;
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 1001;
}

.ribbon-inner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-family: var(--mono);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 1px;
  color: #fff;
}

.ribbon-dot {
  width: 6px;
  height: 6px;
  background: #fff;
  border-radius: 50%;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* ===== NAVBAR ===== */
.landing-nav {
  position: fixed;
  top: 32px;
  left: 0;
  right: 0;
  z-index: 1000;
  background: rgba(10, 10, 10, 0.92);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
}

.nav-inner {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 60px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.nav-brand {
  font-family: var(--mono);
  font-weight: 800;
  font-size: 1rem;
  letter-spacing: 2px;
  color: var(--text);
}

.nav-links {
  display: flex;
  align-items: center;
  gap: 28px;
}

.nav-links a {
  font-family: var(--mono);
  font-size: 0.75rem;
  color: var(--text-dim);
  letter-spacing: 0.5px;
  transition: color 0.2s;
}

.nav-links a:hover { color: var(--text); }

.nav-login-btn {
  padding: 6px 16px;
  border: 1px solid var(--border);
  color: var(--text) !important;
  font-weight: 600;
  transition: border-color 0.2s;
}

.nav-login-btn:hover { border-color: var(--accent); }

.nav-cta-btn {
  background: var(--accent) !important;
  color: #fff !important;
  padding: 6px 16px;
  font-weight: 700;
  transition: background 0.2s;
}

.nav-cta-btn:hover { background: var(--accent-hover) !important; }

.mobile-menu-btn {
  display: none;
  flex-direction: column;
  gap: 5px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
}

.mobile-menu-btn span {
  display: block;
  width: 22px;
  height: 2px;
  background: var(--text);
}

.mobile-menu {
  display: none;
  flex-direction: column;
  padding: 16px 40px 24px;
  gap: 16px;
  border-top: 1px solid var(--border);
}

.mobile-menu a {
  font-family: var(--mono);
  font-size: 0.85rem;
  color: var(--text-dim);
}

/* ===== HERO ===== */
.hero-section {
  padding: 110px 0 60px;
}

.hero-grid {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 60px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 60px;
  align-items: center;
}

.hero-left {
  text-align: left;
}

.hero-right {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.hero-tag {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-family: var(--mono);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 3px;
  color: var(--accent);
  margin-bottom: 24px;
}

.hero-tag-dot {
  width: 8px;
  height: 8px;
  background: var(--accent);
  border-radius: 50%;
  animation: pulse 1.5s infinite;
}

.hero-title {
  font-size: 3.6rem;
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: -1.5px;
  margin: 0 0 24px 0;
  color: var(--text);
}

.hero-accent {
  color: var(--accent);
}

.hero-subtitle {
  font-size: 1.05rem;
  line-height: 1.7;
  color: var(--text-dim);
  max-width: 540px;
  margin: 0 0 36px 0;
}

/* ===== CHAOS WIDGET ===== */
.chaos-card-live {
  background: var(--surface);
  border: 1px solid var(--border);
  padding: 24px 28px;
  text-align: left;
  width: 100%;
}

.chaos-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.chaos-label {
  font-family: var(--mono);
  font-size: 0.7rem;
  color: var(--text-dim);
  letter-spacing: 1px;
}

.chaos-live-dot {
  width: 6px;
  height: 6px;
  background: #22c55e;
  border-radius: 50%;
  animation: pulse 1.5s infinite;
  margin-left: auto;
}

.chaos-live-text {
  font-family: var(--mono);
  font-size: 0.6rem;
  color: #22c55e;
  font-weight: 700;
  letter-spacing: 1px;
}

.chaos-score {
  font-family: var(--mono);
  font-size: 3rem;
  font-weight: 800;
  margin-bottom: 8px;
}

.chaos-bar-track {
  height: 4px;
  background: var(--surface2);
  margin-bottom: 16px;
  overflow: hidden;
}

.chaos-bar-fill {
  height: 100%;
  transition: width 1s ease;
}

.chaos-categories {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.chaos-cat {
  display: flex;
  align-items: center;
  gap: 6px;
  font-family: var(--mono);
  font-size: 0.7rem;
}

.chaos-cat-label {
  color: var(--text-muted);
}

.chaos-cat-score {
  font-weight: 700;
}

.live-counters {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  width: 100%;
}

.counter-item {
  background: var(--surface);
  border: 1px solid var(--border);
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-family: var(--mono);
}

.counter-value {
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--text);
}

.counter-label {
  font-size: 0.68rem;
  color: var(--text-dim);
  letter-spacing: 0.5px;
}

/* ===== HERO CTAs ===== */
.hero-ctas {
  display: flex;
  gap: 14px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.cta-primary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: var(--accent);
  color: #fff;
  padding: 16px 32px;
  font-family: var(--mono);
  font-weight: 700;
  font-size: 0.88rem;
  letter-spacing: 0.5px;
  border: none;
  cursor: pointer;
  transition: background 0.2s, transform 0.15s;
}

.cta-primary:hover {
  background: var(--accent-hover);
  transform: translateY(-2px);
}

.cta-secondary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: transparent;
  color: var(--text);
  padding: 16px 32px;
  font-family: var(--mono);
  font-weight: 700;
  font-size: 0.88rem;
  letter-spacing: 0.5px;
  border: 1px solid var(--border);
  cursor: pointer;
  transition: border-color 0.2s, transform 0.15s;
}

.cta-secondary:hover {
  border-color: var(--accent);
  transform: translateY(-2px);
}

.cta-large {
  padding: 20px 40px;
  font-size: 1rem;
}

.cta-arrow { font-size: 1.1em; }

.hero-trust-line {
  font-family: var(--mono);
  font-size: 0.72rem;
  color: var(--text-muted);
  letter-spacing: 0.5px;
}

/* ===== SECTION COMMON ===== */
.section-inner {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 60px;
}

.section-label {
  font-family: var(--mono);
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 3px;
  color: var(--accent);
  margin-bottom: 16px;
}

.section-title {
  font-size: 2.4rem;
  font-weight: 700;
  letter-spacing: -1px;
  margin: 0 0 48px 0;
  color: var(--text);
  line-height: 1.2;
}

/* ===== PROBLEM ===== */
.problem-section {
  padding: 120px 0;
  border-top: 1px solid var(--border);
}

.problem-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

.problem-card {
  background: var(--surface);
  border: 1px solid var(--border);
  padding: 40px 32px;
}

.problem-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--mono);
  font-size: 1.4rem;
  font-weight: 800;
  color: var(--accent);
  border: 2px solid var(--accent);
  margin-bottom: 20px;
}

.problem-card h3 {
  font-size: 1.1rem;
  font-weight: 700;
  margin: 0 0 12px 0;
  color: var(--text);
}

.problem-card p {
  font-size: 0.9rem;
  line-height: 1.7;
  color: var(--text-dim);
  margin: 0;
}

/* ===== HOW IT WORKS ===== */
.how-section {
  padding: 120px 0;
  border-top: 1px solid var(--border);
}

.pipeline {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0;
}

.pipeline-step {
  position: relative;
  padding: 0 24px;
  text-align: center;
}

.pipeline-num {
  font-family: var(--mono);
  font-size: 0.7rem;
  color: var(--text-muted);
  letter-spacing: 1px;
  margin-bottom: 12px;
}

.pipeline-line {
  width: 100%;
  height: 2px;
  background: var(--border);
  position: relative;
  margin-bottom: 24px;
}

.pipeline-line::before {
  content: '';
  position: absolute;
  left: 50%;
  top: -4px;
  width: 10px;
  height: 10px;
  background: var(--accent);
  border-radius: 50%;
  transform: translateX(-50%);
}

.pipeline-content {}

.pipeline-icon {
  font-size: 2rem;
  color: var(--accent);
  margin-bottom: 16px;
}

.pipeline-content h3 {
  font-family: var(--mono);
  font-size: 0.9rem;
  font-weight: 700;
  letter-spacing: 2px;
  margin: 0 0 10px 0;
  color: var(--text);
}

.pipeline-content p {
  font-size: 0.88rem;
  line-height: 1.6;
  color: var(--text-dim);
  margin: 0 0 12px 0;
}

.pipeline-detail {
  font-family: var(--mono);
  font-size: 0.7rem;
  color: var(--text-muted);
  letter-spacing: 0.5px;
}

/* ===== INTEL PREVIEW ===== */
.intel-preview-section {
  padding: 120px 0;
  border-top: 1px solid var(--border);
}

.intel-showcase {
  position: relative;
}

.intel-panels-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}

.intel-panel-card {
  background: var(--surface);
  border: 1px solid var(--border);
  overflow: hidden;
  transition: border-color 0.2s;
}

.intel-panel-card:hover { border-color: var(--accent); }

.panel-card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  font-family: var(--mono);
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--text);
  letter-spacing: 0.5px;
  border-bottom: 1px solid var(--border);
}

.panel-card-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.panel-card-body {
  padding: 16px;
  font-size: 0.8rem;
  color: var(--text-dim);
  line-height: 1.5;
}

.intel-cta-overlay {
  text-align: center;
  margin-top: 32px;
}

/* ===== USE CASES ===== */
.usecases-section {
  padding: 120px 0;
  border-top: 1px solid var(--border);
}

.usecase-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.usecase-card {
  background: var(--surface);
  border: 1px solid var(--border);
  padding: 40px 32px;
  transition: border-color 0.2s;
}

.usecase-card:hover { border-color: var(--accent); }

.usecase-icon {
  font-size: 2rem;
  margin-bottom: 16px;
}

.usecase-role {
  font-size: 1.1rem;
  font-weight: 700;
  margin: 0 0 16px 0;
  color: var(--text);
}

.usecase-problem,
.usecase-solution {
  font-size: 0.9rem;
  line-height: 1.6;
  color: var(--text-dim);
  margin: 0 0 12px 0;
}

.usecase-problem strong,
.usecase-solution strong {
  color: var(--text);
}

.usecase-quote {
  font-family: var(--mono);
  font-size: 0.8rem;
  color: var(--accent);
  border-left: 2px solid var(--accent);
  padding-left: 12px;
  margin-top: 16px;
  font-style: italic;
}

/* ===== COMPARISON ===== */
.compare-section {
  padding: 120px 0;
  border-top: 1px solid var(--border);
}

.compare-table-wrapper {
  overflow-x: auto;
}

.compare-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.compare-table th {
  font-family: var(--mono);
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.5px;
  color: var(--text-dim);
  padding: 16px 20px;
  text-align: left;
  border-bottom: 1px solid var(--border);
  white-space: nowrap;
}

.compare-table td {
  padding: 16px 20px;
  border-bottom: 1px solid #1a1a1a;
  color: var(--text-dim);
}

.compare-feature {
  color: var(--text) !important;
  font-weight: 600;
  white-space: nowrap;
}

.compare-highlight {
  background: rgba(255, 69, 0, 0.06) !important;
  color: var(--accent) !important;
  font-weight: 700;
}

/* ===== PRICING ===== */
.pricing-section {
  padding: 120px 0;
  border-top: 1px solid var(--border);
}

.pricing-sub {
  font-size: 1rem;
  color: var(--text-dim);
  margin-top: -32px;
  margin-bottom: 48px;
}

.pricing-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
}

.pricing-card {
  background: var(--surface);
  border: 1px solid var(--border);
  padding: 36px 28px;
  display: flex;
  flex-direction: column;
  position: relative;
  transition: border-color 0.2s, transform 0.2s;
}

.pricing-card:hover {
  border-color: var(--accent);
  transform: translateY(-4px);
}

.pricing-card-popular {
  border-color: var(--accent);
  background: #111;
}

.popular-badge {
  position: absolute;
  top: -1px;
  right: 20px;
  background: var(--accent);
  color: #fff;
  font-family: var(--mono);
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 2px;
  padding: 6px 14px;
}

.plan-name {
  font-family: var(--mono);
  font-size: 0.85rem;
  font-weight: 700;
  letter-spacing: 3px;
  color: var(--text);
  margin: 0 0 8px 0;
}

.plan-tagline {
  font-size: 0.8rem;
  color: var(--text-dim);
  margin-bottom: 20px;
}

.plan-price {
  margin-bottom: 28px;
}

.price-amount {
  font-family: var(--mono);
  font-size: 2.2rem;
  font-weight: 800;
  color: var(--text);
}

.price-period {
  font-family: var(--mono);
  font-size: 0.9rem;
  color: var(--text-muted);
}

.plan-features {
  list-style: none;
  padding: 0;
  margin: 0 0 28px 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.plan-features li {
  font-size: 0.85rem;
  color: var(--text-dim);
  padding-left: 20px;
  position: relative;
}

.plan-features li::before {
  content: '\2713';
  position: absolute;
  left: 0;
  color: var(--accent);
  font-weight: 700;
}

.plan-cta {
  display: block;
  text-align: center;
  padding: 14px;
  font-family: var(--mono);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 1px;
  border: 1px solid var(--border);
  color: var(--text);
  transition: all 0.2s;
}

.plan-cta:hover {
  border-color: var(--accent);
  background: rgba(255, 69, 0, 0.08);
}

.plan-cta-primary {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}

.plan-cta-primary:hover {
  background: var(--accent-hover);
  border-color: var(--accent-hover);
}

.plan-cta-enterprise {
  border-color: var(--text-muted);
  color: var(--text-dim);
}

.pricing-guarantee {
  text-align: center;
  font-family: var(--mono);
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 32px;
  letter-spacing: 0.5px;
}

/* ===== TRUST ===== */
.trust-section {
  padding: 80px 0;
  border-top: 1px solid var(--border);
  background: var(--surface);
}

.trust-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}

.trust-item {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.trust-icon {
  font-size: 1.6rem;
  flex-shrink: 0;
  margin-top: 2px;
}

.trust-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.trust-text strong {
  font-size: 0.9rem;
  color: var(--text);
}

.trust-text span {
  font-size: 0.8rem;
  color: var(--text-dim);
}

/* ===== FAQ ===== */
.faq-section {
  padding: 120px 0;
  border-top: 1px solid var(--border);
}

.faq-list {
  max-width: 800px;
}

.faq-item {
  border-bottom: 1px solid var(--border);
  cursor: pointer;
  transition: background 0.2s;
}

.faq-item:hover {
  background: rgba(255, 255, 255, 0.02);
}

.faq-question {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 0;
  font-weight: 600;
  font-size: 1rem;
  color: var(--text);
  gap: 16px;
}

.faq-toggle {
  font-family: var(--mono);
  font-size: 1.4rem;
  color: var(--accent);
  flex-shrink: 0;
  width: 24px;
  text-align: center;
}

.faq-answer {
  padding: 0 0 24px 0;
  font-size: 0.9rem;
  line-height: 1.7;
  color: var(--text-dim);
}

/* ===== FINAL CTA ===== */
.final-cta-section {
  padding: 120px 0;
  border-top: 1px solid var(--border);
  background: var(--surface);
}

.final-cta-inner {
  text-align: center;
}

.final-cta-title {
  font-size: 3rem;
  font-weight: 700;
  letter-spacing: -1px;
  margin: 0 0 20px 0;
  color: var(--text);
}

.final-cta-desc {
  font-size: 1.1rem;
  color: var(--text-dim);
  margin: 0 auto 40px;
  max-width: 560px;
}

.final-cta-btns {
  display: flex;
  gap: 16px;
  justify-content: center;
  flex-wrap: wrap;
}

/* ===== FOOTER ===== */
.landing-footer {
  border-top: 1px solid var(--border);
  padding: 32px 0;
}

.footer-inner {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 16px;
}

.footer-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.footer-brand {
  font-family: var(--mono);
  font-weight: 800;
  font-size: 0.85rem;
  letter-spacing: 2px;
  color: var(--text);
}

.footer-copy {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.footer-links {
  display: flex;
  gap: 24px;
}

.footer-links a {
  font-size: 0.8rem;
  color: var(--text-muted);
  transition: color 0.2s;
}

.footer-links a:hover { color: var(--text); }

/* ===== RESPONSIVE ===== */
@media (max-width: 1024px) {
  .hero-grid {
    grid-template-columns: 1fr;
    gap: 40px;
  }

  .hero-left {
    text-align: center;
  }

  .hero-subtitle {
    margin-left: auto;
    margin-right: auto;
  }

  .hero-ctas {
    justify-content: center;
  }

  .hero-trust-line {
    text-align: center;
  }

  .pipeline,
  .pricing-grid,
  .intel-panels-grid,
  .trust-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .problem-grid {
    grid-template-columns: 1fr;
  }

  .hero-title {
    font-size: 3rem;
  }

  .compare-table {
    font-size: 0.8rem;
  }
}

@media (max-width: 640px) {
  .nav-links {
    display: none;
  }

  .mobile-menu-btn {
    display: flex;
  }

  .mobile-menu {
    display: flex;
  }

  .hero-section {
    padding: 100px 0 40px;
  }

  .section-inner,
  .footer-inner,
  .hero-grid {
    padding: 0 20px;
  }

  .hero-grid {
    gap: 24px;
  }

  .hero-title {
    font-size: 2.2rem;
    letter-spacing: -0.5px;
  }

  .live-counters {
    grid-template-columns: 1fr 1fr;
  }

  .hero-subtitle {
    font-size: 1rem;
  }

  .hero-ctas {
    flex-direction: column;
    align-items: stretch;
  }

  .cta-primary,
  .cta-secondary {
    justify-content: center;
  }

  .hero-left {
    text-align: center;
  }

  .hero-ctas {
    justify-content: center;
  }

  .pipeline,
  .pricing-grid,
  .intel-panels-grid,
  .usecase-grid,
  .trust-grid {
    grid-template-columns: 1fr;
  }

  .problem-section,
  .how-section,
  .intel-preview-section,
  .usecases-section,
  .compare-section,
  .pricing-section,
  .faq-section,
  .final-cta-section,
  .trust-section {
    padding: 80px 0;
  }

  .section-title {
    font-size: 1.8rem;
  }

  .final-cta-title {
    font-size: 2rem;
  }

  .nav-inner,
  .mobile-menu {
    padding-left: 20px;
    padding-right: 20px;
  }

  .landing-footer {
    padding: 24px 0;
  }

  .footer-inner {
    flex-direction: column;
    align-items: flex-start;
  }

  .compare-table-wrapper {
    margin: 0 -20px;
    padding: 0 20px;
  }
}
</style>
