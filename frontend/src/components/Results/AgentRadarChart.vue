<script setup lang="ts">
import type { QAEvaluation } from '~/types/flow'

const props = defineProps<{
  evaluations: QAEvaluation[]
}>()

// Group evaluations by agent_id and average their scores
const agentScores = computed(() => {
  const map = new Map<string, { count: number; compliance: number; empathy: number; resolution: number; process: number }>()

  for (const e of props.evaluations) {
    const existing = map.get(e.agent_id)
    if (existing) {
      existing.count++
      existing.compliance += e.compliance_score
      existing.empathy += e.empathy_score
      existing.resolution += e.resolution_score
      existing.process += e.process_adherence_score
    } else {
      map.set(e.agent_id, {
        count: 1,
        compliance: e.compliance_score,
        empathy: e.empathy_score,
        resolution: e.resolution_score,
        process: e.process_adherence_score,
      })
    }
  }

  return Array.from(map.entries()).map(([id, s]) => ({
    agent_id: id,
    compliance: s.compliance / s.count,
    empathy: s.empathy / s.count,
    resolution: s.resolution / s.count,
    process: s.process / s.count,
  }))
})

const chartOptions = computed(() => ({
  chart: {
    type: 'radar' as const,
    background: 'transparent',
    toolbar: { show: false },
  },
  theme: { mode: 'dark' as const },
  xaxis: {
    categories: ['Compliance', 'Empathy', 'Resolution', 'Process'],
    labels: { style: { colors: ['#9ca3af', '#9ca3af', '#9ca3af', '#9ca3af'], fontSize: '11px' } },
  },
  yaxis: { max: 100, show: false },
  stroke: { width: 2 },
  fill: { opacity: 0.15 },
  markers: { size: 3 },
  legend: {
    labels: { colors: '#9ca3af' },
    position: 'bottom' as const,
  },
  grid: { borderColor: '#374151' },
  colors: ['#3b82f6', '#ef4444', '#22c55e', '#f59e0b', '#a855f7'],
}))

const series = computed(() =>
  agentScores.value.map((a) => ({
    name: a.agent_id,
    data: [
      Math.round(a.compliance),
      Math.round(a.empathy),
      Math.round(a.resolution),
      Math.round(a.process),
    ],
  })),
)
</script>

<template>
  <div class="rounded-lg border border-gray-800 bg-gray-900/40 p-4">
    <h3 class="text-sm font-semibold text-white mb-3">Agent Score Comparison</h3>
    <ClientOnly>
      <apexchart type="radar" height="350" :options="chartOptions" :series="series" />
    </ClientOnly>

    <!-- Per-agent details -->
    <div class="mt-4 space-y-2">
      <details v-for="agent in agentScores" :key="agent.agent_id" class="group">
        <summary class="cursor-pointer text-xs text-gray-400 hover:text-gray-300 py-1">
          {{ agent.agent_id }} — Avg: {{ ((agent.compliance + agent.empathy + agent.resolution + agent.process) / 4).toFixed(1) }}
        </summary>
        <div class="pl-4 py-1 text-xs text-gray-500 grid grid-cols-2 gap-1">
          <span>Compliance: {{ agent.compliance.toFixed(1) }}</span>
          <span>Empathy: {{ agent.empathy.toFixed(1) }}</span>
          <span>Resolution: {{ agent.resolution.toFixed(1) }}</span>
          <span>Process: {{ agent.process.toFixed(1) }}</span>
        </div>
      </details>
    </div>
  </div>
</template>
