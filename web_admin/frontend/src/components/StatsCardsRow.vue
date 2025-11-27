<template>
  <div class="stats-cards-row" :class="containerClass">
    <div v-for="(card, index) in cards" :key="index" :class="getColumnClass()">
      <!-- 特殊卡片插槽支持 -->
      <slot v-if="$slots[`card-${index}`]" :name="`card-${index}`" :card="card" :index="index" />

      <!-- 默认StatCard渲染 -->
      <StatCard
        v-else
        :value="card.value"
        :label="card.label"
        :icon="card.icon"
        :icon-type="card.iconType"
        :variant="card.variant"
        :to="card.to"
        :number-class="card.numberClass"
        :custom-class="card.customClass"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import StatCard from './StatCard.vue';

interface StatCardConfig {
  value: string | number;
  label: string;
  icon: string;
  iconType?: 'total' | 'success' | 'warning' | 'info' | 'primary';
  variant?: 'gradient' | 'glass';
  to?: string;
  numberClass?: string;
  customClass?: string;
}

interface Props {
  /** 统计卡片配置数组 */
  cards: StatCardConfig[];
  /** 每行显示的列数 */
  columns?: number;
  /** 是否启用响应式布局 */
  responsive?: boolean;
  /** 容器间距类 */
  spacing?: string;
  /** 是否在大屏幕上显示 */
  hideOnSmall?: boolean;
  /** 自定义容器CSS类 */
  containerClass?: string;
}

const props = withDefaults(defineProps<Props>(), {
  columns: 4,
  responsive: true,
  spacing: 'q-mb-sm',
  hideOnSmall: true,
  containerClass: '',
});

// 计算容器CSS类
const containerClass = computed(() => {
  const classes = ['row', 'stat-cards-container'];

  if (props.spacing) {
    classes.push(props.spacing);
  }

  if (props.hideOnSmall) {
    classes.push('gt-xs');
  }

  if (props.containerClass) {
    classes.push(props.containerClass);
  }

  return classes.join(' ');
});

// 获取列的CSS类
const getColumnClass = () => {
  if (!props.responsive) {
    return `col-${12 / props.columns} stat-card-col`;
  }

  // 响应式列布局
  const cardCount = props.cards.length;

  if (cardCount <= 3) {
    // 3个或更少卡片:大屏4列,中屏3列,小屏2列
    return 'col-12 col-sm-6 col-md-4 col-lg-4 stat-card-col';
  } else if (cardCount === 4) {
    // 4个卡片:大屏4列,中屏2列
    return 'col-12 col-sm-6 col-md-3 col-lg-3 stat-card-col';
  } else {
    // 5个或更多卡片:使用特殊的2.4列布局
    return 'col-12 col-sm-6 col-md-3 col-lg-2-4 stat-card-col';
  }
};

// 暴露组件方法供父组件调用
defineExpose({
  cards: computed(() => props.cards),
  cardCount: computed(() => props.cards.length),
});
</script>

<style lang="scss" scoped>
.stats-cards-row {
  .stat-card-col {
    // 确保卡片在容器中正确对齐
    display: flex;

    :deep(.stat-card) {
      width: 100%;
      height: 100%;
    }
  }
}

// 支持Quasar的2.4列布局(5列网格)
@media (width >= 1024px) {
  .col-lg-2-4 {
    flex: 0 0 20%;
    max-width: 20%;
  }
}

// 移动端优化
@media (width <= 599px) {
  .stats-cards-row {
    .stat-card-col {
      margin-bottom: 8px;

      &:last-child {
        margin-bottom: 0;
      }
    }
  }
}
</style>
