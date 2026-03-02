<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'
import { CheckCircle, Loader2, AlertCircle, Clock, GitBranch } from 'lucide-vue-next'
import type { FlowStepStatus } from '~/types/flow'

const props = defineProps<{
  data: {
    label: string
    status: FlowStepStatus
    activeAgent: string | null
    summary: string | null
    isRouter: boolean
  }
}>()

const statusConfig = computed(() => {
  const map: Record<FlowStepStatus, { bg: string; border: string; icon: typeof CheckCircle; pulse: boolean }> = {
    pending: { bg: 'bg-gray-800', border: 'border-gray-700', icon: Clock, pulse: false },
    running: { bg: 'bg-blue-900/40', border: 'border-blue-500', icon: Loader2, pulse: true },
    completed: { bg: 'bg-green-900/30', border: 'border-green-600', icon: CheckCircle, pulse: false },
    failed: { bg: 'bg-red-900/30', border: 'border-red-600', icon: AlertCircle, pulse: false },
  }
  return map[props.data.status]
})
</script>

<template>
  <div
    :class="[
      'px-4 py-3 rounded-lg border-2 min-w-[160px] transition-all duration-300',
      statusConfig.bg,
      statusConfig.border,
      statusConfig.pulse ? 'node-running' : '',
    ]"
  >
    <Handle type="target" :position="Position.Left" class="!bg-gray-600" />

    <div class="flex items-center gap-2">
      <GitBranch v-if="data.isRouter" class="h-4 w-4 text-purple-400 shrink-0" />
      <component
        :is="statusConfig.icon"
        v-else
        :class="[
          'h-4 w-4 shrink-0',
          data.status === 'running' ? 'animate-spin text-blue-400' : '',
          data.status === 'completed' ? 'text-green-400' : '',
          data.status === 'failed' ? 'text-red-400' : '',
          data.status === 'pending' ? 'text-gray-500' : '',
        ]"
      />
      <span class="text-sm font-medium text-white truncate">{{ data.label }}</span>
    </div>

    <div v-if="data.activeAgent" class="mt-1.5 text-xs text-blue-300 truncate">
      {{ data.activeAgent }}
    </div>

    <div v-if="data.summary" class="mt-1 text-xs text-gray-400 truncate">
      {{ data.summary }}
    </div>

    <Handle type="source" :position="Position.Right" class="!bg-gray-600" />
  </div>
</template>
