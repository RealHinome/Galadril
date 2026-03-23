<script setup>
const { t } = useI18n();
const wraps = [
	{
		title: t("wraps.synapse.title"),
		description: t("wraps.synapse.description"),
		illustration: "/illustrations/synapse.svg",
	},
	{
		title: t("wraps.vision.title"),
		description: t("wraps.vision.description"),
		illustration: "/illustrations/threat.svg",
	},
	{
		title: t("wraps.scribe.title"),
		description: t("wraps.scribe.description"),
		illustration: "/illustrations/llm.svg",
	},
];
</script>

<template>
	<section
		class="horizontal-section min-h-[100svh] bg-white flex flex-col justify-center overflow-hidden relative py-12"
	>
		<div class="absolute top-12 md:top-16 lg:top-20 left-0 w-full z-10 px-6">
			<h3
				class="text-3xl md:text-5xl font-serif text-center text-gray-900 leading-tight"
			>
				{{ $t("wraps.control") }} <br />
				<span class="italic text-gray-500 text-xl md:text-3xl block">
					{{ $t("wraps.over") }}
				</span>
			</h3>
		</div>
		<div
			class="horizontal-wrap flex gap-8 md:gap-12 px-[10vw] md:px-[15vw] w-max items-center h-full mt-32 md:mt-40 overflow-x-auto snap-x snap-mandatory scroll-smooth"
		>
			<div
				v-for="(slide, index) in wraps"
				:key="index"
				class="snap-center w-[85vw] md:w-[70vw] lg:w-[60vw] xl:w-[50vw] max-w-6xl bg-gray-50 rounded-[2rem] p-8 md:p-12 flex flex-col border border-gray-100 shadow-sm flex-shrink-0 transition-all duration-300"
			>
				<span
					class="text-[10px] font-mono uppercase tracking-[0.2em] text-gray-400 mb-4"
				>
					Step 0{{ index + 1 }}
				</span>

				<div class="flex flex-col gap-4 mb-8">
					<h4
						class="text-xl md:text-2xl font-semibold text-gray-800 tracking-tight"
					>
						{{ slide.title }}
					</h4>
					<p class="text-sm md:text-base text-gray-600 leading-relaxed">
						{{ slide.description }}
					</p>
				</div>

				<div
					class="w-full aspect-video md:aspect-[21/9] bg-white rounded-2xl overflow-hidden relative border border-gray-200/50 p-4 md:p-8"
				>
					<NuxtImg
						:src="slide.illustration"
						:alt="slide.title"
						class="w-full h-full object-contain"
						loading="lazy"
					/>
				</div>
			</div>

			<div class="w-[10vw] md:w-[15vw] flex-shrink-0"></div>
		</div>
	</section>
</template>
