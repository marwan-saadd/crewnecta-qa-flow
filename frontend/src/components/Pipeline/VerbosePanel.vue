<script setup lang="ts">
import type { WSMessage } from '~/types/events'

const props = defineProps<{
  events: WSMessage[]
}>()

const container = ref<HTMLElement>()

// Auto-scroll to bottom
watch(() => props.events.length, () => {
  nextTick(() => {
    if (container.value) {
      container.value.scrollTop = container.value.scrollHeight
    }
  })
})

function formatEvent(event: WSMessage): string {
  const ts = new Date(event.timestamp).toLocaleTimeString()
  const data = JSON.stringify(event.data, null, 0)
  return `[${ts}] ${event.type}: ${data}`
}
</script>

<template>
  <div
    ref="container"
    class="rounded-lg border border-gray-800 bg-gray-950 p-3 font-mono text-xs text-gray-400 max-h-[250px] overflow-y-auto"
  >
    <div v-for="(event, i) in events" :key="i" class="whitespace-pre-wrap mb-0.5">
      <span
        :class="[
          event.type.includes('error') || event.type.includes('failed') ? 'text-red-400' : '',
          event.type.includes('completed') || event.type.includes('finished') ? 'text-green-400' : '',
          event.type.includes('started') ? 'text-blue-400' : '',
        ]"
      >{{ formatEvent(event) }}</span>
    </div>
    <div v-if="events.length === 0" class="text-gray-600">Waiting for events...</div>
  </div>
</template>
