<template>
  <Teleport to="body">
    <transition name="notif-overlay">
      <div v-if="visible" class="notif-overlay" @click.self="$emit('close')"></div>
    </transition>
    <transition name="notif-slide">
      <div v-if="visible" class="notif-panel">
        <div class="notif-header">
          <h3>Notifications</h3>
          <button class="mark-all-btn" @click="handleMarkAllRead" :disabled="unreadCount === 0">
            Mark all read
          </button>
          <button class="close-btn" @click="$emit('close')">&times;</button>
        </div>

        <div class="notif-list" ref="listRef" @scroll="handleScroll">
          <div v-if="loading && notifications.length === 0" class="notif-empty">
            Loading...
          </div>
          <div v-else-if="notifications.length === 0" class="notif-empty">
            No notifications yet.
          </div>
          <div
            v-for="n in notifications"
            :key="n.id"
            class="notif-card"
            :class="{ unread: n.is_read === 0 }"
            @click="handleClick(n)"
          >
            <span class="severity-dot" :class="severityClass(n.severity)"></span>
            <div class="notif-body">
              <div class="notif-title">{{ n.title }}</div>
              <div class="notif-message" v-if="n.message">{{ truncate(n.message, 120) }}</div>
              <div class="notif-time">{{ relativeTime(n.created_at) }}</div>
            </div>
            <span v-if="n.is_read === 0" class="unread-dot"></span>
          </div>
          <div v-if="loading && notifications.length > 0" class="notif-loading-more">
            Loading more...
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup>
import { ref, watch, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { getNotifications, markNotificationRead, markAllNotificationsRead } from '../api/intelligence'

const props = defineProps({
  visible: { type: Boolean, default: false }
})
const emit = defineEmits(['close', 'countUpdated'])

const router = useRouter()

const notifications = ref([])
const loading = ref(false)
const page = ref(1)
const hasMore = ref(true)
const unreadCount = ref(0)
const listRef = ref(null)

async function fetchNotifications(resetList = false) {
  if (loading.value) return
  loading.value = true
  try {
    if (resetList) {
      page.value = 1
      hasMore.value = true
    }
    const raw = await getNotifications({ page: page.value, per_page: 20 })
    // Axios interceptor unwraps response.data → raw = { success, data, unread, total }
    // But raw.data could be the array OR another wrapper
    let items, total, unread
    if (Array.isArray(raw)) {
      items = raw; total = raw.length; unread = 0
    } else if (Array.isArray(raw.data)) {
      items = raw.data; total = raw.total ?? raw.data.length; unread = raw.unread ?? 0
    } else if (raw.data && Array.isArray(raw.data.data)) {
      items = raw.data.data; total = raw.data.total ?? items.length; unread = raw.data.unread ?? 0
    } else {
      items = []; total = 0; unread = 0
    }
    if (resetList) {
      notifications.value = items
    } else {
      notifications.value.push(...items)
    }
    unreadCount.value = unread
    emit('countUpdated', unread)
    if (notifications.value.length >= total) {
      hasMore.value = false
    }
  } catch (e) {
    console.error('Failed to fetch notifications', e)
  } finally {
    loading.value = false
  }
}

function handleScroll() {
  const el = listRef.value
  if (!el || !hasMore.value || loading.value) return
  if (el.scrollTop + el.clientHeight >= el.scrollHeight - 50) {
    page.value++
    fetchNotifications()
  }
}

async function handleClick(n) {
  if (n.is_read === 0) {
    try {
      await markNotificationRead(n.id)
      n.is_read = 1
      unreadCount.value = Math.max(0, unreadCount.value - 1)
      emit('countUpdated', unreadCount.value)
    } catch (e) {
      console.error('Failed to mark notification read', e)
    }
  }
  // Navigate to relevant page
  if (n.signal_id) {
    router.push('/signals')
  }
  emit('close')
}

async function handleMarkAllRead() {
  try {
    await markAllNotificationsRead()
    notifications.value.forEach(n => { n.is_read = 1 })
    unreadCount.value = 0
    emit('countUpdated', 0)
  } catch (e) {
    console.error('Failed to mark all read', e)
  }
}

function severityClass(severity) {
  const map = { critical: 'sev-critical', high: 'sev-high', medium: 'sev-medium', low: 'sev-low', info: 'sev-info' }
  return map[severity] || 'sev-info'
}

function truncate(text, len) {
  if (!text) return ''
  return text.length > len ? text.slice(0, len) + '...' : text
}

function relativeTime(isoStr) {
  if (!isoStr) return ''
  const now = Date.now()
  const then = new Date(isoStr).getTime()
  const diff = Math.max(0, now - then)
  const mins = Math.floor(diff / 60000)
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hours = Math.floor(mins / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 30) return `${days}d ago`
  return new Date(isoStr).toLocaleDateString()
}

watch(() => props.visible, (val) => {
  if (val) fetchNotifications(true)
})
</script>

<style scoped>
.notif-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 10000;
}

.notif-panel {
  position: fixed;
  top: 0;
  right: 0;
  width: 400px;
  max-width: 100vw;
  height: 100vh;
  background: #0a0a0a;
  border-left: 1px solid #333;
  z-index: 10001;
  display: flex;
  flex-direction: column;
  font-family: 'Space Grotesk', system-ui, sans-serif;
}

.notif-header {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #333;
  gap: 12px;
}

.notif-header h3 {
  margin: 0;
  font-size: 1rem;
  color: #fff;
  flex: 1;
  font-family: 'JetBrains Mono', monospace;
}

.mark-all-btn {
  background: none;
  border: 1px solid #444;
  color: #aaa;
  font-size: 0.75rem;
  padding: 4px 10px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.15s;
}

.mark-all-btn:hover:not(:disabled) {
  color: #fff;
  border-color: #FF4500;
}

.mark-all-btn:disabled {
  opacity: 0.3;
  cursor: default;
}

.close-btn {
  background: none;
  border: none;
  color: #888;
  font-size: 1.4rem;
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
}

.close-btn:hover {
  color: #fff;
}

.notif-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.notif-empty,
.notif-loading-more {
  text-align: center;
  color: #666;
  padding: 40px 20px;
  font-size: 0.85rem;
}

.notif-loading-more {
  padding: 12px 20px;
}

.notif-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 20px;
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid #1a1a1a;
}

.notif-card:hover {
  background: #111;
}

.notif-card.unread {
  background: #0d0d0d;
  border-left: 3px solid #FF4500;
}

.severity-dot {
  width: 10px;
  height: 10px;
  min-width: 10px;
  border-radius: 50%;
  margin-top: 5px;
}

.sev-critical { background: #ff2222; }
.sev-high { background: #ff6600; }
.sev-medium { background: #ffaa00; }
.sev-low { background: #44bb44; }
.sev-info { background: #4488ff; }

.notif-body {
  flex: 1;
  min-width: 0;
}

.notif-title {
  color: #eee;
  font-size: 0.85rem;
  font-weight: 600;
  line-height: 1.3;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.notif-message {
  color: #888;
  font-size: 0.78rem;
  line-height: 1.4;
  margin-bottom: 4px;
}

.notif-time {
  color: #555;
  font-size: 0.7rem;
  font-family: 'JetBrains Mono', monospace;
}

.unread-dot {
  width: 8px;
  height: 8px;
  min-width: 8px;
  border-radius: 50%;
  background: #FF4500;
  margin-top: 6px;
}

/* Transitions */
.notif-overlay-enter-active,
.notif-overlay-leave-active {
  transition: opacity 0.2s;
}
.notif-overlay-enter-from,
.notif-overlay-leave-to {
  opacity: 0;
}

.notif-slide-enter-active,
.notif-slide-leave-active {
  transition: transform 0.25s ease;
}
.notif-slide-enter-from,
.notif-slide-leave-to {
  transform: translateX(100%);
}
</style>
