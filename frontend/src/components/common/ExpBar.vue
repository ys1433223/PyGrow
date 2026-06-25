<script setup>
defineProps({
  experience: { type: Number, default: 0 },
  nextLevelXp: { type: Number, default: 100 },
  currentLevel: { type: String, default: '萌新小白' },
  majorLevel: { type: String, default: '初级' },
  progressPercent: { type: Number, default: 0 },
})

const majorColors = {
  '初级': 'from-green-400 to-emerald-500',
  '中级': 'from-blue-500 to-purple-600',
  '高级': 'from-orange-400 to-red-500',
}

const majorBgColors = {
  '初级': 'bg-green-100 text-green-700',
  '中级': 'bg-blue-100 text-blue-700',
  '高级': 'bg-orange-100 text-orange-700',
}
</script>

<template>
  <div class="exp-bar-container">
    <div class="flex justify-between items-center mb-1.5">
      <div class="flex items-center space-x-2">
        <span :class="majorBgColors[majorLevel] || 'bg-blue-100 text-blue-700'" class="text-xs px-2 py-0.5 rounded-full font-medium">{{ majorLevel }}</span>
        <span class="text-sm font-bold text-gray-700">{{ currentLevel }}</span>
      </div>
      <span class="text-xs text-gray-400">{{ experience }} / {{ nextLevelXp }} XP</span>
    </div>
    <div class="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
      <div
        :class="majorColors[majorLevel] || 'from-blue-500 to-purple-600'"
        class="h-full bg-gradient-to-r rounded-full transition-all duration-700 ease-out"
        :style="{ width: progressPercent + '%' }"
      ></div>
    </div>
  </div>
</template>
