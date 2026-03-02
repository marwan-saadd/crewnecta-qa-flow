<script setup lang="ts">
import { Wrench, Bot, Cpu, MessageSquare } from 'lucide-vue-next'
import type { FlowStep } from '~/types/flow'
import type { WSMessage } from '~/types/events'

const props = defineProps<{
  step: FlowStep | null
  verbose: boolean
}>()

function eventIcon(type: string) {
  if (type.startsWith('agent')) return Bot
  if (type.startsWith('tool')) return Wrench
  if (type.startsWith('llm')) return Cpu
  return MessageSquare
}

function eventLabel(event: WSMessage): string {
  switch (event.type) {
    case 'agent_started': return `Agent: ${event.data.agent_name || 'Unknown'}`
    case 'agent_completed': return `Agent completed: ${event.data.agent_name || ''}`
    case 'tool_started': return `Tool: ${event.data.tool_name || 'Unknown'}`
    case 'tool_finished': return `Tool finished: ${event.data.tool_name || ''}`
    case 'tool_error': return `Tool error: ${event.data.error || ''}`
    case 'task_started': return `Task: ${(event.data.task_description as string)?.substring(0, 60) || ''}...`
    case 'task_completed': return 'Task completed'
    case 'crew_started': return `Crew started`
    case 'crew_completed': return 'Crew completed'
    case 'llm_call_started': return 'LLM call...'
    case 'llm_call_completed': return 'LLM response received'
    default: return event.type
  }
}

const visibleEvents = computed(() => {
  if (!props.step) return []
  const events = props.step.events
  if (props.verbose) return events
  return events.filter((e) => !e.verbose_only)
})
</script>

<template>
  <div class="rounded-lg border border-gray-800 bg-gray-900/40 p-4">
    <div v-if="!step" class="text-sm text-gray-500 text-center py-8">
      Waiting for flow to start...
    </div>

    <template v-else>
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-sm font-semibold text-white">{{ step.label }}</h3>
        <span
          :class="[
            'text-xs px-2 py-0.5 rounded-full',
            step.status === 'running' ? 'bg-blue-500/20 text-blue-300' : '',
            step.status === 'completed' ? 'bg-green-500/20 text-green-300' : '',
            step.status === 'failed' ? 'bg-red-500/20 text-red-300' : '',
            step.status === 'pending' ? 'bg-gray-700 text-gray-400' : '',
          ]"
        >
          {{ step.status }}
        </span>
      </div>

      <div v-if="step.activeAgent" class="text-xs text-blue-300 mb-2 flex items-center gap-1">
        <Bot class="h-3 w-3" />
        {{ step.activeAgent }}
      </div>

      <!-- Event log -->
      <div class="space-y-1.5 max-h-[300px] overflow-y-auto">
        <div
          v-for="(event, i) in visibleEvents"
          :key="i"
          class="flex items-start gap-2 text-xs"
        >
          <component :is="eventIcon(event.type)" class="h-3 w-3 mt-0.5 text-gray-500 shrink-0" />
          <span class="text-gray-400">{{ eventLabel(event) }}</span>
        </div>
        <div v-if="visibleEvents.length === 0" class="text-xs text-gray-600">
          No events yet...
        </div>
      </div>

      <div v-if="step.summary" class="mt-3 pt-2 border-t border-gray-800 text-xs text-gray-300">
        {{ step.summary }}
      </div>
    </template>
  </div>
</template>
