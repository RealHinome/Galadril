<template>
	<section
		class="py-32 border-t border-white/5 bg-zinc-950 overflow-hidden relative"
	>
		<div
			class="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center gap-12 relative z-10"
		>
			<div
				class="w-full md:w-1/2 aspect-square relative bg-zinc-900/20 rounded-full border border-white/5"
			>
				<div class="w-full h-full relative flex items-center justify-center">
					<NuxtImg
						class="w-full h-full text-zinc-500 overflow-visible"
						src="/illustrations/mesh.svg"
						draggable="false"
						alt=""
					/>
				</div>
			</div>

			<div class="w-full md:w-1/2 md:pl-10">
				<h2 class="text-3xl md:text-5xl font-serif mb-6">
					{{ $t("ringil.mesh.title") }}
				</h2>
				<p class="text-zinc-400 text-lg font-light leading-relaxed mb-6">
					{{ $t("ringil.mesh.desc") }}
				</p>
			</div>
		</div>
	</section>
</template>
