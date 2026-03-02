import type { WSMessage } from '~/types/events'

export function useFlowWebSocket() {
  let ws: WebSocket | null = null
  const isConnected = ref(false)

  function getWsUrl(runId: string): string {
    // Connect directly to the FastAPI backend for WebSocket
    // Vite proxy doesn't reliably handle WS upgrades
    const host = window.location.hostname
    return `ws://${host}:8000/ws/flow/${runId}`
  }

  function connect(runId: string, onMessage: (msg: WSMessage) => void): void {
    const url = getWsUrl(runId)
    console.log('[WS] Connecting to', url)
    ws = new WebSocket(url)

    ws.onopen = () => {
      console.log('[WS] Connected')
      isConnected.value = true
    }

    ws.onmessage = (event: MessageEvent) => {
      try {
        const msg: WSMessage = JSON.parse(event.data)
        onMessage(msg)
      } catch {
        // ignore malformed messages
      }
    }

    ws.onclose = (event) => {
      console.log('[WS] Disconnected', event.code, event.reason)
      isConnected.value = false
    }

    ws.onerror = (event) => {
      console.error('[WS] Error', event)
      isConnected.value = false
    }
  }

  function send(data: Record<string, unknown>): void {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(data))
    }
  }

  function disconnect(): void {
    if (ws) {
      ws.close()
      ws = null
    }
    isConnected.value = false
  }

  onUnmounted(() => {
    disconnect()
  })

  return { isConnected, connect, send, disconnect }
}
