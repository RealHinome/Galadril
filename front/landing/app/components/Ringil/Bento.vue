<template>
	<section
		class="bento-section py-24 px-6 md:px-12 max-w-7xl mx-auto z-10 relative"
	>
		<div class="grid grid-cols-1 md:grid-cols-3 gap-4 md:gap-6">
			<div
				class="bento-card col-span-1 bg-zinc-900/40 border border-white/5 rounded-[2rem] p-8 flex flex-col justify-between aspect-square"
			>
				<div>
					<svg
						class="w-6 h-6 text-zinc-400 mb-4"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
						stroke-width="1.5"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z"
						/>
					</svg>
					<h3 class="text-2xl font-serif mb-2">
						{{ $t("ringil.bento.agility.title") }}
					</h3>
					<p class="text-sm text-zinc-400">
						{{ $t("ringil.bento.agility.desc") }}
					</p>
				</div>
				<div class="text-6xl md:text-7xl font-light tracking-tighter">
					80<span class="text-xl text-zinc-500 font-mono tracking-normal ml-1"
						>km/h</span
					>
				</div>
			</div>

			<div
				class="bento-card col-span-1 md:col-span-2 bg-zinc-900/40 border border-white/5 rounded-[2rem] p-8 flex flex-col md:flex-row items-center relative overflow-hidden gap-6"
			>
				<div class="relative z-10 md:w-1/2">
					<svg
						class="w-6 h-6 text-zinc-400 mb-4"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
						stroke-width="1.5"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M8.25 3v1.5M4.5 8.25H3m18 0h-1.5M4.5 12H3m18 0h-1.5m-15 3.75H3m18 0h-1.5M8.25 19.5V21M12 3v1.5m0 15V21m3.75-18v1.5m0 15V21m-9-1.5h10.5a2.25 2.25 0 002.25-2.25V6.75a2.25 2.25 0 00-2.25-2.25H6.75A2.25 2.25 0 004.5 6.75v10.5a2.25 2.25 0 002.25 2.25zm.75-12h9v9h-9v-9z"
						/>
					</svg>
					<h3 class="text-2xl font-serif mb-3">
						{{ $t("ringil.bento.intelligence.title") }}
					</h3>
					<p class="text-zinc-400 text-sm leading-relaxed">
						{{ $t("ringil.bento.intelligence.desc") }}
					</p>
				</div>
				<div
					class="md:w-1/2 h-48 md:h-full w-full relative z-0 flex items-center justify-center"
				>
					<NuxtImg
						src="/illustrations/nvidia-jetson.webp"
						class="object-contain w-full h-full scale-125 opacity-70 drop-shadow-[0_0_20px_rgba(255,255,255,0.1)]"
						draggable="false"
						alt="Drone Component"
					/>
				</div>
			</div>

			<div
				class="bento-card col-span-1 md:col-span-3 bg-zinc-900/40 border border-white/5 rounded-[2rem] p-8 md:p-12 flex flex-col md:flex-row items-center gap-8"
			>
				<div class="md:w-1/2">
					<svg
						class="w-6 h-6 text-zinc-400 mb-4"
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
						stroke-width="1.5"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M15.75 17.25v3.375c0 .621-.504 1.125-1.125 1.125h-9.75a1.125 1.125 0 01-1.125-1.125V7.875c0-.621.504-1.125 1.125-1.125H6.75a9.06 9.06 0 011.5.124m7.5 10.376h3.375c.621 0 1.125-.504 1.125-1.125V11.25c0-4.46-3.243-8.161-7.5-8.876a9.06 9.06 0 00-1.5-.124H9.375c-.621 0-1.125.504-1.125 1.125v3.5m7.5 10.375H9.375a1.125 1.125 0 01-1.125-1.125v-9.25m12 6.625v-1.875a3.375 3.375 0 00-3.375-3.375h-1.5a1.125 1.125 0 01-1.125-1.125v-1.5a3.375 3.375 0 00-3.375-3.375H9.75"
						/>
					</svg>
					<h3 class="text-2xl font-serif mb-3">
						{{ $t("ringil.bento.scale.title") }}
					</h3>
					<p class="text-zinc-400 text-sm leading-relaxed max-w-md">
						{{ $t("ringil.bento.scale.desc") }}
					</p>
				</div>
				<div class="md:w-1/2 w-full flex justify-end">
					<div
						class="bg-black/50 border border-white/10 rounded-xl p-5 font-mono text-xs text-zinc-500 w-full max-w-sm"
					>
						<p>
							<span class="text-blue-400">root@galadril:</span>~$ push
							swarm_image_v2.1
						</p>
						<p>checking diffs...</p>
						<p class="text-green-400">✓ bit-to-bit match confirmed</p>
						<p>syncing 1,042 entities...</p>
					</div>
				</div>
			</div>
		</div>
	</section>
</template>
