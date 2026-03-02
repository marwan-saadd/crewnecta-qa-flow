import type { FlowStep, FlowStepStatus } from '~/types/flow'

const PIPELINE_STEPS: Omit<FlowStep, 'status' | 'summary' | 'events' | 'activeAgent'>[] = [
  { id: 'risk_scoring', label: 'Risk Scoring', method_name: 'ingest_and_risk_score' },
  { id: 'qa_analysis', label: 'QA Analysis', method_name: 'deep_qa_analysis' },
  { id: 'compliance_router', label: 'Compliance Router', method_name: 'route_by_compliance' },
  { id: 'escalation', label: 'Compliance Escalation', method_name: 'handle_compliance_escalation' },
  { id: 'patterns', label: 'Pattern Detection', method_name: 'detect_patterns' },
  { id: 'coaching', label: 'Coaching Plans', method_name: 'generate_coaching_plans' },
  { id: 'report', label: 'Final Report', method_name: 'compile_final_report' },
]

export function useFlowState() {
  const steps = ref<FlowStep[]>(
    PIPELINE_STEPS.map((s) => ({
      ...s,
      status: 'pending' as FlowStepStatus,
      summary: null,
      events: [],
      activeAgent: null,
    })),
  )

  function getStepByMethod(methodName: string): FlowStep | undefined {
    return steps.value.find((s) => s.method_name === methodName)
  }

  function updateStepStatus(methodName: string, status: FlowStepStatus, summary?: string): void {
    const step = getStepByMethod(methodName)
    if (step) {
      step.status = status
      if (summary) step.summary = summary
    }
  }

  function setStepAgent(methodName: string, agentName: string | null): void {
    const step = getStepByMethod(methodName)
    if (step) step.activeAgent = agentName
  }

  function resetSteps(): void {
    steps.value.forEach((s) => {
      s.status = 'pending'
      s.summary = null
      s.events = []
      s.activeAgent = null
    })
  }

  const currentStep = computed(() => steps.value.find((s) => s.status === 'running'))

  return { steps, getStepByMethod, updateStepStatus, setStepAgent, resetSteps, currentStep }
}
