<template>
  <div class="entity-detail">
    <router-link to="/entities" class="back-link">&larr; Back to Entities</router-link>

    <div v-if="loading" class="loading-text">Loading...</div>

    <template v-else-if="entity">
      <div class="entity-header">
        <h1 class="page-title">{{ entity.name }}</h1>
        <span class="badge badge-type">{{ entity.entity_type }}</span>
      </div>

      <div class="info-row">
        <div class="info-item">
          <span class="info-label">Country</span>
          <span class="info-value">{{ entity.country || '--' }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">Created</span>
          <span class="info-value mono">{{ formatTime(entity.created_at) }}</span>
        </div>
      </div>

      <!-- Sources -->
      <div class="section-box">
        <h2 class="section-heading">Sources</h2>
        <div v-if="!sources.length" class="empty-state">No sources linked</div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>Type</th>
              <th>URL</th>
              <th>Confidence</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(src, i) in sources" :key="i">
              <td class="mono-cell">{{ src.type }}</td>
              <td>
                <a :href="src.url" target="_blank" class="source-link">{{ src.url }}</a>
              </td>
              <td class="mono-cell">{{ src.confidence != null ? (src.confidence * 100).toFixed(0) + '%' : '--' }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Relationships -->
      <div class="section-box">
        <h2 class="section-heading">Relationships</h2>
        <div v-if="!relationships.length" class="empty-state">No relationships found</div>
        <table v-else class="data-table">
          <thead>
            <tr>
              <th>Related Entity</th>
              <th>Type</th>
              <th>Strength</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(rel, i) in relationships" :key="i">
              <td>{{ rel.related_entity || rel.target_name || '--' }}</td>
              <td><span class="badge">{{ rel.relationship_type || rel.type }}</span></td>
              <td>
                <div class="strength-bar-track">
                  <div
                    class="strength-bar-fill"
                    :style="{ width: ((rel.strength || 0) * 100) + '%' }"
                  ></div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Related Signals -->
      <div class="section-box">
        <h2 class="section-heading">Related Signals ({{ relatedSignals.length }})</h2>
        <div v-if="signalsLoading" class="empty-state">Loading signals...</div>
        <div v-else-if="!relatedSignals.length" class="empty-state">No signals found mentioning this entity</div>
        <div v-else class="signal-list">
          <div v-for="sig in relatedSignals" :key="sig.id" class="signal-item">
            <div class="signal-item__header">
              <span class="badge badge-source">{{ sig.source }}</span>
              <span class="badge badge-cat">{{ sig.category }}</span>
              <span class="signal-item__time">{{ formatRelative(sig.timestamp) }}</span>
            </div>
            <div class="signal-item__title">
              <a v-if="sig.source_url" :href="sig.source_url" target="_blank" class="title-link">{{ sig.title }}</a>
              <span v-else>{{ sig.title }}</span>
            </div>
            <div class="signal-item__meta">
              <span>Anomaly: {{ (sig.anomaly_score * 100).toFixed(0) }}%</span>
              <span>Sentiment: {{ sig.sentiment_score > 0 ? '+' : '' }}{{ sig.sentiment_score.toFixed(2) }}</span>
            </div>
          </div>
        </div>
      </div>
    </template>

    <div v-if="error" class="error-text">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getEntity, listSignals } from '../api/intelligence'

const props = defineProps({
  entityId: { type: [String, Number], required: true }
})

const loading = ref(true)
const signalsLoading = ref(true)
const error = ref('')
const entity = ref(null)
const sources = ref([])
const relationships = ref([])
const relatedSignals = ref([])

const formatTime = (ts) => {
  if (!ts) return '--'
  return new Date(ts).toLocaleString()
}

const formatRelative = (ts) => {
  if (!ts) return '--'
  const diff = Date.now() - new Date(ts).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  return `${Math.floor(hrs / 24)}d ago`
}

onMounted(async () => {
  try {
    const res = await getEntity(props.entityId)
    const d = res.data || res
    entity.value = d
    sources.value = d.sources || []
    relationships.value = d.relationships || []

    // Fetch signals mentioning this entity
    if (d.name) {
      try {
        const sigRes = await listSignals({ entity: d.name, limit: 20 })
        const sigData = sigRes.data || sigRes
        relatedSignals.value = Array.isArray(sigData) ? sigData : (sigData.data || sigData.items || [])
      } catch { /* ignore */ }
    }
  } catch (e) {
    error.value = 'Failed to load entity: ' + e.message
  } finally {
    loading.value = false
    signalsLoading.value = false
  }
})
</script>

<style scoped>
.entity-detail {
  font-family: 'Space Grotesk', system-ui, sans-serif;
  max-width: 1000px;
}

.back-link {
  display: inline-block;
  color: #999;
  text-decoration: none;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  margin-bottom: 20px;
  transition: color 0.15s;
}

.back-link:hover {
  color: #FF4500;
}

.page-title {
  font-size: 1.8rem;
  font-weight: 600;
  color: #FFFFFF;
}

.entity-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}

.info-row {
  display: flex;
  gap: 30px;
  margin-bottom: 30px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #999;
  letter-spacing: 0.5px;
}

.info-value {
  color: #CCC;
  font-size: 0.9rem;
}

.mono {
  font-family: 'JetBrains Mono', monospace;
}

.loading-text {
  font-family: 'JetBrains Mono', monospace;
  color: #999;
  font-size: 0.9rem;
}

.error-text {
  font-family: 'JetBrains Mono', monospace;
  color: #F44336;
  font-size: 0.85rem;
  margin-top: 15px;
}

.empty-state {
  color: #666;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  padding: 20px 0;
}

.section-box {
  border: 1px solid #333;
  padding: 20px;
  margin-bottom: 24px;
  background: #000;
}

.section-heading {
  font-size: 1rem;
  font-weight: 600;
  color: #FFFFFF;
  margin-bottom: 16px;
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 0.5px;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.data-table th {
  text-align: left;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #999;
  padding: 8px 12px;
  border-bottom: 1px solid #333;
}

.data-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #1a1a1a;
  color: #CCC;
}

.mono-cell {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
}

.badge {
  display: inline-block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  padding: 2px 8px;
  border: 1px solid #444;
  color: #CCC;
  letter-spacing: 0.5px;
}

.badge-type {
  border-color: #FF4500;
  color: #FF4500;
}

.source-link {
  color: #FF4500;
  text-decoration: none;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  word-break: break-all;
}

.source-link:hover {
  text-decoration: underline;
}

.strength-bar-track {
  width: 80px;
  height: 8px;
  background: #1a1a1a;
  border: 1px solid #333;
  overflow: hidden;
}

.strength-bar-fill {
  height: 100%;
  background: #FF4500;
  transition: width 0.3s ease;
}

.graph-placeholder {
  min-height: 200px;
  display: flex;
  flex-direction: column;
}

.placeholder-content {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  border: 1px dashed #333;
  min-height: 140px;
}

.signal-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.signal-item {
  border: 1px solid #222;
  padding: 14px;
  background: #0a0a0a;
  transition: border-color 0.15s;
}

.signal-item:hover { border-color: #FF4500; }

.signal-item__header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.signal-item__time {
  margin-left: auto;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #666;
}

.signal-item__title {
  font-size: 0.9rem;
  font-weight: 500;
  margin-bottom: 6px;
  line-height: 1.4;
}

.title-link {
  color: #e8e8e8;
  text-decoration: none;
}

.title-link:hover { text-decoration: underline; color: #FF4500; }

.signal-item__meta {
  display: flex;
  gap: 16px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #888;
}

.badge-source {
  border-color: #444;
  color: #CCC;
}

.badge-cat {
  border-color: #FF4500;
  color: #FF4500;
}
</style>
