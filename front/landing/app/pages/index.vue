<script setup>
import gsap from "gsap";
import ScrollTrigger from "gsap/ScrollTrigger";

gsap.registerPlugin(ScrollTrigger);

let ctx;

onMounted(() => {
	ctx = gsap.context(() => {
		gsap.to(".dashboard-card", {
			scale: 0.85,
			rotateX: 4,
			opacity: 0.8,
			ease: "none",
			scrollTrigger: {
				trigger: ".dashboard-section",
				start: "center center",
				end: "+=100%",
				pin: true,
				scrub: 1,
			},
		});
	});
});

onUnmounted(() => {
	if (ctx) ctx.revert();
});
</script>

<template>
	<div
		class="bg-gray-50 min-h-screen font-sans text-gray-900 overflow-x-hidden"
	>
		<DefaultBanner :message="$t('in_developpement')" />
		<DefaultNavbar />
		<HeroSection />
		<ExampleStudio />
		<ExampleESKG />
		<ExampleMosaic />
		<ExampleDrone />
	</div>
</template>
