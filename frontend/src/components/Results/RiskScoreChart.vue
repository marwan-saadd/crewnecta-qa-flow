<script setup lang="ts">
import type { RiskScore } from '~/types/flow'
import { priorityColor } from '~/utils/formatters'

const props = defineProps<{
  riskScores: RiskScore[]
}>()

const chartOptions = computed(() => ({
  chart: {
    type: 'bar' as const,
    background: 'transparent',
    toolbar: { show: false },
  },
  theme: { mode: 'dark' as const },
  plotOptions: {
    bar: {
      borderRadius: 4,
      distributed: true,
    },
  },
  colors: props.riskScores.map((r) => priorityColor(r.priority_for_review)),
  xaxis: {
    categories: props.riskScores.map((r) => r.interaction_id),
    labels: { style: { colors: '#9ca3af', fontSize: '10px' }, rotate: -45 },
  },
  yaxis: {
    max: 1,
    labels: { style: { colors: '#9ca3af' } },
    title: { text: 'Risk Score', style: { color: '#9ca3af' } },
  },
  grid: { borderColor: '#374151' },
  legend: { show: false },
  tooltip: {
    theme: 'dark',
    y: { formatter: (val: number) => val.toFixed(2) },
  },
}))

const series = computed(() => [
  {
    name: 'Risk Score',
    data: props.riskScores.map((r) => r.risk_score),
  },
])
</script>

<template>
  <div class="rounded-lg border border-gray-800 bg-gray-900/40 p-4">
    <h3 class="text-sm font-semibold text-white mb-3">Risk Score Distribution</h3>
    <ClientOnly>
      <apexchart type="bar" height="280" :options="chartOptions" :series="series" />
    </ClientOnly>

    <!-- Data table -->
    <div class="mt-4 overflow-x-auto">
      <table class="w-full text-xs">
        <thead>
          <tr class="text-gray-500 border-b border-gray-800">
            <th class="text-left py-2 px-2">Interaction</th>
            <th class="text-left py-2 px-2">Score</th>
            <th class="text-left py-2 px-2">Priority</th>
            <th class="text-left py-2 px-2">Risk Factors</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in riskScores" :key="r.interaction_id" class="border-b border-gray-800/50">
            <td class="py-1.5 px-2 text-gray-300">{{ r.interaction_id }}</td>
            <td class="py-1.5 px-2 text-gray-300">{{ r.risk_score.toFixed(2) }}</td>
            <td class="py-1.5 px-2">
              <span
                :class="[
                  'px-1.5 py-0.5 rounded text-xs',
                  r.priority_for_review === 'high' ? 'bg-red-500/20 text-red-300' : '',
                  r.priority_for_review === 'medium' ? 'bg-yellow-500/20 text-yellow-300' : '',
                  r.priority_for_review === 'low' ? 'bg-green-500/20 text-green-300' : '',
                ]"
              >{{ r.priority_for_review }}</span>
            </td>
            <td class="py-1.5 px-2 text-gray-500 max-w-[200px] truncate">{{ r.risk_factors.join(', ') }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
