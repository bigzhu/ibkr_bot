<template>
  <q-card
    :class="[
      'modern-card',
      `modern-card--${variant}`,
      {
        'modern-card--hoverable': hoverable,
        'modern-card--glass': glass,
        'modern-card--elevated': elevated,
      },
    ]"
    :style="cardStyle"
  >
    <!-- 卡片头部 -->
    <div v-if="$slots.header || title" class="modern-card__header">
      <slot name="header">
        <div class="card-header-content">
          <div class="header-main">
            <div v-if="icon" class="header-icon">
              <q-icon :name="icon" :size="iconSize" :color="iconColor" />
            </div>
            <div class="header-text">
              <h3 v-if="title" class="header-title">{{ title }}</h3>
              <p v-if="subtitle" class="header-subtitle">{{ subtitle }}</p>
            </div>
          </div>
          <div v-if="$slots.actions" class="header-actions">
            <slot name="actions" />
          </div>
        </div>
      </slot>
    </div>

    <!-- 卡片内容 -->
    <div class="modern-card__content">
      <slot />
    </div>

    <!-- 卡片底部 -->
    <div v-if="$slots.footer" class="modern-card__footer">
      <slot name="footer" />
    </div>

    <!-- 装饰元素 -->
    <div v-if="variant === 'gradient'" class="card-decoration"></div>
    <div v-if="loading" class="card-loading">
      <q-inner-loading showing :color="loadingColor">
        <LoadingSpinner variant="gear" size="md" />
      </q-inner-loading>
    </div>
  </q-card>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { CSSProperties } from 'vue';
import LoadingSpinner from './LoadingSpinner.vue';

interface Props {
  title?: string;
  subtitle?: string;
  icon?: string;
  iconSize?: string;
  iconColor?: string;
  variant?: 'default' | 'gradient' | 'glass' | 'outlined';
  hoverable?: boolean;
  glass?: boolean;
  elevated?: boolean;
  loading?: boolean;
  loadingColor?: string;
  customStyle?: CSSProperties;
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
  iconSize: '24px',
  iconColor: 'primary',
  hoverable: true,
  glass: false,
  elevated: false,
  loading: false,
  loadingColor: 'primary',
});

// 计算卡片样式
const cardStyle = computed(() => {
  return props.customStyle ?? {};
});
</script>

<style lang="scss" scoped>
@import 'src/css/quasar.variables';

// 🎨 现代化卡片基础样式
// --------------------------------------------------

.modern-card {
  border-radius: $border-radius-lg;
  border: 1px solid rgb(0 0 0 / 5%);
  background: white;
  overflow: visible;
  position: relative;
  transition: all $transition-base $ease-out-cubic;

  .body--dark & {
    background: $dark-surface;
    border-color: rgb(255 255 255 / 10%);
  }

  // 悬浮效果
  &--hoverable:hover {
    transform: translateY(-4px);
    box-shadow: $shadow-xl;
  }

  // 玻璃拟态效果
  &--glass {
    background: rgb(255 255 255 / 10%);
    backdrop-filter: blur(15px);
    border: 1px solid rgb(255 255 255 / 20%);

    .body--dark & {
      background: rgb(255 255 255 / 5%);
      border-color: rgb(255 255 255 / 10%);
    }
  }

  // 阴影效果
  &--elevated {
    box-shadow: $shadow-md;
  }

  // 渐变变体
  &--gradient {
    background: $gradient-primary;
    color: white;
    border: none;

    .header-title,
    .header-subtitle {
      color: white;
    }

    .card-decoration {
      position: absolute;
      top: -50%;
      right: -50%;
      width: 200px;
      height: 200px;
      background: radial-gradient(circle, rgb(255 255 255 / 10%) 0%, transparent 70%);
      pointer-events: none;
    }
  }

  // 描边变体
  &--outlined {
    border: 2px solid var(--q-primary);
    background: rgb(102 126 234 / 2%);

    .body--dark & {
      background: rgb(102 126 234 / 5%);
    }
  }
}

// 🎯 卡片头部
// --------------------------------------------------

.modern-card__header {
  padding: 24px 24px 0;

  .card-header-content {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;

    .header-main {
      display: flex;
      align-items: flex-start;
      flex: 1;

      .header-icon {
        width: 48px;
        height: 48px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgb(102 126 234 / 10%);
        border-radius: 50%;
        margin-right: 16px;

        .body--dark & {
          background: rgb(102 126 234 / 20%);
        }

        .modern-card--gradient & {
          background: rgb(255 255 255 / 20%);
        }
      }

      .header-text {
        flex: 1;

        .header-title {
          font-size: 1.25rem;
          font-weight: 600;
          margin: 0 0 4px;
          color: var(--q-color-grey-8);

          .body--dark & {
            color: var(--q-color-grey-2);
          }
        }

        .header-subtitle {
          font-size: 0.875rem;
          color: var(--q-color-grey-6);
          margin: 0;

          .body--dark & {
            color: var(--q-color-grey-4);
          }
        }
      }
    }

    .header-actions {
      display: flex;
      gap: 8px;
      margin-left: 16px;
    }
  }
}

// 📋 卡片内容
// --------------------------------------------------

.modern-card__content {
  padding: 24px;

  .modern-card__header + & {
    padding-top: 16px;
  }
}

// 👇 卡片底部
// --------------------------------------------------

.modern-card__footer {
  padding: 0 24px 24px;
  border-top: 1px solid rgb(0 0 0 / 5%);
  background: rgb(0 0 0 / 1%);

  .body--dark & {
    border-top-color: rgb(255 255 255 / 10%);
    background: rgb(255 255 255 / 2%);
  }

  .modern-card--gradient & {
    border-top-color: rgb(255 255 255 / 10%);
    background: rgb(255 255 255 / 5%);
  }
}

// 📡 加载状态
// --------------------------------------------------

.card-loading {
  position: absolute;
  inset: 0;
  background: rgb(255 255 255 / 90%);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;

  .body--dark & {
    background: rgb(0 0 0 / 80%);
  }
}

// 📱 响应式优化
// --------------------------------------------------

@media (width <= 768px) {
  .modern-card__header,
  .modern-card__content,
  .modern-card__footer {
    padding-left: 16px;
    padding-right: 16px;
  }

  .modern-card__header {
    padding-top: 16px;

    .card-header-content {
      flex-direction: column;
      align-items: flex-start;
      gap: 16px;

      .header-main {
        width: 100%;
      }

      .header-actions {
        margin-left: 0;
        align-self: stretch;
      }
    }
  }

  .modern-card__content {
    padding-top: 16px;
    padding-bottom: 16px;
  }

  .modern-card__footer {
    padding-bottom: 16px;
  }
}
</style>
