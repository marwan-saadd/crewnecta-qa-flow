/** TypeScript types mirroring the Pydantic state models. */

export type ComplianceSeverity = 'critical' | 'major' | 'minor' | 'none'

export interface InteractionTranscript {
  interaction_id: string
  agent_id: string
  agent_name: string
  channel: string
  timestamp: string
  duration_seconds: number | null
  transcript_text: string
  customer_issue: string
  resolution_status: string
}

export interface RiskScore {
  interaction_id: string
  risk_score: number
  risk_factors: string[]
  priority_for_review: string
}

export interface QAEvaluation {
  interaction_id: string
  agent_id: string
  compliance_score: number
  empathy_score: number
  resolution_score: number
  process_adherence_score: number
  overall_score: number
  compliance_issues: string[]
  strengths: string[]
  improvement_areas: string[]
  compliance_severity: ComplianceSeverity
}

export interface PatternInsight {
  pattern_type: string
  description: string
  affected_agents: string[]
  frequency: string
  evidence_interaction_ids: string[]
  recommended_action: string
}

export interface CoachingPlan {
  agent_id: string
  agent_name: string
  overall_performance: string
  key_strengths: string[]
  priority_improvements: string[]
  specific_examples: string[]
  suggested_training: string[]
  follow_up_timeline: string
}

export interface QAAuditorState {
  raw_transcripts: InteractionTranscript[]
  campaign_name: string
  evaluation_period: string
  compliance_requirements: string[]
  risk_scores: RiskScore[]
  qa_evaluations: QAEvaluation[]
  pattern_insights: PatternInsight[]
  average_scores: Record<string, number>
  has_critical_violations: boolean
  critical_violations: Array<{
    interaction_id: string
    agent_id: string
    issues: string[]
  }>
  agents_needing_coaching: string[]
  coaching_plans: CoachingPlan[]
  compliance_escalation_report: string
  executive_summary: string
  detailed_qa_report: string
  errors: string[]
  processing_status: string
  transcripts_processed: number
  transcripts_failed: number
}

export type FlowStepStatus = 'pending' | 'running' | 'completed' | 'failed'

export interface FlowStep {
  id: string
  label: string
  method_name: string
  status: FlowStepStatus
  summary: string | null
  events: WSMessage[]
  activeAgent: string | null
}

export interface StartFlowResponse {
  run_id: string
}

export interface FlowStateResponse {
  run_id: string
  status: string
  started_at: string | null
  finished_at: string | null
  error: string | null
  state: QAAuditorState | null
}

export interface DemoTranscriptsResponse {
  transcripts: InteractionTranscript[]
  count: number
}
