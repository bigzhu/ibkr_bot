<template>
  <div class="empty-state-display" :class="containerClass">
    <div class="empty-state-content">
      <!-- 图标 -->
      <q-icon :name="resolvedIcon" :size="iconSize" :color="iconColor" class="empty-state-icon" />

      <!-- 主标题 -->
      <div class="empty-state-title" :class="titleClass">
        {{ title || defaultTitle }}
      </div>

      <!-- 副标题/描述 -->
      <div
        v-if="description || defaultDescription"
        class="empty-state-description"
        :class="descriptionClass"
      >
        {{ description || defaultDescription }}
      </div>

      <!-- 操作按钮插槽 -->
      <div v-if="$slots.actions" class="empty-state-actions">
        <slot name="actions" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface Props {
  /** 显示的图标名称 */
  icon?: string;
  /** 图标大小 */
  iconSize?: string;
  /** 图标颜色 */
  iconColor?: string;
  /** 主标题文本 */
  title?: string;
  /** 描述文本 */
  description?: string;
  /** 空状态类型,会影响默认的图标和文本 */
  type?: 'data' | 'orders' | 'trading' | 'config' | 'search' | 'error' | 'custom';
  /** 尺寸变体 */
  size?: 'sm' | 'md' | 'lg';
  /** 是否居中显示 */
  centered?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  type: 'data',
  size: 'md',
  iconSize: '4rem',
  iconColor: 'grey-4',
  centered: true,
});

// 根据类型提供默认配置
const typeConfigs = {
  data: {
    icon: 'inbox',
    title: '暂无数据',
    description: '当前没有可显示的数据',
  },
  orders: {
    icon: 'receipt_long',
    title: '暂无订单',
    description: '还没有相关的订单记录',
  },
  trading: {
    icon: 'trending_up',
    title: '暂无交易记录',
    description: '还没有进行任何交易活动',
  },
  config: {
    icon: 'settings',
    title: '暂无配置',
    description: '还没有配置相关参数',
  },
  search: {
    icon: 'search_off',
    title: '未找到匹配项',
    description: '请尝试调整搜索条件',
  },
  error: {
    icon: 'error_outline',
    title: '加载失败',
    description: '数据加载出现问题,请稍后重试',
  },
  custom: {
    icon: 'help_outline',
    title: '暂无内容',
    description: '',
  },
};

// 计算默认值
const resolvedIcon = computed(() => props.icon ?? typeConfigs[props.type].icon);
const defaultTitle = computed(() => typeConfigs[props.type].title);
const defaultDescription = computed(() => typeConfigs[props.type].description);

// 计算CSS类
const containerClass = computed(() => [
  `empty-state-display--${props.size}`,
  {
    'empty-state-display--centered': props.centered,
  },
]);

const titleClass = computed(() => [
  'text-weight-medium',
  props.size === 'lg' ? 'text-h5' : props.size === 'md' ? 'text-h6' : 'text-subtitle1',
]);

const descriptionClass = computed(() => [props.size === 'lg' ? 'text-body1' : 'text-body2']);
</script>

<style lang="scss" scoped>
.empty-state-title {
  color: var(--q-color-grey-7);

  .body--dark & {
    color: var(--q-color-grey-4);
  }
}

.empty-state-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;

  &--centered {
    text-align: center;
  }

  // 尺寸变体
  &--sm {
    padding: 32px 16px;

    .empty-state-icon {
      margin-bottom: 8px;
    }

    .empty-state-title {
      margin-bottom: 4px;
    }
  }

  &--md {
    padding: 48px 20px;

    .empty-state-icon {
      margin-bottom: 16px;
    }

    .empty-state-title {
      margin-bottom: 8px;
    }
  }

  &--lg {
    padding: 64px 24px;

    .empty-state-icon {
      margin-bottom: 24px;
    }

    .empty-state-title {
      margin-bottom: 12px;
    }
  }
}

.empty-state-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  max-width: 400px;
}

.empty-state-description {
  color: var(--q-color-grey-5);
  line-height: 1.5;

  .body--dark & {
    color: var(--q-color-grey-6);
  }
}

.empty-state-actions {
  margin-top: 24px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}

// 响应式设计
@media (width <= 600px) {
  .empty-state-display {
    &--sm {
      padding: 24px 12px;
    }

    &--md {
      padding: 32px 16px;
    }

    &--lg {
      padding: 48px 20px;
    }
  }

  .empty-state-icon {
    transform: scale(0.8);
  }
}
</style>
