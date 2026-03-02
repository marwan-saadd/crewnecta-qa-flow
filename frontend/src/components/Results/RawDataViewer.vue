<script setup lang="ts">
import { Download, Copy, Check } from 'lucide-vue-next'
import type { QAAuditorState } from '~/types/flow'

const props = defineProps<{
  state: QAAuditorState
}>()

const copied = ref(false)

const jsonString = computed(() => JSON.stringify(props.state, null, 2))

function download() {
  const blob = new Blob([jsonString.value], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `qa-audit-results-${new Date().toISOString().split('T')[0]}.json`
  a.click()
  URL.revokeObjectURL(url)
}

async function copyToClipboard() {
  await navigator.clipboard.writeText(jsonString.value)
  copied.value = true
  setTimeout(() => { copied.value = false }, 2000)
}
</script>

<template>
  <div class="space-y-3">
    <div class="flex gap-2">
      <button
        class="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium bg-gray-800 text-gray-400 border border-gray-700 hover:border-gray-600 transition-colors"
        @click="download"
      >
        <Download class="h-3.5 w-3.5" />
        Download JSON
      </button>
      <button
        class="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium bg-gray-800 text-gray-400 border border-gray-700 hover:border-gray-600 transition-colors"
        @click="copyToClipboard"
      >
        <Check v-if="copied" class="h-3.5 w-3.5 text-green-400" />
        <Copy v-else class="h-3.5 w-3.5" />
        {{ copied ? 'Copied!' : 'Copy' }}
      </button>
    </div>

    <pre class="rounded-lg border border-gray-800 bg-gray-950 p-4 text-xs text-gray-400 font-mono max-h-[500px] overflow-auto whitespace-pre-wrap">{{ jsonString }}</pre>
  </div>
</template>
