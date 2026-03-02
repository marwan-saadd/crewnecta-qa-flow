<script setup lang="ts">
import { Activity, Shield, BarChart3, Users } from 'lucide-vue-next'
import { startFlow } from '~/services/api'

const router = useRouter()
const error = ref('')
const loading = ref(false)

async function handleStart(payload: { use_demo?: boolean; transcripts?: unknown[] }) {
  error.value = ''
  loading.value = true
  try {
    const response = await startFlow(payload)
    console.log('[QA] Flow started, navigating to:', response.run_id)
    await navigateTo(`/flow/${response.run_id}`)
  } catch (e) {
    console.error('[QA] Failed to start flow:', e)
    error.value = e instanceof Error ? e.message : 'Failed to start flow'
    loading.value = false
  }
}
</script>

<template>
  <div class="flex items-center justify-center min-h-[calc(100vh-8rem)]">
    <div class="w-full max-w-lg">
      <!-- Hero card -->
      <div class="rounded-xl border border-gray-800 bg-gray-900/60 backdrop-blur p-8 space-y-6">
        <div class="text-center space-y-2">
          <div class="inline-flex items-center justify-center w-14 h-14 rounded-full bg-sky-500/10 mb-2">
            <Activity class="h-7 w-7 text-sky-400" />
          </div>
          <h1 class="text-2xl font-bold text-white">QA Auditor</h1>
          <p class="text-sm text-gray-400 max-w-sm mx-auto">
            AI-powered quality assurance for customer interactions. Analyze transcripts, detect compliance issues, and generate coaching plans.
          </p>
        </div>

        <!-- Feature badges -->
        <div class="flex justify-center gap-4 text-xs text-gray-500">
          <span class="flex items-center gap-1">
            <Shield class="h-3.5 w-3.5 text-red-400" />
            Compliance
          </span>
          <span class="flex items-center gap-1">
            <BarChart3 class="h-3.5 w-3.5 text-sky-400" />
            Analytics
          </span>
          <span class="flex items-center gap-1">
            <Users class="h-3.5 w-3.5 text-green-400" />
            Coaching
          </span>
        </div>

        <div class="border-t border-gray-800" />

        <!-- Uploader -->
        <TranscriptUploader :loading="loading" @start="handleStart" />

        <!-- Error -->
        <p v-if="error" class="text-sm text-red-400 text-center">{{ error }}</p>
      </div>
    </div>
  </div>
</template>
