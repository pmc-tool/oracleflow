<template>
  <div class="sites-view">
    <div class="page-header">
      <h1 class="page-title">Monitored Sites</h1>
      <button class="btn-orange" @click="showForm = !showForm">
        {{ showForm ? 'Cancel' : 'Add Site' }}
      </button>
    </div>

    <!-- Inline add form -->
    <div v-if="showForm" class="add-form">
      <input
        v-model="newUrl"
        type="text"
        class="text-input"
        placeholder="https://example.com"
        @keyup.enter="discover"
      />
      <button class="btn-orange" :disabled="discovering || !newUrl.trim()" @click="discover">
        {{ discovering ? 'Discovering...' : 'Discover' }}
      </button>
    </div>

    <div v-if="loading" class="loading-text">Loading...</div>

    <div v-else-if="sites.length === 0" class="empty-state">No sites monitored</div>

    <div v-else class="sites-grid">
      <div
        v-for="site in sites"
        :key="site.id"
        class="site-card"
        @click="goToSite(site.id)"
      >
        <div class="card-top">
          <span class="card-domain">{{ site.domain }}</span>
          <span class="status-badge" :class="'status-' + site.status">{{ site.status }}</span>
        </div>
        <div class="card-stats">
          <div class="stat-item">
            <span class="stat-label">Pages</span>
            <span class="stat-value">{{ site.discovered_pages_count ?? site.page_count ?? '--' }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Changes</span>
            <span class="stat-value">{{ site.total_changes ?? 0 }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">Last Checked</span>
            <span class="stat-value ts-value">{{ formatRelativeTime(site.last_checked_at || site.updated_at) }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="error" class="error-text">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listSites, discoverSite } from '../api/intelligence'

const router = useRouter()
const loading = ref(true)
const error = ref('')
const sites = ref([])
const showForm = ref(false)
const newUrl = ref('')
const discovering = ref(false)

const formatRelativeTime = (ts) => {
  if (!ts) return 'never'
  const diff = Date.now() - new Date(ts).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  if (days < 30) return `${days}d ago`
  return new Date(ts).toLocaleDateString()
}

const goToSite = (id) => {
  router.push({ name: 'SiteDetail', params: { siteId: id } })
}

const loadSites = async () => {
  try {
    const res = await listSites()
    const d = res.data || res
    sites.value = Array.isArray(d) ? d : (d.items || d.results || [])
  } catch (e) {
    error.value = 'Failed to load sites: ' + e.message
  } finally {
    loading.value = false
  }
}

const discover = async () => {
  if (!newUrl.value.trim() || discovering.value) return
  discovering.value = true
  error.value = ''
  try {
    let url = newUrl.value.trim()
    if (!url.startsWith('http://') && !url.startsWith('https://')) url = 'https://' + url
    await discoverSite(url)
    newUrl.value = ''
    showForm.value = false
    loading.value = true
    await loadSites()
  } catch (e) {
    if (e.response && e.response.data && e.response.data.upgrade) {
      error.value = `Plan limit reached: your plan allows ${e.response.data.limit} site(s). Upgrade in Settings → Billing.`
    } else {
      error.value = 'Discovery failed: ' + (e.response?.data?.error || e.message)
    }
  } finally {
    discovering.value = false
  }
}

onMounted(loadSites)
</script>

<style scoped>
.sites-view {
  font-family: 'Space Grotesk', system-ui, sans-serif;
  max-width: 1100px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-title {
  font-size: 1.8rem;
  font-weight: 600;
  color: #FFFFFF;
}

.btn-orange {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  font-weight: 600;
  padding: 8px 18px;
  background: #FF4500;
  color: #FFFFFF;
  border: none;
  cursor: pointer;
  letter-spacing: 0.5px;
  transition: opacity 0.15s;
}

.btn-orange:hover:not(:disabled) {
  opacity: 0.85;
}

.btn-orange:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.add-form {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.text-input {
  flex: 1;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.85rem;
  padding: 8px 14px;
  background: #111;
  border: 1px solid #333;
  color: #FFFFFF;
  outline: none;
}

.text-input:focus {
  border-color: #FF4500;
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

/* Site cards grid */
.sites-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}

.site-card {
  background: #141414;
  border: 1px solid #222;
  padding: 20px;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}

.site-card:hover {
  border-color: #FF4500;
  background: #1a1a1a;
}

.card-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-domain {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.95rem;
  font-weight: 600;
  color: #e8e8e8;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
}

.card-stats {
  display: flex;
  gap: 20px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  color: #666;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stat-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.9rem;
  color: #e8e8e8;
  font-weight: 500;
}

.ts-value {
  font-size: 0.75rem;
  color: #999;
}

.status-badge {
  display: inline-block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  padding: 2px 8px;
  border: 1px solid;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  flex-shrink: 0;
}

.status-discovering {
  border-color: #FF9800;
  color: #FF9800;
}

.status-active {
  border-color: #4CAF50;
  color: #4CAF50;
}

.status-inactive {
  border-color: #666;
  color: #666;
}

.status-failed {
  border-color: #F44336;
  color: #F44336;
}

@media (max-width: 768px) {
  .sites-grid {
    grid-template-columns: 1fr;
  }

  .card-stats {
    flex-wrap: wrap;
    gap: 12px;
  }
}
</style>
