<template>
  <div class="panels-grid" @dragover.prevent @drop="onDrop">
    <component v-for="panel in orderedPanels" :key="panel.panelId"
      :is="panel.component" v-bind="panel.props"
      @close="removePanel(panel.panelId)"
      @reorder="handleReorder" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { updateUserPreferences } from '../api/intelligence'

const props = defineProps({
  panels: {
    type: Array,
    default: () => []
    // Each item: { component, props, panelId, defaultRowSpan, defaultColSpan }
  },
  savedPanelOrder: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:panels'])

const ORDER_KEY = 'oracleflow-panel-order'

const panelOrder = ref([])
const removedPanels = ref(new Set())

// Debounce timer for server persistence
let persistTimer = null

// --- Computed ---

const orderedPanels = computed(() => {
  const activePanels = props.panels.filter(p => !removedPanels.value.has(p.panelId))
  if (!panelOrder.value.length) return activePanels

  const panelMap = new Map(activePanels.map(p => [p.panelId, p]))
  const ordered = []

  // First add panels in saved order
  for (const id of panelOrder.value) {
    if (panelMap.has(id)) {
      ordered.push(panelMap.get(id))
      panelMap.delete(id)
    }
  }
  // Then append any new panels not in saved order
  for (const panel of panelMap.values()) {
    ordered.push(panel)
  }

  return ordered
})

// --- Persistence ---

function loadOrder() {
  // Priority: props from server > localStorage fallback
  if (props.savedPanelOrder && props.savedPanelOrder.length > 0) {
    panelOrder.value = [...props.savedPanelOrder]
    return
  }
  try {
    const saved = JSON.parse(localStorage.getItem(ORDER_KEY) || '[]')
    if (Array.isArray(saved) && saved.length) {
      panelOrder.value = saved
    }
  } catch {
    // ignore
  }
}

function saveOrder() {
  const ids = orderedPanels.value.map(p => p.panelId)

  // Always write to localStorage as cache
  try {
    localStorage.setItem(ORDER_KEY, JSON.stringify(ids))
  } catch {
    // ignore
  }

  // Debounce server persistence by 1 second
  if (persistTimer) clearTimeout(persistTimer)
  persistTimer = setTimeout(() => {
    persistToServer(ids)
  }, 1000)
}

async function persistToServer(ids) {
  try {
    await updateUserPreferences({
      dashboard_config: { panel_order: ids }
    })
  } catch {
    // Server save failed; localStorage cache still holds the order
  }
}

// --- Drag and drop ---

let draggedPanelId = null

function onDrop(e) {
  const panelId = e.dataTransfer.getData('text/plain')
  if (!panelId) return

  // Find the drop target panel
  const dropTarget = e.target.closest('.panel')
  if (!dropTarget) return

  const currentOrder = orderedPanels.value.map(p => p.panelId)
  const fromIndex = currentOrder.indexOf(panelId)
  if (fromIndex === -1) return

  // Find the target panel's id by matching the component
  const targetIndex = Array.from(
    e.currentTarget.children
  ).indexOf(dropTarget)

  if (targetIndex === -1 || targetIndex === fromIndex) return

  // Reorder
  const newOrder = [...currentOrder]
  newOrder.splice(fromIndex, 1)
  newOrder.splice(targetIndex, 0, panelId)
  panelOrder.value = newOrder
  saveOrder()
}

function handleReorder(panelId) {
  // Triggered on dragend; order already updated via onDrop
  draggedPanelId = panelId
}

// --- Panel removal ---

function removePanel(panelId) {
  removedPanels.value = new Set([...removedPanels.value, panelId])
  const newOrder = panelOrder.value.filter(id => id !== panelId)
  panelOrder.value = newOrder
  saveOrder()
}

// --- Lifecycle ---

onMounted(() => {
  loadOrder()
})

onUnmounted(() => {
  if (persistTimer) clearTimeout(persistTimer)
})

// Keep order in sync when panels prop changes
watch(() => props.panels, () => {
  if (!panelOrder.value.length) {
    panelOrder.value = props.panels.map(p => p.panelId)
  }
}, { immediate: true })

// Re-load if savedPanelOrder prop changes (e.g. after API fetch)
watch(() => props.savedPanelOrder, (newOrder) => {
  if (newOrder && newOrder.length > 0 && panelOrder.value.length === 0) {
    panelOrder.value = [...newOrder]
  }
})
</script>

<style scoped>
/* ============================================================
   Panels Grid — WM exact: .panels-grid from main.css
   ============================================================ */
.panels-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  grid-auto-flow: row dense;
  grid-auto-rows: minmax(200px, 380px);
  gap: 4px;
  padding: 4px;
  align-content: start;
  align-items: stretch;
  min-height: 0;
  position: relative;
  z-index: 1;
}
</style>
