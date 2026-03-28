<style scoped>
.perspective-1000 {
	perspective: 900px;
}
</style>

<template>
	<section
		class="dashboard-section h-[100svh] w-full flex items-center justify-center overflow-hidden bg-zinc-50 px-4 md:px-12 perspective-1000"
	>
		<div
			class="dashboard-card w-full max-w-6xl max-h-[85vh] aspect-[4/5] md:aspect-video bg-white rounded-xl md:rounded-2xl shadow-[0_25px_50px_-12px_rgba(251,191,36,0.15)] border border-amber-200/40 flex flex-col overflow-hidden relative z-10"
		>
			<div
				class="h-10 md:h-12 bg-zinc-50/80 flex items-center px-4 md:px-6 gap-4 border-b border-zinc-100 shrink-0"
			>
				<div class="flex gap-1.5">
					<div class="w-2.5 h-2.5 rounded-full bg-zinc-200"></div>
					<div class="w-2.5 h-2.5 rounded-full bg-zinc-200"></div>
					<div class="w-2.5 h-2.5 rounded-full bg-zinc-200"></div>
				</div>
				<div
					class="flex-1 bg-white h-7 rounded-md border border-zinc-200/60 flex items-center px-3 text-[10px] md:text-xs text-zinc-300 font-mono truncate"
				>
					https://galadril-studio/supply/factory/detroit
				</div>
				<div class="w-10"></div>
			</div>

			<NuxtImg
				src="/illustrations/galadril-factory.webp"
				width="1000"
				class="w-full h-full"
				draggable="false"
				alt="Galadril Studio for Detroit factory"
			/>
		</div>
	</section>
</template>
