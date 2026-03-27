<template>
  <BasePanel
    panelId="tech-events"
    title="TECH & SECURITY"
    infoTooltip="Representative security data. Live CISA/NVD feed integration planned."
    dataBadge="DEMO"
    :showCount="true"
    :count="currentEvents.length"
  >
    <template #default>
      <div class="tech-container">
        <div class="tech-tabs">
          <button
            class="tech-tab"
            :class="{ 'tech-tab--active': activeTab === 'incidents' }"
            @click="activeTab = 'incidents'"
          >Incidents</button>
          <button
            class="tech-tab"
            :class="{ 'tech-tab--active': activeTab === 'advisories' }"
            @click="activeTab = 'advisories'"
          >Advisories</button>
          <button
            class="tech-tab"
            :class="{ 'tech-tab--active': activeTab === 'patches' }"
            @click="activeTab = 'patches'"
          >Patches</button>
        </div>

        <div class="tech-list">
          <div
            v-for="(evt, idx) in currentEvents"
            :key="idx"
            class="tech-event"
          >
            <div class="tech-event__header">
              <span class="tech-event__dot" :style="{ color: severityColor(evt.severity) }">&#x25CF;</span>
              <span class="tech-event__title">{{ evt.title }}</span>
            </div>
            <div class="tech-event__details">
              <span class="tech-event__detail">{{ evt.detail }}</span>
              <div class="tech-event__meta">
                <span class="tech-event__severity" :style="{ color: severityColor(evt.severity) }">{{ evt.severity }}</span>
                <span class="tech-event__time">{{ evt.time }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
  </BasePanel>
</template>

<script setup>
import { ref, computed } from 'vue'
import BasePanel from '../BasePanel.vue'

const activeTab = ref('incidents')

function severityColor(level) {
  if (level === 'CRITICAL') return '#ff4444'
  if (level === 'HIGH') return '#ff8800'
  if (level === 'ELEVATED') return '#ffaa00'
  return '#44aa44'
}

const incidents = ref([
  {
    severity: 'CRITICAL',
    title: 'Log4j Exploit Activity',
    detail: 'CVE-2021-44228 | Active scanning detected across enterprise networks',
    time: '2h ago'
  },
  {
    severity: 'HIGH',
    title: 'Microsoft Patch Tuesday',
    detail: '15 critical vulnerabilities patched including RCE in Exchange Server',
    time: '6h ago'
  },
  {
    severity: 'ELEVATED',
    title: 'AWS Service Disruption',
    detail: 'us-east-1 partial outage affecting S3 and Lambda services',
    time: '1h ago'
  },
  {
    severity: 'HIGH',
    title: 'SolarWinds Follow-on Activity',
    detail: 'New IOCs detected matching SUNBURST derivative | Government sector',
    time: '4h ago'
  },
  {
    severity: 'CRITICAL',
    title: 'Ivanti VPN Zero-Day',
    detail: 'CVE-2026-0188 | Active exploitation in the wild | Patch pending',
    time: '30m ago'
  }
])

const advisories = ref([
  {
    severity: 'CRITICAL',
    title: 'CISA Emergency Directive 26-02',
    detail: 'Federal agencies must patch Ivanti VPN within 48 hours',
    time: '1h ago'
  },
  {
    severity: 'HIGH',
    title: 'NSA Advisory: Chinese APT Activity',
    detail: 'Targeting telecommunications infrastructure in Southeast Asia',
    time: '8h ago'
  },
  {
    severity: 'ELEVATED',
    title: 'EU NIS2 Compliance Deadline',
    detail: 'New cybersecurity requirements effective for critical infrastructure',
    time: '1d ago'
  },
  {
    severity: 'HIGH',
    title: 'NCSC Advisory: Ransomware Trends',
    detail: 'Healthcare and education sectors seeing 40% increase in attacks',
    time: '2d ago'
  }
])

const patches = ref([
  {
    severity: 'CRITICAL',
    title: 'Chrome 124.0.6367.91',
    detail: 'Fixes 3 actively exploited zero-days in V8 engine',
    time: '3h ago'
  },
  {
    severity: 'HIGH',
    title: 'Linux Kernel 6.8.3',
    detail: 'Patches privilege escalation in netfilter subsystem',
    time: '12h ago'
  },
  {
    severity: 'ELEVATED',
    title: 'Apache Struts 6.4.0',
    detail: 'Fixes path traversal vulnerability CVE-2026-0215',
    time: '1d ago'
  },
  {
    severity: 'HIGH',
    title: 'Cisco IOS XE 17.12.2',
    detail: 'Addresses web UI command injection CVE-2026-0301',
    time: '2d ago'
  }
])

const currentEvents = computed(() => {
  if (activeTab.value === 'advisories') return advisories.value
  if (activeTab.value === 'patches') return patches.value
  return incidents.value
})
</script>

<style scoped>
.tech-container {
  overflow-y: auto;
  flex: 1;
}

.tech-tabs {
  display: flex;
  border-bottom: 1px solid var(--border, #2a2a2a);
}

.tech-tab {
  flex: 1;
  padding: 8px 12px;
  background: none;
  border: none;
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-dim, #888);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  cursor: pointer;
  transition: color 0.15s ease, border-color 0.15s ease;
  border-bottom: 2px solid transparent;
}

.tech-tab:hover {
  color: var(--text, #e8e8e8);
}

.tech-tab--active {
  color: var(--accent, #fff);
  border-bottom-color: var(--accent, #fff);
}

.tech-list {
  padding: 0;
}

.tech-event {
  padding: 10px 12px;
  border-bottom: 1px solid var(--border, #2a2a2a);
  transition: background 0.15s ease;
}

.tech-event:hover {
  background: var(--surface-hover, #1e1e1e);
}

.tech-event__header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.tech-event__dot {
  font-size: 10px;
  flex-shrink: 0;
}

.tech-event__title {
  font-family: 'SF Mono', monospace;
  font-size: 12px;
  font-weight: 700;
  color: var(--text, #e8e8e8);
}

.tech-event__details {
  padding-left: 18px;
}

.tech-event__detail {
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--text-dim, #888);
  line-height: 1.4;
}

.tech-event__meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 4px;
}

.tech-event__severity {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.tech-event__time {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  color: var(--text-muted, #666);
}
</style>
