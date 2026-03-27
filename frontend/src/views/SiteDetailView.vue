<template>
  <div class="site-detail">
    <!-- Back nav -->
    <router-link to="/sites" class="back-link">&larr; All Sites</router-link>

    <div v-if="loading" class="loading-text">Loading site...</div>

    <template v-else-if="site">
      <!-- Site header -->
      <div class="site-header">
        <div class="header-left">
          <h1 class="site-url">{{ site.domain || site.url }}</h1>
          <div class="header-meta">
            <span class="status-badge" :class="'status-' + site.status">{{ site.status }}</span>
            <span class="meta-sep">|</span>
            <span class="meta-item">Discovered {{ formatDate(site.created_at) }}</span>
            <span class="meta-sep">|</span>
            <span class="meta-item">{{ pages.length }} pages</span>
          </div>
        </div>
      </div>

      <!-- Pages list -->
      <div v-if="pagesLoading" class="loading-text">Loading pages...</div>

      <div v-else-if="pages.length === 0" class="empty-state">No pages discovered yet</div>

      <div v-else class="pages-section">
        <h2 class="section-title">Monitored Pages</h2>

        <table class="data-table">
          <thead>
            <tr>
              <th>Path</th>
              <th>Type</th>
              <th>Last Checked</th>
              <th>Changes</th>
              <th>Significance</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <template v-for="page in pages" :key="page.id">
              <tr
                class="page-row"
                :class="{ 'row-expanded': expandedPageId === page.id }"
                @click="togglePage(page)"
              >
                <td class="path-cell">{{ page.path || '/' }}</td>
                <td>
                  <span class="type-tag">{{ formatPageType(page.page_type) }}</span>
                </td>
                <td class="ts-cell">{{ formatRelativeTime(page.last_checked_at || (page.last_snapshot && page.last_snapshot.captured_at) || page.last_crawled) }}</td>
                <td class="mono-cell">{{ page.change_count ?? page.diff_count ?? 0 }}</td>
                <td>
                  <span
                    v-if="page.highest_significance"
                    class="sig-badge"
                    :class="'sig-' + page.highest_significance.toLowerCase()"
                  >
                    {{ page.highest_significance }}
                  </span>
                  <span v-else class="sig-badge sig-none">NONE</span>
                </td>
                <td class="expand-cell">
                  <span class="expand-icon">{{ expandedPageId === page.id ? '&#9650;' : '&#9660;' }}</span>
                </td>
              </tr>

              <!-- Expanded: change history -->
              <tr v-if="expandedPageId === page.id" class="history-row">
                <td colspan="6">
                  <div class="history-panel">
                    <div v-if="diffsLoading" class="loading-text">Loading changes...</div>

                    <div v-else-if="diffs.length === 0" class="empty-state">No changes detected</div>

                    <div v-else class="timeline">
                      <div
                        v-for="diff in diffs"
                        :key="diff.id"
                        class="timeline-entry"
                      >
                        <div class="timeline-left">
                          <span class="timeline-date">{{ formatChangeDate(diff.detected_at) }}</span>
                          <span class="timeline-summary">
                            {{ diff.change_percentage != null ? diff.change_percentage + '% content changed' : 'Content changed' }}
                          </span>
                          <span
                            class="sig-badge small"
                            :class="'sig-' + (diff.significance || 'none').toLowerCase()"
                          >
                            {{ diff.significance || 'NONE' }}
                          </span>
                        </div>
                        <button
                          class="btn-view-diff"
                          @click.stop="viewDiff(page, diff)"
                        >
                          {{ activeDiffId === diff.id ? 'Hide Diff' : 'View Diff' }}
                        </button>
                      </div>
                    </div>

                    <!-- Inline diff viewer -->
                    <div v-if="activeDiffId && diffDetail" class="diff-viewer">
                      <div class="diff-header">
                        <span class="diff-title">Diff Viewer</span>
                        <button class="btn-close-diff" @click.stop="closeDiff">&times;</button>
                      </div>
                      <div v-if="diffDetailLoading" class="loading-text">Loading diff...</div>
                      <div v-else class="diff-content">
                        <div
                          v-for="(line, idx) in diffLines"
                          :key="idx"
                          class="diff-line"
                          :class="line.type"
                        >
                          <span class="diff-line-prefix">{{ line.prefix }}</span>
                          <span class="diff-line-text">{{ line.text }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>
    </template>

    <div v-if="error" class="error-text">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getSite, getSitePages, getPageDiffs, getDiffDetail } from '../api/intelligence'

const props = defineProps({
  siteId: { type: [String, Number], required: true }
})

const loading = ref(true)
const pagesLoading = ref(false)
const diffsLoading = ref(false)
const diffDetailLoading = ref(false)
const error = ref('')
const site = ref(null)
const pages = ref([])
const diffs = ref([])
const diffDetail = ref(null)
const expandedPageId = ref(null)
const activeDiffId = ref(null)

// Formatters
const formatDate = (ts) => {
  if (!ts) return '--'
  return new Date(ts).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

const formatRelativeTime = (ts) => {
  if (!ts) return 'never'
  const elapsed = Date.now() - new Date(ts).getTime()
  const mins = Math.floor(elapsed / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24) return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  if (days < 30) return `${days}d ago`
  return new Date(ts).toLocaleDateString()
}

const formatChangeDate = (ts) => {
  if (!ts) return '--'
  const d = new Date(ts)
  const month = d.toLocaleDateString('en-US', { month: 'short' })
  const day = d.getDate()
  const time = d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true }).toLowerCase()
  return `${month} ${day} ${time}`
}

const formatPageType = (t) => {
  if (!t) return 'page'
  return t.replace(/_/g, ' ')
}

// Compute diff lines from diffDetail
const diffLines = computed(() => {
  if (!diffDetail.value) return []

  // If the API returns pre-computed lines
  if (diffDetail.value.lines && Array.isArray(diffDetail.value.lines)) {
    return diffDetail.value.lines.map((l) => ({
      type: l.type || 'context',
      prefix: l.type === 'added' ? '+' : l.type === 'removed' ? '-' : ' ',
      text: l.text || l.content || ''
    }))
  }

  // Otherwise compute from before/after text
  const beforeObj = diffDetail.value.before || {}
  const afterObj = diffDetail.value.after || {}
  const beforeText = beforeObj.content_text || diffDetail.value.before_text || diffDetail.value.old_text || ''
  const afterText = afterObj.content_text || diffDetail.value.after_text || diffDetail.value.new_text || ''
  const before = beforeText.split('\n')
  const after = afterText.split('\n')
  return computeSimpleDiff(before, after)
})

const computeSimpleDiff = (oldLines, newLines) => {
  const result = []
  const maxLen = Math.max(oldLines.length, newLines.length)
  let oi = 0
  let ni = 0

  while (oi < oldLines.length || ni < newLines.length) {
    if (oi >= oldLines.length) {
      result.push({ type: 'added', prefix: '+', text: newLines[ni] })
      ni++
    } else if (ni >= newLines.length) {
      result.push({ type: 'removed', prefix: '-', text: oldLines[oi] })
      oi++
    } else if (oldLines[oi] === newLines[ni]) {
      result.push({ type: 'context', prefix: ' ', text: oldLines[oi] })
      oi++
      ni++
    } else {
      // Look ahead for a match
      let foundOld = -1
      let foundNew = -1
      const lookAhead = Math.min(5, maxLen)

      for (let k = 1; k <= lookAhead; k++) {
        if (ni + k < newLines.length && oldLines[oi] === newLines[ni + k] && foundNew === -1) {
          foundNew = ni + k
        }
        if (oi + k < oldLines.length && oldLines[oi + k] === newLines[ni] && foundOld === -1) {
          foundOld = oi + k
        }
      }

      if (foundOld !== -1 && (foundNew === -1 || (foundOld - oi) <= (foundNew - ni))) {
        while (oi < foundOld) {
          result.push({ type: 'removed', prefix: '-', text: oldLines[oi] })
          oi++
        }
      } else if (foundNew !== -1) {
        while (ni < foundNew) {
          result.push({ type: 'added', prefix: '+', text: newLines[ni] })
          ni++
        }
      } else {
        result.push({ type: 'removed', prefix: '-', text: oldLines[oi] })
        result.push({ type: 'added', prefix: '+', text: newLines[ni] })
        oi++
        ni++
      }
    }
  }

  return result
}

// Data loading
const loadSite = async () => {
  try {
    const res = await getSite(props.siteId)
    site.value = res.data || res
  } catch (e) {
    error.value = 'Failed to load site: ' + e.message
  } finally {
    loading.value = false
  }
}

const loadPages = async () => {
  pagesLoading.value = true
  try {
    const res = await getSitePages(props.siteId)
    const d = res.data || res
    pages.value = Array.isArray(d) ? d : (d.items || d.results || [])
  } catch (e) {
    // Fallback: if site response included pages inline
    if (site.value && site.value.pages) {
      pages.value = site.value.pages
    } else {
      error.value = 'Failed to load pages: ' + e.message
    }
  } finally {
    pagesLoading.value = false
  }
}

const togglePage = async (page) => {
  if (expandedPageId.value === page.id) {
    expandedPageId.value = null
    diffs.value = []
    activeDiffId.value = null
    diffDetail.value = null
    return
  }

  expandedPageId.value = page.id
  activeDiffId.value = null
  diffDetail.value = null
  diffsLoading.value = true

  try {
    const res = await getPageDiffs(props.siteId, page.id)
    const d = res.data || res
    diffs.value = Array.isArray(d) ? d : (d.items || d.results || [])
  } catch (e) {
    error.value = 'Failed to load diffs: ' + e.message
    diffs.value = []
  } finally {
    diffsLoading.value = false
  }
}

const viewDiff = async (page, diff) => {
  if (activeDiffId.value === diff.id) {
    closeDiff()
    return
  }

  activeDiffId.value = diff.id
  diffDetailLoading.value = true
  diffDetail.value = null

  try {
    const res = await getDiffDetail(props.siteId, page.id, diff.id)
    diffDetail.value = res.data || res
  } catch (e) {
    error.value = 'Failed to load diff detail: ' + e.message
  } finally {
    diffDetailLoading.value = false
  }
}

const closeDiff = () => {
  activeDiffId.value = null
  diffDetail.value = null
}

onMounted(async () => {
  await loadSite()
  if (site.value) {
    await loadPages()
  }
})
</script>

<style scoped>
.site-detail {
  font-family: 'Space Grotesk', system-ui, sans-serif;
  max-width: 1100px;
  color: #e8e8e8;
}

/* Back link */
.back-link {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8rem;
  color: #999;
  text-decoration: none;
  display: inline-block;
  margin-bottom: 20px;
  transition: color 0.15s;
}

.back-link:hover {
  color: #FF4500;
}

/* Site header */
.site-header {
  margin-bottom: 32px;
  padding-bottom: 20px;
  border-bottom: 1px solid #222;
}

.site-url {
  font-size: 1.6rem;
  font-weight: 600;
  color: #FFFFFF;
  margin: 0 0 10px 0;
  font-family: 'JetBrains Mono', monospace;
}

.header-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.meta-item {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #999;
}

.meta-sep {
  color: #333;
  font-size: 0.7rem;
}

/* Section */
.section-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #e8e8e8;
  margin: 0 0 16px 0;
}

/* Loading / empty / error */
.loading-text {
  font-family: 'JetBrains Mono', monospace;
  color: #999;
  font-size: 0.85rem;
  padding: 12px 0;
}

.empty-state {
  font-family: 'JetBrains Mono', monospace;
  color: #666;
  font-size: 0.85rem;
  padding: 20px 0;
}

.error-text {
  font-family: 'JetBrains Mono', monospace;
  color: #F44336;
  font-size: 0.85rem;
  margin-top: 15px;
}

/* Status badge */
.status-badge {
  display: inline-block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  padding: 2px 8px;
  border: 1px solid;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

.status-discovering { border-color: #FF9800; color: #FF9800; }
.status-active { border-color: #4CAF50; color: #4CAF50; }
.status-inactive { border-color: #666; color: #666; }
.status-failed { border-color: #F44336; color: #F44336; }

/* Data table */
.data-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.data-table th {
  text-align: left;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #666;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  padding: 8px 12px;
  border-bottom: 1px solid #333;
}

.data-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #1a1a1a;
  color: #CCC;
}

.page-row {
  cursor: pointer;
  transition: background 0.15s;
}

.page-row:hover {
  background: #1a1a1a;
}

.row-expanded {
  background: #141414;
}

.path-cell {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 500;
  color: #e8e8e8;
}

.mono-cell {
  font-family: 'JetBrains Mono', monospace;
}

.ts-cell {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #999;
}

.expand-cell {
  text-align: right;
  width: 30px;
}

.expand-icon {
  font-size: 0.6rem;
  color: #666;
}

/* Type tag */
.type-tag {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  padding: 2px 6px;
  background: #1a1a1a;
  border: 1px solid #333;
  color: #999;
  white-space: nowrap;
}

/* Significance badges */
.sig-badge {
  display: inline-block;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  padding: 2px 8px;
  border: 1px solid;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  font-weight: 600;
}

.sig-badge.small {
  font-size: 0.6rem;
  padding: 1px 6px;
}

.sig-critical { border-color: #ef4444; color: #ef4444; background: rgba(239, 68, 68, 0.08); }
.sig-high { border-color: #f97316; color: #f97316; background: rgba(249, 115, 22, 0.08); }
.sig-moderate { border-color: #eab308; color: #eab308; background: rgba(234, 179, 8, 0.08); }
.sig-low { border-color: #22c55e; color: #22c55e; background: rgba(34, 197, 94, 0.08); }
.sig-none { border-color: #666; color: #666; background: rgba(102, 102, 102, 0.05); }

/* History panel */
.history-row td {
  padding: 0;
  border-bottom: 1px solid #222;
}

.history-panel {
  background: #0e0e0e;
  padding: 16px 20px;
  border-top: 1px solid #222;
}

/* Timeline */
.timeline {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.timeline-entry {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: #141414;
  border: 1px solid #222;
  transition: border-color 0.15s;
}

.timeline-entry:hover {
  border-color: #333;
}

.timeline-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.timeline-date {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #999;
  min-width: 120px;
}

.timeline-summary {
  font-family: 'Space Grotesk', system-ui, sans-serif;
  font-size: 0.85rem;
  color: #ccc;
}

.btn-view-diff {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  padding: 4px 12px;
  background: transparent;
  border: 1px solid #FF4500;
  color: #FF4500;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  white-space: nowrap;
}

.btn-view-diff:hover {
  background: #FF4500;
  color: #FFFFFF;
}

/* Diff viewer */
.diff-viewer {
  margin-top: 16px;
  border: 1px solid #333;
  background: #0a0a0a;
}

.diff-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 14px;
  background: #141414;
  border-bottom: 1px solid #333;
}

.diff-title {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  color: #999;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.btn-close-diff {
  font-size: 1.1rem;
  background: none;
  border: none;
  color: #666;
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
}

.btn-close-diff:hover {
  color: #e8e8e8;
}

.diff-content {
  padding: 12px 0;
  max-height: 500px;
  overflow-y: auto;
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.78rem;
  line-height: 1.6;
}

.diff-line {
  padding: 1px 14px;
  white-space: pre-wrap;
  word-break: break-word;
}

.diff-line.context {
  color: #888;
}

.diff-line.added {
  background: rgba(34, 197, 94, 0.1);
  color: #22c55e;
}

.diff-line.removed {
  background: rgba(239, 68, 68, 0.1);
  color: #ef4444;
}

.diff-line-prefix {
  display: inline-block;
  width: 16px;
  color: inherit;
  opacity: 0.6;
  user-select: none;
}

.diff-line-text {
  color: inherit;
}

/* Responsive */
@media (max-width: 768px) {
  .data-table {
    display: block;
    overflow-x: auto;
  }

  .timeline-entry {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .timeline-left {
    gap: 8px;
  }

  .timeline-date {
    min-width: auto;
  }

  .site-url {
    font-size: 1.2rem;
    word-break: break-all;
  }
}
</style>
