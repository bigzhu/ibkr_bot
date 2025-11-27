<template>
  <q-btn
    :class="[
      'modern-btn',
      `modern-btn--${variant}`,
      {
        'modern-btn--loading': loading,
        'modern-btn--disabled': disable,
        'modern-btn--full-width': fullWidth,
      },
    ]"
    :color="btnColor"
    :size="size"
    :loading="loading"
    :disable="disable"
    :no-caps="noCaps"
    :unelevated="unelevated"
    :flat="flat"
    :outline="outline"
    :round="round"
    :dense="dense"
    v-bind="$attrs"
    @click="handleClick"
  >
    <!-- 图标前缀 -->
    <q-icon
      v-if="icon && !iconRight"
      :name="icon"
      :size="iconSize"
      :class="{ 'q-mr-sm': $slots.default }"
    />

    <!-- 按钮文本 -->
    <span v-if="$slots.default" class="btn-text">
      <slot />
    </span>

    <!-- 图标后缀 -->
    <q-icon
      v-if="icon && iconRight"
      :name="icon"
      :size="iconSize"
      :class="{ 'q-ml-sm': $slots.default }"
    />

    <!-- 渐变背景 -->
    <div v-if="variant === 'gradient'" class="btn-gradient-bg"></div>

    <!-- 波纹效果 -->
    <div
      v-if="variant === 'ripple'"
      class="btn-ripple"
      :class="{ 'ripple-active': rippleActive }"
    ></div>
  </q-btn>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

interface Props {
  variant?: 'default' | 'gradient' | 'glass' | 'outline' | 'ripple' | 'ghost';
  icon?: string;
  iconRight?: boolean;
  iconSize?: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  loading?: boolean;
  disable?: boolean;
  fullWidth?: boolean;
  noCaps?: boolean;
  unelevated?: boolean;
  flat?: boolean;
  outline?: boolean;
  round?: boolean;
  dense?: boolean;
  color?: string;
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
  iconSize: '18px',
  size: 'md',
  noCaps: true,
  unelevated: true,
  color: 'primary',
});

const emit = defineEmits<{
  click: [event: MouseEvent];
}>();

const rippleActive = ref(false);

// 计算按钮颜色
const btnColor = computed(() => {
  if (props.variant === 'gradient') return undefined;
  return props.color;
});

// 处理点击事件
const handleClick = (event: MouseEvent) => {
  if (props.variant === 'ripple') {
    rippleActive.value = true;
    setTimeout(() => {
      rippleActive.value = false;
    }, 600);
  }

  emit('click', event);
};
</script>

<style lang="scss" scoped>
@import 'src/css/quasar.variables';

// 🎨 现代化按钮样式
// --------------------------------------------------

.modern-btn {
  font-weight: 500;
  border-radius: $border-radius-sm;
  transition: all $transition-base $ease-out-cubic;
  position: relative;
  overflow: hidden;

  // 默认悬浮效果
  &:hover:not(.modern-btn--disabled, .modern-btn--loading) {
    transform: translateY(-2px);
    box-shadow: $shadow-md;
  }

  // 激活效果
  &:active:not(.modern-btn--disabled, .modern-btn--loading) {
    transform: translateY(-1px);
  }

  // 全宽按钮
  &--full-width {
    width: 100%;
  }

  // 渐变变体
  &--gradient {
    background: $gradient-primary !important;
    color: white !important;
    border: none;

    .btn-gradient-bg {
      position: absolute;
      inset: 0;
      background: linear-gradient(
        135deg,
        rgb(255 255 255 / 20%) 0%,
        rgb(255 255 255 / 10%) 100%
      );
      pointer-events: none;
      opacity: 0;
      transition: opacity $transition-base;
    }

    &:hover .btn-gradient-bg {
      opacity: 1;
    }

    &::before {
      content: '';
      position: absolute;
      top: 0;
      left: -100%;
      width: 100%;
      height: 100%;
      background: linear-gradient(90deg, transparent, rgb(255 255 255 / 30%), transparent);
      transition: left 0.6s;
      z-index: 1;
    }

    &:hover::before {
      left: 100%;
    }
  }

  // 玻璃拟态变体
  &--glass {
    background: rgb(255 255 255 / 10%) !important;
    backdrop-filter: blur(10px) !important;
    border: 1px solid rgb(255 255 255 / 20%) !important;
    color: var(--q-primary) !important;

    .body--dark & {
      background: rgb(255 255 255 / 5%) !important;
      border-color: rgb(255 255 255 / 10%) !important;
    }

    &:hover {
      background: rgb(255 255 255 / 15%) !important;

      .body--dark & {
        background: rgb(255 255 255 / 10%) !important;
      }
    }
  }

  // 幽灵变体
  &--ghost {
    background: transparent !important;
    border: 2px solid currentcolor !important;

    &:hover {
      background: currentcolor !important;
      color: white !important;
    }
  }

  // 波纹变体
  &--ripple {
    .btn-ripple {
      position: absolute;
      top: 50%;
      left: 50%;
      width: 0;
      height: 0;
      border-radius: 50%;
      background: rgb(255 255 255 / 30%);
      transform: translate(-50%, -50%);
      transition: all 0.6s ease-out;

      &.ripple-active {
        width: 300px;
        height: 300px;
        opacity: 0;
      }
    }
  }

  // 尺寸变体
  &.q-btn--xs {
    min-height: 24px;
    padding: 4px 12px;
    font-size: 0.75rem;
  }

  &.q-btn--sm {
    min-height: 32px;
    padding: 6px 16px;
    font-size: 0.875rem;
  }

  &.q-btn--md {
    min-height: 40px;
    padding: 8px 20px;
    font-size: 0.875rem;
  }

  &.q-btn--lg {
    min-height: 48px;
    padding: 12px 24px;
    font-size: 1rem;
  }

  &.q-btn--xl {
    min-height: 56px;
    padding: 16px 32px;
    font-size: 1.125rem;
  }

  // 禁用状态
  &--disabled {
    opacity: 0.6 !important;
    cursor: not-allowed !important;
    transform: none !important;
    box-shadow: none !important;
  }

  // 加载状态
  &--loading {
    pointer-events: none;
  }
}

// 🎯 按钮文本
// --------------------------------------------------

.btn-text {
  position: relative;
  z-index: 2;
  transition: all $transition-base;
}

// 📱 响应式优化
// --------------------------------------------------

@media (width <= 768px) {
  .modern-btn {
    &.q-btn--lg {
      min-height: 44px;
      padding: 10px 20px;
    }

    &.q-btn--xl {
      min-height: 48px;
      padding: 12px 24px;
      font-size: 1rem;
    }
  }
}

// 🌙 深色模式优化
// --------------------------------------------------

.body--dark {
  .modern-btn--gradient {
    box-shadow: 0 4px 12px rgb(0 0 0 / 30%);

    &:hover {
      box-shadow: 0 8px 25px rgb(0 0 0 / 40%);
    }
  }
}

</style>
