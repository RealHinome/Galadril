<template>
	<section
		class="py-32 border-t border-white/5 bg-zinc-950 overflow-hidden relative"
	>
		<div
			class="max-w-7xl mx-auto px-6 flex flex-col lg:flex-row items-center justify-between gap-16 relative z-10"
		>
			<div class="w-full lg:w-1/2 flex flex-col items-start text-left">
				<NuxtImg
					class="w-16 md:w-20 mb-8 opacity-60"
					alt="Galadril Logo"
					src="/favicon.webp"
					draggable="false"
					format="webp"
				/>
				<h2 class="text-3xl md:text-5xl font-serif mb-6">
					{{ $t("ringil.galadril.title") }}
				</h2>
				<p class="text-zinc-400 text-lg font-light leading-relaxed mb-10">
					{{ $t("ringil.galadril.desc_p1") }} <strong>Zenoh</strong>
					{{ $t("ringil.galadril.desc_p2") }}
				</p>
				<NuxtLink to="/">
					<button
						class="px-8 py-3 border border-white/20 text-white rounded-full font-medium hover:bg-white hover:text-black transition-colors flex items-center gap-2"
					>
						{{ $t("ringil.galadril.explore") }}
						<svg
							xmlns="http://www.w3.org/2000/svg"
							fill="none"
							viewBox="0 0 24 24"
							stroke-width="2"
							stroke="currentColor"
							class="w-4 h-4"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3"
							/>
						</svg>
					</button>
				</NuxtLink>
			</div>

			<div class="w-full lg:w-1/2 flex justify-center lg:justify-end">
				<ExampleEventStream />
			</div>
		</div>
	</section>
</template>
