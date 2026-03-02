<script setup lang="ts">
import { Star, CheckCircle, AlertTriangle, AlertOctagon } from 'lucide-vue-next'
import type { CoachingPlan } from '~/types/flow'

defineProps<{
  plans: CoachingPlan[]
}>()

function perfIcon(performance: string) {
  const map: Record<string, typeof Star> = {
    exceeds: Star,
    meets: CheckCircle,
    below: AlertTriangle,
    critical: AlertOctagon,
  }
  return map[performance] || AlertTriangle
}

function perfColor(performance: string): string {
  const map: Record<string, string> = {
    exceeds: 'text-yellow-400',
    meets: 'text-green-400',
    below: 'text-orange-400',
    critical: 'text-red-400',
  }
  return map[performance] || 'text-gray-400'
}
</script>

<template>
  <div class="space-y-3">
    <div v-if="plans.length === 0" class="text-sm text-gray-500 text-center py-8">
      No coaching plans generated.
    </div>

    <details
      v-for="plan in plans"
      :key="plan.agent_id"
      class="rounded-lg border border-gray-800 bg-gray-900/40 group"
    >
      <summary class="cursor-pointer p-4 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <component :is="perfIcon(plan.overall_performance)" :class="['h-5 w-5', perfColor(plan.overall_performance)]" />
          <div>
            <span class="text-sm font-medium text-white">{{ plan.agent_name }}</span>
            <span class="text-xs text-gray-500 ml-2">({{ plan.agent_id }})</span>
          </div>
        </div>
        <span class="text-xs text-gray-500">{{ plan.follow_up_timeline }}</span>
      </summary>

      <div class="px-4 pb-4 space-y-3 border-t border-gray-800 pt-3">
        <!-- Performance -->
        <div>
          <p class="text-xs text-gray-500 uppercase tracking-wider mb-1">Performance</p>
          <span :class="['text-sm font-medium capitalize', perfColor(plan.overall_performance)]">
            {{ plan.overall_performance }}
          </span>
        </div>

        <!-- Strengths -->
        <div v-if="plan.key_strengths.length > 0">
          <p class="text-xs text-gray-500 uppercase tracking-wider mb-1">Strengths</p>
          <ul class="space-y-0.5">
            <li v-for="(s, i) in plan.key_strengths" :key="i" class="text-xs text-green-300/80">+ {{ s }}</li>
          </ul>
        </div>

        <!-- Priority improvements -->
        <div v-if="plan.priority_improvements.length > 0">
          <p class="text-xs text-gray-500 uppercase tracking-wider mb-1">Priority Improvements</p>
          <ul class="space-y-0.5">
            <li v-for="(p, i) in plan.priority_improvements" :key="i" class="text-xs text-orange-300/80">- {{ p }}</li>
          </ul>
        </div>

        <!-- Specific examples -->
        <div v-if="plan.specific_examples.length > 0">
          <p class="text-xs text-gray-500 uppercase tracking-wider mb-1">Specific Examples</p>
          <ul class="space-y-0.5">
            <li v-for="(e, i) in plan.specific_examples" :key="i" class="text-xs text-gray-400">{{ e }}</li>
          </ul>
        </div>

        <!-- Suggested training -->
        <div v-if="plan.suggested_training.length > 0">
          <p class="text-xs text-gray-500 uppercase tracking-wider mb-1">Suggested Training</p>
          <ul class="space-y-0.5">
            <li v-for="(t, i) in plan.suggested_training" :key="i" class="text-xs text-sky-300/80">{{ t }}</li>
          </ul>
        </div>
      </div>
    </details>
  </div>
</template>
