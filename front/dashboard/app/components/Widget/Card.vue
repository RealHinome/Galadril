<script setup>
defineProps(["title", "value", "icon", "trend"]);
</script>

<template>
  <div
    class="bg-white border border-zinc-200 rounded-xl p-4 flex items-center gap-4 transition-all hover:ring-2 hover:ring-amber-100 group"
  >
    <div
      class="p-3 bg-zinc-50 rounded-lg text-amber-600 group-hover:bg-amber-50 transition-colors shrink-0"
    >
      <component :is="icon" class="w-6 h-6" />
    </div>

    <div class="min-w-0 flex-1">
      <p
        class="text-xs font-bold text-zinc-500 uppercase tracking-tighter truncate leading-tight"
      >
        {{ title }}
      </p>
      <div class="flex items-center gap-2">
        <h3 class="text-2xl font-black text-zinc-900 tabular-nums">
          {{ value }}
        </h3>
        <span
          v-if="trend !== 'Stable'"
          :class="
            trend.startsWith('+')
              ? 'text-emerald-600 bg-emerald-50'
              : 'text-rose-600 bg-rose-50'
          "
          class="text-[10px] px-1.5 py-0.5 rounded-full font-bold"
        >
          {{ trend }}%
        </span>
      </div>
    </div>
  </div>
</template>
