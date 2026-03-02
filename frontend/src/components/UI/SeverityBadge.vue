<script setup lang="ts">
import type { ComplianceSeverity } from '~/types/flow'

defineProps<{
  severity: ComplianceSeverity
}>()

const colorMap: Record<ComplianceSeverity, string> = {
  critical: 'bg-red-500/20 text-red-300 border-red-500/30',
  major: 'bg-orange-500/20 text-orange-300 border-orange-500/30',
  minor: 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30',
  none: 'bg-green-500/20 text-green-300 border-green-500/30',
}
</script>

<template>
  <span
    :class="['inline-flex px-2 py-0.5 rounded-full text-xs font-medium border', colorMap[severity]]"
  >
    {{ severity.toUpperCase() }}
  </span>
</template>
