<script setup>
const { t, tm, rt } = useI18n();

const simulatedId = ref("E1");

const impacts = computed(() => ({
	E1: tm("graph_section.impacts.e1"),
	E3: tm("graph_section.impacts.e3"),
}));

const eskgData = computed(() => ({
	nodes: [
		{
			id: "E1",
			type: "Event",
			label: t("graph_section.nodes.e1.label"),
			description: t("graph_section.nodes.e1.desc"),
		},
		{
			id: "S1",
			type: "State",
			label: t("graph_section.nodes.s1.label"),
			description: t("graph_section.nodes.s1.desc"),
		},
		{
			id: "E2",
			type: "Event",
			label: t("graph_section.nodes.e2.label"),
			description: t("graph_section.nodes.e2.desc"),
		},
		{
			id: "E3",
			type: "Event",
			label: t("graph_section.nodes.e3.label"),
			description: t("graph_section.nodes.e3.desc"),
		},
		{
			id: "S2",
			type: "State",
			label: t("graph_section.nodes.s2.label"),
			description: t("graph_section.nodes.s2.desc"),
		},
	],
	edges: [
		{ source: "E1", target: "S1", type: "trig" },
		{ source: "S1", target: "E2", type: "lead" },
		{ source: "E3", target: "S2", type: "impact" },
		{ source: "E1", target: "E3", type: "escalate" },
	],
}));
</script>

<template>
	<section
		class="min-h-screen md:h-screen py-12 md:py-8 bg-[#fdfdfc] flex flex-col"
	>
		<div class="max-w-[1600px] mx-auto px-4 w-full flex-1 flex flex-col">
			<div class="py-8 md:py-12">
				<h3
					class="text-2xl sm:text-3xl md:text-5xl font-serif text-center text-gray-900 leading-tight"
				>
					{{ t("graph_section.title") }}<br />
					<span class="italic text-gray-500 text-base md:text-3xl block mt-2">
						{{ t("graph_section.subtitle") }}
					</span>
				</h3>
			</div>

			<div
				class="grid grid-cols-1 lg:grid-cols-2 gap-6 items-stretch flex-1 pb-8"
			>
				<div
					class="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden flex flex-col min-h-[400px] md:min-h-0"
				>
					<div
						class="px-5 py-4 border-b border-slate-100 flex justify-between items-center bg-white"
					>
						<h3
							class="text-[10px] md:text-[11px] font-bold text-slate-400 uppercase tracking-widest font-mono"
						>
							{{ t("graph_section.labels.causal_map") }}
						</h3>
						<div class="flex gap-2">
							<span
								class="w-2 h-2 rounded-full bg-amber-400 animate-pulse"
							></span>
						</div>
					</div>
					<div class="flex-1 relative bg-slate-50/30">
						<GraphCausal
							v-if="eskgData"
							:data="eskgData"
							:highlight-id="simulatedId"
						/>
					</div>
				</div>

				<div
					class="bg-white border border-slate-200 rounded-xl shadow-sm flex flex-col"
				>
					<div class="px-5 py-4 border-b border-slate-100 bg-white">
						<h3
							class="text-[10px] md:text-[11px] font-bold text-slate-400 uppercase tracking-widest font-mono"
						>
							{{ t("graph_section.labels.simulation_panel") }}
						</h3>
					</div>

					<div class="p-6 md:p-8 flex-1 flex flex-col">
						<div class="mb-6 md:mb-10">
							<label
								class="text-[10px] font-bold text-amber-600 uppercase tracking-tighter mb-3 block"
							>
								{{ t("graph_section.labels.decision_trigger") }}
							</label>
							<div class="relative">
								<select
									v-model="simulatedId"
									class="w-full appearance-none bg-slate-50 border border-slate-200 rounded-lg p-3 md:p-4 text-sm font-semibold text-slate-700 focus:border-amber-500 focus:ring-4 focus:ring-amber-500/10 outline-none transition-all cursor-pointer"
								>
									<option value="E1">
										{{ t("graph_section.options.e1") }}
									</option>
									<option value="E3">
										{{ t("graph_section.options.e3") }}
									</option>
								</select>
								<div
									class="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400"
								>
									<svg
										class="w-4 h-4"
										fill="none"
										stroke="currentColor"
										viewBox="0 0 24 24"
									>
										<path
											d="M19 9l-7 7-7-7"
											stroke-width="2"
											stroke-linecap="round"
											stroke-linejoin="round"
										/>
									</svg>
								</div>
							</div>
						</div>

						<div class="flex-1 space-y-6">
							<div
								class="p-4 md:p-5 bg-amber-50/50 border border-amber-100 rounded-xl"
							>
								<div class="flex items-center gap-2 mb-4">
									<div class="w-1.5 h-4 bg-amber-500 rounded-full"></div>
									<span
										class="text-[11px] font-bold text-slate-800 uppercase tracking-tight"
									>
										{{ t("graph_section.labels.predicted_shifts") }}
									</span>
								</div>
								<div class="space-y-4">
									<div
										v-for="(txt, i) in impacts[simulatedId]"
										:key="i"
										class="flex items-start gap-3"
									>
										<span class="text-amber-500 text-sm font-bold">↳</span>
										<p
											class="text-xs md:text-[13px] text-slate-600 leading-snug font-medium"
										>
											{{ rt(txt) }}
										</p>
									</div>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	</section>
</template>
