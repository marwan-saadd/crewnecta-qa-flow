/** WebSocket event message types. */

export interface WSMessage {
  run_id: string
  type: WSEventType
  verbose_only: boolean
  timestamp: string
  data: Record<string, unknown>
}

export type WSEventType =
  | 'flow_started'
  | 'flow_finished'
  | 'step_started'
  | 'step_finished'
  | 'step_failed'
  | 'step_completed'
  | 'crew_started'
  | 'crew_completed'
  | 'agent_started'
  | 'agent_completed'
  | 'task_started'
  | 'task_completed'
  | 'tool_started'
  | 'tool_finished'
  | 'tool_error'
  | 'llm_call_started'
  | 'llm_call_completed'
  | 'state_snapshot'
  | 'run_status'
  | 'ack'
