<template>
  <div class="layer-sidebar" :class="{ collapsed: !expanded }">
    <div class="sidebar-header" @click="expanded = !expanded">
      <span class="sidebar-toggle">{{ expanded ? '\u25BC' : '\u25B6' }}</span>
      <span class="sidebar-title">LAYERS</span>
    </div>

    <template v-if="expanded">
      <div class="sidebar-search">
        <input
          type="text"
          v-model="searchQuery"
          placeholder="Search layers..."
          class="search-input"
        />
      </div>

      <div class="layer-list">
        <label
          v-for="layer in filteredLayers"
          :key="layer.id"
          class="layer-item"
        >
          <input
            type="checkbox"
            :checked="layer.enabled"
            :style="{ accentColor: layer.color }"
            @change="toggleLayer(layer)"
          />
          <span class="layer-icon">{{ layer.icon }}</span>
          <span class="layer-label">{{ layer.label }}</span>
        </label>
      </div>

      <div class="sidebar-footer">
        &copy; OracleFlow
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'

const LAYERS = [
  { id: 'conflicts', icon: '\u2715', label: 'CONFLICT ZONES', enabled: true, color: '#ff4444' },
  { id: 'bases', icon: '\uD83C\uDFF0', label: 'MILITARY BASES', enabled: true, color: '#ff8800' },
  { id: 'nuclear', icon: '\u2622', label: 'NUCLEAR SITES', enabled: false, color: '#ffaa00' },
  { id: 'earthquakes', icon: '\uD83C\uDF0B', label: 'EARTHQUAKES', enabled: true, color: '#ff6600' },
  { id: 'fires', icon: '\uD83D\uDD25', label: 'WILDFIRES', enabled: false, color: '#ff4400' },
  { id: 'cables', icon: '\uD83D\uDD0C', label: 'UNDERSEA CABLES', enabled: false, color: '#3388ff' },
  { id: 'pipelines', icon: '\uD83D\uDD34', label: 'PIPELINES', enabled: false, color: '#ff8800' },
  { id: 'radiation', icon: '\u2622', label: 'RADIATION WATCH', enabled: false, color: '#ffaa00' },
  { id: 'spaceports', icon: '\uD83D\uDE80', label: 'SPACEPORTS', enabled: false, color: '#aa88ff' },
  { id: 'outages', icon: '\u26A1', label: 'INTERNET OUTAGES', enabled: false, color: '#ff4444' },
  { id: 'cyber', icon: '\uD83D\uDEE1', label: 'CYBER THREATS', enabled: false, color: '#ff4444' },
  { id: 'hotspots', icon: '\uD83C\uDFAF', label: 'INTEL HOTSPOTS', enabled: false, color: '#ff8800' },
]

const emit = defineEmits(['layerToggle'])

const expanded = ref(true)
const searchQuery = ref('')
const layers = reactive(LAYERS.map(l => ({ ...l })))

const filteredLayers = computed(() => {
  const q = searchQuery.value.toLowerCase().trim()
  if (!q) return layers
  return layers.filter(l => l.label.toLowerCase().includes(q))
})

function toggleLayer(layer) {
  layer.enabled = !layer.enabled
  emit('layerToggle', layer.id, layer.enabled)
}

function getActiveLayers() {
  return new Set(layers.filter(l => l.enabled).map(l => l.id))
}

defineExpose({ getActiveLayers, layers })
</script>

<style scoped>
.layer-sidebar {
  position: absolute;
  left: 10px;
  top: 10px;
  z-index: 10;
  width: 220px;
  background: rgba(10, 10, 10, 0.92);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid var(--wm-border, #2a2a2a);
  border-radius: 4px;
  display: flex;
  flex-direction: column;
  font-family: 'SF Mono', monospace;
  font-size: 12px;
  color: var(--wm-text, #e8e8e8);
  user-select: none;
}

.layer-sidebar.collapsed {
  width: auto;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  cursor: pointer;
  border-bottom: 1px solid var(--wm-border, #2a2a2a);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  color: var(--wm-text-dim, #888);
}

.sidebar-header:hover {
  color: var(--wm-text, #e8e8e8);
}

.sidebar-toggle {
  font-size: 9px;
}

.sidebar-search {
  padding: 6px 8px;
  border-bottom: 1px solid var(--wm-border, #2a2a2a);
}

.search-input {
  width: 100%;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--wm-border, #2a2a2a);
  border-radius: 3px;
  padding: 5px 8px;
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--wm-text, #e8e8e8);
  outline: none;
  box-sizing: border-box;
}

.search-input::placeholder {
  color: var(--wm-text-dim, #888);
}

.search-input:focus {
  border-color: #444;
}

.layer-list {
  max-height: 50vh;
  overflow-y: auto;
  padding: 4px 0;
}

.layer-list::-webkit-scrollbar {
  width: 4px;
}

.layer-list::-webkit-scrollbar-track {
  background: transparent;
}

.layer-list::-webkit-scrollbar-thumb {
  background: #333;
  border-radius: 2px;
}

.layer-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  cursor: pointer;
  transition: background 0.15s;
}

.layer-item:hover {
  background: rgba(255, 255, 255, 0.04);
}

.layer-item input[type="checkbox"] {
  width: 13px;
  height: 13px;
  margin: 0;
  cursor: pointer;
  flex-shrink: 0;
}

.layer-icon {
  font-size: 12px;
  flex-shrink: 0;
  width: 16px;
  text-align: center;
}

.layer-label {
  font-size: 11px;
  font-family: 'SF Mono', monospace;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--wm-text, #e8e8e8);
}

.sidebar-footer {
  padding: 8px 10px;
  border-top: 1px solid var(--wm-border, #2a2a2a);
  font-size: 10px;
  color: var(--wm-text-dim, #888);
  text-align: center;
  letter-spacing: 0.05em;
}
</style>
