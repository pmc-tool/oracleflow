<template>
  <div class="entities-view">
    <h1 class="page-title">Entities</h1>

    <!-- Filter bar -->
    <div class="filter-bar">
      <select v-model="filters.entity_type" class="filter-select">
        <option value="">All Types</option>
        <option v-for="t in typeOptions" :key="t" :value="t">{{ t }}</option>
      </select>
      <input
        v-model="filters.country"
        type="text"
        class="text-input"
        placeholder="Filter by country..."
      />
      <button class="btn-clear" @click="clearFilters">Clear</button>
    </div>

    <div v-if="loading" class="loading-text">Loading...</div>

    <div v-else-if="entities.length === 0" class="empty-state">No entities tracked</div>

    <table v-else class="data-table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Type</th>
          <th>Country</th>
          <th>Created</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="ent in entities"
          :key="ent.id"
          class="clickable-row"
          @click="goToEntity(ent.id)"
        >
          <td>{{ ent.name }}</td>
          <td><span class="badge badge-type">{{ ent.entity_type }}</span></td>
          <td class="mono-cell">{{ ent.country || '--' }}</td>
          <td class="ts-cell">{{ formatTime(ent.created_at) }}</td>
        </tr>
      </tbody>
    </table>

    <div v-if="error" class="error-text">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listEntities } from '../api/intelligence'

const router = useRouter()
const loading = ref(true)
const error = ref('')
const entities = ref([])
const page = ref(1)

const typeOptions = ['person', 'organization', 'government', 'company', 'political_party', 'other']

const filters = reactive({
  entity_type: '',
  country: '',
})

const formatTime = (ts) => {
  if (!ts) return '--'
  return new Date(ts).toLocaleDateString()
}

const goToEntity = (id) => {
  router.push({ name: 'EntityDetail', params: { entityId: id } })
}

const clearFilters = () => {
  filters.entity_type = ''
  filters.country = ''
}

const loadEntities = async () => {
  loading.value = true
  error.value = ''
  try {
    const params = {}
    if (filters.entity_type) params.entity_type = filters.entity_type
    if (filters.country) params.country = filters.country

    const res = await listEntities(params)
    const d = res.data || res
    entities.value = Array.isArray(d) ? d : (d.items || d.results || [])
  } catch (e) {
    error.value = 'Failed to load entities: ' + e.message
  } finally {
    loading.value = false
  }
}

let filterTimeout = null
watch(filters, () => {
  clearTimeout(filterTimeout)
  filterTimeout = setTimeout(() => {
    page.value = 1
    loadEntities()
  }, 300)
})

onMounted(loadEntities)
</script>

<style scoped>
.entities-view {
  font-family: 'Space Grotesk', system-ui, sans-serif;
  max-width: 1000px;
}

.page-title {
  font-size: 1.8rem;
  font-weight: 600;
  margin-bottom: 24px;
  color: #FFFFFF;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.filter-select {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  padding: 6px 12px;
  background: #111;
  border: 1px solid #333;
  color: #CCC;
  outline: none;
  cursor: pointer;
  min-width: 140px;
}

.filter-select:focus {
  border-color: #FF4500;
}

.text-input {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  padding: 6px 12px;
  background: #111;
  border: 1px solid #333;
  color: #CCC;
  outline: none;
  min-width: 160px;
}

.text-input:focus {
  border-color: #FF4500;
}

.btn-clear {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  padding: 6px 14px;
  background: transparent;
  border: 1px solid #333;
  color: #999;
  cursor: pointer;
  transition: all 0.15s;
}

.btn-clear:hover {
  border-color: #FF4500;
  color: #FF4500;
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
  padding: 30px 0;
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
  letter-spacing: 0.5px;
  padding: 8px 12px;
  border-bottom: 1px solid #333;
}

.data-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #1a1a1a;
  color: #CCC;
}

.clickable-row {
  cursor: pointer;
  transition: background 0.15s;
}

.clickable-row:hover {
  background: #111;
}

.mono-cell {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
}

.ts-cell {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #666;
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
</style>
