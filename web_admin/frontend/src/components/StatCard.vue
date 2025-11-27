<template>
  <ModernCard :variant="variant" :class="cardClasses" @click="handleClick">
    <div class="stat-content">
      <div class="stat-icon" :class="iconClass">
        <q-icon :name="icon" />
      </div>
      <div class="stat-details">
        <div class="stat-number" :class="numberClass">{{ displayValue }}</div>
        <div class="stat-label">{{ label }}</div>
      </div>
    </div>
  </ModernCard>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import ModernCard from 'src/components/ModernCard.vue';

interface Props {
  /** 显示的数值 */
  value: string | number;
  /** 卡片标签 */
  label: string;
  /** 图标名称 */
  icon: string;
  /** 图标样式类型 */
  iconType?: 'total' | 'success' | 'warning' | 'info' | 'primary';
  /** 卡片变体 */
  variant?: 'gradient' | 'glass';
  /** 点击时跳转的路由 */
  to?: string;
  /** 数值样式类 */
  numberClass?: string;
  /** 自定义CSS类 */
  customClass?: string;
}

const props = withDefaults(defineProps<Props>(), {
  iconType: 'total',
  variant: 'gradient',
  to: undefined,
  numberClass: '',
  customClass: '',
});

const router = useRouter();

// 图标样式类映射
const iconClass = computed(() => {
  const iconClasses: Record<string, string> = {
    total: 'total-icon',
    success: 'success-icon',
    warning: 'warning-icon',
    info: 'info-icon',
    primary: 'primary-icon',
  };
  return iconClasses[props.iconType] || 'total-icon';
});

// 卡片CSS类
const cardClasses = computed(() => {
  const classes = ['stat-card'];

  if (props.to) {
    classes.push('clickable-card');
  }

  if (props.customClass) {
    classes.push(props.customClass);
  }

  return classes.join(' ');
});

// 显示值处理
const displayValue = computed(() => {
  if (typeof props.value === 'number') {
    return props.value.toString();
  }
  return props.value || '-';
});

// 点击处理
const handleClick = () => {
  if (props.to) {
    void router.push(props.to);
  }
};
</script>

<style lang="scss" scoped>
// 可点击卡片的悬停效果
.clickable-card {
  cursor: pointer;
  transition: transform 0.2s ease;

  &:hover {
    transform: translateY(-2px);
  }
}
</style>
