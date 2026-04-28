<script setup lang="ts">
const props = defineProps(["data", "highlightId"]);
const cyRef = ref(null);
let cy: any = null;

const applyStyles = (id: string | null) => {
	if (!cy) return;
	cy.elements().removeClass("simulated");
	if (id) {
		const el = cy.getElementById(id);
		el.addClass("simulated");
		el.successors().addClass("simulated");
	}
};

onMounted(async () => {
	const cytoscape = (await import("cytoscape")).default;

	cy = cytoscape({
		container: cyRef.value,
		minZoom: 0.7,
		maxZoom: 1.2,
		elements: [
			...props.data.nodes.map((n) => ({ data: n })),
			...props.data.edges.map((e, i) => ({ data: { id: `e${i}`, ...e } })),
		],
		style: [
			{
				selector: "node",
				style: {
					width: 28,
					height: 28,
					"background-color": "#ffffff",
					"border-width": 1.5,
					"border-color": "#e2e8f0",
					label: "data(label)",
					"text-valign": "bottom",
					"text-margin-y": 8,
					color: "#64748b",
					"font-family": "Inter, sans-serif",
					"font-size": "9px",
					"font-weight": 600,
					shape: "round-rectangle",
				},
			},
			{
				selector: "node[type='Event']",
				style: {
					"border-color": "#f59e0b",
					"background-color": "#fffbeb",
				},
			},
			{
				selector: "node[type='State']",
				style: {
					"border-color": "#475569",
					"background-color": "#f8fafc",
				},
			},
			{
				selector: "edge",
				style: {
					width: 1.2,
					"line-color": "#cbd5e1",
					"curve-style": "bezier",
					"control-point-step-size": 40,
					"target-arrow-shape": "navajowhite",
					"target-arrow-color": "#cbd5e1",
					"arrow-scale": 0.5,
					opacity: 0.4,
				},
			},
			{
				selector: ".simulated",
				style: {
					"border-color": "#f59e0b",
					"border-width": 3,
					"line-color": "#f59e0b",
					"target-arrow-color": "#f59e0b",
					opacity: 1,
					color: "#b45309",
				},
			},
		],
		layout: {
			name: "breadthfirst",
			directed: true,
			padding: 40,
			spacingFactor: 1.2,
		},
	});

	watch(
		() => props.highlightId,
		(newVal) => applyStyles(newVal),
		{ immediate: true },
	);
});
</script>

<template>
	<div class="w-full h-full bg-[#fafaf9]">
		<div ref="cyRef" class="w-full h-full relative z-10"></div>
		<div class="absolute inset-0 pointer-events-none opacity-[0.03]"></div>
	</div>
</template>
