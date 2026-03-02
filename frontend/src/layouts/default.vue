<script setup lang="ts">
import { Activity } from 'lucide-vue-next'
</script>

<template>
  <div class="min-h-screen bg-gray-950 text-white">
    <nav class="border-b border-gray-800 bg-gray-900/80 backdrop-blur-sm sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-14">
          <NuxtLink to="/" class="flex items-center gap-2 text-white font-semibold text-lg">
            <Activity class="h-5 w-5 text-sky-400" />
            <span>CrewNecta QA</span>
          </NuxtLink>
          <span class="text-xs text-gray-500">Intelligent QA Auditor & Coaching Engine</span>
        </div>
      </div>
    </nav>
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <slot />
    </main>
  </div>
</template>
