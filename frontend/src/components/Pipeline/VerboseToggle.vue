<script setup lang="ts">
import { Eye, EyeOff } from 'lucide-vue-next'

const verbose = defineModel<boolean>({ required: true })
</script>

<template>
  <button
    class="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-colors"
    :class="verbose ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' : 'bg-gray-800 text-gray-400 border border-gray-700 hover:border-gray-600'"
    @click="verbose = !verbose"
  >
    <Eye v-if="verbose" class="h-3.5 w-3.5" />
    <EyeOff v-else class="h-3.5 w-3.5" />
    {{ verbose ? 'Verbose' : 'Summary' }}
  </button>
</template>
