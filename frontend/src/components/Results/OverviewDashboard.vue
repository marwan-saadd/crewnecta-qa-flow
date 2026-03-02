<script setup lang="ts">
import type { QAAuditorState } from '~/types/flow'

const props = defineProps<{
  state: QAAuditorState
}>()

const metrics = computed(() => [
  { label: 'Transcripts', value: props.state.raw_transcripts.length, color: 'sky' },
  { label: 'Avg Score', value: props.state.average_scores?.overall?.toFixed(1) ?? 'N/A', color: 'green' },
  { label: 'Critical Violations', value: props.state.critical_violations.length, color: 'red' },
  { label: 'Agents Coached', value: props.state.coaching_plans.length, color: 'purple' },
])
</script>

<template>
  <div class="space-y-6">
    <!-- Metric cards -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-3">
      <MetricCard
        v-for="m in metrics"
        :key="m.label"
        :label="m.label"
        :value="m.value"
        :color="m.color"
      />
    </div>

    <!-- Executive summary -->
    <div v-if="state.executive_summary" class="rounded-lg border border-gray-800 bg-gray-900/40 p-4">
      <h3 class="text-sm font-semibold text-white mb-3">Executive Summary</h3>
      <pre class="text-xs text-gray-400 whitespace-pre-wrap font-mono leading-relaxed">{{ state.executive_summary }}</pre>
    </div>

    <!-- Errors -->
    <div v-if="state.errors.length > 0" class="rounded-lg border border-red-900/50 bg-red-950/20 p-4">
      <h3 class="text-sm font-semibold text-red-300 mb-2">Errors ({{ state.errors.length }})</h3>
      <ul class="space-y-1">
        <li v-for="(err, i) in state.errors" :key="i" class="text-xs text-red-400">{{ err }}</li>
      </ul>
    </div>
  </div>
</template>
