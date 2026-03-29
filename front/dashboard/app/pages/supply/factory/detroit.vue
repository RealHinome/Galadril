<script setup>
import { ref } from "vue";
import { ChartBarIcon, BeakerIcon, TruckIcon } from "@heroicons/vue/24/outline";

const selectedFacility = ref(null);

const topMetrics = [
  {
    id: 1,
    title: "Overall Equipment Effectiveness",
    value: "84.2%",
    icon: ChartBarIcon,
    trend: "+2.1",
    status: "healthy",
  },
  {
    id: 2,
    title: "Stockouts",
    value: "14",
    icon: BeakerIcon,
    trend: "+3",
    status: "warning",
  },
  {
    id: 3,
    title: "On-Time In-Full",
    value: "91.5%",
    icon: TruckIcon,
    trend: "-1.4",
    status: "critical",
  },
];

const facilityPoints = [
  {
    name: "Detroit Assembly - Main",
    country: "United States of America",
    value: [-83.0458, 42.3314, 100],
    meta: {
      id: "FAC-DET-01",
      target: "Final Assembly Line",
      status: "Operational - High Load",
      severity: "warning",
      metrics: {
        throughput: "45 units/hr",
        backlog: "128 units",
        labor_availability: "92%",
      },
      issue: "Cycle time deviation in Chassis Weld section (+12s).",
    },
  },
  {
    name: "New Mexico Semiconductor Hub",
    country: "United States of America",
    value: [-106.0181, 34.5199, 100],
    targetCoords: [-83.0458, 42.3314],
    meta: {
      id: "SUP-NM-88",
      target: "Tier 1 Supplier",
      status: "Inbound Delay",
      severity: "critical",
      metrics: {
        lead_time_variance: "+4 days",
        inventory_on_hand: "2.5 days",
        safety_stock_level: "Below Min",
      },
      issue: "Port congestion at Long Beach affecting silicon sub-components.",
    },
  },
  {
    name: "Chicago Logistics Center",
    country: "United States of America",
    value: [-87.6298, 41.8781, 100],
    targetCoords: [-83.0458, 42.3314],
    meta: {
      id: "DIST-CHI-04",
      target: "Distribution Center",
      status: "Optimized",
      severity: "normal",
      metrics: {
        dock_to_stock_time: "4.2 hrs",
        outbound_fill_rate: "99.2%",
        carrier_performance: "Excellent",
      },
      issue: "Cross-docking efficiency improved via new slotting strategy.",
    },
  },
];

const handleSelectNode = (nodeMeta) => {
  selectedFacility.value = nodeMeta;
};

const handleClose = () => {
  selectedFacility.value = null;
};

const handleAction = (actionType, id) => {
  console.log(`Action: ${actionType} on ${id}`);
  selectedFacility.value = null;
};
</script>

<template>
  <div class="flex h-full max-h-screen bg-zinc-50 font-sans overflow-hidden">
    <div class="flex-1 flex flex-col min-w-0 h-full">
      <header
        class="p-4 border-b border-zinc-200 bg-white shadow-sm flex-shrink-0"
      >
        <div class="flex flex-row gap-4 w-full">
          <WidgetCard
            v-for="metric in topMetrics"
            :key="metric.id"
            v-bind="metric"
            class="flex-1 min-w-0"
          />
        </div>
      </header>

      <main class="flex-1 relative min-h-0 bg-zinc-100">
        <WidgetMap
          :points="facilityPoints"
          @select-node="handleSelectNode"
          class="absolute inset-0 w-full h-full"
        />
      </main>
    </div>

    <NavbarAction
      class="h-full flex-shrink-0"
      :selected-item="selectedFacility"
      @close="handleClose"
      @approve="(id) => handleAction('Approve', id)"
      @modify="(id) => handleAction('Modify', id)"
      @reject="(id) => handleAction('Reject', id)"
    />
  </div>
</template>
