<template>
  <div class="map-search-overlay" v-if="visible" @keydown.esc="close">
    <div class="map-search-box">
      <div class="search-input-row">
        <span class="search-icon">&#128269;</span>
        <input
          ref="searchInput"
          v-model="query"
          type="text"
          class="search-input"
          placeholder="Search countries, cities..."
          @keydown.esc="close"
          @keydown.enter="selectFirst"
          @keydown.down.prevent="moveSelection(1)"
          @keydown.up.prevent="moveSelection(-1)"
          autocomplete="off"
        />
        <button class="search-close" @click="close">&times;</button>
      </div>
      <ul class="search-results" v-if="filtered.length > 0">
        <li
          v-for="(item, idx) in filtered"
          :key="item.code"
          class="search-result-item"
          :class="{ highlighted: idx === highlightIdx }"
          @click="selectCountry(item)"
          @mouseenter="highlightIdx = idx"
        >
          <span class="result-name">{{ item.name }}</span>
          <span class="result-code">{{ item.code }}</span>
        </li>
      </ul>
      <div class="search-empty" v-else-if="query.length > 0">
        No results
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false }
})

const emit = defineEmits(['close', 'countrySelected'])

const query = ref('')
const highlightIdx = ref(0)
const searchInput = ref(null)

const COUNTRIES = [
  { name: 'United States', code: 'US', coords: [-98, 39] },
  { name: 'United Kingdom', code: 'GB', coords: [-2, 54] },
  { name: 'Jamaica', code: 'JM', coords: [-77, 18] },
  { name: 'Trinidad and Tobago', code: 'TT', coords: [-61, 10] },
  { name: 'Barbados', code: 'BB', coords: [-59, 13] },
  { name: 'Ukraine', code: 'UA', coords: [32, 49] },
  { name: 'Russia', code: 'RU', coords: [100, 60] },
  { name: 'China', code: 'CN', coords: [105, 35] },
  { name: 'Iran', code: 'IR', coords: [53, 32] },
  { name: 'Israel', code: 'IL', coords: [35, 31] },
  { name: 'India', code: 'IN', coords: [79, 22] },
  { name: 'Japan', code: 'JP', coords: [138, 36] },
  { name: 'Germany', code: 'DE', coords: [10, 51] },
  { name: 'France', code: 'FR', coords: [2, 47] },
  { name: 'Brazil', code: 'BR', coords: [-52, -10] },
  { name: 'Australia', code: 'AU', coords: [134, -25] },
  { name: 'South Africa', code: 'ZA', coords: [25, -29] },
  { name: 'Nigeria', code: 'NG', coords: [8, 10] },
  { name: 'Egypt', code: 'EG', coords: [30, 27] },
  { name: 'Saudi Arabia', code: 'SA', coords: [45, 24] },
  { name: 'South Korea', code: 'KR', coords: [128, 36] },
  { name: 'Mexico', code: 'MX', coords: [-102, 23] },
  { name: 'Argentina', code: 'AR', coords: [-64, -34] },
  { name: 'Colombia', code: 'CO', coords: [-74, 4] },
  { name: 'Canada', code: 'CA', coords: [-106, 56] },
  { name: 'Italy', code: 'IT', coords: [12, 42] },
  { name: 'Spain', code: 'ES', coords: [-4, 40] },
  { name: 'Turkey', code: 'TR', coords: [35, 39] },
  { name: 'Indonesia', code: 'ID', coords: [120, -2] },
  { name: 'Pakistan', code: 'PK', coords: [70, 30] },
  { name: 'Bangladesh', code: 'BD', coords: [90, 24] },
  { name: 'Poland', code: 'PL', coords: [20, 52] },
  { name: 'Netherlands', code: 'NL', coords: [5, 52] },
  { name: 'Sweden', code: 'SE', coords: [16, 62] },
  { name: 'Norway', code: 'NO', coords: [10, 62] },
  { name: 'Finland', code: 'FI', coords: [26, 64] },
  { name: 'Taiwan', code: 'TW', coords: [121, 24] },
  { name: 'Philippines', code: 'PH', coords: [122, 12] },
  { name: 'Thailand', code: 'TH', coords: [101, 15] },
  { name: 'Vietnam', code: 'VN', coords: [106, 16] },
  { name: 'North Korea', code: 'KP', coords: [127, 40] },
  { name: 'Syria', code: 'SY', coords: [38, 35] },
  { name: 'Iraq', code: 'IQ', coords: [44, 33] },
  { name: 'Afghanistan', code: 'AF', coords: [66, 34] },
  { name: 'Yemen', code: 'YE', coords: [48, 16] },
  { name: 'Ethiopia', code: 'ET', coords: [40, 9] },
  { name: 'Kenya', code: 'KE', coords: [38, 0] },
  { name: 'Morocco', code: 'MA', coords: [-6, 32] },
  { name: 'Algeria', code: 'DZ', coords: [3, 28] },
  { name: 'Libya', code: 'LY', coords: [17, 27] },
  { name: 'Sudan', code: 'SD', coords: [30, 15] },
  { name: 'Venezuela', code: 'VE', coords: [-66, 7] },
  { name: 'Chile', code: 'CL', coords: [-71, -35] },
  { name: 'Peru', code: 'PE', coords: [-76, -10] },
  { name: 'Cuba', code: 'CU', coords: [-80, 22] },
  { name: 'Greece', code: 'GR', coords: [22, 39] },
  { name: 'Portugal', code: 'PT', coords: [-8, 39] },
  { name: 'Belgium', code: 'BE', coords: [4, 51] },
  { name: 'Switzerland', code: 'CH', coords: [8, 47] },
  { name: 'Austria', code: 'AT', coords: [14, 47] },
  { name: 'Romania', code: 'RO', coords: [25, 46] },
  { name: 'Hungary', code: 'HU', coords: [20, 47] },
  { name: 'Czech Republic', code: 'CZ', coords: [15, 50] },
  { name: 'New Zealand', code: 'NZ', coords: [174, -41] },
  { name: 'Singapore', code: 'SG', coords: [104, 1] },
  { name: 'Malaysia', code: 'MY', coords: [102, 4] },
  { name: 'United Arab Emirates', code: 'AE', coords: [54, 24] },
  { name: 'Qatar', code: 'QA', coords: [51, 25] },
  { name: 'Somalia', code: 'SO', coords: [46, 6] },
  { name: 'Myanmar', code: 'MM', coords: [96, 20] },
  { name: 'Jordan', code: 'JO', coords: [36, 31] },
  { name: 'Lebanon', code: 'LB', coords: [36, 34] },
  { name: 'Palestine', code: 'PS', coords: [35, 32] },
]

const filtered = computed(() => {
  if (!query.value) return []
  const q = query.value.toLowerCase()
  return COUNTRIES.filter(c =>
    c.name.toLowerCase().includes(q) || c.code.toLowerCase().includes(q)
  ).slice(0, 10)
})

watch(() => filtered.value, () => {
  highlightIdx.value = 0
})

watch(() => props.visible, (v) => {
  if (v) {
    query.value = ''
    highlightIdx.value = 0
    nextTick(() => {
      searchInput.value?.focus()
    })
  }
})

function moveSelection(dir) {
  const len = filtered.value.length
  if (len === 0) return
  highlightIdx.value = (highlightIdx.value + dir + len) % len
}

function selectFirst() {
  if (filtered.value.length > 0) {
    selectCountry(filtered.value[highlightIdx.value])
  }
}

function selectCountry(item) {
  emit('countrySelected', { code: item.code, coords: item.coords, name: item.name })
  close()
}

function close() {
  emit('close')
}
</script>

<style scoped>
.map-search-overlay {
  position: absolute;
  top: 12px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 100;
  width: 360px;
  max-width: 90%;
}

.map-search-box {
  background: rgba(14, 14, 14, 0.96);
  border: 1px solid #2a2a2a;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(8px);
}

.search-input-row {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  gap: 8px;
  border-bottom: 1px solid #222;
}

.search-icon {
  font-size: 14px;
  opacity: 0.5;
  flex-shrink: 0;
}

.search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: #e8e8e8;
  font-family: 'SF Mono', monospace;
  font-size: 13px;
  letter-spacing: 0.02em;
}

.search-input::placeholder {
  color: #555;
}

.search-close {
  background: transparent;
  border: none;
  color: #666;
  font-size: 18px;
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
  transition: color 0.15s;
}

.search-close:hover {
  color: #e8e8e8;
}

.search-results {
  list-style: none;
  margin: 0;
  padding: 4px 0;
  max-height: 260px;
  overflow-y: auto;
}

.search-result-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 14px;
  cursor: pointer;
  transition: background 0.1s;
}

.search-result-item:hover,
.search-result-item.highlighted {
  background: rgba(255, 255, 255, 0.06);
}

.result-name {
  color: #e8e8e8;
  font-family: 'SF Mono', monospace;
  font-size: 12px;
}

.result-code {
  color: #666;
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  letter-spacing: 0.5px;
}

.search-empty {
  padding: 12px 14px;
  color: #555;
  font-family: 'SF Mono', monospace;
  font-size: 12px;
  text-align: center;
}

/* Scrollbar */
.search-results::-webkit-scrollbar {
  width: 4px;
}

.search-results::-webkit-scrollbar-thumb {
  background: #333;
  border-radius: 2px;
}

.search-results::-webkit-scrollbar-track {
  background: transparent;
}
</style>
