<template>
  <q-chip v-if="side" :color="side === 'BUY' ? 'green-10' : 'red-10'" text-color="white" size="sm">
    {{ side }}
  </q-chip>
  <span v-else class="text-grey-5">-</span>
</template>

<script setup lang="ts">
interface Props {
  side: string | null | undefined;
}

defineProps<Props>();
</script>
