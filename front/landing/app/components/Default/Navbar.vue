<template>
	<header
		class="top-0 w-full flex justify-between items-center px-6 md:px-8 py-4 md:py-6 z-50 mix-blend-difference text-white"
	>
		<div class="text-lg md:text-xl font-sans tracking-widest uppercase">
			Galadril
		</div>
		<div class="md:flex space-x-6 text-sm font-medium">
			<NuxtLink to="mailto:galadril@gravitalia.com" class="hover:opacity-70">{{
				$t("contact")
			}}</NuxtLink>
		</div>
	</header>
</template>
