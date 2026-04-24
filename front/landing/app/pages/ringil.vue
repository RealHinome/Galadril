<script setup>
import gsap from "gsap";
import ScrollTrigger from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

let ctx;

onMounted(() => {
	ctx = gsap.context(() => {
		gsap.from(".hero-element", {
			y: 40,
			opacity: 0,
			duration: 1.2,
			stagger: 0.15,
			ease: "power3.out",
			delay: 0.2,
		});

		gsap.from(".bento-card", {
			scrollTrigger: {
				trigger: ".bento-section",
				start: "top 80%",
			},
			y: 30,
			opacity: 0,
			duration: 0.8,
			stagger: 0.1,
			ease: "power2.out",
		});
	});
});

onUnmounted(() => {
	if (ctx) ctx.revert();
});
</script>

<template>
	<div
		class="bg-black min-h-screen font-sans text-white overflow-x-hidden selection:bg-zinc-800 selection:text-white"
	>
		<DefaultNavbar class="absolute top-0 w-full z-50" />
		<RingilHero />
		<RingilBento />
		<RingilMesh />
		<RingilTrack />
		<RingilGaladril />
	</div>
</template>
