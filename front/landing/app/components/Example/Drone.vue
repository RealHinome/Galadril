<script setup>
const { t } = useI18n();
</script>

<template>
	<section class="py-16 md:py-24 bg-black text-white overflow-hidden">
		<div class="max-w-5xl mx-auto px-6">
			<div class="flex flex-col md:flex-row gap-12 lg:gap-16 items-center">
				<div class="w-full md:w-1/2 text-left">
					<h2
						class="text-3xl sm:text-4xl md:text-5xl font-serif mb-6 md:mb-8 italic leading-tight"
					>
						{{ t("ringil_intro.title") }} <br />
						<span
							class="text-amber-500 not-italic font-sans font-bold block mt-2 md:inline md:mt-0"
						>
							{{ t("ringil_intro.title_highlight") }}
						</span>
					</h2>

					<div
						class="space-y-6 text-gray-400 font-light text-base md:text-lg leading-relaxed"
					>
						<i18n-t keypath="ringil_intro.p1" tag="p">
							<template #project>
								<strong class="text-white font-medium">Projet Ringil</strong>
							</template>
						</i18n-t>

						<p>{{ t("ringil_intro.p2") }}</p>
					</div>

					<div class="mt-8 md:mt-10">
						<NuxtLink to="/ringil" class="group inline-flex items-center gap-4">
							<span
								class="text-white font-semibold border-b border-amber-500 pb-1 group-hover:text-amber-500 transition-colors"
							>
								{{ t("ringil_intro.cta") }}
							</span>
							<svg
								class="w-5 h-5 text-amber-500 group-hover:translate-x-2 transition-transform duration-300"
								fill="none"
								viewBox="0 0 24 24"
								stroke="currentColor"
							>
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M17 8l4 4m0 0l-4 4m4-4H3"
								/>
							</svg>
						</NuxtLink>
					</div>
				</div>

				<div class="w-full md:w-1/2 relative mt-8 md:mt-0">
					<div
						class="absolute -inset-2 md:-inset-4 bg-amber-500/10 blur-2xl md:blur-3xl rounded-full"
					></div>

					<div
						class="relative bg-[#0A0A0A] border border-white/10 rounded-lg p-5 md:p-6 font-mono text-[11px] md:text-[12px] leading-relaxed shadow-2xl"
					>
						<div
							class="flex items-center gap-2 mb-4 border-b border-white/5 pb-2"
						>
							<span
								class="w-2 h-2 rounded-full bg-amber-500 animate-pulse"
							></span>
							<span
								class="text-gray-500 text-[9px] md:text-[10px] uppercase tracking-tighter"
							>
								{{ t("ringil_intro.terminal.feed_label") }}
							</span>
						</div>

						<div class="space-y-4">
							<div>
								<span class="text-green-500/90 font-bold">[INPUT]</span>
								<span class="text-gray-300 ml-1 break-all"
									>InstinctEvent::AnomalyDetected</span
								>
								<div
									class="pl-4 text-gray-500 italic text-[10px] md:text-[11px] mt-1"
								>
									{{ t("ringil_intro.terminal.anomaly_forward") }}
								</div>
							</div>

							<div>
								<span class="text-amber-500/90 font-bold">[ANALYSIS]</span>
								<span class="text-gray-300 ml-1">Propagation_Map_Update</span>
								<div class="pl-4 text-gray-500 text-[10px] md:text-[11px] mt-1">
									{{
										t("ringil_intro.terminal.analysis_status", {
											value: "0.98",
										})
									}}
								</div>
							</div>

							<div
								class="pt-4 border-t border-white/5 flex justify-between items-end"
							>
								<div class="space-y-1">
									<div
										class="text-[9px] md:text-[10px] text-gray-600 uppercase tracking-wider"
									>
										{{ t("ringil_intro.terminal.swarm_sync") }}
									</div>
									<div class="text-white font-medium">
										{{ t("ringil_intro.terminal.units", { count: "1,042" }) }}
									</div>
								</div>
								<div class="text-right space-y-1">
									<div
										class="text-[9px] md:text-[10px] text-gray-600 uppercase tracking-wider"
									>
										{{ t("ringil_intro.terminal.edge_latency") }}
									</div>
									<div class="text-amber-500 font-bold">12ms</div>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	</section>
</template>
