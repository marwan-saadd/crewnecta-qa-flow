<script setup lang="ts">
import type { QAEvaluation, QAAuditorState } from '~/types/flow'

const props = defineProps<{
  state: QAAuditorState
}>()

const evaluationsWithIssues = computed(() =>
  props.state.qa_evaluations.filter(
    (e) => e.compliance_severity !== 'none' || e.compliance_issues.length > 0,
  ),
)
</script>

<template>
  <div class="space-y-4">
    <!-- Escalation report -->
    <div
      v-if="state.compliance_escalation_report"
      class="rounded-lg border border-red-900/50 bg-red-950/20 p-4"
    >
      <h3 class="text-sm font-semibold text-red-300 mb-2">Compliance Escalation Report</h3>
      <pre class="text-xs text-red-200/80 whitespace-pre-wrap font-mono">{{ state.compliance_escalation_report }}</pre>
    </div>

    <!-- Per-interaction compliance -->
    <div class="space-y-2">
      <div
        v-for="evaluation in state.qa_evaluations"
        :key="evaluation.interaction_id"
        class="rounded-lg border border-gray-800 bg-gray-900/40 p-3"
      >
        <div class="flex items-center justify-between mb-1">
          <span class="text-sm font-medium text-gray-300">{{ evaluation.interaction_id }}</span>
          <SeverityBadge :severity="evaluation.compliance_severity" />
        </div>
        <p class="text-xs text-gray-500 mb-1">Agent: {{ evaluation.agent_id }}</p>
        <p class="text-xs text-gray-500">Compliance Score: {{ evaluation.compliance_score.toFixed(1) }}</p>

        <div v-if="evaluation.compliance_issues.length > 0" class="mt-2">
          <p class="text-xs text-red-400 font-medium mb-1">Issues:</p>
          <ul class="space-y-0.5">
            <li
              v-for="(issue, i) in evaluation.compliance_issues"
              :key="i"
              class="text-xs text-red-300/80 pl-3 relative before:content-[''] before:absolute before:left-0 before:top-1.5 before:w-1.5 before:h-1.5 before:rounded-full before:bg-red-500/40"
            >
              {{ issue }}
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>
