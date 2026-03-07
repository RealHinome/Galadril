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
		class="horizontal-section h-[100svh] bg-white flex flex-col justify-center overflow-hidden relative"
	>
		<h3
			class="absolute top-16 md:top-20 w-full text-3xl md:text-5xl font-serif text-center text-gray-900 z-10 px-4"
		>
			{{ $t("wraps.control") }} <br /><span class="italic text-gray-500">{{
				$t("wraps.over")
			}}</span>
		</h3>

		<div
			class="horizontal-wrap flex gap-4 md:gap-8 px-[5vw] md:px-[10vw] w-max items-center h-full mt-16 md:mt-20"
		>
			<div
				v-for="(slide, index) in wraps"
				:key="index"
				class="w-[85vw] sm:w-[60vw] md:w-[45vw] h-[55vh] md:h-[50vh] bg-gray-50 rounded-2xl md:rounded-3xl p-6 md:p-10 flex flex-col border border-gray-200 shadow-sm flex-shrink-0"
			>
				<h4
					class="text-xl md:text-2xl font-semibold mb-2 md:mb-4 text-gray-800"
				>
					#0{{ index + 1 }} &ndash; {{ slide.title }}
				</h4>
				<p class="text-sm md:text-base text-gray-500 mb-6 md:mb-8">
					{{ slide.description }}
				</p>
				<div
					class="flex-1 bg-gray-200 rounded-lg md:rounded-xl overflow-hidden relative"
				>
					<div
						class="absolute inset-0 bg-gradient-to-t from-gray-300 to-transparent"
					>
						<NuxtImg width="50%" :src="slide.illustration" />
					</div>
				</div>
			</div>
		</div>
	</section>
</template>
