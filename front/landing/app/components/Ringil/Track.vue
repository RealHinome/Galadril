<template>
	<section class="py-32 bg-black overflow-hidden flex flex-col items-center">
		<div class="text-center max-w-2xl px-6 mb-16 z-10">
			<h2 class="text-3xl md:text-5xl font-serif mb-4">
				{{ $t("ringil.track.title") }}
			</h2>
			<p class="text-zinc-400 font-light">{{ $t("ringil.track.desc") }}</p>
		</div>

		<div class="w-full max-w-4xl px-6">
			<ExampleTrack />
		</div>
	</section>
</template>
