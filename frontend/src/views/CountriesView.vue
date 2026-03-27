<template>
  <div class="countries-view">
    <h1 class="page-title">Countries</h1>

    <div v-if="loading" class="loading-text">Loading...</div>

    <div v-else-if="countries.length === 0" class="empty-state">No countries available</div>

    <div v-else class="countries-grid">
      <div
        v-for="c in countries"
        :key="c.code"
        class="country-card"
        @click="goToCountry(c.code)"
      >
        <span class="country-flag">{{ getFlag(c.code) }}</span>
        <div class="country-info">
          <h3 class="country-name">{{ c.name }}</h3>
          <div class="country-meta">
            <span v-if="c.region" class="meta-item">{{ c.region }}</span>
            <span v-if="c.languages" class="meta-item meta-lang">{{ formatLanguages(c.languages) }}</span>
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
import { listCountries } from '../api/intelligence'

const router = useRouter()
const loading = ref(true)
const error = ref('')
const countries = ref([])

const getFlag = (code) => {
  if (!code || code.length < 2) return ''
  return String.fromCodePoint(
    ...code.toUpperCase().split('').map(c => 127397 + c.charCodeAt(0))
  )
}

const formatLanguages = (langs) => {
  if (Array.isArray(langs)) return langs.slice(0, 3).join(', ')
  if (typeof langs === 'string') return langs
  return ''
}

const goToCountry = (code) => {
  router.push({ name: 'CountryDetail', params: { code } })
}

onMounted(async () => {
  try {
    const res = await listCountries()
    const d = res.data || res
    countries.value = Array.isArray(d) ? d : (d.items || d.results || [])
  } catch (e) {
    error.value = 'Failed to load countries: ' + e.message
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.countries-view {
  font-family: 'Space Grotesk', system-ui, sans-serif;
  max-width: 1200px;
}

.page-title {
  font-size: 1.8rem;
  font-weight: 600;
  margin-bottom: 30px;
  color: #FFFFFF;
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

.countries-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.country-card {
  border: 1px solid #333;
  padding: 20px;
  background: #000;
  cursor: pointer;
  transition: all 0.15s;
  display: flex;
  align-items: flex-start;
  gap: 14px;
}

.country-card:hover {
  border-color: #FF4500;
  background: #0a0a0a;
}

.country-flag {
  font-size: 2rem;
  line-height: 1;
}

.country-info {
  flex: 1;
  min-width: 0;
}

.country-name {
  font-size: 1rem;
  font-weight: 600;
  color: #FFFFFF;
  margin: 0 0 6px;
}

.country-meta {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.meta-item {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #999;
  letter-spacing: 0.3px;
}

.meta-lang {
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

@media (max-width: 1024px) {
  .countries-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 640px) {
  .countries-grid { grid-template-columns: 1fr; }
}
</style>
