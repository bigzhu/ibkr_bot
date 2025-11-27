<template>
  <q-td
    :props="props"
    :class="{ 'disabled-cell': !isActive }"
    class="text-right"
  >
    <slot />
  </q-td>
</template>

<script setup lang="ts">
interface Props {
  props: Record<string, unknown>;
  isActive: boolean;
}

withDefaults(defineProps<Props>(), {
  isActive: true,
});
</script>
