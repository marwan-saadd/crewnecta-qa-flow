import { defineStore } from 'pinia'
import type { QAAuditorState, FlowStep, FlowStepStatus } from '~/types/flow'
import type { WSMessage } from '~/types/events'

export const useFlowStore = defineStore('flow', () => {
  // --- State ---
  const runId = ref<string | null>(null)
  const flowStatus = ref<'idle' | 'running' | 'completed' | 'failed'>('idle')
  const steps = ref<FlowStep[]>(createInitialSteps())
  const state = ref<QAAuditorState | null>(null)
  const verboseEnabled = ref(false)
  const events = ref<WSMessage[]>([])
  const activeAgent = ref<string | null>(null)
  const routeBranch = ref<string | null>(null)

  // --- Computed ---
  const currentStep = computed(() => steps.value.find((s) => s.status === 'running'))
  const isRunning = computed(() => flowStatus.value === 'running')
  const isCompleted = computed(() => flowStatus.value === 'completed')
  const results = computed(() => state.value)

  const filteredEvents = computed(() => {
    if (verboseEnabled.value) return events.value
    return events.value.filter((e) => !e.verbose_only)
  })

  // --- Actions ---
  function startRun(id: string): void {
    runId.value = id
    flowStatus.value = 'running'
    steps.value = createInitialSteps()
    state.value = null
    events.value = []
    activeAgent.value = null
    routeBranch.value = null
  }

  function handleEvent(event: WSMessage): void {
    events.value.push(event)

    switch (event.type) {
      case 'flow_started':
        flowStatus.value = 'running'
        break

      case 'flow_finished':
        flowStatus.value = 'completed'
        break

      case 'step_started': {
        const methodName = event.data.method_name as string
        updateStep(methodName, 'running')
        // Push event to the step
        const step = findStep(methodName)
        if (step) step.events.push(event)
        break
      }

      case 'step_finished':
      case 'step_completed': {
        const methodName = event.data.method_name as string
        const summary = (event.data.summary as string) || null
        updateStep(methodName, 'completed', summary)

        // Detect router branch
        if (methodName === 'route_by_compliance' && summary) {
          if (summary.toLowerCase().includes('escalation')) {
            routeBranch.value = 'compliance_escalation'
          } else {
            routeBranch.value = 'standard_analysis'
          }
        }

        const step = findStep(methodName)
        if (step) step.events.push(event)
        break
      }

      case 'step_failed': {
        const methodName = event.data.method_name as string
        updateStep(methodName, 'failed')
        const step = findStep(methodName)
        if (step) step.events.push(event)
        break
      }

      case 'agent_started':
        activeAgent.value = (event.data.agent_name as string) || null
        if (currentStep.value) {
          currentStep.value.activeAgent = activeAgent.value
          currentStep.value.events.push(event)
        }
        break

      case 'agent_completed':
        if (currentStep.value) {
          currentStep.value.events.push(event)
        }
        activeAgent.value = null
        break

      case 'tool_started':
      case 'tool_finished':
      case 'tool_error':
      case 'task_started':
      case 'task_completed':
      case 'crew_started':
      case 'crew_completed':
        if (currentStep.value) {
          currentStep.value.events.push(event)
        }
        break

      case 'state_snapshot':
        state.value = event.data as unknown as QAAuditorState
        break

      case 'run_status': {
        const status = event.data.status as string
        if (status === 'completed') {
          flowStatus.value = 'completed'
        } else if (status === 'failed') {
          flowStatus.value = 'failed'
        }
        break
      }
    }
  }

  function reset(): void {
    runId.value = null
    flowStatus.value = 'idle'
    steps.value = createInitialSteps()
    state.value = null
    events.value = []
    activeAgent.value = null
    verboseEnabled.value = false
    routeBranch.value = null
  }

  /**
   * Infer step progress from polled state (fallback when WS events are missed).
   * Called when state is fetched via GET /api/flow/{runId}/state.
   */
  function syncFromPolledState(polledState: QAAuditorState): void {
    state.value = polledState

    // Infer which steps have completed based on state contents
    if (polledState.risk_scores.length > 0) {
      updateStep('ingest_and_risk_score', 'completed',
        `Scored ${polledState.transcripts_processed} transcripts`)
    }
    if (polledState.qa_evaluations.length > 0) {
      updateStep('deep_qa_analysis', 'completed',
        `Avg score: ${polledState.average_scores?.overall?.toFixed(1) ?? 'N/A'}`)
    }
    if (polledState.qa_evaluations.length > 0 && (polledState.has_critical_violations || polledState.risk_scores.length > 0)) {
      // Router ran if we have evaluations and moved past QA analysis
      if (polledState.has_critical_violations) {
        updateStep('route_by_compliance', 'completed', 'Routing to escalation')
        routeBranch.value = 'compliance_escalation'
      } else if (polledState.pattern_insights.length > 0 || polledState.coaching_plans.length > 0 || polledState.processing_status === 'complete') {
        updateStep('route_by_compliance', 'completed', 'Standard analysis path')
        routeBranch.value = 'standard_analysis'
      }
    }
    if (polledState.compliance_escalation_report) {
      updateStep('handle_compliance_escalation', 'completed', 'Escalation report generated')
    }
    if (polledState.pattern_insights.length > 0) {
      updateStep('detect_patterns', 'completed',
        `${polledState.pattern_insights.length} patterns found`)
    }
    if (polledState.coaching_plans.length > 0) {
      updateStep('generate_coaching_plans', 'completed',
        `${polledState.coaching_plans.length} plans generated`)
    }
    if (polledState.processing_status === 'complete') {
      updateStep('compile_final_report', 'completed', 'Reports compiled')
    }
  }

  // --- Helpers ---
  function findStep(methodName: string): FlowStep | undefined {
    return steps.value.find((s) => s.method_name === methodName)
  }

  function updateStep(methodName: string, status: FlowStepStatus, summary?: string): void {
    const step = findStep(methodName)
    if (step) {
      step.status = status
      if (summary) step.summary = summary
    }
  }

  return {
    runId,
    flowStatus,
    steps,
    state,
    verboseEnabled,
    events,
    activeAgent,
    routeBranch,
    currentStep,
    isRunning,
    isCompleted,
    results,
    filteredEvents,
    startRun,
    handleEvent,
    syncFromPolledState,
    reset,
  }
})

function createInitialSteps(): FlowStep[] {
  return [
    { id: 'risk_scoring', label: 'Risk Scoring', method_name: 'ingest_and_risk_score', status: 'pending', summary: null, events: [], activeAgent: null },
    { id: 'qa_analysis', label: 'QA Analysis', method_name: 'deep_qa_analysis', status: 'pending', summary: null, events: [], activeAgent: null },
    { id: 'compliance_router', label: 'Compliance Router', method_name: 'route_by_compliance', status: 'pending', summary: null, events: [], activeAgent: null },
    { id: 'escalation', label: 'Compliance Escalation', method_name: 'handle_compliance_escalation', status: 'pending', summary: null, events: [], activeAgent: null },
    { id: 'patterns', label: 'Pattern Detection', method_name: 'detect_patterns', status: 'pending', summary: null, events: [], activeAgent: null },
    { id: 'coaching', label: 'Coaching Plans', method_name: 'generate_coaching_plans', status: 'pending', summary: null, events: [], activeAgent: null },
    { id: 'report', label: 'Final Report', method_name: 'compile_final_report', status: 'pending', summary: null, events: [], activeAgent: null },
  ]
}
