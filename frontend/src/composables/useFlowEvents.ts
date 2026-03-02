import type { WSMessage } from '~/types/events'

export function useFlowEvents() {
  const allEvents = ref<WSMessage[]>([])
  const verboseEnabled = ref(false)

  function addEvent(event: WSMessage): void {
    allEvents.value.push(event)
  }

  const filteredEvents = computed(() => {
    if (verboseEnabled.value) return allEvents.value
    return allEvents.value.filter((e) => !e.verbose_only)
  })

  function clearEvents(): void {
    allEvents.value = []
  }

  return { allEvents, verboseEnabled, filteredEvents, addEvent, clearEvents }
}
