<template>
  <div class="page-header" :class="marginClass">
    <div class="header-icon">
      <q-icon :name="icon" :size="iconSize" class="text-gradient" />
      <div class="icon-glow" :class="glowClass"></div>
    </div>
    <div class="header-content">
      <h1 class="header-title">{{ title }}</h1>
      <p class="header-subtitle">{{ subtitle }}</p>
    </div>
    <div v-if="hasActions" class="header-actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, useSlots } from 'vue';

interface Props {
  /** 页面标题 */
  title: string;
  /** 页面副标题 */
  subtitle: string;
  /** 头部图标 */
  icon: string;
  /** 图标大小 */
  iconSize?: string;
  /** 图标发光效果类型 */
  glowType?: 'default' | 'pulse' | 'config';
  /** 底部边距 */
  margin?: 'sm' | 'md' | 'lg' | 'xl';
}

const props = withDefaults(defineProps<Props>(), {
  iconSize: '2.5rem',
  glowType: 'default',
  margin: 'md',
});

const slots = useSlots();

// 是否有操作按钮
const hasActions = computed(() => !!slots.actions);

// 图标发光效果样式类
const glowClass = computed(() => {
  const glowClasses: Record<string, string> = {
    default: '',
    pulse: 'icon-glow--pulse',
    config: 'icon-glow--config',
  };
  return glowClasses[props.glowType] || '';
});

// 底部边距样式类
const marginClass = computed(() => {
  const marginClasses: Record<string, string> = {
    sm: 'q-mb-sm',
    md: 'q-mb-md',
    lg: 'q-mb-lg',
    xl: 'q-mb-xl',
  };
  return marginClasses[props.margin] || 'q-mb-md';
});
</script>

<style lang="scss" scoped>
// 页面头部样式已在全局样式中定义,这里只做必要的补充
</style>
