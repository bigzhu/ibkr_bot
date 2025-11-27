<template>
  <div
    :class="[
      'loading-spinner',
      `loading-spinner--${variant}`,
      `loading-spinner--${size}`,
      {
        'loading-spinner--overlay': overlay,
        'loading-spinner--centered': centered,
      },
    ]"
    :style="spinnerStyle"
  >
    <!-- 背景遮罩 -->
    <div v-if="overlay" class="spinner-backdrop" @click="$emit('backdrop-click')"></div>

    <!-- 加载器容器 -->
    <div class="spinner-container">
      <!-- 不同类型的加载器 -->

      <!-- 默认圆环 -->
      <div v-if="variant === 'default'" class="spinner-default">
        <div class="spinner-circle"></div>
      </div>

      <!-- 脉冲圆点 -->
      <div v-else-if="variant === 'pulse'" class="spinner-pulse">
        <div
          class="pulse-dot"
          v-for="i in 3"
          :key="i"
          :style="{ animationDelay: `${i * 0.1}s` }"
        ></div>
      </div>

      <!-- 旋转方块 -->
      <div v-else-if="variant === 'cube'" class="spinner-cube">
        <div class="cube-face" v-for="i in 6" :key="i"></div>
      </div>

      <!-- 波浪 -->
      <div v-else-if="variant === 'wave'" class="spinner-wave">
        <div
          class="wave-bar"
          v-for="i in 5"
          :key="i"
          :style="{ animationDelay: `${i * 0.1}s` }"
        ></div>
      </div>

      <!-- 齿轮 -->
      <div v-else-if="variant === 'gear'" class="spinner-gear">
        <q-spinner-gears :size="gearSize" :color="color" />
      </div>

      <!-- 渐变环 -->
      <div v-else-if="variant === 'gradient'" class="spinner-gradient">
        <div class="gradient-ring"></div>
      </div>

      <!-- 加载文本 -->
      <div v-if="showText" class="spinner-text">
        <div class="text-content">{{ text }}</div>
        <div v-if="progress !== undefined" class="progress-text">{{ Math.round(progress) }}%</div>
      </div>

      <!-- 进度条 -->
      <div v-if="progress !== undefined && showProgress" class="spinner-progress">
        <q-linear-progress
          :value="progress / 100"
          :color="color"
          track-color="grey-3"
          size="4px"
          rounded
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import type { CSSProperties } from 'vue';

interface Props {
  variant?: 'default' | 'pulse' | 'cube' | 'wave' | 'gear' | 'gradient';
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  color?: string;
  overlay?: boolean;
  centered?: boolean;
  text?: string;
  showText?: boolean;
  progress?: number;
  showProgress?: boolean;
  customStyle?: CSSProperties;
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
  size: 'md',
  color: 'primary',
  overlay: false,
  centered: false,
  text: '加载中...',
  showText: false,
  showProgress: false,
});

defineEmits<{
  'backdrop-click': [];
}>();

// 计算样式
const spinnerStyle = computed<CSSProperties>(() => props.customStyle ?? {});

// 计算齿轮尺寸
const gearSize = computed(() => {
  const sizeMap: Record<'xs' | 'sm' | 'md' | 'lg' | 'xl', string> = {
    xs: '20px',
    sm: '30px',
    md: '40px',
    lg: '50px',
    xl: '60px',
  };
  return sizeMap[props.size];
});
</script>

<style lang="scss" scoped>
@import 'src/css/quasar.variables';

// 🎨 加载器容器样式
// --------------------------------------------------

.loading-spinner {
  position: relative;
  display: inline-block;

  &--centered {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    z-index: 9999;
  }

  &--overlay {
    position: fixed;
    inset: 0;
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: center;
  }
}

// 🌫️ 背景遮罩
// --------------------------------------------------

.spinner-backdrop {
  position: absolute;
  inset: 0;
  background: rgb(255 255 255 / 80%);
  backdrop-filter: blur(2px);

  .body--dark & {
    background: rgb(0 0 0 / 80%);
  }
}

// 📦 容器样式
// --------------------------------------------------

.spinner-container {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

// 🔄 默认圆环
// --------------------------------------------------

.spinner-default {
  .spinner-circle {
    border: 3px solid rgb(102 126 234 / 20%);
    border-top-color: var(--q-primary);
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }
}

// 🔵 脉冲圆点
// --------------------------------------------------

.spinner-pulse {
  display: flex;
  gap: 8px;

  .pulse-dot {
    background: var(--q-primary);
    border-radius: 50%;
    animation: pulse-bounce 1.4s infinite both;
  }
}

// 📦 旋转方块
// --------------------------------------------------

.spinner-cube {
  position: relative;
  transform-style: preserve-3d;
  animation: cube-rotate 2s infinite linear;

  .cube-face {
    position: absolute;
    width: 100%;
    height: 100%;
    background: var(--q-primary);
    opacity: 0.8;

    &:nth-child(1) {
      transform: rotateY(0deg) translateZ(16px);
    }

    &:nth-child(2) {
      transform: rotateY(90deg) translateZ(16px);
    }

    &:nth-child(3) {
      transform: rotateY(180deg) translateZ(16px);
    }

    &:nth-child(4) {
      transform: rotateY(-90deg) translateZ(16px);
    }

    &:nth-child(5) {
      transform: rotateX(90deg) translateZ(16px);
    }

    &:nth-child(6) {
      transform: rotateX(-90deg) translateZ(16px);
    }
  }
}

// 🌊 波浪
// --------------------------------------------------

.spinner-wave {
  display: flex;
  gap: 4px;
  align-items: end;

  .wave-bar {
    background: var(--q-primary);
    border-radius: 2px;
    animation: wave-bounce 1.2s infinite;
  }
}


// 🌈 渐变环
// --------------------------------------------------

.spinner-gradient {
  .gradient-ring {
    border-radius: 50%;
    background: conic-gradient(var(--q-primary), var(--q-secondary), var(--q-primary));
    animation: gradient-spin 1.5s linear infinite;
    position: relative;

    &::before {
      content: '';
      position: absolute;
      top: 50%;
      left: 50%;
      width: 75%;
      height: 75%;
      background: white;
      border-radius: 50%;
      transform: translate(-50%, -50%);

      .body--dark & {
        background: $dark-surface;
      }
    }
  }
}

// 📝 文本样式
// --------------------------------------------------

.spinner-text {
  text-align: center;

  .text-content {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--q-color-grey-7);

    .body--dark & {
      color: var(--q-color-grey-4);
    }
  }

  .progress-text {
    font-size: 0.75rem;
    color: var(--q-primary);
    margin-top: 4px;
    font-weight: 600;
  }
}

// 📊 进度条
// --------------------------------------------------

.spinner-progress {
  width: 120px;
}

// 🎯 尺寸变体
// --------------------------------------------------

.loading-spinner--xs {
  .spinner-default .spinner-circle,
  .spinner-gradient .gradient-ring {
    width: 20px;
    height: 20px;
  }

  .spinner-pulse .pulse-dot {
    width: 4px;
    height: 4px;
  }

  .spinner-cube {
    width: 16px;
    height: 16px;
  }

  .spinner-wave .wave-bar {
    width: 2px;
    height: 16px;
  }
}

.loading-spinner--sm {
  .spinner-default .spinner-circle,
  .spinner-gradient .gradient-ring {
    width: 30px;
    height: 30px;
  }

  .spinner-pulse .pulse-dot {
    width: 6px;
    height: 6px;
  }

  .spinner-cube {
    width: 24px;
    height: 24px;
  }

  .spinner-wave .wave-bar {
    width: 3px;
    height: 24px;
  }
}

.loading-spinner--md {
  .spinner-default .spinner-circle,
  .spinner-gradient .gradient-ring {
    width: 40px;
    height: 40px;
  }

  .spinner-pulse .pulse-dot {
    width: 8px;
    height: 8px;
  }

  .spinner-cube {
    width: 32px;
    height: 32px;
  }

  .spinner-wave .wave-bar {
    width: 4px;
    height: 32px;
  }
}

.loading-spinner--lg {
  .spinner-default .spinner-circle,
  .spinner-gradient .gradient-ring {
    width: 50px;
    height: 50px;
  }

  .spinner-pulse .pulse-dot {
    width: 10px;
    height: 10px;
  }

  .spinner-cube {
    width: 40px;
    height: 40px;
  }

  .spinner-wave .wave-bar {
    width: 5px;
    height: 40px;
  }
}

.loading-spinner--xl {
  .spinner-default .spinner-circle,
  .spinner-gradient .gradient-ring {
    width: 60px;
    height: 60px;
  }

  .spinner-pulse .pulse-dot {
    width: 12px;
    height: 12px;
  }

  .spinner-cube {
    width: 48px;
    height: 48px;
  }

  .spinner-wave .wave-bar {
    width: 6px;
    height: 48px;
  }
}

// 🎭 关键帧动画
// --------------------------------------------------

@keyframes spin {
  from {
    transform: rotate(0deg);
  }

  to {
    transform: rotate(360deg);
  }
}

@keyframes pulse-bounce {
  0%,
  80%,
  100% {
    transform: scale(0.8);
    opacity: 0.5;
  }

  40% {
    transform: scale(1);
    opacity: 1;
  }
}

@keyframes cube-rotate {
  0% {
    transform: rotateX(0deg) rotateY(0deg);
  }

  100% {
    transform: rotateX(360deg) rotateY(360deg);
  }
}

@keyframes wave-bounce {
  0%,
  40%,
  100% {
    transform: scaleY(1);
  }

  20% {
    transform: scaleY(2);
  }
}

@keyframes gradient-spin {
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
  .spinner-text .text-content {
    font-size: 0.8125rem;
  }

  .spinner-progress {
    width: 100px;
  }
}
</style>
