<script setup>
import gsap from "gsap";
import ScrollTrigger from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

let ctx;

onMounted(() => {
	ctx = gsap.context(() => {
		const tlVision = gsap.timeline({
			scrollTrigger: {
				trigger: ".vision-container",
				start: "top 70%",
				end: "+=30%",
				scrub: 1,
			},
		});
		tlVision
			.to(".bounding-box", {
				width: "120px",
				height: "180px",
				opacity: 1,
				ease: "none",
			})
			.to(".vision-target", { opacity: 1, duration: 0.5 }, "<");
	});
});

onUnmounted(() => {
	if (ctx) ctx.revert();
});
</script>

<template>
	<div
		class="vision-container relative w-full aspect-[21/9] bg-zinc-900/50 border border-zinc-800 rounded-xl overflow-hidden flex items-center justify-center"
	>
		<svg viewBox="0 0 400 200" class="w-full h-full text-zinc-700" fill="none">
			<pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
				<path
					d="M 20 0 L 0 0 0 20"
					fill="none"
					stroke="currentColor"
					stroke-width="0.5"
					stroke-opacity="0.2"
				/>
			</pattern>
			<rect width="400" height="200" fill="url(#grid)" />

			<path
				class="vision-target opacity-20 transition-opacity"
				d="M190 80 Q200 70 210 80 L215 120 L205 180 L195 180 L185 120 Z M200 60 A10 10 0 1 0 200 40 A10 10 0 1 0 200 60"
				fill="currentColor"
			/>
		</svg>

		<div
			class="bounding-box absolute w-[20px] h-[20px] border-2 border-red-500 bg-red-500/10 opacity-0 pointer-events-none flex items-start"
		>
			<span
				class="bg-red-500 text-white text-[10px] font-mono px-1 py-0.5 -mt-5 uppercase whitespace-nowrap"
				>ID: 8492 [98%]</span
			>
		</div>

		<div class="absolute top-4 left-4 flex gap-2">
			<span
				class="px-2 py-1 bg-black/80 border border-zinc-700 rounded text-[10px] font-mono text-zinc-400"
				>CAM_FRONT</span
			>
			<span
				class="px-2 py-1 bg-black/80 border border-zinc-700 rounded text-[10px] font-mono text-red-400 flex items-center gap-1"
			>
				<span class="w-1.5 h-1.5 bg-red-500 rounded-full animate-pulse"></span>
				REC
			</span>
		</div>
	</div>
</template>
