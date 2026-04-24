<script setup>
const logs = ref([]);
let intervalId;

const generateEvent = () => {
	const eventTypes = [
		"ObstacleDetected",
		"PersonTracked",
		"PersonIdentityExtracted",
		"TrackLost",
	];

	const type = eventTypes[Math.floor(Math.random() * eventTypes.length)];
	const trackId = Math.floor(1000 + Math.random() * 9000);
	const nodeId = Math.floor(10 + Math.random() * 90);
	const now = new Date();
	const timestamp = `${now.getHours().toString().padStart(2, "0")}:${now.getMinutes().toString().padStart(2, "0")}:${now.getSeconds().toString().padStart(2, "0")}.${now.getMilliseconds().toString().padStart(3, "0")}`;
	const loc = `[${(48.8 + Math.random() * 0.1).toFixed(4)}, ${(2.3 + Math.random() * 0.1).toFixed(4)}]`;

	let payload = "";
	let colorClass = "";

	switch (type) {
		case "ObstacleDetected":
			colorClass = "text-yellow-400";
			payload = `{
  "id": ${Math.floor(Math.random() * 500)},
  "class": "Tree",
  "obb": { "center": [12.4, 5.1], "extents": [0.5, 2.0] },
  "confidence": ${(0.7 + Math.random() * 0.2).toFixed(2)}
}`;
			break;
		case "PersonTracked":
			colorClass = "text-blue-400";
			payload = `{
  "track_id": ${trackId},
  "obb": { "center": [8.2, -1.4], "extents": [0.6, 1.8] }
}`;
			break;
		case "PersonIdentityExtracted":
			colorClass = "text-purple-400";
			payload = `{
  "track_id": ${trackId},
  "embedding": [0.12, -0.45, 0.89, ...]
}`;
			break;
		case "TrackLost":
			colorClass = "text-red-400";
			payload = `${trackId}`;
			break;
	}

	return {
		id: Math.random().toString(36).substr(2, 9),
		timestamp,
		node: `zenoh:ringil/node-${nodeId}`,
		type,
		payload,
		colorClass,
		loc,
	};
};

onMounted(() => {
	for (let i = 0; i < 3; i++) {
		logs.value.push(generateEvent());
	}

	const loop = () => {
		logs.value.unshift(generateEvent());
		if (logs.value.length > 8) {
			logs.value.pop();
		}
		intervalId = setTimeout(loop, 800 + Math.random() * 1200);
	};

	intervalId = setTimeout(loop, 1000);
});

onUnmounted(() => {
	clearTimeout(intervalId);
});
</script>

<template>
	<div
		class="w-full max-w-2xl bg-[#0a0a0a] border border-zinc-800 rounded-xl overflow-hidden shadow-2xl flex flex-col font-mono text-[10px] md:text-xs"
	>
		<div
			class="flex items-center justify-between px-4 py-2 bg-zinc-900 border-b border-zinc-800"
		>
			<div class="flex gap-1.5">
				<div class="w-2.5 h-2.5 rounded-full bg-zinc-700"></div>
				<div class="w-2.5 h-2.5 rounded-full bg-zinc-700"></div>
				<div class="w-2.5 h-2.5 rounded-full bg-zinc-700"></div>
			</div>
			<div class="text-zinc-500 flex items-center gap-2">
				<span
					class="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"
				></span>
				Stream
			</div>
		</div>

		<div
			class="p-4 h-[350px] overflow-hidden relative flex flex-col justify-start"
		>
			<div
				class="absolute bottom-0 left-0 w-full h-16 bg-gradient-to-t from-[#0a0a0a] to-transparent z-10 pointer-events-none"
			></div>

			<TransitionGroup name="log-list" tag="div" class="flex flex-col gap-3">
				<div
					v-for="log in logs"
					:key="log.id"
					class="flex flex-col gap-1 text-zinc-300"
				>
					<div class="flex flex-wrap gap-2 text-zinc-500">
						<span>[{{ log.timestamp }}]</span>
						<span class="text-zinc-400">{{ log.node }}</span>
						<span>pos:{{ log.loc }}</span>
					</div>
					<div class="pl-4 border-l border-zinc-800">
						<span class="font-bold" :class="log.colorClass"
							>InstinctEvent::{{ log.type }}</span
						>
						<pre class="text-zinc-400 mt-1 whitespace-pre-wrap">{{
							log.payload
						}}</pre>
					</div>
				</div>
			</TransitionGroup>
		</div>
	</div>
</template>

<style scoped>
.log-list-move,
.log-list-enter-active,
.log-list-leave-active {
	transition: all 0.5s ease;
}
.log-list-enter-from {
	opacity: 0;
	transform: translateY(-20px);
}
.log-list-leave-to {
	opacity: 0;
	transform: translateY(20px);
}
</style>
