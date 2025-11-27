<template>
  <div
    :class="[
      'status-indicator',
      `status-indicator--${variant}`,
      `status-indicator--${status}`,
      {
        'status-indicator--animated': animated,
        'status-indicator--pulsing': pulsing,
        'status-indicator--blinking': blinking,
      },
    ]"
  >
    <div class="indicator-dot">
      <div v-if="animated" class="dot-ripple"></div>
    </div>

    <div v-if="showLabel || $slots.default" class="indicator-content">
      <div class="indicator-label">
        <slot>{{ label }}</slot>
      </div>
      <div v-if="description" class="indicator-description">
        {{ description }}
      </div>
    </div>

    <!-- 工具提示 -->
    <q-tooltip v-if="tooltip" class="bg-dark text-white">
      {{ tooltip }}
    </q-tooltip>
  </div>
</template>

<script setup lang="ts">
interface Props {
  status: 'success' | 'warning' | 'error' | 'info' | 'neutral' | 'loading';
  variant?: 'default' | 'large' | 'small' | 'minimal';
  label?: string;
  description?: string;
  tooltip?: string;
  showLabel?: boolean;
  animated?: boolean;
  pulsing?: boolean;
  blinking?: boolean;
}

withDefaults(defineProps<Props>(), {
  variant: 'default',
  showLabel: true,
  animated: false,
  pulsing: false,
  blinking: false,
});
</script>

<style lang="scss" scoped>
@import 'src/css/quasar.variables';

// 🎨 状态指示器基础样式
// --------------------------------------------------

.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 8px;

  // 默认尺寸
  .indicator-dot {
    position: relative;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    transition: all $transition-base;
  }
}

// 📏 尺寸变体
// --------------------------------------------------

.status-indicator--large {
  gap: 12px;

  .indicator-dot {
    width: 12px;
    height: 12px;
  }
}

.status-indicator--small {
  gap: 6px;

  .indicator-dot {
    width: 6px;
    height: 6px;
  }
}

.status-indicator--minimal {
  gap: 4px;

  .indicator-dot {
    width: 4px;
    height: 4px;
  }
}

// 🎯 状态颜色
// --------------------------------------------------

.status-indicator--success {
  .indicator-dot {
    background-color: var(--q-positive);
    box-shadow: 0 0 0 2px rgb(0 212 170 / 20%);
  }
}

.status-indicator--warning {
  .indicator-dot {
    background-color: var(--q-warning);
    box-shadow: 0 0 0 2px rgb(255 212 59 / 20%);
  }
}

.status-indicator--error {
  .indicator-dot {
    background-color: var(--q-negative);
    box-shadow: 0 0 0 2px rgb(255 107 107 / 20%);
  }
}

.status-indicator--info {
  .indicator-dot {
    background-color: var(--q-info);
    box-shadow: 0 0 0 2px rgb(116 192 252 / 20%);
  }
}

.status-indicator--neutral {
  .indicator-dot {
    background-color: var(--q-color-grey-5);
    box-shadow: 0 0 0 2px rgb(158 158 158 / 20%);
  }
}

.status-indicator--loading {
  .indicator-dot {
    background: conic-gradient(var(--q-primary), transparent);
    animation: spin 1s linear infinite;

    &::before {
      content: '';
      position: absolute;
      top: 50%;
      left: 50%;
      width: 60%;
      height: 60%;
      background: white;
      border-radius: 50%;
      transform: translate(-50%, -50%);

      .body--dark & {
        background: $dark-surface;
      }
    }
  }
}

// 🎪 动画效果
// --------------------------------------------------

.status-indicator--animated {
  .indicator-dot {
    position: relative;

    .dot-ripple {
      position: absolute;
      inset: -4px;
      border-radius: 50%;
      border: 1px solid currentcolor;
      animation: ripple 2s infinite;
      opacity: 0;
    }
  }

  &.status-indicator--success .dot-ripple {
    border-color: var(--q-positive);
  }

  &.status-indicator--warning .dot-ripple {
    border-color: var(--q-warning);
  }

  &.status-indicator--error .dot-ripple {
    border-color: var(--q-negative);
  }

  &.status-indicator--info .dot-ripple {
    border-color: var(--q-info);
  }
}

.status-indicator--pulsing .indicator-dot {
  animation: pulse 2s infinite;
}

.status-indicator--blinking .indicator-dot {
  animation: blink 1.5s infinite;
}

// 📝 内容样式
// --------------------------------------------------

.indicator-content {
  .indicator-label {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--q-color-grey-8);
    line-height: 1.4;

    .body--dark & {
      color: var(--q-color-grey-2);
    }
  }

  .indicator-description {
    font-size: 0.75rem;
    color: var(--q-color-grey-6);
    margin-top: 2px;
    line-height: 1.3;

    .body--dark & {
      color: var(--q-color-grey-4);
    }
  }
}

// 🎭 关键帧动画
// --------------------------------------------------

@keyframes ripple {
  0% {
    transform: scale(1);
    opacity: 1;
  }

  100% {
    transform: scale(2.5);
    opacity: 0;
  }
}

@keyframes pulse {
  0%,
  100% {
    transform: scale(1);
    opacity: 1;
  }

  50% {
    transform: scale(1.2);
    opacity: 0.7;
  }
}

@keyframes blink {
  0%,
  50% {
    opacity: 1;
  }

  51%,
  100% {
    opacity: 0.3;
  }
}

@keyframes spin {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}

// 📱 响应式优化
// --------------------------------------------------

@media (width <= 768px) {
  .status-indicator {
    gap: 6px;
  }

  .indicator-content {
    .indicator-label {
      font-size: 0.8125rem;
    }

    .indicator-description {
      font-size: 0.6875rem;
    }
  }
}
</style>
