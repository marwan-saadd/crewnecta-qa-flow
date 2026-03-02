<script setup lang="ts">
import { Upload, Database, Loader2 } from 'lucide-vue-next'

const props = defineProps<{
  loading?: boolean
}>()

const emit = defineEmits<{
  start: [payload: { use_demo?: boolean; transcripts?: unknown[] }]
}>()

const mode = ref<'demo' | 'upload'>('demo')
const uploadedTranscripts = ref<unknown[] | null>(null)
const fileName = ref('')
const fileError = ref('')

async function handleFileUpload(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  fileError.value = ''
  fileName.value = file.name

  try {
    const text = await file.text()
    const data = JSON.parse(text)
    const transcripts = data.transcripts || data
    if (!Array.isArray(transcripts) || transcripts.length === 0) {
      throw new Error('File must contain an array of transcripts')
    }
    uploadedTranscripts.value = transcripts
  } catch (e) {
    fileError.value = e instanceof Error ? e.message : 'Invalid JSON file'
    uploadedTranscripts.value = null
  }
}

function handleStart() {
  if (props.loading) return

  if (mode.value === 'demo') {
    emit('start', { use_demo: true })
  } else if (uploadedTranscripts.value) {
    emit('start', { transcripts: uploadedTranscripts.value })
  }
}

const canStart = computed(() => {
  if (mode.value === 'demo') return true
  return !!uploadedTranscripts.value
})
</script>

<template>
  <div class="space-y-6">
    <!-- Mode selector -->
    <div class="flex gap-3">
      <button
        :class="[
          'flex-1 px-4 py-3 rounded-lg border text-sm font-medium transition-all',
          mode === 'demo'
            ? 'border-sky-500 bg-sky-500/10 text-sky-400'
            : 'border-gray-700 bg-gray-800/50 text-gray-400 hover:border-gray-600',
        ]"
        @click="mode = 'demo'"
      >
        <Database class="h-4 w-4 inline mr-2" />
        Use Demo Data
      </button>
      <button
        :class="[
          'flex-1 px-4 py-3 rounded-lg border text-sm font-medium transition-all',
          mode === 'upload'
            ? 'border-sky-500 bg-sky-500/10 text-sky-400'
            : 'border-gray-700 bg-gray-800/50 text-gray-400 hover:border-gray-600',
        ]"
        @click="mode = 'upload'"
      >
        <Upload class="h-4 w-4 inline mr-2" />
        Upload JSON
      </button>
    </div>

    <!-- Demo info -->
    <div v-if="mode === 'demo'" class="text-sm text-gray-400 bg-gray-800/50 rounded-lg p-4">
      <p>10 realistic BPO transcripts covering 5 agents across scenarios including:</p>
      <ul class="mt-2 space-y-1 list-disc list-inside text-gray-500">
        <li>Compliance violations (critical & minor)</li>
        <li>Empathy failures and process issues</li>
        <li>Excellent customer saves</li>
        <li>Escalation handling</li>
      </ul>
    </div>

    <!-- File upload -->
    <div v-if="mode === 'upload'" class="space-y-3">
      <label
        class="flex items-center justify-center w-full h-28 border-2 border-dashed border-gray-700 rounded-lg cursor-pointer hover:border-gray-600 transition-colors"
      >
        <div class="text-center">
          <Upload class="h-6 w-6 mx-auto text-gray-500 mb-1" />
          <p class="text-sm text-gray-400">
            {{ fileName || 'Click to upload JSON file' }}
          </p>
        </div>
        <input type="file" accept=".json" class="hidden" @change="handleFileUpload" />
      </label>
      <p v-if="uploadedTranscripts" class="text-sm text-green-400">
        {{ uploadedTranscripts.length }} transcripts loaded
      </p>
      <p v-if="fileError" class="text-sm text-red-400">{{ fileError }}</p>
    </div>

    <!-- Start button -->
    <button
      :disabled="!canStart || loading"
      :class="[
        'w-full py-3 px-4 rounded-lg font-medium text-sm transition-all',
        canStart && !loading
          ? 'bg-sky-500 hover:bg-sky-600 text-white'
          : 'bg-gray-700 text-gray-500 cursor-not-allowed',
      ]"
      @click="handleStart"
    >
      <template v-if="loading">
        <Loader2 class="h-4 w-4 inline mr-2 animate-spin" />
        Starting...
      </template>
      <template v-else>
        Start QA Audit
      </template>
    </button>
  </div>
</template>
