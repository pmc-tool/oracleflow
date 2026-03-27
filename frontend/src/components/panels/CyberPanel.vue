<template>
  <BasePanel panelId="cyber" title="CYBER THREATS" :showCount="true" :count="activeCount">
    <template #default>
      <div class="cyber-container">
        <div class="cyber-tabs">
          <button
            class="cyber-tab"
            :class="{ 'cyber-tab--active': activeTab === 'active' }"
            @click="activeTab = 'active'"
          >Active</button>
          <button
            class="cyber-tab"
            :class="{ 'cyber-tab--active': activeTab === 'recent' }"
            @click="activeTab = 'recent'"
          >Recent</button>
          <button
            class="cyber-tab"
            :class="{ 'cyber-tab--active': activeTab === 'advisories' }"
            @click="activeTab = 'advisories'"
          >Advisories</button>
        </div>

        <div v-if="loading" class="cyber-empty">
          Scanning threat landscape...
        </div>

        <div v-if="activeTab === 'active' && !loading" class="cyber-list">
          <div
            v-for="(threat, idx) in activeThreats"
            :key="idx"
            class="cyber-threat"
          >
            <div class="cyber-threat__header">
              <span class="cyber-threat__dot" :style="{ color: severityColor(threat.severity) }">&#x25CF;</span>
              <span class="cyber-threat__level" :style="{ color: severityColor(threat.severity) }">{{ threat.severity }}</span>
              <span class="cyber-threat__name">
                <a
                  v-if="threat.sourceUrl"
                  :href="threat.sourceUrl"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="cyber-threat__link"
                >{{ threat.name }}</a>
                <span v-else>{{ threat.name }}</span>
              </span>
              <span class="cyber-threat__time">{{ threat.detected }}</span>
            </div>
            <div class="cyber-threat__detail">
              <span class="cyber-threat__label">Target:</span>
              <span class="cyber-threat__val">{{ threat.target }}</span>
            </div>
            <div class="cyber-threat__detail">
              <span class="cyber-threat__label">Source:</span>
              <span class="cyber-threat__val">{{ threat.source }}</span>
            </div>
            <div v-if="threat.mitreAttack && threat.mitreAttack.length" class="cyber-threat__mitre">
              <span
                v-for="technique in threat.mitreAttack"
                :key="technique"
                class="mitre-badge"
              >{{ technique }}</span>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'recent' && !loading" class="cyber-list">
          <div
            v-for="(threat, idx) in recentThreats"
            :key="idx"
            class="cyber-threat"
          >
            <div class="cyber-threat__header">
              <span class="cyber-threat__dot" :style="{ color: severityColor(threat.severity) }">&#x25CF;</span>
              <span class="cyber-threat__level" :style="{ color: severityColor(threat.severity) }">{{ threat.severity }}</span>
              <span class="cyber-threat__name">
                <a
                  v-if="threat.sourceUrl"
                  :href="threat.sourceUrl"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="cyber-threat__link"
                >{{ threat.name }}</a>
                <span v-else>{{ threat.name }}</span>
              </span>
              <span class="cyber-threat__time">{{ threat.detected }}</span>
            </div>
            <div class="cyber-threat__detail">
              <span class="cyber-threat__label">Target:</span>
              <span class="cyber-threat__val">{{ threat.target }}</span>
            </div>
            <div class="cyber-threat__detail">
              <span class="cyber-threat__label">Source:</span>
              <span class="cyber-threat__val">{{ threat.source }}</span>
            </div>
            <div v-if="threat.mitreAttack && threat.mitreAttack.length" class="cyber-threat__mitre">
              <span
                v-for="technique in threat.mitreAttack"
                :key="technique"
                class="mitre-badge"
              >{{ technique }}</span>
            </div>
          </div>
        </div>

        <div v-if="activeTab === 'advisories' && !loading" class="cyber-list">
          <div
            v-for="(adv, idx) in advisories"
            :key="idx"
            class="cyber-threat"
          >
            <div class="cyber-threat__header">
              <span class="cyber-threat__dot" :style="{ color: severityColor(adv.severity) }">&#x25CF;</span>
              <span class="cyber-threat__level" :style="{ color: severityColor(adv.severity) }">{{ adv.severity }}</span>
              <span class="cyber-threat__name">{{ adv.name }}</span>
              <span class="cyber-threat__time">{{ adv.detected }}</span>
            </div>
            <div class="cyber-threat__detail">
              <span class="cyber-threat__label">Advisory:</span>
              <span class="cyber-threat__val">{{ adv.advisory }}</span>
            </div>
          </div>
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
const loading = ref(false)
const activeTab = ref('active')
let refreshInterval = null

const placeholderActive = [
  { severity: 'CRITICAL', name: 'DDoS Campaign', target: 'Financial sector', source: 'Multiple botnets', detected: '2h ago' },
  { severity: 'HIGH', name: 'Ransomware Variant', target: 'Healthcare systems', source: 'Unknown APT', detected: '6h ago' },
  { severity: 'ELEVATED', name: 'Phishing Campaign', target: 'Government agencies', source: 'State-sponsored', detected: '12h ago' },
  { severity: 'HIGH', name: 'Zero-Day Exploit', target: 'Enterprise VPNs', source: 'APT-29', detected: '18h ago' },
  { severity: 'CRITICAL', name: 'Supply Chain Attack', target: 'Software vendors', source: 'Lazarus Group', detected: '1h ago' },
]

const placeholderRecent = [
  { severity: 'HIGH', name: 'Credential Stuffing', target: 'E-commerce platforms', source: 'Distributed actors', detected: '2d ago' },
  { severity: 'ELEVATED', name: 'Watering Hole Attack', target: 'Energy sector', source: 'APT-41', detected: '3d ago' },
  { severity: 'CRITICAL', name: 'Wiper Malware', target: 'Critical infrastructure', source: 'Sandworm', detected: '4d ago' },
]

const placeholderAdvisories = [
  { severity: 'CRITICAL', name: 'CVE-2026-1847', advisory: 'Remote code execution in widely used library', detected: '1d ago' },
  { severity: 'HIGH', name: 'CVE-2026-1792', advisory: 'Privilege escalation in container runtime', detected: '3d ago' },
  { severity: 'ELEVATED', name: 'CVE-2026-1685', advisory: 'SQL injection in CMS framework', detected: '5d ago' },
]

function getSourceUrl(item) {
  if (item.source_url) return item.source_url
  try {
    const raw = item.raw_data_json
    if (typeof raw === 'string') {
      const parsed = JSON.parse(raw)
      return parsed.link || parsed.url || parsed.source_url || null
    }
    if (raw && typeof raw === 'object') {
      return raw.link || raw.url || raw.source_url || null
    }
  } catch { /* ignore */ }
  return null
}

const cyberSignals = computed(() => {
  return signals.value.filter(s => (s.category || '').toLowerCase() === 'cyber')
})

const activeThreats = computed(() => {
  if (cyberSignals.value.length === 0) return placeholderActive
  return cyberSignals.value
    .filter(s => (s.anomaly_score || 0) >= 0.4)
    .slice(0, 5)
    .map(s => ({
      severity: getSeverity(s),
      name: s.title || s.signal_type || 'Unknown Threat',
      target: s.country || 'Multiple sectors',
      source: s.source || 'Unknown',
      detected: formatTimeAgo(s.timestamp),
      sourceUrl: getSourceUrl(s),
      mitreAttack: s.entities?.mitre_attack || [],
    }))
})

const recentThreats = computed(() => {
  if (cyberSignals.value.length === 0) return placeholderRecent
  return cyberSignals.value
    .filter(s => (s.anomaly_score || 0) < 0.4)
    .slice(0, 5)
    .map(s => ({
      severity: getSeverity(s),
      name: s.title || s.signal_type || 'Unknown Threat',
      target: s.country || 'Multiple sectors',
      source: s.source || 'Unknown',
      detected: formatTimeAgo(s.timestamp),
      sourceUrl: getSourceUrl(s),
      mitreAttack: s.entities?.mitre_attack || [],
    }))
})

const advisories = computed(() => {
  return placeholderAdvisories
})

const activeCount = computed(() => {
  return activeThreats.value.length
})

function getSeverity(signal) {
  const score = signal.anomaly_score || 0
  if (score >= 0.8) return 'CRITICAL'
  if (score >= 0.6) return 'HIGH'
  if (score >= 0.4) return 'ELEVATED'
  return 'NORMAL'
}

function severityColor(level) {
  if (level === 'CRITICAL') return '#ff4444'
  if (level === 'HIGH') return '#ff8800'
  if (level === 'ELEVATED') return '#ffaa00'
  return '#44aa44'
}

function formatTimeAgo(dateStr) {
  if (!dateStr) return ''
  const now = Date.now()
  const then = new Date(dateStr).getTime()
  const diff = Math.floor((now - then) / 1000)
  if (diff < 60) return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`
  return `${Math.floor(diff / 86400)}d ago`
}

async function fetchSignals() {
  loading.value = true
  try {
    const res = await listSignals({ limit: 100, category: 'cyber' })
    const data = res.data?.data || res.data?.results || res.data || []
    signals.value = Array.isArray(data) ? data : []
  } catch (err) {
    console.error('[CyberPanel] fetch error:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchSignals()
  refreshInterval = setInterval(fetchSignals, 60000)
})

onUnmounted(() => {
  if (refreshInterval) clearInterval(refreshInterval)
})
</script>

<style scoped>
.cyber-container {
  overflow-y: auto;
  flex: 1;
}

.cyber-badge {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  font-weight: 700;
  color: #ff4444;
  margin-left: auto;
}

.cyber-tabs {
  display: flex;
  border-bottom: 1px solid var(--wm-border, #2a2a2a);
}

.cyber-tab {
  flex: 1;
  padding: 8px 12px;
  background: none;
  border: none;
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  font-weight: 600;
  color: var(--wm-text-dim, #888);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  cursor: pointer;
  transition: color 0.15s ease, border-color 0.15s ease;
  border-bottom: 2px solid transparent;
}

.cyber-tab:hover {
  color: var(--wm-text, #e8e8e8);
}

.cyber-tab--active {
  color: var(--wm-accent, #fff);
  border-bottom-color: var(--wm-accent, #fff);
}

.cyber-list {
  padding: 0;
}

.cyber-threat {
  padding: 10px 12px;
  border-bottom: 1px solid var(--wm-border, #2a2a2a);
  transition: background 0.15s ease;
}

.cyber-threat:hover {
  background: var(--wm-surface-hover, #1e1e1e);
}

.cyber-threat__header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 6px;
}

.cyber-threat__dot {
  font-size: 10px;
}

.cyber-threat__level {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.cyber-threat__name {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  font-weight: 600;
  color: var(--wm-text, #e8e8e8);
  flex: 1;
}

.cyber-threat__link {
  color: inherit;
  text-decoration: none;
}

.cyber-threat__link:hover {
  text-decoration: underline;
}

.cyber-threat__time {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  color: var(--wm-text-dim, #888);
  margin-left: auto;
  flex-shrink: 0;
}

.cyber-threat__detail {
  display: flex;
  align-items: center;
  gap: 6px;
  padding-left: 18px;
  margin-bottom: 2px;
}

.cyber-threat__label {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--wm-text-dim, #888);
  min-width: 64px;
}

.cyber-threat__val {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--wm-text-secondary, #ccc);
}

.cyber-threat__mitre {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  padding-left: 18px;
  margin-top: 4px;
}

.mitre-badge {
  display: inline-block;
  font-family: 'SF Mono', monospace;
  font-size: 9px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 2px;
  letter-spacing: 0.3px;
  color: #ce93d8;
  background: rgba(206, 147, 216, 0.1);
  border: 1px solid rgba(206, 147, 216, 0.3);
}

.cyber-empty {
  padding: 24px;
  text-align: center;
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--wm-text-dim, #888);
}
</style>
