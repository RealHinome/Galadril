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
		<h3
			class="absolute top-8 md:top-20 w-full text-2xl sm:text-3xl md:text-5xl font-serif text-center text-gray-900 z-10 px-6"
		>
			{{ $t("wraps.control") }} <br />
			<span class="italic text-gray-500 text-xl sm:text-2xl md:text-4xl">
				{{ $t("wraps.over") }}
			</span>
		</h3>

		<div
			class="horizontal-wrap flex gap-6 md:gap-12 px-[7vw] md:px-[15vw] w-max items-center h-full mt-24 md:mt-32 overflow-x-auto snap-x snap-mandatory scroll-px-[7vw]"
		>
			<div
				v-for="(slide, index) in wraps"
				:key="index"
				class="snap-center w-[86vw] sm:w-[65vw] md:w-[50vw] lg:w-[50vw] max-w-3xl h-[60vh] md:h-[65vh] bg-gray-50 rounded-3xl p-6 md:p-10 flex flex-col border border-gray-200 shadow-sm flex-shrink-0 transition-transform duration-300"
			>
				<span
					class="text-xs font-mono uppercase tracking-widest text-gray-400 mb-2"
				>
					Step 0{{ index + 1 }}
				</span>

				<h4 class="text-xl md:text-2xl font-semibold mb-3 text-gray-800">
					{{ slide.title }}
				</h4>

				<p
					class="text-sm md:text-md text-gray-600 mb-6 leading-relaxed line-clamp-3 md:line-clamp-none"
				>
					{{ slide.description }}
				</p>

				<div
					class="flex-1 bg-gray-100 rounded-2xl overflow-hidden relative group"
				>
					<NuxtImg
						:src="slide.illustration"
						alt=""
						class="absolute inset-0 w-full h-full object-cover object-center"
						loading="lazy"
					/>
					<div
						class="absolute inset-0 bg-gradient-to-t from-black/5 to-transparent"
					></div>
				</div>
			</div>
		</div>
	</section>
</template>
