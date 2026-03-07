<template>
	<div class="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
		<NuxtLink
			to="https://github.com/RealHinome/Galadril"
			target="_blank"
			rel="noreferrer"
		>
			<button
				class="flex px-8 py-3 bg-black text-white rounded-full font-medium hover:bg-zinc-800 transition-colors duration-200"
			>
				<NuxtImg width="30" src="/github.svg" draggable="false" alt="GitHub" />
				<span class="mt-0.5 ml-2">{{ $t("source_code") }}</span>
			</button>
		</NuxtLink>

		<NuxtLink to="/docs">
			<button
				class="px-8 py-3 rounded-full border border-gray-300 bg-white/50 backdrop-blur-md hover:bg-gray-100 transition shadow-sm text-gray-800 font-medium"
			>
				{{ $t("read_documentation") }}
			</button>
		</NuxtLink>
	</div>
</template>
