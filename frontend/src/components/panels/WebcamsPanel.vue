<template>
  <BasePanel
    panelId="webcams"
    title="LIVE WEBCAMS"
    :showCount="true"
    :count="totalCount"
    :defaultColSpan="2"
    :defaultRowSpan="2"
  >
    <template #tabs>
      <div class="webcam-tabs">
        <button
          v-for="tab in regionTabs"
          :key="tab"
          class="webcam-tab"
          :class="{ active: activeRegion === tab }"
          @click="activeRegion = tab"
        >{{ tab }}</button>
        <div class="webcam-view-toggle">
          <button
            class="view-btn"
            :class="{ active: viewMode === 'grid' }"
            @click="viewMode = 'grid'"
            title="Grid view"
          >&#8862;</button>
          <button
            class="view-btn"
            :class="{ active: viewMode === 'list' }"
            @click="viewMode = 'list'"
            title="List view"
          >&#8801;</button>
        </div>
      </div>
    </template>

    <template #default>
      <div class="webcam-grid" :class="{ 'webcam-grid--list': viewMode === 'list' }">
        <div
          v-for="cam in visibleCams"
          :key="cam.name"
          class="webcam-card"
        >
          <div class="webcam-card__header">
            <span class="webcam-live-dot"></span>
            <span class="webcam-card__title">{{ cam.name }}</span>
            <span class="webcam-card__source">{{ cam.source }}</span>
          </div>
          <div class="webcam-card__embed">
            <iframe
              v-if="!isCamFailed(cam.name)"
              :src="cam.url"
              frameborder="0"
              allow="autoplay; encrypted-media; picture-in-picture"
              allowfullscreen
              loading="lazy"
              referrerpolicy="strict-origin-when-cross-origin"
              @error="onCamError(cam.name)"
            ></iframe>
            <a
              class="webcam-card__fallback"
              :class="{ 'webcam-card__fallback--visible': isCamFailed(cam.name) }"
              :href="'https://www.youtube.com/watch?v=' + (cam.videoId || getVideoId(cam.url))"
              target="_blank"
              rel="noopener"
              title="Watch on YouTube"
            >
              <span class="fallback-icon">&#9654;</span>
              <span class="fallback-text">{{ cam.name }}</span>
              <span class="fallback-hint">Watch live on YouTube &#8599;</span>
            </a>
          </div>
        </div>
        <div v-if="visibleCams.length === 0" class="webcam-empty">
          No webcams available for this region
        </div>
      </div>
    </template>
  </BasePanel>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import BasePanel from '../BasePanel.vue'

function getVideoId(url) {
  const match = url.match(/embed\/([^?]+)/)
  return match ? match[1] : ''
}

// Build YouTube embed URL matching WorldMonitor's exact format
function buildEmbed(videoId) {
  const origin = typeof window !== 'undefined' ? window.location.origin : ''
  return `https://www.youtube.com/embed/${videoId}?autoplay=1&mute=1&controls=0&modestbranding=1&playsinline=1&rel=0&enablejsapi=1&origin=${origin}`
}

// Track which cams have failed to load
const failedCams = reactive(new Set())

function onCamError(camName) {
  failedCams.add(camName)
}

function isCamFailed(camName) {
  return failedCams.has(camName)
}

const WEBCAMS = {
  SPACE: [
    { name: 'ISS EARTH VIEW', videoId: 'vytmBNhc9ig', url: buildEmbed('vytmBNhc9ig'), source: 'NASA' },
    { name: 'NASA TV', videoId: 'nA9UZF-SZoQ', url: buildEmbed('nA9UZF-SZoQ'), source: 'NASA' },
  ],
  MIDEAST: [
    { name: 'AL JAZEERA LIVE', videoId: 'gCNeDWCI0vo', url: buildEmbed('gCNeDWCI0vo'), source: 'Al Jazeera' },
    { name: 'JERUSALEM', videoId: 'e34xb-Fbl0U', url: buildEmbed('e34xb-Fbl0U'), source: 'Western Wall' },
    { name: 'MECCA', videoId: 'Cm1v4bteXbI', url: buildEmbed('Cm1v4bteXbI'), source: 'Makkah Live' },
  ],
  EUROPE: [
    { name: 'KYIV', videoId: '-Q7FuPINDjA', url: buildEmbed('-Q7FuPINDjA'), source: 'DW News' },
    { name: 'PARIS', videoId: 'OzYp4NRZlwQ', url: buildEmbed('OzYp4NRZlwQ'), source: 'EarthCam' },
    { name: 'LONDON', videoId: 'Lxqcg1qt0XU', url: buildEmbed('Lxqcg1qt0XU'), source: 'EarthCam' },
  ],
  AMERICAS: [
    { name: 'WASHINGTON DC', videoId: '1wV9lLe14aU', url: buildEmbed('1wV9lLe14aU'), source: 'Axis' },
    { name: 'NEW YORK', videoId: '4qyZLflp-sI', url: buildEmbed('4qyZLflp-sI'), source: 'EarthCam' },
    { name: 'MIAMI', videoId: '5YCajRjvWCg', url: buildEmbed('5YCajRjvWCg'), source: 'Florida Cams' },
  ],
  ASIA: [
    { name: 'TAIPEI', videoId: 'z_fY1pj1VBw', url: buildEmbed('z_fY1pj1VBw'), source: 'Taiwan' },
    { name: 'TOKYO', videoId: '_k-5U7IeK8g', url: buildEmbed('_k-5U7IeK8g'), source: 'Tokyo 4K' },
    { name: 'SEOUL', videoId: '-JhoMGoAfFc', url: buildEmbed('-JhoMGoAfFc'), source: 'Seoul' },
    { name: 'SYDNEY', videoId: '7pcL-0Wo77U', url: buildEmbed('7pcL-0Wo77U'), source: 'Sydney' },
  ],
}

// Region tabs in the required order: SPACE first, then geographic regions
const regionTabs = ['SPACE', 'MIDEAST', 'EUROPE', 'AMERICAS', 'ASIA', 'ALL']
const activeRegion = ref('SPACE')
const viewMode = ref('grid')

const totalCount = computed(() => {
  return Object.values(WEBCAMS).reduce((sum, arr) => sum + arr.length, 0)
})

const visibleCams = computed(() => {
  if (activeRegion.value === 'ALL') {
    return Object.values(WEBCAMS).flat()
  }
  return WEBCAMS[activeRegion.value] || []
})

// Listen for YouTube embed errors via postMessage
if (typeof window !== 'undefined') {
  window.addEventListener('message', (event) => {
    try {
      if (event.origin.includes('youtube.com')) {
        const data = typeof event.data === 'string' ? JSON.parse(event.data) : event.data
        if (data?.event === 'onError' || data?.info?.errorCode === 150 || data?.info?.errorCode === 153) {
          // Mark all visible cams as potentially failed -- YouTube doesn't tell us which iframe
          // The fallback is already always rendered behind the iframe (z-index layering)
        }
      }
    } catch {
      // ignore
    }
  })
}
</script>

<style scoped>
.webcam-tabs {
  display: flex;
  align-items: center;
  gap: 2px;
  overflow-x: auto;
  padding: 4px 8px;
  scrollbar-width: none;
}

.webcam-tabs::-webkit-scrollbar {
  display: none;
}

.webcam-tab {
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: var(--text-dim, #888);
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  text-transform: uppercase;
  letter-spacing: 1px;
  padding: 4px 8px;
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.15s ease;
}

.webcam-tab:hover {
  color: var(--text, #e8e8e8);
}

.webcam-tab.active {
  background: var(--surface-hover, #1e1e1e);
  border-bottom: 2px solid var(--green, #44ff88);
  color: var(--text, #e8e8e8);
}

.webcam-view-toggle {
  display: flex;
  gap: 0;
  margin-left: auto;
  flex-shrink: 0;
}

.view-btn {
  background: transparent;
  border: 1px solid var(--border, #2a2a2a);
  color: var(--text-dim, #888);
  font-size: 14px;
  width: 26px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;
}

.view-btn:first-child {
  border-radius: 2px 0 0 2px;
}

.view-btn:last-child {
  border-radius: 0 2px 2px 0;
  border-left: none;
}

.view-btn.active {
  background: var(--surface-hover, #1e1e1e);
  color: var(--text, #e8e8e8);
  border-color: var(--border-strong, #444);
}

.view-btn:hover:not(.active) {
  color: var(--text, #e8e8e8);
}

/* Grid layout */
.webcam-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  padding: 4px;
}

.webcam-grid--list {
  grid-template-columns: 1fr;
}

/* Card */
.webcam-card {
  display: flex;
  flex-direction: column;
  border: 1px solid var(--border, #2a2a2a);
  background: var(--bg, #0a0a0a);
  overflow: hidden;
}

.webcam-card__header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 5px 8px;
  border-bottom: 1px solid var(--border, #2a2a2a);
}

.webcam-live-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--semantic-critical, #ff4444);
  flex-shrink: 0;
  animation: livePulse 1.5s ease-in-out infinite;
}

@keyframes livePulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.webcam-card__title {
  font-family: 'SF Mono', monospace;
  font-size: 10px;
  font-weight: 600;
  color: var(--text, #e8e8e8);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.webcam-card__source {
  font-family: 'SF Mono', monospace;
  font-size: 9px;
  color: var(--text-muted, #666);
  margin-left: auto;
  flex-shrink: 0;
}

.webcam-card__embed {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  background: #000;
}

.webcam-card__embed iframe {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: none;
  z-index: 1;
}

.webcam-card__fallback {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
  text-decoration: none;
  color: var(--text-dim, #888);
  z-index: 0;
  transition: background 0.2s;
}

.webcam-card__fallback:hover {
  background: linear-gradient(135deg, #111 0%, #1a2a3e 100%);
  color: var(--text, #e8e8e8);
}

.fallback-icon {
  font-size: 32px;
  color: #ff4444;
  margin-bottom: 8px;
}

.fallback-text {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 1px;
  text-transform: uppercase;
  margin-bottom: 4px;
}

.fallback-hint {
  font-size: 9px;
  color: var(--text-muted, #666);
}

/* When iframe fails, bring fallback to front */
.webcam-card__fallback--visible {
  z-index: 2;
}

.webcam-empty {
  grid-column: 1 / -1;
  padding: 24px;
  text-align: center;
  font-family: 'SF Mono', monospace;
  font-size: 11px;
  color: var(--text-dim, #888);
}
</style>
