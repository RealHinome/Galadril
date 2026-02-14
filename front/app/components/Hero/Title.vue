<template>
	<h1
		class="text-5xl md:text-7xl lg:text-8xl font-serif tracking-tight text-slate-900 leading-[1.1]"
	>
		<slot name="title">{{ $t("title") }}</slot>
		<br />
		<span class="italic"
			><slot name="subtitle">{{ $t("subtitle") }}</slot></span
		>
	</h1>
</template>

<style scoped>
h1 {
	font-family: "Source Serif 4", serif;
}
</style>
