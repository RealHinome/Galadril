<script setup>
import { useI18n } from "vue-i18n";
import {
  MagnifyingGlassIcon,
  BoltIcon,
  DocumentTextIcon,
  PlusCircleIcon,
} from "@heroicons/vue/24/outline";

const props = defineProps({
  isOpen: Boolean,
});

const { t } = useI18n();
const emit = defineEmits(["close", "select"]);
const searchQuery = ref("");
const inputRef = ref(null);
const activeIndex = ref(0);

const commands = computed(() => [
  {
    label: t("command_palette.commands.approve_all.label"),
    description: t("command_palette.commands.approve_all.description"),
    type: t("command_palette.commands.approve_all.type"),
    icon: BoltIcon,
  },
  {
    label: t("command_palette.commands.generate_report.label"),
    description: t("command_palette.commands.generate_report.description"),
    type: t("command_palette.commands.generate_report.type"),
    icon: DocumentTextIcon,
  },
  {
    label: t("command_palette.commands.create_dashboard.label"),
    description: t("command_palette.commands.create_dashboard.description"),
    type: t("command_palette.commands.create_dashboard.type"),
    icon: PlusCircleIcon,
    href: "/builder",
  },
]);

const filteredResults = computed(() => {
  if (!searchQuery.value) return commands.value;
  return commands.value.filter(
    (c) =>
      c.label.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      c.type.toLowerCase().includes(searchQuery.value.toLowerCase()),
  );
});

const close = () => {
  emit("close");
};

const selectItem = async (item) => {
  if (item) {
    if (item.href) {
      await navigateTo(item.href, { external: true });
    } else {
      emit("select", item);
    }
    close();
  }
};

watch(
  () => props.isOpen,
  (newVal) => {
    if (newVal) {
      activeIndex.value = 0;
      setTimeout(() => inputRef.value?.focus(), 50);
    } else {
      searchQuery.value = "";
    }
  },
);

watch(searchQuery, () => {
  activeIndex.value = 0;
});

const handleKeyDown = (e) => {
  if (!props.isOpen) return;

  if (e.key === "Escape") {
    e.preventDefault();
    close();
  } else if (e.key === "ArrowDown") {
    e.preventDefault();
    activeIndex.value = (activeIndex.value + 1) % filteredResults.value.length;
  } else if (e.key === "ArrowUp") {
    e.preventDefault();
    activeIndex.value =
      (activeIndex.value - 1 + filteredResults.value.length) %
      filteredResults.value.length;
  } else if (e.key === "Enter") {
    e.preventDefault();
    selectItem(filteredResults.value[activeIndex.value]);
  }
};

onMounted(() => {
  window.addEventListener("keydown", handleKeyDown);
});

onUnmounted(() => {
  window.removeEventListener("keydown", handleKeyDown);
});
</script>

<template>
  <Teleport to="body">
    <Transition
      enter-active-class="transition-opacity duration-200 ease-out"
      enter-from-class="opacity-0"
      enter-to-class="opacity-100"
      leave-active-class="transition-opacity duration-150 ease-in"
      leave-from-class="opacity-100"
      leave-to-class="opacity-0"
    >
      <div
        v-if="isOpen"
        @click="close"
        class="fixed inset-0 bg-slate-900/40 backdrop-blur-[2px] z-[100] flex justify-center pt-32 p-4"
      >
        <div
          @click.stop
          class="bg-white border border-slate-200 w-full max-w-[600px] h-fit rounded-2xl shadow-2xl overflow-hidden flex flex-col"
        >
          <div class="flex items-center border-b border-slate-100 px-4 py-4">
            <MagnifyingGlassIcon class="w-6 h-6 text-slate-400 mr-3" />
            <input
              ref="inputRef"
              v-model="searchQuery"
              type="text"
              :placeholder="$t('command_palette.placeholder')"
              class="w-full bg-transparent border-none focus:ring-0 text-md text-slate-900 outline-none placeholder:text-slate-400"
            />
          </div>

          <div class="max-h-[400px] overflow-y-auto p-2">
            <div
              v-if="searchQuery === ''"
              class="px-3 py-2 text-[11px] text-slate-400 uppercase tracking-wider"
            >
              {{ $t("command_palette.sections.quick_actions") }}
            </div>

            <div class="space-y-1">
              <div
                v-for="(item, index) in filteredResults"
                :key="index"
                @mouseenter="activeIndex = index"
                @click="selectItem(item)"
                :class="[
                  'flex items-center px-3 py-3 rounded-xl cursor-pointer transition-colors group',
                  activeIndex === index ? 'bg-amber-50' : 'hover:bg-amber-50',
                ]"
              >
                <component
                  :is="item.icon"
                  :class="[
                    'w-5 h-5 mr-3 transition-colors',
                    activeIndex === index
                      ? 'text-amber-600'
                      : 'text-slate-400 group-hover:text-amber-600',
                  ]"
                />
                <div class="flex-1">
                  <div
                    :class="[
                      'text-sm font-medium transition-colors',
                      activeIndex === index
                        ? 'text-slate-900'
                        : 'text-slate-700 group-hover:text-slate-900',
                    ]"
                  >
                    {{ item.label }}
                  </div>
                  <div
                    :class="[
                      'text-xs transition-colors',
                      activeIndex === index
                        ? 'text-amber-700/60'
                        : 'text-slate-400 group-hover:text-amber-700/60',
                    ]"
                  >
                    {{ item.description }}
                  </div>
                </div>
                <div
                  :class="[
                    'text-[10px] font-medium px-2 py-1 rounded-md uppercase transition-colors',
                    activeIndex === index
                      ? 'text-amber-400 bg-amber-100'
                      : 'text-slate-300 bg-slate-50 group-hover:text-amber-400 group-hover:bg-amber-100',
                  ]"
                >
                  {{ item.type }}
                </div>
              </div>
            </div>
          </div>

          <div
            class="bg-slate-50 px-4 py-3 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400"
          >
            <div class="flex space-x-4">
              <span
                ><kbd
                  class="bg-white border border-slate-200 px-1 rounded shadow-sm text-slate-500"
                  >↑↓</kbd
                >
                {{ $t("command_palette.footer.navigate") }}</span
              >
              <span
                ><kbd
                  class="bg-white border border-slate-200 px-1 rounded shadow-sm text-slate-500"
                  >enter</kbd
                >
                {{ $t("command_palette.footer.select") }}</span
              >
            </div>
            <span
              >{{ $t("command_palette.footer.press") }}
              <kbd
                class="bg-white border border-slate-200 px-1 rounded shadow-sm text-slate-500"
                >esc</kbd
              >
              {{ $t("command_palette.footer.close") }}</span
            >
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>
