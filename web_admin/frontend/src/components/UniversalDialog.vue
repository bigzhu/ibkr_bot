<template>
  <q-dialog
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    :persistent="persistent"
    :maximized="maximized || (responsive && $q.screen.lt.md)"
    :position="position"
  >
    <component :is="cardComponent" :class="dialogClasses">
      <!-- 对话框头部 -->
      <template #header v-if="showHeader">
        <div class="dialog-header" :class="headerClass">
          <div v-if="icon" class="dialog-icon">
            <q-icon :name="icon" :size="iconSize" :color="iconColor" />
          </div>
          <div class="dialog-content">
            <div class="dialog-title">{{ title }}</div>
            <div v-if="subtitle" class="dialog-subtitle">{{ subtitle }}</div>
          </div>
          <div v-if="showCloseButton" class="dialog-close">
            <q-btn icon="close" flat round dense v-close-popup />
          </div>
        </div>
      </template>

      <!-- 对话框内容区域 -->
      <div class="dialog-body" :class="bodyClass">
        <!-- 加载状态 -->
        <div v-if="loading" class="dialog-loading">
          <q-spinner-dots :color="loadingColor" size="40px" />
          <div class="loading-text">{{ loadingText }}</div>
        </div>

        <!-- 确认删除模式 -->
        <div v-else-if="type === 'confirm-delete'" class="delete-confirmation">
          <div class="warning-text">
            {{ confirmMessage }}
            <strong v-if="confirmTarget">{{ confirmTarget }}</strong>
          </div>
          <div v-if="requireInputConfirmation" class="confirmation-input">
            <ModernInput
              v-model="confirmInput"
              :placeholder="inputPlaceholder"
              variant="outlined"
              :rules="inputRules"
              :help-text="inputHelpText"
            />
          </div>
        </div>

        <!-- 自定义内容插槽 -->
        <div v-else-if="type === 'custom'">
          <slot name="content" />
        </div>

        <!-- 简单确认模式 -->
        <div v-else-if="type === 'confirm'" class="confirm-content">
          <div class="confirm-message">{{ confirmMessage }}</div>
        </div>

        <!-- 信息展示模式 -->
        <div v-else-if="type === 'info'" class="info-content">
          <slot name="content" />
        </div>
      </div>

      <!-- 对话框操作按钮 -->
      <div v-if="showActions" class="dialog-actions" :class="actionsClass">
        <!-- 自定义操作按钮插槽 -->
        <template v-if="$slots.actions">
          <slot name="actions" />
        </template>

        <!-- 默认操作按钮 -->
        <template v-else>
          <!-- 取消按钮 -->
          <ModernButton
            v-if="showCancelButton"
            :variant="cancelButtonVariant"
            @click="handleCancel"
          >
            {{ cancelText }}
          </ModernButton>

          <!-- 确认按钮 -->
          <ModernButton
            v-if="showConfirmButton"
            :variant="confirmButtonVariant"
            :color="confirmButtonColor"
            :icon="confirmButtonIcon"
            :loading="confirmLoading"
            :disabled="confirmDisabled"
            @click="handleConfirm"
          >
            {{ confirmText }}
          </ModernButton>
        </template>
      </div>
    </component>
  </q-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useQuasar } from 'quasar';
import ModernButton from './ModernButton.vue';
import ModernCard from './ModernCard.vue';
import ModernInput from './ModernInput.vue';

type DialogType = 'confirm' | 'confirm-delete' | 'info' | 'custom';
type DialogVariant = 'card' | 'modern-card';

interface Props {
  /** v-model 绑定值 */
  modelValue: boolean;

  /** 对话框类型 */
  type?: DialogType;

  /** 对话框标题 */
  title?: string;

  /** 对话框副标题 */
  subtitle?: string;

  /** 标题图标 */
  icon?: string;

  /** 图标大小 */
  iconSize?: string;

  /** 图标颜色 */
  iconColor?: string;

  /** 确认消息 */
  confirmMessage?: string;

  /** 确认目标(如删除的项目名称) */
  confirmTarget?: string;

  /** 是否需要输入确认 */
  requireInputConfirmation?: boolean;

  /** 输入占位符 */
  inputPlaceholder?: string;

  /** 输入帮助文本 */
  inputHelpText?: string;

  /** 是否持久化(不允许点击外部关闭) */
  persistent?: boolean;

  /** 是否响应式(移动端最大化) */
  responsive?: boolean;

  /** 是否最大化 */
  maximized?: boolean;

  /** 对话框位置 */
  position?: 'standard' | 'top' | 'bottom';

  /** 对话框变体 */
  variant?: DialogVariant;

  /** 是否显示头部 */
  showHeader?: boolean;

  /** 是否显示关闭按钮 */
  showCloseButton?: boolean;

  /** 是否显示操作区域 */
  showActions?: boolean;

  /** 是否显示取消按钮 */
  showCancelButton?: boolean;

  /** 是否显示确认按钮 */
  showConfirmButton?: boolean;

  /** 取消按钮文本 */
  cancelText?: string;

  /** 确认按钮文本 */
  confirmText?: string;

  /** 取消按钮变体 */
  cancelButtonVariant?: string;

  /** 确认按钮变体 */
  confirmButtonVariant?: string;

  /** 确认按钮颜色 */
  confirmButtonColor?: string;

  /** 确认按钮图标 */
  confirmButtonIcon?: string;

  /** 确认按钮加载状态 */
  confirmLoading?: boolean;

  /** 确认按钮禁用状态 */
  confirmDisabled?: boolean;

  /** 加载状态 */
  loading?: boolean;

  /** 加载文本 */
  loadingText?: string;

  /** 加载颜色 */
  loadingColor?: string;

  /** 自定义CSS类 */
  customClass?: string;
}

const props = withDefaults(defineProps<Props>(), {
  type: 'confirm',
  iconSize: '2.5rem',
  iconColor: 'warning',
  persistent: true,
  responsive: true,
  maximized: false,
  position: 'standard',
  variant: 'modern-card',
  showHeader: true,
  showCloseButton: true,
  showActions: true,
  showCancelButton: true,
  showConfirmButton: true,
  cancelText: '取消',
  confirmText: '确认',
  cancelButtonVariant: 'ghost',
  confirmButtonVariant: 'ghost',
  confirmButtonColor: 'negative',
  confirmButtonIcon: '',
  confirmLoading: false,
  confirmDisabled: false,
  requireInputConfirmation: false,
  loading: false,
  loadingText: '加载中...',
  loadingColor: 'primary',
  customClass: '',
});

const emit = defineEmits<{
  'update:modelValue': [value: boolean];
  confirm: [confirmInput?: string];
  cancel: [];
}>();

const $q = useQuasar();

// 确认输入值
const confirmInput = ref('');

// 计算属性
const cardComponent = computed(() => {
  return props.variant === 'modern-card' ? ModernCard : 'q-card';
});

const dialogClasses = computed(() => {
  const classes = [];

  if (props.type === 'confirm-delete') {
    classes.push('delete-dialog-card');
  } else {
    classes.push('dialog-card');
  }

  if (props.customClass) {
    classes.push(props.customClass);
  }

  return classes.join(' ');
});

const headerClass = computed(() => {
  const classes = [];

  if (props.type === 'confirm-delete') {
    classes.push('warning');
  }

  return classes.join(' ');
});

const bodyClass = computed(() => {
  return 'q-pa-md';
});

const actionsClass = computed(() => {
  return 'q-pa-md';
});

// 输入验证规则
const inputRules = computed(() => {
  if (!props.requireInputConfirmation || !props.confirmTarget) {
    return [];
  }

  return [
    (val: string) => {
      const isValid = val && val.trim().toUpperCase() === props.confirmTarget?.toUpperCase();
      return isValid || `输入的名称不正确,请输入: ${props.confirmTarget}`;
    },
  ];
});

// 确认按钮禁用状态
const confirmDisabled = computed(() => {
  if (props.confirmDisabled) return true;

  if (props.requireInputConfirmation && props.confirmTarget) {
    return (
      !confirmInput.value ||
      confirmInput.value.trim().toUpperCase() !== props.confirmTarget.toUpperCase()
    );
  }

  return false;
});

// 事件处理
const handleCancel = () => {
  emit('cancel');
  emit('update:modelValue', false);
};

const handleConfirm = () => {
  emit('confirm', confirmInput.value);
  emit('update:modelValue', false);
};

// 监听对话框打开关闭,重置输入
watch(
  () => props.modelValue,
  (newValue) => {
    if (!newValue) {
      confirmInput.value = '';
    }
  },
);
</script>

<style lang="scss" scoped>
.dialog-card {
  min-width: 300px;
  max-width: 600px;
}

.delete-dialog-card {
  min-width: 400px;
  max-width: 500px;
}

.dialog-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;

  .dialog-icon {
    flex-shrink: 0;
  }

  &.warning {
    .dialog-icon {
      color: #f57c00;
    }
  }

  .dialog-content {
    flex: 1;

    .dialog-title {
      font-size: 1.25rem;
      font-weight: 600;
      color: var(--q-primary);
      margin-bottom: 4px;
    }

    .dialog-subtitle {
      font-size: 0.875rem;
      color: var(--q-grey-6);
    }
  }

  .dialog-close {
    flex-shrink: 0;
  }
}

.dialog-body {
  .dialog-loading {
    text-align: center;
    padding: 2rem 1rem;

    .loading-text {
      margin-top: 1rem;
      color: var(--q-grey-6);
    }
  }

  .delete-confirmation {
    .warning-text {
      font-size: 1rem;
      margin-bottom: 1.5rem;
      color: var(--q-grey-8);

      strong {
        color: var(--q-negative);
        font-weight: 600;
      }
    }

    .confirmation-input {
      margin-bottom: 1rem;
    }
  }

  .confirm-content,
  .info-content {
    .confirm-message {
      font-size: 1rem;
      color: var(--q-grey-8);
      line-height: 1.5;
    }
  }
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

// 移动端适配
@media (width <= 599px) {
  .dialog-card,
  .delete-dialog-card {
    min-width: auto;
    max-width: 100vw;
  }

  .dialog-header {
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: 12px;

    .dialog-close {
      position: absolute;
      top: 8px;
      right: 8px;
    }
  }

  .dialog-actions {
    flex-direction: column-reverse;
    gap: 8px;
  }
}
</style>
