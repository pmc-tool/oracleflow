<template>
  <div class="world-map-wrapper">
    <div class="world-map-container" ref="mapContainer"></div>

    <!-- Globe BETA badge -->
    <span v-if="projection === '3d' || projection === '3D'" class="globe-beta-badge">BETA</span>

    <!-- Layer legend at bottom -->
    <div class="map-legend">
      <div class="legend-item" v-for="item in legendItems" :key="item.label">
        <span
          v-if="item.shape === 'triangle'"
          class="legend-shape legend-triangle"
          :style="{ borderBottomColor: item.color }"
        ></span>
        <span
          v-else-if="item.shape === 'diamond'"
          class="legend-shape legend-diamond"
          :style="{ background: item.color }"
        ></span>
        <span
          v-else-if="item.shape === 'square'"
          class="legend-shape legend-square"
          :style="{ background: item.color }"
        ></span>
        <span
          v-else-if="item.shape === 'line'"
          class="legend-shape legend-line"
          :style="{ background: item.color }"
        ></span>
        <span
          v-else
          class="legend-dot"
          :style="{ background: item.color }"
        ></span>
        <span class="legend-label">{{ item.label }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'

import militaryBasesData from '../data/military-bases.json'
import nuclearSitesData from '../data/nuclear-sites.json'
import underseaCablesData from '../data/undersea-cables.json'

const props = defineProps({
  riskData: { type: Object, default: () => ({}) },
  selectedCountry: { type: String, default: '' },
  activeLayers: { type: Set, default: () => new Set(['conflicts', 'bases', 'earthquakes']) },
  signals: { type: Array, default: () => [] },
  projection: { type: String, default: '2d' }
})

const emit = defineEmits(['countrySelected'])

// Expose flyTo so MapSearch can drive the map
function flyTo(center, zoom = 4) {
  if (map) {
    map.flyTo({ center, zoom, speed: 1.2 })
  }
}
defineExpose({ flyTo })

const mapContainer = ref(null)
let map = null
let popup = null
let hoveredCountryId = null
let selectedFeatureId = null
let mapLoaded = false

// Static risk-level legend items
const BASE_LEGEND = [
  { label: 'Low', color: '#1a3a1a' },
  { label: 'Normal', color: '#44aa44' },
  { label: 'Elevated', color: '#ffaa00' },
  { label: 'High', color: '#ff8800' },
  { label: 'Critical', color: '#ff4444' }
]

// WorldMonitor legend: distinct colors + shapes per layer
const LAYER_LEGEND = {
  conflicts: { label: 'High Alert', color: '#ff4444', shape: 'circle' },
  bases: { label: 'Base', color: '#1a5276', shape: 'triangle' },
  nuclear: { label: 'Nuclear', color: '#ff8800', shape: 'circle' },
  earthquakes: { label: 'Elevated', color: '#ffaa00', shape: 'circle' },
  cables: { label: 'Cables', color: '#3388ff', shape: 'line' },
  fires: { label: 'Monitoring', color: '#ff6600', shape: 'circle' },
  pipelines: { label: 'Pipelines', color: '#cc6600', shape: 'line' },
  radiation: { label: 'Radiation', color: '#44ff88', shape: 'circle' },
  spaceports: { label: 'Spaceports', color: '#aa88ff', shape: 'diamond' },
  outages: { label: 'Datacenter', color: '#8844cc', shape: 'square' },
  cyber: { label: 'Cyber', color: '#ff44aa', shape: 'circle' },
  hotspots: { label: 'Aircraft', color: '#44ff88', shape: 'circle' }
}

const legendItems = computed(() => {
  const active = []
  for (const [id, meta] of Object.entries(LAYER_LEGEND)) {
    if (props.activeLayers.has(id)) {
      active.push(meta)
    }
  }
  return [...BASE_LEGEND, ...active]
})

// ---- Color helpers ----

function riskColor(score) {
  if (score == null) return 'rgba(255,255,255,0.03)'
  if (score <= 0) return '#1a3a1a'
  if (score < 30) return interpolateColor(score, 0, 30, '#1a3a1a', '#44aa44')
  if (score < 50) return interpolateColor(score, 30, 50, '#44aa44', '#ffaa00')
  if (score < 70) return interpolateColor(score, 50, 70, '#ffaa00', '#ff8800')
  if (score < 90) return interpolateColor(score, 70, 90, '#ff8800', '#ff4444')
  return '#ff4444'
}

function interpolateColor(value, minVal, maxVal, colorA, colorB) {
  const t = (value - minVal) / (maxVal - minVal)
  const a = hexToRgb(colorA)
  const b = hexToRgb(colorB)
  const r = Math.round(a.r + (b.r - a.r) * t)
  const g = Math.round(a.g + (b.g - a.g) * t)
  const bl = Math.round(a.b + (b.b - a.b) * t)
  return `rgb(${r},${g},${bl})`
}

function hexToRgb(hex) {
  const h = hex.replace('#', '')
  return {
    r: parseInt(h.substring(0, 2), 16),
    g: parseInt(h.substring(2, 4), 16),
    b: parseInt(h.substring(4, 6), 16)
  }
}

function statusTag(score) {
  if (score == null) return '<span style="color:#666;">NO DATA</span>'
  if (score > 80) return '<span style="color:#ff4444;font-weight:700;">CRISIS</span>'
  if (score > 60) return '<span style="color:#ff8800;font-weight:700;">HIGH</span>'
  if (score > 40) return '<span style="color:#ffaa00;font-weight:700;">ELEVATED</span>'
  return '<span style="color:#44aa44;font-weight:700;">STABLE</span>'
}

function buildFillColor(riskData) {
  const expr = ['match', ['get', 'ISO_A2']]
  for (const [code, score] of Object.entries(riskData)) {
    expr.push(code, riskColor(score))
  }
  expr.push('rgba(255,255,255,0.03)')
  return expr
}

function findFeatureByCode(code) {
  if (!map || !code) return null
  const features = map.querySourceFeatures('countries', { sourceLayer: '' })
  return features.find(f => f.properties.ISO_A2 === code) || null
}

function updateSelectedHighlight(code) {
  if (!map || !map.getLayer('countries-selected-border')) return
  if (selectedFeatureId !== null) {
    map.setFeatureState({ source: 'countries', id: selectedFeatureId }, { selected: false })
  }
  if (code) {
    const feat = findFeatureByCode(code)
    if (feat) {
      selectedFeatureId = feat.id
      map.setFeatureState({ source: 'countries', id: selectedFeatureId }, { selected: true })
    }
  } else {
    selectedFeatureId = null
  }
}

// ---- GeoJSON builders for data layers ----

function buildBasesGeoJSON() {
  return {
    type: 'FeatureCollection',
    features: militaryBasesData.map(b => ({
      type: 'Feature',
      properties: { name: b.name, country: b.country, type: b.type },
      geometry: { type: 'Point', coordinates: [b.lng, b.lat] }
    }))
  }
}

function buildNuclearGeoJSON() {
  return {
    type: 'FeatureCollection',
    features: nuclearSitesData.map(n => ({
      type: 'Feature',
      properties: { name: n.name, country: n.country, type: n.type },
      geometry: { type: 'Point', coordinates: [n.lng, n.lat] }
    }))
  }
}

function buildConflictGeoJSON(signals) {
  const geopolitical = signals.filter(s => s.category === 'geopolitical' && s.lat && s.lng)
  return {
    type: 'FeatureCollection',
    features: geopolitical.map(s => ({
      type: 'Feature',
      properties: { name: s.title || 'Conflict', severity: s.severity || 50 },
      geometry: { type: 'Point', coordinates: [s.lng, s.lat] }
    }))
  }
}

function buildEarthquakeGeoJSON(signals) {
  const quakes = signals.filter(s => s.source === 'usgs' && s.lat && s.lng)
  return {
    type: 'FeatureCollection',
    features: quakes.map(s => ({
      type: 'Feature',
      properties: { name: s.title || 'Earthquake', magnitude: s.magnitude || 4 },
      geometry: { type: 'Point', coordinates: [s.lng, s.lat] }
    }))
  }
}

// ---- GeoJSON builders for new layers ----

function buildFiresGeoJSON(signals) {
  const fires = signals.filter(s =>
    (s.source === 'nasa_firms' || s.category === 'climate') && s.lat && s.lng
  )
  return {
    type: 'FeatureCollection',
    features: fires.map(s => ({
      type: 'Feature',
      properties: {
        name: s.title || 'Wildfire',
        confidence: s.confidence || s.severity || 50
      },
      geometry: { type: 'Point', coordinates: [s.lng, s.lat] }
    }))
  }
}

const PIPELINES_GEOJSON = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: { name: 'Nord Stream', status: 'Damaged' },
      geometry: {
        type: 'LineString',
        coordinates: [[12.0, 54.5], [14.0, 54.8], [16.5, 55.2], [19.0, 55.5], [21.5, 56.0], [24.0, 57.0], [27.0, 59.5], [30.0, 60.0]]
      }
    },
    {
      type: 'Feature',
      properties: { name: 'Keystone XL', status: 'Cancelled' },
      geometry: {
        type: 'LineString',
        coordinates: [[-110.0, 50.5], [-109.0, 48.0], [-104.0, 44.0], [-100.0, 41.0], [-97.0, 38.5], [-96.0, 35.5], [-95.5, 30.0]]
      }
    },
    {
      type: 'Feature',
      properties: { name: 'Trans-Siberian Pipeline', status: 'Active' },
      geometry: {
        type: 'LineString',
        coordinates: [[73.0, 61.0], [80.0, 60.5], [90.0, 58.0], [100.0, 56.0], [110.0, 54.0], [120.0, 52.0], [130.0, 50.0], [135.0, 48.5]]
      }
    },
    {
      type: 'Feature',
      properties: { name: 'Druzhba Pipeline', status: 'Active' },
      geometry: {
        type: 'LineString',
        coordinates: [[52.0, 54.0], [45.0, 53.5], [40.0, 53.0], [35.0, 52.5], [30.0, 51.5], [25.0, 50.5], [20.0, 50.0], [15.0, 49.5]]
      }
    },
    {
      type: 'Feature',
      properties: { name: 'Trans-Adriatic Pipeline (TAP)', status: 'Active' },
      geometry: {
        type: 'LineString',
        coordinates: [[40.5, 40.0], [36.0, 39.5], [30.0, 39.8], [26.0, 40.5], [21.0, 40.8], [19.5, 41.0], [18.0, 40.5]]
      }
    },
    {
      type: 'Feature',
      properties: { name: 'TAPI Pipeline', status: 'Planned' },
      geometry: {
        type: 'LineString',
        coordinates: [[62.0, 38.0], [65.0, 36.5], [66.0, 34.0], [67.5, 31.0], [69.0, 28.0], [70.0, 25.5]]
      }
    }
  ]
}

function buildRadiationGeoJSON(signals) {
  const rads = signals.filter(s =>
    (s.category === 'radiation' || s.source === 'radiation') && s.lat && s.lng
  )
  return {
    type: 'FeatureCollection',
    features: rads.map(s => ({
      type: 'Feature',
      properties: {
        name: s.title || 'Radiation Alert',
        level: s.severity || s.value || 50
      },
      geometry: { type: 'Point', coordinates: [s.lng, s.lat] }
    }))
  }
}

const SPACEPORTS_DATA = [
  { name: 'Cape Canaveral', country: 'USA', lat: 28.3922, lng: -80.6077 },
  { name: 'Baikonur Cosmodrome', country: 'Kazakhstan', lat: 45.965, lng: 63.305 },
  { name: 'Guiana Space Centre (Kourou)', country: 'French Guiana', lat: 5.232, lng: -52.769 },
  { name: 'Vandenberg SFB', country: 'USA', lat: 34.7420, lng: -120.5724 },
  { name: 'Jiuquan Satellite Launch Center', country: 'China', lat: 40.9581, lng: 100.2913 },
  { name: 'Satish Dhawan (Sriharikota)', country: 'India', lat: 13.7199, lng: 80.2304 },
  { name: 'Wenchang Spacecraft Launch Site', country: 'China', lat: 19.6145, lng: 110.9510 },
  { name: 'Plesetsk Cosmodrome', country: 'Russia', lat: 62.9271, lng: 40.5777 }
]

function buildSpaceportsGeoJSON() {
  return {
    type: 'FeatureCollection',
    features: SPACEPORTS_DATA.map(s => ({
      type: 'Feature',
      properties: { name: s.name, country: s.country },
      geometry: { type: 'Point', coordinates: [s.lng, s.lat] }
    }))
  }
}

function buildOutagesGeoJSON(signals) {
  const outages = signals.filter(s =>
    s.category === 'cyber' &&
    s.signal_type && s.signal_type.toLowerCase().includes('outage') &&
    s.lat && s.lng
  )
  return {
    type: 'FeatureCollection',
    features: outages.map(s => ({
      type: 'Feature',
      properties: {
        name: s.title || 'Internet Outage',
        severity: s.severity || 50
      },
      geometry: { type: 'Point', coordinates: [s.lng, s.lat] }
    }))
  }
}

function buildCyberGeoJSON(signals) {
  const cyber = signals.filter(s => s.category === 'cyber' && s.lat && s.lng)
  return {
    type: 'FeatureCollection',
    features: cyber.map(s => ({
      type: 'Feature',
      properties: {
        name: s.title || 'Cyber Threat',
        severity: s.severity || 50
      },
      geometry: { type: 'Point', coordinates: [s.lng, s.lat] }
    }))
  }
}

function buildHotspotsGeoJSON(signals) {
  const hotspots = signals.filter(s =>
    s.anomaly_score != null && s.anomaly_score > 0.7 && s.lat && s.lng
  )
  return {
    type: 'FeatureCollection',
    features: hotspots.map(s => ({
      type: 'Feature',
      properties: {
        name: s.title || 'Intel Hotspot',
        score: s.anomaly_score
      },
      geometry: { type: 'Point', coordinates: [s.lng, s.lat] }
    }))
  }
}

// ---- Layer management ----

const LAYER_SOURCES = {
  conflicts: 'layer-conflicts',
  bases: 'layer-bases',
  nuclear: 'layer-nuclear',
  earthquakes: 'layer-earthquakes',
  cables: 'layer-cables',
  fires: 'layer-fires',
  pipelines: 'layer-pipelines',
  radiation: 'layer-radiation',
  spaceports: 'layer-spaceports',
  outages: 'layer-outages',
  cyber: 'layer-cyber',
  hotspots: 'layer-hotspots'
}

const LAYER_IDS = {
  'conflicts-glow': 'layer-conflicts-glow',
  conflicts: 'layer-conflicts-circles',
  'bases-label': 'layer-bases-label',
  bases: 'layer-bases-markers',
  nuclear: 'layer-nuclear-markers',
  'nuclear-glow': 'layer-nuclear-glow',
  'nuclear-glow-outer': 'layer-nuclear-glow-outer',
  'earthquakes-glow': 'layer-earthquakes-glow',
  earthquakes: 'layer-earthquakes-circles',
  cables: 'layer-cables-lines',
  fires: 'layer-fires-circles',
  'fires-glow': 'layer-fires-glow',
  pipelines: 'layer-pipelines-lines',
  radiation: 'layer-radiation-circles',
  'radiation-glow': 'layer-radiation-glow',
  'spaceports-label': 'layer-spaceports-label',
  spaceports: 'layer-spaceports-markers',
  outages: 'layer-outages-squares',
  'outages-label': 'layer-outages-label',
  cyber: 'layer-cyber-markers',
  'cyber-label': 'layer-cyber-label',
  hotspots: 'layer-hotspots-circles',
  'hotspots-glow': 'layer-hotspots-glow'
}

function removeLayerSafe(layerId) {
  if (map.getLayer(layerId)) map.removeLayer(layerId)
}

function removeSourceSafe(sourceId) {
  if (map.getSource(sourceId)) map.removeSource(sourceId)
}

// ---- Existing layer add functions ----

function addConflictsLayer() {
  const src = LAYER_SOURCES.conflicts
  const glowLyr = LAYER_IDS['conflicts-glow']
  const lyr = LAYER_IDS.conflicts
  removeLayerSafe(lyr)
  removeLayerSafe(glowLyr)
  removeSourceSafe(src)

  map.addSource(src, {
    type: 'geojson',
    data: buildConflictGeoJSON(props.signals)
  })

  map.addLayer({
    id: glowLyr,
    type: 'circle',
    source: src,
    paint: {
      'circle-radius': 20,
      'circle-color': '#ff4444',
      'circle-opacity': 0.25,
      'circle-stroke-width': 0
    }
  })

  map.addLayer({
    id: lyr,
    type: 'circle',
    source: src,
    paint: {
      'circle-radius': 6,
      'circle-color': '#ff4444',
      'circle-opacity': 0.9,
      'circle-stroke-width': 2,
      'circle-stroke-color': '#ff0000'
    }
  })
}

function addBasesLayer() {
  const src = LAYER_SOURCES.bases
  const lyr = LAYER_IDS.bases
  const labelLyr = LAYER_IDS['bases-label']
  removeLayerSafe(labelLyr)
  removeLayerSafe(lyr)
  removeSourceSafe(src)

  map.addSource(src, {
    type: 'geojson',
    data: buildBasesGeoJSON()
  })

  map.addLayer({
    id: lyr,
    type: 'circle',
    source: src,
    paint: {
      'circle-radius': 5,
      'circle-color': '#0d2d42',
      'circle-opacity': 0.7,
      'circle-stroke-width': 1,
      'circle-stroke-color': '#2980b9'
    }
  })

  map.addLayer({
    id: labelLyr,
    type: 'symbol',
    source: src,
    layout: {
      'text-field': '\u25B2',
      'text-size': 12,
      'text-allow-overlap': true,
      'text-ignore-placement': true,
      'text-anchor': 'center',
      'text-offset': [0, -0.05]
    },
    paint: {
      'text-color': '#2980b9',
      'text-halo-color': '#0a1a2a',
      'text-halo-width': 1
    }
  })
}

function addNuclearLayer() {
  const src = LAYER_SOURCES.nuclear
  const outerGlowLyr = LAYER_IDS['nuclear-glow-outer']
  const glowLyr = LAYER_IDS['nuclear-glow']
  const mainLyr = LAYER_IDS.nuclear
  removeLayerSafe(mainLyr)
  removeLayerSafe(glowLyr)
  removeLayerSafe(outerGlowLyr)
  removeSourceSafe(src)

  map.addSource(src, {
    type: 'geojson',
    data: buildNuclearGeoJSON()
  })

  map.addLayer({
    id: outerGlowLyr,
    type: 'circle',
    source: src,
    paint: {
      'circle-radius': 30,
      'circle-color': 'transparent',
      'circle-opacity': 1,
      'circle-stroke-width': 2,
      'circle-stroke-color': '#ff8800',
      'circle-stroke-opacity': 0.15
    }
  })

  map.addLayer({
    id: glowLyr,
    type: 'circle',
    source: src,
    paint: {
      'circle-radius': 18,
      'circle-color': '#ff8800',
      'circle-opacity': 0.12,
      'circle-stroke-width': 0
    }
  })

  map.addLayer({
    id: mainLyr,
    type: 'circle',
    source: src,
    paint: {
      'circle-radius': 7,
      'circle-color': '#ff8800',
      'circle-opacity': 0.95,
      'circle-stroke-width': 2,
      'circle-stroke-color': '#ffaa00'
    }
  })
}

function addEarthquakesLayer() {
  const src = LAYER_SOURCES.earthquakes
  const glowLyr = LAYER_IDS['earthquakes-glow']
  const lyr = LAYER_IDS.earthquakes
  removeLayerSafe(lyr)
  removeLayerSafe(glowLyr)
  removeSourceSafe(src)

  map.addSource(src, {
    type: 'geojson',
    data: buildEarthquakeGeoJSON(props.signals)
  })

  map.addLayer({
    id: glowLyr,
    type: 'circle',
    source: src,
    paint: {
      'circle-radius': [
        'interpolate', ['linear'], ['get', 'magnitude'],
        2, 12,
        5, 25,
        7, 40,
        9, 60
      ],
      'circle-color': '#ffaa00',
      'circle-opacity': 0.15,
      'circle-stroke-width': 0
    }
  })

  map.addLayer({
    id: lyr,
    type: 'circle',
    source: src,
    paint: {
      'circle-radius': [
        'interpolate', ['linear'], ['get', 'magnitude'],
        2, 4,
        5, 7,
        7, 10,
        9, 14
      ],
      'circle-color': '#ffaa00',
      'circle-opacity': 0.8,
      'circle-stroke-width': 2,
      'circle-stroke-color': '#ffcc00'
    }
  })
}

function addCablesLayer() {
  const src = LAYER_SOURCES.cables
  const lyr = LAYER_IDS.cables
  removeLayerSafe(lyr)
  removeSourceSafe(src)

  map.addSource(src, {
    type: 'geojson',
    data: underseaCablesData
  })
  map.addLayer({
    id: lyr,
    type: 'line',
    source: src,
    paint: {
      'line-color': '#3388ff',
      'line-width': 1.5,
      'line-opacity': 0.7
    }
  })
}

// ---- NEW LAYER: Fires (WILDFIRES) ----

function addFiresLayer() {
  const src = LAYER_SOURCES.fires
  const glowLyr = LAYER_IDS['fires-glow']
  const lyr = LAYER_IDS.fires
  removeLayerSafe(lyr)
  removeLayerSafe(glowLyr)
  removeSourceSafe(src)

  map.addSource(src, {
    type: 'geojson',
    data: buildFiresGeoJSON(props.signals)
  })

  // Fires glow — orange-red halo, size based on confidence
  map.addLayer({
    id: glowLyr,
    type: 'circle',
    source: src,
    paint: {
      'circle-radius': [
        'interpolate', ['linear'], ['get', 'confidence'],
        10, 10,
        50, 18,
        90, 28
      ],
      'circle-color': '#ff4400',
      'circle-opacity': 0.18,
      'circle-stroke-width': 0
    }
  })

  // Fires core — orange-red circles, size based on confidence
  map.addLayer({
    id: lyr,
    type: 'circle',
    source: src,
    paint: {
      'circle-radius': [
        'interpolate', ['linear'], ['get', 'confidence'],
        10, 4,
        50, 6,
        90, 10
      ],
      'circle-color': '#ff4400',
      'circle-opacity': 0.9,
      'circle-stroke-width': 2,
      'circle-stroke-color': '#ff6600'
    }
  })
}

// ---- NEW LAYER: Pipelines ----

function addPipelinesLayer() {
  const src = LAYER_SOURCES.pipelines
  const lyr = LAYER_IDS.pipelines
  removeLayerSafe(lyr)
  removeSourceSafe(src)

  map.addSource(src, {
    type: 'geojson',
    data: PIPELINES_GEOJSON
  })

  // Pipelines — dashed yellow lines
  map.addLayer({
    id: lyr,
    type: 'line',
    source: src,
    paint: {
      'line-color': '#cc6600',
      'line-width': 2,
      'line-opacity': 0.75,
      'line-dasharray': [4, 3]
    }
  })
}

// ---- NEW LAYER: Radiation ----

function addRadiationLayer() {
  const src = LAYER_SOURCES.radiation
  const glowLyr = LAYER_IDS['radiation-glow']
  const lyr = LAYER_IDS.radiation
  removeLayerSafe(lyr)
  removeLayerSafe(glowLyr)
  removeSourceSafe(src)

  map.addSource(src, {
    type: 'geojson',
    data: buildRadiationGeoJSON(props.signals)
  })

  // Radiation glow — purple pulsing halo
  map.addLayer({
    id: glowLyr,
    type: 'circle',
    source: src,
    paint: {
      'circle-radius': 22,
      'circle-color': '#9b59b6',
      'circle-opacity': 0.2,
      'circle-stroke-width': 2,
      'circle-stroke-color': '#9b59b6',
      'circle-stroke-opacity': 0.3
    }
  })

  // Radiation core — purple circles
  map.addLayer({
    id: lyr,
    type: 'circle',
    source: src,
    paint: {
      'circle-radius': 7,
      'circle-color': '#9b59b6',
      'circle-opacity': 0.9,
      'circle-stroke-width': 2,
      'circle-stroke-color': '#bb77dd'
    }
  })
}

// ---- NEW LAYER: Spaceports ----

function addSpaceportsLayer() {
  const src = LAYER_SOURCES.spaceports
  const lyr = LAYER_IDS.spaceports
  const labelLyr = LAYER_IDS['spaceports-label']
  removeLayerSafe(labelLyr)
  removeLayerSafe(lyr)
  removeSourceSafe(src)

  map.addSource(src, {
    type: 'geojson',
    data: buildSpaceportsGeoJSON()
  })

  // Spaceports — white diamond background circle
  map.addLayer({
    id: lyr,
    type: 'circle',
    source: src,
    paint: {
      'circle-radius': 6,
      'circle-color': '#1a1a2e',
      'circle-opacity': 0.8,
      'circle-stroke-width': 1.5,
      'circle-stroke-color': '#aa88ff'
    }
  })

  // Spaceports — diamond symbol using text layer
  map.addLayer({
    id: labelLyr,
    type: 'symbol',
    source: src,
    layout: {
      'text-field': '\u25C6',
      'text-size': 12,
      'text-allow-overlap': true,
      'text-ignore-placement': true,
      'text-anchor': 'center'
    },
    paint: {
      'text-color': '#ffffff',
      'text-halo-color': '#aa88ff',
      'text-halo-width': 1
    }
  })
}

// ---- NEW LAYER: Outages ----

function addOutagesLayer() {
  const src = LAYER_SOURCES.outages
  const lyr = LAYER_IDS.outages
  const labelLyr = LAYER_IDS['outages-label']
  removeLayerSafe(labelLyr)
  removeLayerSafe(lyr)
  removeSourceSafe(src)

  map.addSource(src, {
    type: 'geojson',
    data: buildOutagesGeoJSON(props.signals)
  })

  // Outages — red square background circle
  map.addLayer({
    id: lyr,
    type: 'circle',
    source: src,
    paint: {
      'circle-radius': 6,
      'circle-color': '#2a0a0a',
      'circle-opacity': 0.8,
      'circle-stroke-width': 1.5,
      'circle-stroke-color': '#ff4444'
    }
  })

  // Outages — square symbol using text layer
  map.addLayer({
    id: labelLyr,
    type: 'symbol',
    source: src,
    layout: {
      'text-field': '\u25A0',
      'text-size': 12,
      'text-allow-overlap': true,
      'text-ignore-placement': true,
      'text-anchor': 'center'
    },
    paint: {
      'text-color': '#ff4444',
      'text-halo-color': '#330000',
      'text-halo-width': 1
    }
  })
}

// ---- NEW LAYER: Cyber ----

function addCyberLayer() {
  const src = LAYER_SOURCES.cyber
  const lyr = LAYER_IDS.cyber
  const labelLyr = LAYER_IDS['cyber-label']
  removeLayerSafe(labelLyr)
  removeLayerSafe(lyr)
  removeSourceSafe(src)

  map.addSource(src, {
    type: 'geojson',
    data: buildCyberGeoJSON(props.signals)
  })

  // Cyber — purple triangle background circle
  map.addLayer({
    id: lyr,
    type: 'circle',
    source: src,
    paint: {
      'circle-radius': 6,
      'circle-color': '#1a0a2a',
      'circle-opacity': 0.8,
      'circle-stroke-width': 1.5,
      'circle-stroke-color': '#ff44aa'
    }
  })

  // Cyber — triangle symbol using text layer
  map.addLayer({
    id: labelLyr,
    type: 'symbol',
    source: src,
    layout: {
      'text-field': '\u25B2',
      'text-size': 11,
      'text-allow-overlap': true,
      'text-ignore-placement': true,
      'text-anchor': 'center',
      'text-offset': [0, -0.05]
    },
    paint: {
      'text-color': '#ff44aa',
      'text-halo-color': '#1a0a2a',
      'text-halo-width': 1
    }
  })
}

// ---- NEW LAYER: Hotspots ----

function addHotspotsLayer() {
  const src = LAYER_SOURCES.hotspots
  const glowLyr = LAYER_IDS['hotspots-glow']
  const lyr = LAYER_IDS.hotspots
  removeLayerSafe(lyr)
  removeLayerSafe(glowLyr)
  removeSourceSafe(src)

  map.addSource(src, {
    type: 'geojson',
    data: buildHotspotsGeoJSON(props.signals)
  })

  // Hotspots glow — animated pulsing red halo
  map.addLayer({
    id: glowLyr,
    type: 'circle',
    source: src,
    paint: {
      'circle-radius': [
        'interpolate', ['linear'], ['get', 'score'],
        0.7, 18,
        0.85, 25,
        1.0, 35
      ],
      'circle-color': '#ff4444',
      'circle-opacity': 0.2,
      'circle-stroke-width': 2,
      'circle-stroke-color': '#ff0000',
      'circle-stroke-opacity': 0.3
    }
  })

  // Hotspots core — red circles
  map.addLayer({
    id: lyr,
    type: 'circle',
    source: src,
    paint: {
      'circle-radius': [
        'interpolate', ['linear'], ['get', 'score'],
        0.7, 5,
        0.85, 7,
        1.0, 10
      ],
      'circle-color': '#ff4444',
      'circle-opacity': 0.9,
      'circle-stroke-width': 2,
      'circle-stroke-color': '#ff8800'
    }
  })
}

// ---- Remove layer functions ----

function removeConflictsLayer() {
  removeLayerSafe(LAYER_IDS.conflicts)
  removeLayerSafe(LAYER_IDS['conflicts-glow'])
  removeSourceSafe(LAYER_SOURCES.conflicts)
}

function removeBasesLayer() {
  removeLayerSafe(LAYER_IDS['bases-label'])
  removeLayerSafe(LAYER_IDS.bases)
  removeSourceSafe(LAYER_SOURCES.bases)
}

function removeNuclearLayer() {
  removeLayerSafe(LAYER_IDS.nuclear)
  removeLayerSafe(LAYER_IDS['nuclear-glow'])
  removeLayerSafe(LAYER_IDS['nuclear-glow-outer'])
  removeSourceSafe(LAYER_SOURCES.nuclear)
}

function removeEarthquakesLayer() {
  removeLayerSafe(LAYER_IDS.earthquakes)
  removeLayerSafe(LAYER_IDS['earthquakes-glow'])
  removeSourceSafe(LAYER_SOURCES.earthquakes)
}

function removeCablesLayer() {
  removeLayerSafe(LAYER_IDS.cables)
  removeSourceSafe(LAYER_SOURCES.cables)
}

function removeFiresLayer() {
  removeLayerSafe(LAYER_IDS.fires)
  removeLayerSafe(LAYER_IDS['fires-glow'])
  removeSourceSafe(LAYER_SOURCES.fires)
}

function removePipelinesLayer() {
  removeLayerSafe(LAYER_IDS.pipelines)
  removeSourceSafe(LAYER_SOURCES.pipelines)
}

function removeRadiationLayer() {
  removeLayerSafe(LAYER_IDS.radiation)
  removeLayerSafe(LAYER_IDS['radiation-glow'])
  removeSourceSafe(LAYER_SOURCES.radiation)
}

function removeSpaceportsLayer() {
  removeLayerSafe(LAYER_IDS['spaceports-label'])
  removeLayerSafe(LAYER_IDS.spaceports)
  removeSourceSafe(LAYER_SOURCES.spaceports)
}

function removeOutagesLayer() {
  removeLayerSafe(LAYER_IDS['outages-label'])
  removeLayerSafe(LAYER_IDS.outages)
  removeSourceSafe(LAYER_SOURCES.outages)
}

function removeCyberLayer() {
  removeLayerSafe(LAYER_IDS['cyber-label'])
  removeLayerSafe(LAYER_IDS.cyber)
  removeSourceSafe(LAYER_SOURCES.cyber)
}

function removeHotspotsLayer() {
  removeLayerSafe(LAYER_IDS.hotspots)
  removeLayerSafe(LAYER_IDS['hotspots-glow'])
  removeSourceSafe(LAYER_SOURCES.hotspots)
}

// ---- Layer adders/removers maps ----

const layerAdders = {
  conflicts: addConflictsLayer,
  bases: addBasesLayer,
  nuclear: addNuclearLayer,
  earthquakes: addEarthquakesLayer,
  cables: addCablesLayer,
  fires: addFiresLayer,
  pipelines: addPipelinesLayer,
  radiation: addRadiationLayer,
  spaceports: addSpaceportsLayer,
  outages: addOutagesLayer,
  cyber: addCyberLayer,
  hotspots: addHotspotsLayer
}

const layerRemovers = {
  conflicts: removeConflictsLayer,
  bases: removeBasesLayer,
  nuclear: removeNuclearLayer,
  earthquakes: removeEarthquakesLayer,
  cables: removeCablesLayer,
  fires: removeFiresLayer,
  pipelines: removePipelinesLayer,
  radiation: removeRadiationLayer,
  spaceports: removeSpaceportsLayer,
  outages: removeOutagesLayer,
  cyber: removeCyberLayer,
  hotspots: removeHotspotsLayer
}

function syncLayers(activeLayers) {
  if (!map || !mapLoaded) return

  for (const [id, adder] of Object.entries(layerAdders)) {
    if (activeLayers.has(id)) {
      adder()
    } else {
      layerRemovers[id]()
    }
  }
}

// ---- Popup for data layer markers ----

function setupLayerPopups() {
  // Point layers with standard name/country/type popups
  const pointLayerIds = [
    LAYER_IDS.conflicts,
    LAYER_IDS.bases,
    LAYER_IDS.nuclear,
    LAYER_IDS.earthquakes,
    LAYER_IDS.fires,
    LAYER_IDS.radiation,
    LAYER_IDS.spaceports,
    LAYER_IDS.outages,
    LAYER_IDS.cyber,
    LAYER_IDS.hotspots
  ]

  for (const lyrId of pointLayerIds) {
    map.on('mouseenter', lyrId, (e) => {
      if (!e.features || e.features.length === 0) return
      map.getCanvas().style.cursor = 'pointer'
      const feat = e.features[0]
      const p = feat.properties
      const coord = feat.geometry.coordinates.slice()

      popup
        .setLngLat(coord)
        .setHTML(
          `<div style="font-family:'SF Mono',monospace;font-size:11px;">` +
          `<strong style="color:#e8e8e8;">${p.name || 'Unknown'}</strong>` +
          (p.country ? `<br><span style="color:#888;">${p.country}</span>` : '') +
          (p.type ? `<br><span style="color:#888;text-transform:uppercase;font-size:10px;">${p.type}</span>` : '') +
          (p.score ? `<br><span style="color:#ff8800;font-size:10px;">SCORE: ${p.score}</span>` : '') +
          (p.severity ? `<br><span style="color:#ff4444;font-size:10px;">SEV: ${p.severity}</span>` : '') +
          (p.confidence ? `<br><span style="color:#ff6600;font-size:10px;">CONF: ${p.confidence}</span>` : '') +
          (p.level ? `<br><span style="color:#9b59b6;font-size:10px;">LEVEL: ${p.level}</span>` : '') +
          `</div>`
        )
        .addTo(map)
    })

    map.on('mouseleave', lyrId, () => {
      map.getCanvas().style.cursor = ''
      popup.remove()
    })
  }

  // Cable popups
  map.on('mouseenter', LAYER_IDS.cables, (e) => {
    if (!e.features || e.features.length === 0) return
    map.getCanvas().style.cursor = 'pointer'
    const p = e.features[0].properties
    popup
      .setLngLat(e.lngLat)
      .setHTML(
        `<div style="font-family:'SF Mono',monospace;font-size:11px;">` +
        `<strong style="color:#e8e8e8;">${p.name || 'Cable'}</strong>` +
        (p.capacity ? `<br><span style="color:#3388ff;">${p.capacity}</span>` : '') +
        `</div>`
      )
      .addTo(map)
  })

  map.on('mouseleave', LAYER_IDS.cables, () => {
    map.getCanvas().style.cursor = ''
    popup.remove()
  })

  // Pipeline popups
  map.on('mouseenter', LAYER_IDS.pipelines, (e) => {
    if (!e.features || e.features.length === 0) return
    map.getCanvas().style.cursor = 'pointer'
    const p = e.features[0].properties
    popup
      .setLngLat(e.lngLat)
      .setHTML(
        `<div style="font-family:'SF Mono',monospace;font-size:11px;">` +
        `<strong style="color:#e8e8e8;">${p.name || 'Pipeline'}</strong>` +
        (p.status ? `<br><span style="color:#cc6600;text-transform:uppercase;font-size:10px;">${p.status}</span>` : '') +
        `</div>`
      )
      .addTo(map)
  })

  map.on('mouseleave', LAYER_IDS.pipelines, () => {
    map.getCanvas().style.cursor = ''
    popup.remove()
  })
}

// ---- Mount ----

onMounted(async () => {
  const isGlobe = props.projection === '3d' || props.projection === '3D'
  map = new maplibregl.Map({
    container: mapContainer.value,
    style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
    center: [0, 20],
    zoom: 1.5,
    renderWorldCopies: false,
    projection: isGlobe ? 'globe' : 'mercator',
    pitchWithRotate: isGlobe,
    dragRotate: isGlobe,
    touchZoomRotate: isGlobe ? true : false,
    attributionControl: false,
    maxPitch: isGlobe ? 60 : 0,
  })

  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')

  popup = new maplibregl.Popup({
    closeButton: false,
    closeOnClick: false,
    className: 'risk-popup'
  })

  map.on('load', async () => {
    let geojson
    try {
      const res = await fetch(
        'https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson'
      )
      geojson = await res.json()
    } catch {
      console.warn('Failed to load countries GeoJSON')
      return
    }

    map.addSource('countries', {
      type: 'geojson',
      data: geojson,
      generateId: true
    })

    map.addLayer({
      id: 'countries-fill',
      type: 'fill',
      source: 'countries',
      paint: {
        'fill-color': buildFillColor(props.riskData),
        'fill-opacity': [
          'case',
          ['boolean', ['feature-state', 'hover'], false],
          0.7,
          0.5
        ]
      }
    })

    map.addLayer({
      id: 'countries-border',
      type: 'line',
      source: 'countries',
      paint: {
        'line-color': '#2a2a2a',
        'line-width': 0.5
      }
    })

    map.addLayer({
      id: 'countries-selected-border',
      type: 'line',
      source: 'countries',
      paint: {
        'line-color': [
          'case',
          ['boolean', ['feature-state', 'selected'], false],
          '#e8e8e8',
          'transparent'
        ],
        'line-width': [
          'case',
          ['boolean', ['feature-state', 'selected'], false],
          2.5,
          0
        ]
      }
    })

    // Hover
    map.on('mousemove', 'countries-fill', (e) => {
      if (e.features.length === 0) return
      map.getCanvas().style.cursor = 'pointer'

      if (hoveredCountryId !== null) {
        map.setFeatureState({ source: 'countries', id: hoveredCountryId }, { hover: false })
      }

      hoveredCountryId = e.features[0].id
      map.setFeatureState({ source: 'countries', id: hoveredCountryId }, { hover: true })

      const feat = e.features[0]
      const code = feat.properties.ISO_A2
      const name = feat.properties.ADMIN || feat.properties.NAME || code
      const score = props.riskData[code]
      const scoreText = score != null ? Math.round(score) : 'N/A'
      const scoreColorVal = score != null ? riskColor(score) : '#666'

      popup
        .setLngLat(e.lngLat)
        .setHTML(
          `<div style="font-family:'SF Mono',monospace;font-size:12px;">` +
          `<strong style="color:#e8e8e8;">${name}</strong><br>` +
          `<span style="color:${scoreColorVal};font-size:16px;font-weight:700;">${scoreText}</span>` +
          `<span style="margin-left:8px;font-size:10px;">${statusTag(score)}</span>` +
          `</div>`
        )
        .addTo(map)
    })

    map.on('mouseleave', 'countries-fill', () => {
      map.getCanvas().style.cursor = ''
      if (hoveredCountryId !== null) {
        map.setFeatureState({ source: 'countries', id: hoveredCountryId }, { hover: false })
      }
      hoveredCountryId = null
      popup.remove()
    })

    // Click
    map.on('click', 'countries-fill', (e) => {
      if (e.features.length === 0) return
      const code = e.features[0].properties.ISO_A2
      if (code && code !== '-99') {
        emit('countrySelected', code)
      }
    })

    // Mark map as loaded, then sync data layers
    mapLoaded = true
    syncLayers(props.activeLayers)
    setupLayerPopups()

    // Apply any projection change that was requested while loading
    if (pendingProjection !== null) {
      applyProjection(pendingProjection)
      pendingProjection = null
    } else {
      // Apply atmosphere if starting in globe mode
      applyAtmosphere(props.projection)
    }

    // Apply initial selection if present
    if (props.selectedCountry) {
      setTimeout(() => updateSelectedHighlight(props.selectedCountry), 500)
    }
  })
})

// ---- Globe / projection helpers ----

function applyAtmosphere(mode) {
  if (!map) return
  const isGlobe = mode === '3d' || mode === '3D' || mode === 'globe'
  if (isGlobe) {
    try {
      map.setFog({
        color: 'rgb(5, 5, 20)',
        'high-color': 'rgb(20, 20, 40)',
        'horizon-blend': 0.1,
        'space-color': 'rgb(5, 5, 15)',
        'star-intensity': 0.6
      })
    } catch {
      // fog not supported in this style version — skip silently
    }
  } else {
    try {
      map.setFog(null)
    } catch {
      // ignore
    }
  }
}

// ---- Watchers ----

function applyProjection(mode) {
  if (!map) return
  const isGlobe = mode === '3d' || mode === '3D' || mode === 'globe'

  try {
    // MapLibre v5+ string API
    map.setProjection(isGlobe ? 'globe' : 'mercator')
  } catch {
    try {
      // Fallback: object API (MapLibre v4)
      map.setProjection(isGlobe ? { type: 'globe' } : { type: 'mercator' })
    } catch {
      console.warn('Globe projection not supported in this MapLibre version')
    }
  }

  // Toggle rotation for globe mode
  if (isGlobe) {
    map.dragRotate.enable()
    map.touchZoomRotate.enable()
    map.setMaxPitch(60)
  } else {
    map.dragRotate.disable()
    map.touchZoomRotate.disableRotation()
    map.setMaxPitch(0)
    map.setPitch(0)
    map.setBearing(0)
  }
  applyAtmosphere(mode)
}

// Track pending projection so it can be applied once the map style loads
let pendingProjection = null

watch(() => props.projection, (newVal) => {
  if (!map) return

  if (!mapLoaded) {
    // Map style not yet loaded — queue the projection change
    pendingProjection = newVal
    return
  }

  applyProjection(newVal)
})

watch(() => props.riskData, (newData) => {
  if (map && map.getLayer('countries-fill')) {
    map.setPaintProperty('countries-fill', 'fill-color', buildFillColor(newData))
  }
}, { deep: true })

watch(() => props.selectedCountry, (code) => {
  updateSelectedHighlight(code)
})

watch(() => props.activeLayers, (newLayers) => {
  syncLayers(newLayers)
}, { deep: true })

watch(() => props.signals, () => {
  if (!map || !mapLoaded) return
  // Refresh signal-dependent layers if active
  if (props.activeLayers.has('conflicts')) addConflictsLayer()
  if (props.activeLayers.has('earthquakes')) addEarthquakesLayer()
  if (props.activeLayers.has('fires')) addFiresLayer()
  if (props.activeLayers.has('radiation')) addRadiationLayer()
  if (props.activeLayers.has('outages')) addOutagesLayer()
  if (props.activeLayers.has('cyber')) addCyberLayer()
  if (props.activeLayers.has('hotspots')) addHotspotsLayer()
}, { deep: true })

onUnmounted(() => {
  if (map) map.remove()
})
</script>

<style scoped>
.world-map-wrapper {
  width: 100%;
  height: 100%;
  position: relative;
  background: #020a08;
  overflow: hidden;
}

.world-map-container {
  width: 100%;
  height: 100%;
  background: #020a08;
}

/* Override MapLibre default canvas background */
.world-map-container :deep(.maplibregl-canvas) {
  background: #020a08 !important;
}

.map-legend {
  position: absolute;
  bottom: 8px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
  background: #0a0a0a;
  border: 1px solid #2a2a2a;
  padding: 5px 12px;
  border-radius: 4px;
  z-index: 10;
  max-width: 90%;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
}

.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-shape {
  flex-shrink: 0;
}

.legend-triangle {
  width: 0;
  height: 0;
  border-left: 5px solid transparent;
  border-right: 5px solid transparent;
  border-bottom: 9px solid;
}

.legend-diamond {
  width: 8px;
  height: 8px;
  transform: rotate(45deg);
}

.legend-square {
  width: 8px;
  height: 8px;
  border-radius: 1px;
}

.legend-line {
  width: 14px;
  height: 2px;
  border-radius: 1px;
}

.legend-label {
  font-family: 'SF Mono', 'Monaco', 'Cascadia Code', monospace;
  font-size: 9px;
  color: #888;
  text-transform: capitalize;
  letter-spacing: 0.03em;
  white-space: nowrap;
}

.globe-beta-badge {
  position: absolute;
  top: 10px;
  left: 10px;
  background: #44ff88;
  color: #000;
  font-family: 'SF Mono', 'Monaco', 'Cascadia Code', monospace;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 1px;
  padding: 2px 8px;
  z-index: 10;
  pointer-events: none;
}

.world-map-container :deep(.maplibregl-ctrl-top-right) {
  top: 8px;
  right: 8px;
}

.world-map-container :deep(.maplibregl-ctrl-group) {
  background: #141414;
  border: 1px solid #2a2a2a;
}

.world-map-container :deep(.maplibregl-ctrl-group button) {
  background-color: #141414;
  border-color: #2a2a2a;
}

.world-map-container :deep(.maplibregl-ctrl-group button + button) {
  border-top-color: #2a2a2a;
}

.world-map-container :deep(.maplibregl-ctrl-group button:hover) {
  background-color: #222;
}

.world-map-container :deep(.maplibregl-ctrl-group button span) {
  filter: invert(1);
}
</style>

<style>
.risk-popup .maplibregl-popup-content {
  background: #141414;
  border: 1px solid #2a2a2a;
  padding: 8px 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.5);
}

.risk-popup .maplibregl-popup-tip {
  border-top-color: #141414;
}
</style>
