<script setup>
import { useI18n } from "vue-i18n";
import {
  ChartBarIcon,
  BeakerIcon,
  TruckIcon,
  Squares2X2Icon,
  ClockIcon,
  CubeIcon,
} from "@heroicons/vue/24/outline";

const { t } = useI18n();

const topMetrics = computed(() => [
  {
    id: 1,
    title: "Active Runs",
    value: "1,284",
    icon: Squares2X2Icon,
    trend: "+12",
  },
  {
    id: 2,
    title: "Efficiency",
    value: "84.2%",
    icon: ChartBarIcon,
    trend: "+2.1",
  },
  { id: 3, title: "Stockouts", value: "14", icon: BeakerIcon, trend: "+3" },
  {
    id: 4,
    title: "On-time delivery",
    value: "91.5%",
    icon: TruckIcon,
    trend: "-1.4",
  },
]);

const alertsData = computed(() => [
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

const recentItems = ref([
  { id: "ID: 44920-AA", name: "Batch_X992_Detroit", icon: ClockIcon },
  { id: "ID: 44921-BB", name: "Batch_X993_Chicago", icon: ClockIcon },
  { id: "ID: 44922-CC", name: "Batch_X994_Austin", icon: ClockIcon },
]);
</script>

<template>
  <main class="p-6 bg-zinc-50 min-h-screen space-y-6">
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <WidgetCard
        v-for="metric in topMetrics"
        :key="metric.id"
        v-bind="metric"
      />
    </div>

    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <WidgetLineChart
        class="lg:col-span-2"
        title="Throughput delivery"
        :icon="CubeIcon"
        :data="[120, 150, 110, 240, 180, 210]"
        :categories="['00:00', '04:00', '08:00', '12:00', '16:00', '20:00']"
        color="#d97706"
        :show-tooltip="false"
      />
      <WidgetAlerts
        :title="$t('dashboard.alerts.title')"
        :alerts="alertsData"
      />
    </div>

    <WidgetObjects
      :title="$t('dashboard.recent_objects.title')"
      :items="recentItems"
    />
  </main>
</template>
