<script setup lang="ts">
import { AlertTriangle, Users, BookOpen, FileText } from 'lucide-vue-next'
import type { PatternInsight } from '~/types/flow'

defineProps<{
  patterns: PatternInsight[]
}>()

function typeIcon(type: string) {
  const map: Record<string, typeof AlertTriangle> = {
    agent_specific: Users,
    systemic: AlertTriangle,
    script_issue: FileText,
    training_gap: BookOpen,
  }
  return map[type] || AlertTriangle
}

function typeColor(type: string): string {
  const map: Record<string, string> = {
    agent_specific: 'text-blue-400 bg-blue-500/10 border-blue-500/30',
    systemic: 'text-red-400 bg-red-500/10 border-red-500/30',
    script_issue: 'text-yellow-400 bg-yellow-500/10 border-yellow-500/30',
    training_gap: 'text-purple-400 bg-purple-500/10 border-purple-500/30',
  }
  return map[type] || 'text-gray-400 bg-gray-500/10 border-gray-500/30'
}
</script>

<template>
  <div class="space-y-3">
    <div v-if="patterns.length === 0" class="text-sm text-gray-500 text-center py-8">
      No patterns detected.
    </div>

    <div
      v-for="(pattern, i) in patterns"
      :key="i"
      class="rounded-lg border border-gray-800 bg-gray-900/40 p-4"
    >
      <div class="flex items-start gap-3">
        <div :class="['p-2 rounded-lg border', typeColor(pattern.pattern_type)]">
          <component :is="typeIcon(pattern.pattern_type)" class="h-4 w-4" />
        </div>
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-1">
            <span class="text-xs uppercase tracking-wider text-gray-500">{{ pattern.pattern_type.replace('_', ' ') }}</span>
            <span v-if="pattern.frequency" class="text-xs text-gray-600">| {{ pattern.frequency }}</span>
          </div>
          <p class="text-sm text-gray-300 mb-2">{{ pattern.description }}</p>

          <div v-if="pattern.affected_agents.length > 0" class="mb-2">
            <span class="text-xs text-gray-500">Affected: </span>
            <span
              v-for="(agent, j) in pattern.affected_agents"
              :key="j"
              class="inline-flex text-xs bg-gray-800 text-gray-400 px-1.5 py-0.5 rounded mr-1"
            >{{ agent }}</span>
          </div>

          <div v-if="pattern.recommended_action" class="text-xs text-sky-400/80">
            Recommended: {{ pattern.recommended_action }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
