<style scoped>
.perspective-1000 {
	perspective: 1000px;
}
</style>

<template>
	<section
		class="dashboard-section h-[100svh] flex items-center justify-center overflow-hidden perspective-1000 px-4 md:px-8 relative bg-zinc-50"
	>
		<!--
      <div class="absolute w-[60%] h-[60%] bg-amber-400/30 rounded-full blur-[120px] animate-pulse-slow z-0"></div>
      <div class="absolute w-[40%] h-[40%] bg-yellow-500/20 rounded-full blur-[80px] z-0"></div>
      -->

		<div
			class="dashboard-card w-full max-w-md lg:max-w-4xl 2xl:lg:max-w-6xl aspect-[1/2] lg:aspect-[4/3] md:aspect-video bg-white rounded-xl md:rounded-2xl shadow-[0_0_50px_-12px_rgba(251,191,36,0.4)] border border-amber-200/50 overflow-hidden flex flex-col transform-gpu origin-center relative z-10"
		>
			<div
				class="h-10 md:h-12 bg-zinc-100 flex items-center px-3 md:px-4 gap-2 border-b border-zinc-200"
			>
				<div class="flex gap-1.5">
					<div
						class="w-2.5 h-2.5 md:w-3 md:h-3 rounded-full bg-zinc-400/50"
					></div>
					<div
						class="w-2.5 h-2.5 md:w-3 md:h-3 rounded-full bg-zinc-400/50"
					></div>
					<div
						class="w-2.5 h-2.5 md:w-3 md:h-3 rounded-full bg-zinc-400/50"
					></div>
				</div>
				<div
					class="ml-2 md:ml-4 flex-1 bg-white h-6 rounded border border-zinc-200 flex items-center px-2 md:px-3 text-[10px] md:text-xs text-zinc-500/60 font-mono truncate"
				>
					https://galadril-studio/system/3
				</div>
			</div>

			<div class="flex-1 p-4 md:p-8 relative">
				<!--
            <div class="absolute inset-0 opacity-[0.1]" style="background-image: radial-gradient(#d1d5db 1px, transparent 1px); background-size: 24px 24px;"></div>
        -->

				<div
					class="relative z-10 h-full flex flex-col gap-4 md:gap-6 animate-pulse-slow"
				>
					<div
						class="flex items-center justify-between border-b border-zinc-100 pb-4"
					>
						<div class="space-y-1">
							<div class="h-5 w-32 bg-zinc-200/50 rounded"></div>
							<div class="h-3 w-48 bg-zinc-100/60 rounded"></div>
						</div>
						<div class="flex gap-2">
							<div class="h-8 w-8 bg-zinc-100/40 rounded-full"></div>
							<div class="h-8 w-24 bg-zinc-200/60 rounded-lg"></div>
						</div>
					</div>

					<div class="grid grid-cols-12 gap-4 flex-1">
						<div
							class="col-span-3 space-y-4 hidden md:block border-r border-zinc-100 pr-4"
						>
							<div class="h-3 w-16 bg-zinc-200/40 rounded mb-4"></div>
							<div
								class="h-10 w-full bg-white border border-zinc-200/70 rounded-md"
							></div>
							<div class="h-3 w-20 bg-zinc-200/40 rounded pt-4"></div>
							<div
								class="h-10 w-full bg-white border border-zinc-200/70 rounded-md"
							></div>
						</div>

						<div class="col-span-12 md:col-span-9 grid grid-cols-2 gap-4">
							<div
								class="bg-white p-4 rounded-xl border border-zinc-100 shadow-sm flex flex-col"
							>
								<div class="h-3 w-2/3 bg-zinc-100/80 rounded mb-6"></div>
								<div class="flex-1 flex items-end gap-2 px-2">
									<div class="w-full bg-zinc-100/60 rounded-t h-[40%]"></div>
									<div class="w-full bg-zinc-300/40 rounded-t h-[80%] relative">
										<div
											class="absolute bottom-0 w-full bg-zinc-400/50 h-1/2 rounded-t"
										></div>
									</div>
									<div class="w-full bg-zinc-100/60 rounded-t h-[60%]"></div>
								</div>
							</div>

							<div
								class="bg-white p-4 rounded-xl border border-zinc-200 shadow-sm flex flex-col"
							>
								<div class="h-3 w-1/2 bg-zinc-100/80 rounded mb-6"></div>
								<div class="flex-1 flex items-end gap-1">
									<div class="flex-1 bg-zinc-100/80 h-[20%] rounded-t"></div>
									<div class="flex-1 bg-zinc-100/80 h-[50%] rounded-t"></div>
									<div class="flex-1 bg-zinc-300/50 h-[90%] rounded-t"></div>
									<div class="flex-1 bg-zinc-300/50 h-[75%] rounded-t"></div>
									<div class="flex-1 bg-zinc-100/80 h-[40%] rounded-t"></div>
								</div>
							</div>

							<div
								class="col-span-2 bg-white p-4 rounded-xl border border-zinc-200 shadow-sm flex flex-col"
							>
								<div class="h-3 w-1/4 bg-zinc-100/80 rounded mb-4"></div>
								<div class="flex-1 relative overflow-hidden">
									<svg
										viewBox="0 0 400 100"
										class="w-full h-full stroke-zinc-400/50 fill-zinc-400/10 stroke-2"
									>
										<path
											d="M0,80 Q50,20 100,70 T200,40 T300,60 T400,20 L400,100 L0,100 Z"
										/>
									</svg>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	</section>
</template>
