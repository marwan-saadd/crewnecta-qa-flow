<script setup lang="ts">
defineProps<{
  label: string
  value: string | number
  color?: string
  subtitle?: string
}>()
</script>

<template>
  <div class="rounded-lg border border-gray-800 bg-gray-900/60 p-4">
    <p class="text-xs text-gray-500 uppercase tracking-wider">{{ label }}</p>
    <p class="text-2xl font-bold mt-1" :class="color ? `text-${color}-400` : 'text-white'">
      {{ value }}
    </p>
    <p v-if="subtitle" class="text-xs text-gray-500 mt-0.5">{{ subtitle }}</p>
  </div>
</template>
