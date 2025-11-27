<template>
  <div v-if="signalValue !== null && signalValue !== undefined" class="relative-position">
    <q-linear-progress
      :value="progressValue"
      size="20px"
      :color="signalColor"
      class="rounded-borders"
    />
    <div class="absolute-center text-white text-weight-medium text-caption">
      {{ signalValue }}
    </div>
  </div>
  <span v-else class="text-grey-8">-</span>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  signalValue: number | null | undefined;
  orderSide?: string | null | undefined;
  maxValue?: number; // 最大信号值,用于计算进度百分比
}

const props = withDefaults(defineProps<Props>(), {
  maxValue: 12,
});

// 计算进度值 (0-1之间)
const progressValue = computed(() => {
  if (props.signalValue === null || props.signalValue === undefined) {
    return 0;
  }

  return Math.min(Math.abs(props.signalValue) / props.maxValue, 1);
});

// 获取信号颜色 - 根据交易方向使用红/绿色系,强信号更亮,弱信号更暗
const signalColor = computed(() => {
  if (props.signalValue === null || props.signalValue === undefined) {
    return 'grey-8';
  }

  const strength = Math.abs(props.signalValue);

  // 根据交易方向决定颜色系
  if (props.orderSide === 'SELL') {
    // SELL使用红色系渐变 - 强信号更亮,弱信号更暗
    if (strength >= 9) return 'red-6'; // 强信号 - 较亮红色
    if (strength >= 4) return 'red-8'; // 中等信号 - 深红色
    return 'red-10'; // 弱信号 - 最深红色
  } else if (props.orderSide === 'BUY') {
    // BUY使用绿色系渐变 - 强信号更亮,弱信号更暗
    if (strength >= 9) return 'green-6'; // 强信号 - 较亮绿色
    if (strength >= 4) return 'green-8'; // 中等信号 - 深绿色
    return 'green-10'; // 弱信号 - 最深绿色
  } else {
    // 无交易方向时使用灰色系(兼容旧数据)
    if (strength >= 9) return 'grey-6';
    if (strength >= 4) return 'grey-8';
    return 'grey-10';
  }
});
</script>
