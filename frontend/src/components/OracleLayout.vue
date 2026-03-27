<template>
  <div class="oracle-layout">
    <OracleNav />
    <main class="oracle-main" :class="{ 'dark-mode': isDarkRoute, 'intel-full': isIntelRoute }">
      <slot />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import OracleNav from './OracleNav.vue'

const route = useRoute()
const isDarkRoute = true
const isIntelRoute = computed(() => route.path.startsWith('/intel'))
</script>

<style scoped>
.oracle-layout {
  display: flex;
  flex-direction: row;
  min-height: 100vh;
}

.oracle-main {
  flex-grow: 1;
  overflow-y: auto;
  overflow-x: hidden;
  height: 100vh;
  min-width: 0;
}

.oracle-main.dark-mode {
  background: #000000;
  color: #FFFFFF;
  padding: 30px;
}

.oracle-main.intel-full {
  padding: 0;
  overflow: hidden;
}

/* Legacy layout overrides (no longer needed) */
</style>
