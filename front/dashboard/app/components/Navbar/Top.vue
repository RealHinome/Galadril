<script setup>
import { computed, onMounted, onUnmounted } from "vue";
import { useRoute } from "vue-router";
import {
  HomeIcon,
  ChevronRightIcon,
  ChevronDownIcon,
  MagnifyingGlassIcon,
} from "@heroicons/vue/24/outline";

const emit = defineEmits(["open-command"]);
const route = useRoute();
const { t, te } = useI18n();

const breadcrumbs = computed(() => {
  const pathNodes = route.path.split("/").filter((node) => node !== "");

  return pathNodes.map((node, index) => {
    const path = "/" + pathNodes.slice(0, index + 1).join("/");

    const i18nKey = `routes.${node}`;
    const label = te(i18nKey)
      ? t(i18nKey)
      : node.replace(/-/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());

    return {
      label,
      path,
      isLast: index === pathNodes.length - 1,
    };
  });
});

const handleGlobalKeyDown = (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === "k") {
    event.preventDefault();
    emit("open-command");
  }
};

onMounted(() => {
  window.addEventListener("keydown", handleGlobalKeyDown);
});

onUnmounted(() => {
  window.removeEventListener("keydown", handleGlobalKeyDown);
});
</script>

<template>
  <nav
    class="flex items-center justify-between h-14 px-4 bg-white border-b border-zinc-200 text-zinc-900 select-none shadow-sm relative z-40"
  >
    <div class="flex items-center space-x-1 text-sm font-medium">
      <NuxtLink
        to="/"
        class="flex items-center hover:bg-zinc-100 px-2 py-1.5 rounded-lg cursor-pointer transition group"
      >
        <HomeIcon
          class="w-4 h-4 mr-2 text-zinc-400 group-hover:text-amber-600"
        />
        <span class="text-zinc-700 group-hover:text-zinc-950">
          {{ $t("navbar.brand") }}
        </span>
      </NuxtLink>

      <template v-for="(crumb, index) in breadcrumbs" :key="crumb.path">
        <ChevronRightIcon class="w-3.5 h-3.5 text-zinc-300" />

        <div v-if="!crumb.isLast" class="relative group">
          <NuxtLink
            :to="crumb.path"
            class="flex items-center hover:bg-amber-50 px-2 py-1.5 rounded-lg cursor-pointer transition"
          >
            <span class="text-amber-700">{{ crumb.label }}</span>
            <ChevronDownIcon class="w-3 h-3 ml-1.5 text-amber-400" />
          </NuxtLink>

          <div
            class="absolute left-0 mt-1 w-48 bg-white border border-zinc-200 rounded-lg shadow-lg opacity-0 group-hover:opacity-100 translate-y-1 group-hover:translate-y-0 transition-all pointer-events-none group-hover:pointer-events-auto p-1 z-50"
          >
            <NuxtLink
              :to="crumb.path"
              class="block px-3 py-2 text-xs text-zinc-700 hover:bg-zinc-100 rounded-md"
            >
              {{ crumb.label }} {{ $t("navbar.breadcrumbs.overview_suffix") }}
            </NuxtLink>
            <div class="h-px bg-zinc-100 my-1"></div>
            <span
              class="block px-3 py-1 text-[10px] text-zinc-400 uppercase font-bold"
            >
              {{ $t("navbar.breadcrumbs.quick_access") }}
            </span>
            <a
              href="#"
              class="block px-3 py-2 text-xs text-zinc-700 hover:bg-zinc-100 rounded-md"
            >
              {{ $t("navbar.breadcrumbs.analytics") }}
            </a>
          </div>
        </div>

        <span v-else class="px-2 py-1.5 text-zinc-500 font-normal">
          {{ crumb.label }}
        </span>
      </template>
    </div>

    <button
      @click="$emit('open-command')"
      class="flex items-center bg-zinc-50 border border-zinc-200 px-3 py-1.5 rounded-xl text-zinc-500 hover:border-amber-400 hover:bg-amber-50 transition-all group w-72"
    >
      <MagnifyingGlassIcon class="w-4 h-4 mr-2.5 group-hover:text-amber-600" />
      <span class="text-sm flex-1 text-left">
        {{ $t("navbar.search.placeholder") }}
      </span>
      <kbd
        class="hidden sm:inline-block px-1.5 py-0.5 border border-zinc-200 rounded-md bg-white text-zinc-400 text-[10px] font-sans group-hover:border-amber-300 group-hover:text-amber-600"
      >
        {{ $t("navbar.search.shortcut") }}
      </kbd>
    </button>
  </nav>
</template>
