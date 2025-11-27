<template>
  <div class="text-weight-medium" :class="percentageColor">
    {{ formattedPercentage }}
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { formatAmount } from 'src/utils/formatters';

interface Props {
  value: string | number | null | undefined;
  precision?: number; // 小数位精度
  showSign?: boolean; // 是否显示正负号
}

const props = withDefaults(defineProps<Props>(), {
  precision: 2,
  showSign: true,
});

// 计算格式化后的百分比显示
const formattedPercentage = computed(() => {
  if (props.value === null || props.value === undefined || props.value === '') {
    return '-';
  }

  const numValue = Number(props.value);

  if (isNaN(numValue)) {
    return '-';
  }

  if (numValue === 0) {
    return '0%';
  }

  // 使用 formatAmount 进行格式化,然后添加 % 符号
  let formatted = formatAmount(numValue);

  // 添加正号(如果需要且为正数)
  if (props.showSign && numValue > 0) {
    formatted = '+' + formatted;
  }

  return formatted + '%';
});

// 计算百分比颜色
const percentageColor = computed(() => {
  if (props.value === null || props.value === undefined || props.value === '') {
    return 'text-grey-8';
  }

  const numValue = Number(props.value);

  if (isNaN(numValue) || numValue === 0) {
    return 'text-grey-8';
  }

  return numValue > 0 ? 'text-green-8' : 'text-red-8';
});
</script>
