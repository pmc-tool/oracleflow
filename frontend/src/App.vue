<template>
  <OracleLayout v-if="!isAuthRoute">
    <router-view />
    <OnboardingGuide />
  </OracleLayout>
  <router-view v-else />
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import OracleLayout from './components/OracleLayout.vue'
import OnboardingGuide from './components/OnboardingGuide.vue'

const route = useRoute()

const publicRoutes = ['/login', '/register', '/forgot-password', '/terms', '/privacy']
const isAuthRoute = computed(() => route.path === '/' || publicRoutes.some(r => route.path.startsWith(r)))
</script>

<style>
/* Global style reset */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: 'JetBrains Mono', 'Space Grotesk', 'Noto Sans SC', monospace;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #e8e8e8;
  background-color: #0a0a0a;
}

::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
  background: #000000;
}

::-webkit-scrollbar-thumb:hover {
  background: #333333;
}

button {
  font-family: inherit;
}
</style>
