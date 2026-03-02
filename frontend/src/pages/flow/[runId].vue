<script setup lang="ts">
import { ArrowLeft, Loader2, Wifi, WifiOff } from 'lucide-vue-next'
import { useFlowStore } from '~/stores/flow'
import { useFlowWebSocket } from '~/composables/useFlowWebSocket'
import { getFlowState } from '~/services/api'

const route = useRoute()
const router = useRouter()
const runId = route.params.runId as string

const store = useFlowStore()
const { isConnected, connect, disconnect } = useFlowWebSocket()

// Initialize the store
store.startRun(runId)

// Connect WebSocket
connect(runId, (event) => {
  store.handleEvent(event)
})

// Poll for state — both on mount and periodically
async function pollState() {
  try {
    const data = await getFlowState(runId)
    if (data.state) {
      store.syncFromPolledState(data.state)
    }
    if (data.status === 'completed') {
      store.flowStatus = 'completed'
    } else if (data.status === 'failed') {
      store.flowStatus = 'failed'
    }
  } catch {
    // ignore
  }
}

const pollTimer = ref<ReturnType<typeof setInterval> | null>(null)

onMounted(async () => {
  // Initial poll
  await pollState()

  // Poll every 3 seconds until done
  pollTimer.value = setInterval(async () => {
    if (store.flowStatus === 'completed' || store.flowStatus === 'failed') {
      if (pollTimer.value) clearInterval(pollTimer.value)
      return
    }
    await pollState()
  }, 3000)
})

onUnmounted(() => {
  disconnect()
  if (pollTimer.value) clearInterval(pollTimer.value)
})

const activeTab = ref('overview')
const tabs = [
  { key: 'overview', label: 'Overview' },
  { key: 'risk', label: 'Risk Scores' },
  { key: 'agents', label: 'Agent Scores' },
  { key: 'compliance', label: 'Compliance' },
  { key: 'patterns', label: 'Patterns' },
  { key: 'coaching', label: 'Coaching' },
  { key: 'raw', label: 'Raw Data' },
]
</script>

<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-3">
        <button
          class="p-1.5 rounded-md hover:bg-gray-800 text-gray-400 transition-colors"
          @click="router.push('/')"
        >
          <ArrowLeft class="h-4 w-4" />
        </button>
        <div>
          <h1 class="text-lg font-semibold text-white">QA Audit Run</h1>
          <p class="text-xs text-gray-500 font-mono">{{ runId }}</p>
        </div>
      </div>

      <div class="flex items-center gap-3">
        <!-- WS connection indicator -->
        <span class="flex items-center gap-1 text-xs" :class="isConnected ? 'text-green-400' : 'text-gray-600'">
          <Wifi v-if="isConnected" class="h-3 w-3" />
          <WifiOff v-else class="h-3 w-3" />
        </span>

        <VerboseToggle v-model="store.verboseEnabled" />

        <span
          :class="[
            'text-xs px-2.5 py-1 rounded-full font-medium',
            store.flowStatus === 'running' ? 'bg-blue-500/20 text-blue-300' : '',
            store.flowStatus === 'completed' ? 'bg-green-500/20 text-green-300' : '',
            store.flowStatus === 'failed' ? 'bg-red-500/20 text-red-300' : '',
            store.flowStatus === 'idle' ? 'bg-gray-700 text-gray-400' : '',
          ]"
        >
          <Loader2 v-if="store.flowStatus === 'running'" class="h-3 w-3 inline mr-1 animate-spin" />
          {{ store.flowStatus }}
        </span>
      </div>
    </div>

    <!-- Pipeline Graph -->
    <ClientOnly>
      <FlowGraph :steps="store.steps" :route-branch="store.routeBranch" />
    </ClientOnly>

    <!-- Running / idle state: always show activity panel -->
    <div v-if="store.flowStatus === 'running' || store.flowStatus === 'idle'" class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <StepDetailPanel
        :step="store.currentStep ?? null"
        :verbose="store.verboseEnabled"
      />
      <div class="rounded-lg border border-gray-800 bg-gray-900/40 p-4">
        <h3 class="text-sm font-semibold text-white mb-3">Event Log</h3>
        <div class="space-y-1 max-h-[300px] overflow-y-auto">
          <div
            v-for="(event, i) in store.filteredEvents.slice(-30)"
            :key="i"
            class="text-xs text-gray-500"
          >
            <span class="text-gray-600">{{ new Date(event.timestamp).toLocaleTimeString() }}</span>
            <span class="ml-2" :class="{
              'text-blue-400': event.type.includes('started'),
              'text-green-400': event.type.includes('completed') || event.type.includes('finished'),
              'text-red-400': event.type.includes('error') || event.type.includes('failed'),
            }">{{ event.type }}</span>
            <span v-if="event.data.method_name" class="ml-1 text-gray-400">{{ event.data.method_name }}</span>
            <span v-if="event.data.agent_name" class="ml-1 text-gray-400">{{ event.data.agent_name }}</span>
            <span v-if="event.data.tool_name" class="ml-1 text-gray-400">{{ event.data.tool_name }}</span>
          </div>
          <div v-if="store.filteredEvents.length === 0" class="text-gray-600 py-4 text-center">
            <Loader2 class="h-4 w-4 inline animate-spin mr-2" />
            Waiting for flow events...
          </div>
        </div>
      </div>
    </div>

    <!-- Completed state: results dashboard -->
    <div v-if="store.isCompleted && store.state">
      <!-- Tab navigation -->
      <div class="flex gap-1 border-b border-gray-800 mb-4 overflow-x-auto">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          :class="[
            'px-4 py-2 text-sm font-medium transition-colors whitespace-nowrap',
            activeTab === tab.key
              ? 'text-sky-400 border-b-2 border-sky-400'
              : 'text-gray-500 hover:text-gray-300',
          ]"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Tab panels -->
      <div v-show="activeTab === 'overview'">
        <OverviewDashboard :state="store.state" />
      </div>

      <div v-show="activeTab === 'risk'">
        <RiskScoreChart :risk-scores="store.state.risk_scores" />
      </div>

      <div v-show="activeTab === 'agents'">
        <AgentRadarChart :evaluations="store.state.qa_evaluations" />
      </div>

      <div v-show="activeTab === 'compliance'">
        <CompliancePanel :state="store.state" />
      </div>

      <div v-show="activeTab === 'patterns'">
        <PatternInsights :patterns="store.state.pattern_insights" />
      </div>

      <div v-show="activeTab === 'coaching'">
        <CoachingPlanCard :plans="store.state.coaching_plans" />
      </div>

      <div v-show="activeTab === 'raw'">
        <RawDataViewer :state="store.state" />
      </div>
    </div>

    <!-- Failed state -->
    <div v-if="store.flowStatus === 'failed'" class="rounded-lg border border-red-900/50 bg-red-950/20 p-6 text-center">
      <p class="text-red-400 font-medium">Flow execution failed</p>
      <p class="text-sm text-red-300/60 mt-1">Check the backend logs for details.</p>
      <button
        class="mt-4 px-4 py-2 rounded-lg bg-gray-800 text-gray-300 text-sm hover:bg-gray-700 transition-colors"
        @click="router.push('/')"
      >
        Back to Home
      </button>
    </div>
  </div>
</template>
