<template>
  <q-chip
    v-if="timeframe"
    :color="getTimeframeColor(timeframe, orderSide)"
    text-color="white"
    size="sm"
    class="text-no-transform"
  >
    {{ timeframe }}
  </q-chip>
  <span v-else class="text-grey-5">-</span>
</template>

<script setup lang="ts">
interface Props {
  timeframe: string | null | undefined;
  orderSide?: string | null;
}

defineProps<Props>();

const getTimeframeColor = (timeframe: string, orderSide?: string | null) => {
  if (!timeframe) return 'grey-8';

  // 将时间周期转换为小写进行匹配
  const normalizedTimeframe = timeframe.toLowerCase();

  // 定义时间周期的重要性级别(数字越大越重要)
  const timeframeImportance: Record<string, number> = {
    '1m': 1, // 最不重要
    '3m': 2,
    '5m': 3,
    '15m': 4,
    '30m': 5,
    '1h': 6,
    '2h': 7,
    '4h': 8, // 最重要
  };

  const importance = timeframeImportance[normalizedTimeframe] || 1;

  // 根据交易方向和重要性决定颜色
  if (orderSide === 'SELL') {
    // SELL使用红色系 - 重要时间周期更亮
    if (importance >= 7) return 'red-6'; // 4h, 2h - 较亮红色,最重要
    if (importance >= 4) return 'red-8'; // 1h, 30m, 15m - 深红色,中等重要
    return 'red-10'; // 5m, 3m, 1m - 最深红色,不太重要
  } else if (orderSide === 'BUY') {
    // BUY使用绿色系 - 重要时间周期更亮
    if (importance >= 7) return 'green-6'; // 4h, 2h - 较亮绿色,最重要
    if (importance >= 4) return 'green-8'; // 1h, 30m, 15m - 深绿色,中等重要
    return 'green-10'; // 5m, 3m, 1m - 最深绿色,不太重要
  } else {
    // 无交易方向时使用灰色系(兼容旧数据)
    if (importance >= 7) return 'grey-6';
    if (importance >= 4) return 'grey-8';
    return 'grey-10';
  }
};
</script>
