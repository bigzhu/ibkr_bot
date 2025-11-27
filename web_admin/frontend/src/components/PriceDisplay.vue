<template>
  <div class="text-weight-medium" :class="getValueColor(value)">
    {{ formatPrice }}
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { formatAmount, formatQuantity } from 'src/utils/formatters';

interface Props {
  value: string | number | null | undefined;
  type?: 'price' | 'amount' | 'quantity';
  showDollar?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  type: 'price',
  showDollar: false,
});

const formatPrice = computed(() => {
  if (!props.value || props.value === '' || props.value === null || props.value === undefined) {
    return '-';
  }

  let formatted = '';
  if (props.type === 'amount') {
    formatted = formatAmount(props.value);
  } else if (props.type === 'quantity') {
    formatted = formatQuantity(props.value);
  } else {
    // 价格类型: 使用 formatAmount 固定为 2 位小数(如 USDC 计价)
    formatted = formatAmount(props.value);
  }

  return props.showDollar ? `$${formatted}` : formatted;
});

const getValueColor = (value: Props['value']) => {
  if (value === null || value === undefined || value === '') {
    return 'text-grey-8';
  }

  const numericValue = typeof value === 'string' ? Number.parseFloat(value) : value;

  if (typeof numericValue !== 'number' || Number.isNaN(numericValue) || numericValue === 0) {
    return 'text-grey-8';
  }

  return '';
};
</script>
