<template>
  <q-badge
    :color="getStatusColor(status)"
    :label="getStatusLabel(status)"
    class="q-px-sm q-py-xs"
  />
</template>

<script setup lang="ts">
interface Props {
  status: string | null | undefined;
}

defineProps<Props>();

const getStatusColor = (status: string | null | undefined) => {
  if (!status) return 'grey';

  switch (status) {
    case 'FILLED':
      return 'positive';
    case 'PARTIALLY_FILLED':
      return 'warning';
    case 'CANCELED':
      return 'negative';
    case 'PENDING':
      return 'info';
    default:
      return 'warning';
  }
};

const getStatusLabel = (status: string | null | undefined) => {
  if (!status) return '-';

  switch (status) {
    case 'FILLED':
      return '已成交';
    case 'PARTIALLY_FILLED':
      return '部分成交';
    case 'CANCELED':
      return '已取消';
    case 'PENDING':
      return '等待中';
    default:
      return status;
  }
};
</script>
