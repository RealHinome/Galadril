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

		const horizontalWrap = document.querySelector(".horizontal-wrap");
		const getScrollAmount = () =>
			-(
				horizontalWrap.scrollWidth -
				window.innerWidth +
				window.innerWidth * 0.1
			);

		gsap.to(".horizontal-wrap", {
			x: getScrollAmount,
			ease: "none",
			scrollTrigger: {
				trigger: ".horizontal-section",
				start: "top top",
				end: () => `+=${Math.abs(getScrollAmount())}`,
				pin: true,
				scrub: 1,
				invalidateOnRefresh: true,
			},
		});

		gsap.to(".expand-image", {
			width: "100vw",
			height: "100vh",
			borderRadius: "0px",
			ease: "power1.inOut",
			scrollTrigger: {
				trigger: ".image-section",
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
		<ExampleWrap />
		<ExampleExpand />
	</div>
</template>
