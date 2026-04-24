<template>
	<section
		class="relative h-[100svh] flex flex-col items-center justify-center px-6 overflow-hidden"
	>
		<div
			class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-zinc-800/30 blur-[120px] rounded-full pointer-events-none"
		></div>

		<div class="z-10 text-center max-w-4xl w-full mt-10">
			<div
				class="hero-element inline-flex items-center gap-2 px-3 py-1 mb-6 border border-white/10 bg-white/5 rounded-full text-xs font-mono tracking-widest text-zinc-400 uppercase"
			>
				<div class="w-1.5 h-1.5 rounded-full bg-white animate-pulse"></div>
				{{ $t("ringil.hero.project") }}
			</div>
			<h1
				class="hero-element text-5xl md:text-7xl lg:text-8xl font-serif tracking-tight mb-6"
			>
				{{ $t("ringil.hero.title_p1") }} <br />
				<span class="italic text-zinc-400">{{
					$t("ringil.hero.title_p2")
				}}</span>
			</h1>
			<p
				class="hero-element text-lg md:text-xl text-zinc-200 max-w-2xl mx-auto font-light leading-relaxed mb-8"
			>
				{{ $t("ringil.hero.description") }}
			</p>
			<NuxtLink
				to="https://github.com/RealHinome/Ringil"
				target="_blank"
				rel="noreferrer"
				class="hero-element inline-block"
			>
				<button
					class="px-8 py-3 bg-white text-black rounded-full font-medium hover:bg-zinc-200 transition-colors flex items-center gap-2"
				>
					<NuxtImg
						width="20"
						src="/github.svg"
						draggable="false"
						alt="GitHub"
						class="invert"
					/>
					{{ $t("ringil.hero.discover") }}
				</button>
			</NuxtLink>
		</div>

		<div
			class="hero-element absolute bottom-[-5%] w-full max-w-5xl h-[45vh] md:h-[55vh] flex justify-center pointer-events-none"
		>
			<NuxtImg
				src="/illustrations/drone.webp"
				alt="Drone Ringil"
				class="w-full h-full object-contain object-bottom opacity-80"
				draggable="false"
			/>
			<div
				class="absolute bottom-0 w-full h-1/3 bg-gradient-to-t from-black to-transparent"
			></div>
		</div>
	</section>
</template>
