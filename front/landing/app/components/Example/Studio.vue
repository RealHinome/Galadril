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
					https://galadril-studio/system/3
				</div>
				<div class="w-10"></div>
			</div>

			<div
				class="flex-1 p-4 md:p-8 flex flex-col gap-4 md:gap-8 overflow-hidden animate-pulse"
			>
				<div class="flex items-center justify-between shrink-0">
					<div class="space-y-2">
						<div class="h-4 md:h-5 w-32 md:w-48 bg-zinc-100 rounded"></div>
						<div class="h-2 md:h-2.5 w-24 md:w-32 bg-zinc-50 rounded"></div>
					</div>
					<div class="h-8 w-8 md:h-10 md:w-10 bg-zinc-50 rounded-full"></div>
				</div>

				<div
					class="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-8 min-h-0"
				>
					<div
						class="bg-white p-4 rounded-xl border border-zinc-100/80 shadow-sm flex flex-col relative overflow-hidden"
					>
						<div class="h-2 w-16 bg-zinc-100 rounded-full mb-8"></div>
						<div class="flex-1 flex items-end justify-center gap-4">
							<div class="w-4 md:w-6 bg-zinc-50 rounded-t h-[30%]"></div>
							<div
								class="w-4 md:w-6 bg-zinc-200 rounded-t h-[65%] relative overflow-hidden"
							>
								<div class="absolute top-0 w-full bg-zinc-100 h-1/2"></div>
							</div>
							<div class="w-4 md:w-6 bg-zinc-50 rounded-t h-[45%]"></div>
						</div>
					</div>

					<div
						class="bg-white p-4 rounded-xl border border-zinc-100/80 shadow-sm flex flex-col"
					>
						<div class="h-2 w-16 bg-zinc-100 rounded-full mb-8"></div>
						<div class="flex-1 flex items-end gap-2 px-2">
							<div class="flex-1 bg-zinc-50 h-[30%] rounded-t-sm"></div>
							<div class="flex-1 bg-zinc-100 h-[70%] rounded-t-sm"></div>
							<div class="flex-1 bg-zinc-200 h-[50%] rounded-t-sm"></div>
							<div class="flex-1 bg-zinc-50 h-[20%] rounded-t-sm"></div>
						</div>
					</div>

					<div
						class="md:col-span-2 bg-white rounded-xl border border-zinc-100/80 shadow-sm flex flex-col relative min-h-[120px] md:min-h-0"
					>
						<div class="p-4 relative z-10">
							<div class="h-2 w-16 bg-zinc-100 rounded-full"></div>
						</div>
						<div class="absolute inset-0 top-12 overflow-hidden">
							<svg
								viewBox="0 0 1000 200"
								preserveAspectRatio="none"
								class="w-full h-full scale-110 translate-y-4"
							>
								<path
									d="M-50,180 C100,200 200,20 350,150 C500,280 650,50 800,160 C900,240 1050,100 1100,180 L1100,300 L-50,300 Z"
									fill="none"
									stroke="#e4e4e7"
									stroke-width="2"
								/>
								<path
									d="M-50,180 C100,200 200,20 350,150 C500,280 650,50 800,160 C900,240 1050,100 1100,180 L1100,300 L-50,300 Z"
									class="fill-zinc-50/30"
								/>
							</svg>
						</div>
					</div>
				</div>
			</div>
		</div>
	</section>
</template>
