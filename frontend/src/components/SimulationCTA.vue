<template>
  <Transition name="cta-slide">
    <div v-if="showBanner" class="simulation-cta">
      <div class="cta-content">
        <span class="cta-text">
          You have 1 free simulation. Try it on a real scenario
        </span>
        <router-link to="/simulate" class="cta-link">&rarr;</router-link>
      </div>
      <button class="cta-dismiss" @click="dismissBanner" title="Dismiss">&times;</button>
    </div>
  </Transition>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { listSimulations } from '../api/intelligence'

const DISMISS_KEY = 'of_simulation_cta_dismissed'

const props = defineProps({
  maxSimulations: {
    type: Number,
    default: 0
  }
})

const showBanner = ref(false)

function dismissBanner() {
  showBanner.value = false
  localStorage.setItem(DISMISS_KEY, 'true')
}

onMounted(async () => {
  // Don't show if dismissed or plan doesn't allow simulations
  if (localStorage.getItem(DISMISS_KEY)) return
  if (props.maxSimulations <= 0) return

  // Check if user has already run a simulation
  try {
    const res = await listSimulations()
    const data = res.data || res
    const sims = Array.isArray(data) ? data : (data.items || data.results || [])
    if (sims.length > 0) return // Already ran one
  } catch {
    // If API fails, still show the CTA
  }

  showBanner.value = true
})
</script>

<style scoped>
.simulation-cta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 16px;
  background: linear-gradient(90deg, #FF4500 0%, #e03e00 100%);
  font-family: 'JetBrains Mono', monospace;
  flex-shrink: 0;
}

.cta-content {
  display: flex;
  align-items: center;
  gap: 8px;
}

.cta-text {
  font-size: 12px;
  font-weight: 600;
  color: #ffffff;
  letter-spacing: 0.3px;
}

.cta-link {
  color: #ffffff;
  font-size: 16px;
  font-weight: 700;
  text-decoration: none;
  transition: transform 0.2s;
  display: inline-block;
}

.cta-link:hover {
  transform: translateX(3px);
}

.cta-dismiss {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.7);
  font-size: 18px;
  cursor: pointer;
  padding: 0 4px;
  line-height: 1;
  transition: color 0.2s;
}

.cta-dismiss:hover {
  color: #ffffff;
}

/* Transition */
.cta-slide-enter-active,
.cta-slide-leave-active {
  transition: all 0.3s ease;
}

.cta-slide-enter-from,
.cta-slide-leave-to {
  opacity: 0;
  max-height: 0;
  padding-top: 0;
  padding-bottom: 0;
  overflow: hidden;
}

.cta-slide-enter-to,
.cta-slide-leave-from {
  max-height: 50px;
}
</style>
