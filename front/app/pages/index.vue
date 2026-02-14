<template>
	<div
		class="relative min-h-screen w-full flex flex-col items-center justify-center overflow-hidden bg-white px-6"
	>
		<HeroBackground />

		<div
			class="relative z-10 max-w-4xl w-full flex flex-col items-center justify-center text-center space-y-8"
		>
			<NuxtImg
				class="w-52"
				width="150"
				alt="Logo"
				src="/favicon.png"
				draggable="false"
				format="webp"
			/>

			<HeroTitle />

			<HeroActions />

			<div class="max-w-2xl mx-auto pt-8">
				<p class="text-lg md:text-xl text-slate-600 leading-relaxed font-light">
					{{ $t("description") }}
				</p>
			</div>
		</div>
	</div>
</template>
