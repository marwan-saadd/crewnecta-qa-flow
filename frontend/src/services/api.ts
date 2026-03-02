import type { StartFlowResponse, FlowStateResponse, DemoTranscriptsResponse } from '~/types/flow'

const API_BASE = '/api'

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options?.headers as Record<string, string>) },
    ...options,
  })
  if (!res.ok) {
    const body = await res.text()
    throw new Error(`API error ${res.status}: ${body}`)
  }
  return res.json()
}

export async function startFlow(payload: { use_demo?: boolean; transcripts?: unknown[] }): Promise<StartFlowResponse> {
  return apiFetch<StartFlowResponse>('/flow/start', {
    method: 'POST',
    body: JSON.stringify(payload),
  })
}

export async function getFlowState(runId: string): Promise<FlowStateResponse> {
  return apiFetch<FlowStateResponse>(`/flow/${runId}/state`)
}

export async function getDemoTranscripts(): Promise<DemoTranscriptsResponse> {
  return apiFetch<DemoTranscriptsResponse>('/transcripts/demo')
}
