<template>
  <div class="category-tabs">
    <button
      v-for="cat in allCategories"
      :key="cat"
      class="tab-pill"
      :class="{ active: modelValue === cat }"
      @click="$emit('update:modelValue', cat)"
    >
      {{ cat }}
    </button>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  categories: { type: Array, default: () => [] },
  modelValue: { type: String, default: 'All' }
})

defineEmits(['update:modelValue'])

const allCategories = computed(() => ['All', ...props.categories])
</script>

<style scoped>
.category-tabs {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.tab-pill {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.7rem;
  padding: 4px 12px;
  border: 1px solid #444;
  background: transparent;
  color: #999;
  cursor: pointer;
  transition: all 0.15s;
  letter-spacing: 0.5px;
}

.tab-pill:hover {
  border-color: #666;
  color: #CCC;
}

.tab-pill.active {
  background: #FF4500;
  border-color: #FF4500;
  color: #FFFFFF;
  font-weight: 600;
}
</style>
