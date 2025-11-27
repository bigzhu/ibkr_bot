<template>
  <div :class="getAmountColor(value)">
    {{ formatAmount }}
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { formatQuantity } from 'src/utils/formatters';

interface Props {
  value: string | number | null | undefined;
  showDollar?: boolean;
  type?: 'normal' | 'income' | 'expense'; // 显示类型:正常/收入/支出
}

const props = withDefaults(defineProps<Props>(), {
  showDollar: true,
  type: 'normal',
});

const formatAmount = computed(() => {
  if (!props.value || props.value === '' || props.value === null || props.value === undefined) {
    return '-';
  }

  const formatted = formatQuantity(props.value);
  return props.showDollar ? `$${formatted}` : formatted;
});

const getAmountColor = (value: number | string | null | undefined) => {
  const numericValue = typeof value === 'string' ? Number.parseFloat(value) : value;

  // 处理空值,无效值和零值,统一显示灰色
  if (
    value === null ||
    value === undefined ||
    value === '' ||
    typeof numericValue !== 'number' ||
    Number.isNaN(numericValue) ||
    numericValue === 0
  ) {
    return 'text-grey-8';
  }

  // 如果是负数,无论什么类型都显示红色
  if (numericValue < 0) {
    return 'text-negative';
  }

  // 根据type参数决定颜色
  if (props.type === 'income') {
    return 'text-positive'; // 收入用绿色
  } else if (props.type === 'expense') {
    return 'text-negative'; // 支出用红色
  }

  return ''; // 默认不指定颜色,使用默认文本颜色
};
</script>
