<template>
	<section
		class="relative flex flex-col items-center justify-center pt-12 2xl:pt-24 pb-12 px-4 md:px-8"
	>
		<div
			class="relative z-10 max-w-4xl w-full flex flex-col items-center justify-center text-center space-y-8"
		>
			<div
				class="absolute inset-0 -z-10 bg-zinc-400/20 blur-3xl rounded-full scale-75"
			></div>
			<NuxtImg
				class="w-32 lg:w-48 2xl:w-52"
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
	</section>
</template>
