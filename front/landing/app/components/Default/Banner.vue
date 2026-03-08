<script setup>
defineProps({
	message: {
		type: String,
	},
	showClose: {
		type: Boolean,
		default: false,
	},
});

const emit = defineEmits(["close"]);
</script>

<template>
	<div
		class="relative w-full overflow-hidden border-b border-white/10 bg-white/5 backdrop-blur-xl before:absolute before:inset-y-0 before:-left-full before:w-full before:bg-gradient-to-r before:from-transparent before:via-white/[0.03] before:to-transparent"
	>
		<div
			class="absolute inset-0 bg-gradient-to-r from-transparent via-gray-500/5 to-transparent"
		></div>

		<div
			class="relative mx-auto flex max-w-7xl items-center justify-between px-4 py-3"
		>
			<div class="flex-1 flex justify-center">
				<p class="text-[13px] tracking-tight text-gray-400 font-light">
					{{ message }}
				</p>
			</div>

			<button
				v-if="showClose"
				@click="emit('close')"
				class="ml-4 text-gray-500 hover:text-white transition-colors"
				aria-label="Fermer"
			>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					width="16"
					height="16"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="1.5"
					stroke-linecap="round"
					stroke-linejoin="round"
				>
					<path d="M18 6 6 18" />
					<path d="m6 6 12 12" />
				</svg>
			</button>
		</div>
	</div>
</template>
