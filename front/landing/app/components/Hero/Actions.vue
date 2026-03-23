<template>
	<div class="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
		<NuxtLink
			to="https://github.com/RealHinome/Galadril"
			target="_blank"
			rel="noreferrer"
			class="w-full sm:w-56"
		>
			<button
				class="flex items-center justify-center w-full px-8 py-3 bg-black text-white rounded-full font-medium hover:bg-zinc-800 transition-colors duration-200"
			>
				<NuxtImg width="30" src="/github.svg" draggable="false" alt="GitHub" />
				<span class="ml-2">{{ $t("source_code") }}</span>
			</button>
		</NuxtLink>

		<NuxtLink to="https://realhinome.github.io/Galadril/" class="w-full sm:w-56">
			<button
				class="w-full px-8 py-3 rounded-full border border-slate-300 bg-white/50 backdrop-blur-md transition shadow-sm text-slate-800 font-medium"
			>
				{{ $t("read_documentation") }}
			</button>
		</NuxtLink>
	</div>
</template>
