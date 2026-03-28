<script setup>
import { ref, computed } from "vue";
import { useI18n } from "vue-i18n";
import {
  ArrowUpRightIcon,
  ExclamationTriangleIcon,
  CubeIcon,
  ClockIcon,
} from "@heroicons/vue/24/outline";
import { graphic } from "echarts/core";

const { t } = useI18n();

const chartOptions = ref({
  grid: { top: 10, right: 10, bottom: 20, left: 30 },
  xAxis: {
    type: "category",
    data: ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"],
    axisLine: { lineStyle: { color: "#e4e4e7" } },
    axisLabel: { fontSize: 10, color: "#71717a" },
  },
  yAxis: {
    type: "value",
    splitLine: { lineStyle: { color: "#f4f4f5" } },
    axisLabel: { fontSize: 10, color: "#71717a" },
  },
  series: [
    {
      data: [120, 150, 110, 240, 180, 210],
      type: "line",
      smooth: true,
      symbol: "none",
      lineStyle: { color: "#d97706", width: 2 },
      areaStyle: {
        color: new graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: "rgba(217, 119, 6, 0.2)" },
          { offset: 1, color: "rgba(217, 119, 6, 0)" },
        ]),
      },
    },
  ],
});

const criticalAlerts = computed(() => [
  {
    id: 1,
    title: t("dashboard.alerts.items.supply_gap"),
    meta: t("dashboard.alerts.items.site_a12"),
    status: t("dashboard.alerts.status.critical"),
    time: "2m ago",
  },
  {
    id: 2,
    title: t("dashboard.alerts.items.anomaly"),
    meta: t("dashboard.alerts.items.maintenance"),
    status: t("dashboard.alerts.status.warning"),
    time: "14m ago",
  },
]);
</script>

<template>
  <main class="p-6 bg-zinc-50 min-h-screen space-y-6">
    <header class="flex flex-col space-y-1">
      <h1 class="text-xl font-semibold text-zinc-900 tracking-tight">
        {{ $t("dashboard.header.title") }}
      </h1>
      <p class="text-sm text-zinc-500">
        {{ $t("dashboard.header.sync_label") }}
        <span class="text-emerald-600 font-medium">{{
          $t("dashboard.header.sync_status")
        }}</span>
      </p>
    </header>

    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div
        v-for="i in 4"
        :key="i"
        class="bg-white border border-zinc-200 p-4 rounded-xl shadow-sm"
      >
        <div class="flex justify-between items-start">
          <span
            class="text-[10px] font-bold text-zinc-400 uppercase tracking-widest"
          >
            {{ $t("dashboard.stats.active_runs") }}
          </span>
        </div>
        <div class="mt-2 flex items-baseline space-x-2">
          <span class="text-2xl font-mono font-semibold text-zinc-900"
            >1,284</span
          >
          <span class="text-xs text-emerald-600 font-medium">+12%</span>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div
        class="lg:col-span-2 bg-white border border-zinc-200 rounded-2xl overflow-hidden flex flex-col"
      >
        <div
          class="px-5 py-4 border-b border-zinc-100 flex justify-between items-center"
        >
          <h3 class="text-sm font-semibold text-zinc-800 flex items-center">
            <CubeIcon class="w-4 h-4 mr-2 text-amber-600" />
            {{ $t("dashboard.charts.throughput_title") }}
          </h3>
          <button class="text-xs text-zinc-400 hover:text-zinc-600 transition">
            {{ $t("dashboard.charts.view_details") }}
          </button>
        </div>
        <div class="p-6 h-80">
          <VChart :option="chartOptions" autoresize />
        </div>
      </div>

      <div class="bg-white border border-zinc-200 rounded-2xl flex flex-col">
        <div class="px-5 py-4 border-b border-zinc-100">
          <h3 class="text-sm font-semibold text-zinc-800 flex items-center">
            <ExclamationTriangleIcon class="w-4 h-4 mr-2 text-amber-600" />
            {{ $t("dashboard.alerts.title") }}
          </h3>
        </div>
        <div class="flex-1 overflow-y-auto">
          <div
            v-for="alert in criticalAlerts"
            :key="alert.id"
            class="p-4 border-b border-zinc-50 hover:bg-zinc-50 transition cursor-pointer group"
          >
            <div class="flex justify-between items-start mb-1">
              <span
                class="text-xs font-medium text-zinc-900 group-hover:text-amber-700"
                >{{ alert.title }}</span
              >
              <span class="text-[10px] text-zinc-400 font-mono">{{
                alert.time
              }}</span>
            </div>
            <p class="text-[11px] text-zinc-500 mb-2">{{ alert.meta }}</p>
            <div class="flex items-center space-x-2">
              <span
                class="px-1.5 py-0.5 rounded text-[9px] font-bold uppercase border border-amber-200 bg-amber-50 text-amber-700"
              >
                {{ alert.status }}
              </span>
            </div>
          </div>
        </div>
        <div class="p-3 bg-zinc-50 text-center">
          <button
            class="text-[11px] font-medium text-zinc-500 hover:text-zinc-800 transition"
          >
            {{ $t("dashboard.alerts.open_manager") }}
          </button>
        </div>
      </div>
    </div>

    <div class="bg-white border border-zinc-200 rounded-2xl p-6">
      <div class="flex items-center justify-between mb-6">
        <h3 class="text-sm font-semibold text-zinc-800">
          {{ $t("dashboard.recent_objects.title") }}
        </h3>
      </div>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <div
          v-for="n in 3"
          :key="n"
          class="flex items-center p-3 border border-zinc-100 rounded-xl hover:border-amber-200 transition group cursor-pointer"
        >
          <div
            class="w-10 h-10 bg-zinc-100 rounded-lg flex items-center justify-center mr-4 group-hover:bg-amber-50"
          >
            <ClockIcon
              class="w-5 h-5 text-zinc-400 group-hover:text-amber-600"
            />
          </div>
          <div class="flex-1">
            <p class="text-xs font-bold text-zinc-800">
              Batch_X992_Detroit
            </p>
            <p class="text-[10px] text-zinc-400 font-mono">ID: 44920-AA</p>
          </div>
          <ArrowUpRightIcon
            class="w-4 h-4 text-zinc-300 group-hover:text-amber-600"
          />
        </div>
      </div>
    </div>
  </main>
</template>
