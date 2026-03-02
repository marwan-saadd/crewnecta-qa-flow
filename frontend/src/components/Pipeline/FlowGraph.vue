<script setup lang="ts">
import { VueFlow } from '@vue-flow/core'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import dagre from 'dagre'
import type { FlowStep } from '~/types/flow'
import StepNode from './StepNode.vue'

const props = defineProps<{
  steps: FlowStep[]
  routeBranch: string | null
}>()

const edgeDefs = [
  { from: 'risk_scoring', to: 'qa_analysis' },
  { from: 'qa_analysis', to: 'compliance_router' },
  { from: 'compliance_router', to: 'escalation' },
  { from: 'compliance_router', to: 'patterns' },
  { from: 'escalation', to: 'patterns' },
  { from: 'patterns', to: 'coaching' },
  { from: 'coaching', to: 'report' },
]

const graphData = computed(() => {
  const g = new dagre.graphlib.Graph()
  g.setDefaultEdgeLabel(() => ({}))
  g.setGraph({ rankdir: 'LR', nodesep: 40, ranksep: 80 })

  const stepIds = props.steps.map((s) => s.id)

  for (const step of props.steps) {
    g.setNode(step.id, { width: 180, height: 70 })
  }

  for (const e of edgeDefs) {
    if (stepIds.includes(e.from) && stepIds.includes(e.to)) {
      g.setEdge(e.from, e.to)
    }
  }

  dagre.layout(g)

  const nodes = props.steps.map((step) => {
    const pos = g.node(step.id)
    return {
      id: step.id,
      type: 'step',
      position: { x: pos.x - 90, y: pos.y - 35 },
      data: {
        label: step.label,
        status: step.status,
        activeAgent: step.activeAgent,
        summary: step.summary,
        isRouter: step.id === 'compliance_router',
      },
    }
  })

  const edges = edgeDefs
    .filter((e) => stepIds.includes(e.from) && stepIds.includes(e.to))
    .map((e) => {
      const sourceStep = props.steps.find((s) => s.id === e.from)
      const targetStep = props.steps.find((s) => s.id === e.to)

      let animated = false
      let style: Record<string, string> = { stroke: '#4b5563' }

      if (sourceStep?.status === 'running' || targetStep?.status === 'running') {
        animated = true
        style = { stroke: '#3b82f6' }
      }

      if (sourceStep?.status === 'completed' && targetStep?.status !== 'pending') {
        style = { stroke: '#22c55e' }
      }

      if (e.from === 'compliance_router' && props.routeBranch) {
        if (e.to === 'escalation' && props.routeBranch !== 'compliance_escalation') {
          style = { stroke: '#1f2937', strokeDasharray: '5 5' }
        }
        if (e.to === 'patterns' && props.routeBranch === 'compliance_escalation') {
          style = { stroke: '#1f2937', strokeDasharray: '5 5' }
        }
      }

      return {
        id: `${e.from}-${e.to}`,
        source: e.from,
        target: e.to,
        animated,
        style,
      }
    })

  return { nodes, edges }
})

const nodeTypes = { step: markRaw(StepNode) }
</script>

<template>
  <div class="h-[220px] rounded-lg border border-gray-800 bg-gray-900/40 overflow-hidden">
    <VueFlow
      :nodes="graphData.nodes"
      :edges="graphData.edges"
      :node-types="nodeTypes"
      :default-viewport="{ x: 20, y: 20, zoom: 0.85 }"
      :pan-on-drag="true"
      :zoom-on-scroll="false"
      :prevent-scrolling="false"
      fit-view-on-init
    />
  </div>
</template>
