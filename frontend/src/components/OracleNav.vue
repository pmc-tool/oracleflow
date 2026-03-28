<template>
  <nav class="oracle-nav">
    <div class="nav-top-row">
      <div class="nav-logo">OracleFlow</div>
      <button class="bell-btn" @click="showNotifications = true">
        <span class="bell-icon">&#128276;</span>
        <span v-if="unreadCount > 0" class="bell-badge">{{ unreadCount > 99 ? '99+' : unreadCount }}</span>
      </button>
    </div>

    <div class="nav-section-label">INTELLIGENCE</div>
    <div class="nav-links">
      <router-link to="/intel" class="nav-link" active-class="active">
        <span class="nav-icon">&#9636;</span>
        <span>Dashboard</span>
      </router-link>
      <router-link to="/sites" class="nav-link" active-class="active">
        <span class="nav-icon">&#9673;</span>
        <span>Sites</span>
      </router-link>
      <router-link to="/signals" class="nav-link" active-class="active">
        <span class="nav-icon">&#9655;</span>
        <span>Signals</span>
      </router-link>
      <router-link to="/entities" class="nav-link" active-class="active">
        <span class="nav-icon">&#9670;</span>
        <span>Entities</span>
      </router-link>
      <router-link to="/countries" class="nav-link" active-class="active">
        <span class="nav-icon">&#9728;</span>
        <span>Countries</span>
      </router-link>
    </div>

    <div class="nav-divider"></div>

    <div class="nav-section-label">SIMULATION</div>
    <div class="nav-links">
      <router-link to="/simulations" class="nav-link" active-class="active">
        <span class="nav-icon">&#9776;</span>
        <span>Simulations</span>
      </router-link>
      <router-link to="/simulate" class="nav-link nav-sub-link" active-class="active">
        <span class="nav-icon">&#9881;</span>
        <span>New Simulation</span>
      </router-link>
      <router-link to="/simulate/advanced" class="nav-link nav-sub-link" active-class="active">
        <span class="nav-icon">&#9998;</span>
        <span>Advanced (Upload)</span>
      </router-link>
    </div>

    <div class="nav-divider"></div>
    <div class="nav-section-label">ACCOUNT</div>
    <div class="nav-links">
      <router-link to="/settings" class="nav-link" active-class="active">
        <span class="nav-icon">&#9881;</span>
        <span>Settings</span>
      </router-link>
    </div>

    <div class="nav-footer">
      <button class="nav-signout-btn" @click="handleSignOut">Sign Out</button>
      <span class="nav-version">v0.1.0</span>
    </div>
    <NotificationPanel
      :visible="showNotifications"
      @close="showNotifications = false"
      @countUpdated="(c) => unreadCount = c"
    />
  </nav>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { getUnreadCount } from '../api/intelligence'
import NotificationPanel from './NotificationPanel.vue'

const router = useRouter()

const showNotifications = ref(false)
const unreadCount = ref(0)
let pollTimer = null
let evtSource = null

async function fetchUnreadCount() {
  try {
    const res = await getUnreadCount()
    const d = res.data || res
    unreadCount.value = d.unread ?? 0
  } catch (e) {
    // Silently ignore polling errors
  }
}

function initSSE() {
  // Use Server-Sent Events for real-time updates (no npm dependency needed)
  try {
    evtSource = new EventSource('/api/events/stream')
    evtSource.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data)
        if (payload.type === 'notification') {
          // Increment unread count immediately on new notification
          unreadCount.value += 1
        } else if (payload.type === 'signal') {
          // New high-anomaly signal arrived — could show a toast or badge
          // For now, just bump the unread count as a notification is likely incoming
        }
      } catch (e) {
        // Ignore malformed SSE data
      }
    }
    evtSource.onerror = () => {
      // SSE connection lost — fall back to polling
      if (evtSource) {
        evtSource.close()
        evtSource = null
      }
      // Start polling as fallback
      if (!pollTimer) {
        pollTimer = setInterval(fetchUnreadCount, 60000)
      }
    }
  } catch (e) {
    // EventSource not supported or failed — use polling fallback
    pollTimer = setInterval(fetchUnreadCount, 60000)
  }
}

onMounted(() => {
  fetchUnreadCount()
  initSSE()
  // If SSE didn't start, polling is already set up by the error handler.
  // But also set a slow fallback poll (every 5 min) for count accuracy.
  pollTimer = setInterval(fetchUnreadCount, 300000)
})

onBeforeUnmount(() => {
  if (pollTimer) clearInterval(pollTimer)
  if (evtSource) {
    evtSource.close()
    evtSource = null
  }
})

function handleSignOut() {
  localStorage.removeItem('of_token')
  localStorage.removeItem('of_user')
  localStorage.removeItem('of_onboarding_done')
  window.location.href = '/login'
}
</script>

<style scoped>
.oracle-nav {
  width: 220px;
  min-width: 220px;
  height: 100vh;
  background: #000000;
  border-right: 1px solid #333;
  display: flex;
  flex-direction: column;
  padding: 20px 0;
  position: sticky;
  top: 0;
}

.nav-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px 25px;
}

.nav-logo {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 800;
  font-size: 1.1rem;
  color: #FF4500;
  letter-spacing: 1px;
}

.bell-btn {
  position: relative;
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  line-height: 1;
}

.bell-icon {
  font-size: 1.2rem;
  filter: grayscale(1) brightness(1.5);
  transition: filter 0.15s;
}

.bell-btn:hover .bell-icon {
  filter: grayscale(0);
}

.bell-badge {
  position: absolute;
  top: -4px;
  right: -6px;
  background: #ff2222;
  color: #fff;
  font-size: 0.6rem;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  min-width: 16px;
  height: 16px;
  line-height: 16px;
  text-align: center;
  border-radius: 8px;
  padding: 0 4px;
}

.nav-links {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 20px;
  color: #FFFFFF;
  text-decoration: none;
  font-family: 'Space Grotesk', system-ui, sans-serif;
  font-size: 0.9rem;
  font-weight: 400;
  transition: background 0.15s;
  border-left: 3px solid transparent;
}

.nav-link:hover {
  background: #111;
}

.nav-link.active {
  border-left-color: #FF4500;
  background: #111;
  font-weight: 600;
}

.nav-sub-link {
  padding-left: 34px;
  font-size: 0.82rem;
  opacity: 0.75;
}

.nav-sub-link:hover,
.nav-sub-link.active {
  opacity: 1;
}

.nav-icon {
  font-size: 1rem;
  width: 20px;
  text-align: center;
  line-height: 1;
}

.nav-divider {
  height: 1px;
  background: #333;
  margin: 15px 20px;
}

.nav-section-label {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.65rem;
  color: #666;
  padding: 8px 20px 4px;
  letter-spacing: 2px;
  font-weight: 600;
}

.nav-footer {
  padding: 15px 20px;
  border-top: 1px solid #333;
  margin-top: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.nav-signout-btn {
  background: none;
  border: none;
  color: #cc3333;
  font-family: 'Space Grotesk', system-ui, sans-serif;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  text-align: left;
  padding: 0;
  opacity: 0.7;
  transition: opacity 0.15s, color 0.15s;
}

.nav-signout-btn:hover {
  opacity: 1;
  color: #ff4444;
}

.nav-version {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  color: #555;
}
</style>
