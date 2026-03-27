<template>
  <div class="panel" :class="panelClasses" :style="panelStyle"
       draggable="true" @dragstart="onDragStart" @dragend="onDragEnd">

    <!-- Header — WM exact: .panel-header -->
    <div class="panel-header">
      <div class="panel-header-left">
        <span class="panel-title">{{ title }}</span>
        <span v-if="infoTooltip" class="icon-btn" @click="showInfo = !showInfo">?</span>
        <span v-if="hasNew" class="panel-new-badge">NEW</span>
      </div>
      <span v-if="dataBadge" class="panel-data-badge">{{ dataBadge }}</span>
      <span v-if="showCount" class="panel-count">{{ count }}</span>
      <button v-if="closable" class="icon-btn panel-close-btn" @click="$emit('close')">&#215;</button>
    </div>

    <!-- Info tooltip (shown on ? click) -->
    <div v-if="showInfo && infoTooltip" class="panel-info-tooltip">{{ infoTooltip }}</div>

    <!-- Tabs slot -->
    <slot name="tabs" />

    <!-- Content — WM exact: .panel-content -->
    <div class="panel-content">
      <slot />
    </div>

    <!-- Resize handles — WM exact -->
    <div class="panel-resize-handle" @mousedown="startRowResize"></div>
    <div class="panel-col-resize-handle" @mousedown="startColResize"></div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  panelId: { type: String, required: true },
  title: { type: String, required: true },
  showCount: { type: Boolean, default: false },
  count: { type: Number, default: 0 },
  infoTooltip: { type: String, default: '' },
  closable: { type: Boolean, default: true },
  defaultRowSpan: { type: Number, default: 1 },
  defaultColSpan: { type: Number, default: 1 },
  trackActivity: { type: Boolean, default: false },
  dataBadge: { type: String, default: '' }
})

const emit = defineEmits(['close', 'reorder'])

const showInfo = ref(false)
const hasNew = ref(false)
const rowSpan = ref(props.defaultRowSpan)
const colSpan = ref(props.defaultColSpan)

let newBadgeTimer = null

// --- Computed ---

const panelClasses = computed(() => {
  const classes = []
  if (rowSpan.value >= 1) classes.push(`span-${rowSpan.value}`)
  if (colSpan.value >= 2) classes.push(`col-span-${colSpan.value}`)
  return classes
})

const panelStyle = computed(() => {
  if (rowSpan.value === 1 && colSpan.value === 1) return {}
  const style = {}
  if (rowSpan.value > 1) {
    style.gridRow = `span ${rowSpan.value}`
  }
  if (colSpan.value >= 2) {
    style.gridColumn = `span ${colSpan.value}`
  }
  return style
})

// --- localStorage persistence ---

const ROW_SPAN_KEY = 'oracleflow-panel-spans'
const COL_SPAN_KEY = 'oracleflow-panel-col-spans'

function loadSpans() {
  try {
    const rowSpans = JSON.parse(localStorage.getItem(ROW_SPAN_KEY) || '{}')
    const colSpans = JSON.parse(localStorage.getItem(COL_SPAN_KEY) || '{}')
    if (rowSpans[props.panelId]) rowSpan.value = rowSpans[props.panelId]
    if (colSpans[props.panelId]) colSpan.value = colSpans[props.panelId]
  } catch {
    // ignore parse errors
  }
}

function saveRowSpan() {
  try {
    const spans = JSON.parse(localStorage.getItem(ROW_SPAN_KEY) || '{}')
    spans[props.panelId] = rowSpan.value
    localStorage.setItem(ROW_SPAN_KEY, JSON.stringify(spans))
  } catch {
    // ignore
  }
}

function saveColSpan() {
  try {
    const spans = JSON.parse(localStorage.getItem(COL_SPAN_KEY) || '{}')
    spans[props.panelId] = colSpan.value
    localStorage.setItem(COL_SPAN_KEY, JSON.stringify(spans))
  } catch {
    // ignore
  }
}

// --- Resize: row (bottom edge) ---

function startRowResize(e) {
  e.preventDefault()
  const startY = e.clientY
  const startSpan = rowSpan.value

  function onMouseMove(ev) {
    const delta = ev.clientY - startY
    const spanDelta = Math.round(delta / 80)
    const newSpan = Math.max(1, Math.min(4, startSpan + spanDelta))
    if (newSpan !== rowSpan.value) {
      rowSpan.value = newSpan
    }
  }

  function onMouseUp() {
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
    saveRowSpan()
  }

  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}

// --- Resize: col (right edge) ---

function startColResize(e) {
  e.preventDefault()
  const startX = e.clientX
  const startSpan = colSpan.value

  function onMouseMove(ev) {
    const delta = ev.clientX - startX
    const spanDelta = Math.round(delta / 200)
    const newSpan = Math.max(1, Math.min(3, startSpan + spanDelta))
    if (newSpan !== colSpan.value) {
      colSpan.value = newSpan
    }
  }

  function onMouseUp() {
    document.removeEventListener('mousemove', onMouseMove)
    document.removeEventListener('mouseup', onMouseUp)
    saveColSpan()
  }

  document.addEventListener('mousemove', onMouseMove)
  document.addEventListener('mouseup', onMouseUp)
}

// --- Drag and drop ---

function onDragStart(e) {
  e.dataTransfer.setData('text/plain', props.panelId)
  e.dataTransfer.effectAllowed = 'move'
}

function onDragEnd() {
  emit('reorder', props.panelId)
}

// --- NEW badge ---

function markNew() {
  hasNew.value = true
  if (newBadgeTimer) clearTimeout(newBadgeTimer)
  newBadgeTimer = setTimeout(() => {
    hasNew.value = false
    newBadgeTimer = null
  }, 3000)
}

// --- Lifecycle ---

onMounted(() => {
  loadSpans()
})

onBeforeUnmount(() => {
  if (newBadgeTimer) clearTimeout(newBadgeTimer)
})

defineExpose({ markNew })
</script>

<style scoped>
/* ============================================================
   Panel — WM exact: .panel from main.css
   ============================================================ */
.panel {
  background: var(--surface);
  border: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  height: 100%;
  min-height: 200px;
  min-width: 0;
  cursor: grab;
  transition: transform 0.15s, box-shadow 0.15s;
  position: relative;
  contain: content;
}

.panel:active {
  cursor: grabbing;
}

/* Row span classes — WM exact */
.panel.span-1 {
  grid-row: span 1 !important;
  min-height: 200px !important;
}

.panel.span-2 {
  grid-row: span 2 !important;
  min-height: 400px !important;
}

.panel.span-3 {
  grid-row: span 3 !important;
  min-height: 600px !important;
}

.panel.span-4 {
  grid-row: span 4 !important;
  min-height: 800px !important;
}

/* Col span classes — WM exact */
.panel.col-span-1 {
  grid-column: span 1 !important;
}

.panel.col-span-2 {
  grid-column: span 2 !important;
}

.panel.col-span-3 {
  grid-column: span 3 !important;
}

/* ============================================================
   Panel Header — WM exact: .panel-header from main.css
   ============================================================ */
.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 6px 10px;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
  position: relative;
  transition: background-color 0.3s ease, border-color 0.3s ease;
}

.panel-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Push the first element after header-left to the right — WM exact */
.panel-header > .panel-header-left + * {
  margin-left: auto;
}

.panel-title {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ============================================================
   Icon buttons in panel headers — WM exact
   ============================================================ */
.panel-header .icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 4px;
  border: none;
  background: transparent;
  color: var(--text-dim);
  font-size: 12px;
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
  flex-shrink: 0;
}

.panel-header .icon-btn:hover {
  background: var(--overlay-subtle);
  color: var(--text);
}

/* Close button — WM exact */
.panel-header .panel-close-btn {
  font-size: 14px;
  opacity: 0;
  transition: opacity 0.15s ease, background 0.15s ease, color 0.15s ease;
  order: 999;
}

.panel:hover .panel-close-btn {
  opacity: 1;
}

.panel-header .panel-close-btn:hover {
  background: color-mix(in srgb, var(--semantic-critical) 15%, transparent);
  color: var(--semantic-critical);
}

@media (hover: none) {
  .panel-header .panel-close-btn {
    opacity: 0.7;
  }
}

/* NEW badge */
.panel-new-badge {
  background: var(--green, #44ff88);
  color: #000;
  font-size: 9px;
  font-weight: 700;
  padding: 1px 5px;
  letter-spacing: 0.5px;
  animation: newBadgeFade 3s ease-out forwards;
  flex-shrink: 0;
}

@keyframes newBadgeFade {
  0% { opacity: 1; }
  70% { opacity: 1; }
  100% { opacity: 0; }
}

/* Data badge */
.panel-data-badge {
  font-size: 10px;
  color: var(--text-muted);
  letter-spacing: 0.5px;
  white-space: nowrap;
}

/* Count */
.panel-count {
  font-size: 10px;
  color: var(--text-dim);
  font-weight: 600;
}

/* Info tooltip */
.panel-info-tooltip {
  padding: 8px 12px;
  font-size: 11px;
  color: var(--text-dim);
  background: var(--surface-hover);
  border-bottom: 1px solid var(--border);
  line-height: 1.4;
}

/* ============================================================
   Panel Content — WM exact: .panel-content from main.css
   ============================================================ */
.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  min-width: 0;
  user-select: none;
  scrollbar-width: thin;
  scrollbar-color: var(--scrollbar-thumb) transparent;
  will-change: scroll-position;
  contain: layout style;
}

.panel-content::-webkit-scrollbar {
  width: 4px;
}

.panel-content::-webkit-scrollbar-track {
  background: transparent;
}

.panel-content::-webkit-scrollbar-thumb {
  background: var(--border);
  border-radius: 2px;
}

/* ============================================================
   Panel Resize Handles — WM exact from main.css
   ============================================================ */
.panel-resize-handle {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 20px;
  cursor: ns-resize;
  background: linear-gradient(to top, rgba(68, 136, 255, 0.15), transparent);
  z-index: 100;
  transition: background 0.2s;
  touch-action: none;
  pointer-events: auto !important;
  user-select: none;
}

.panel-resize-handle:hover,
.panel-resize-handle.active {
  background: linear-gradient(to top, rgba(68, 136, 255, 0.5), transparent);
}

.panel-resize-handle::after {
  content: '⋯';
  position: absolute;
  bottom: 2px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 16px;
  letter-spacing: 2px;
  color: var(--text-dim);
  transition: color 0.2s;
}

.panel-resize-handle:hover::after {
  color: var(--accent);
}

/* Right-edge handle — WM exact */
.panel-col-resize-handle {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  width: 20px;
  cursor: ew-resize;
  background: linear-gradient(to left, rgba(68, 136, 255, 0.15), transparent);
  z-index: 100;
  transition: background 0.2s;
  touch-action: none;
  pointer-events: auto !important;
  user-select: none;
}

.panel-col-resize-handle:hover,
.panel-col-resize-handle.active {
  background: linear-gradient(to left, rgba(68, 136, 255, 0.5), transparent);
}

.panel-col-resize-handle::after {
  content: '⋮';
  position: absolute;
  right: 3px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 16px;
  letter-spacing: 2px;
  color: var(--text-dim);
  transition: color 0.2s;
}

.panel-col-resize-handle:hover::after {
  color: var(--accent);
}

@media (max-width: 768px) {
  .panel-col-resize-handle {
    display: none;
  }
}
</style>
