<template>
  <div class="modern-input-wrapper">
    <label v-if="label" class="modern-input-label" :for="inputId">
      {{ label }}
      <span v-if="required" class="required-mark">*</span>
    </label>

    <q-input
      :id="inputId"
      :class="[
        'modern-input',
        `modern-input--${variant}`,
        {
          'modern-input--error': hasError,
          'modern-input--success': hasSuccess,
          'modern-input--focused': focused,
        },
      ]"
      :model-value="modelValue"
      :type="computedType"
      :placeholder="placeholder"
      :readonly="readonly"
      :disable="disable"
      :loading="loading"
      :dense="dense"
      :filled="variant === 'filled'"
      :outlined="variant === 'outlined'"
      :standout="variant === 'standout'"
      :rules="rules"
      :lazy-rules="lazyRules"
      v-bind="$attrs"
      @update:model-value="$emit('update:modelValue', $event)"
      @focus="onFocus"
      @blur="onBlur"
      @keyup="$emit('keyup', $event)"
      @keydown="$emit('keydown', $event)"
    >
      <!-- 前缀插槽 -->
      <template v-slot:prepend>
        <slot name="prepend">
          <q-icon v-if="prependIcon" :name="prependIcon" :color="iconColor" />
        </slot>
      </template>

      <!-- 后缀插槽 -->
      <template v-slot:append>
        <slot name="append">
          <!-- 密码可见性切换 -->
          <q-btn
            v-if="type === 'password' && showPasswordToggle"
            flat
            round
            dense
            :icon="showPassword ? 'visibility_off' : 'visibility'"
            @click="togglePasswordVisibility"
            color="grey-6"
            size="sm"
          />
          <!-- 清除按钮 -->
          <q-btn
            v-else-if="clearable && modelValue && !readonly && !disable"
            flat
            round
            dense
            icon="close"
            @click="clearValue"
            color="grey-6"
            size="sm"
          />
          <!-- 自定义图标 -->
          <q-icon
            v-else-if="appendIcon"
            :name="appendIcon"
            :color="iconColor"
            :class="{ 'cursor-pointer': appendIconClickable }"
            @click="appendIconClickable && $emit('append-click')"
          />
        </slot>
      </template>

      <!-- 底部插槽 - 错误和帮助信息 -->
      <template v-slot:hint>
        <slot name="hint">{{ hint }}</slot>
      </template>

      <template v-slot:error>
        <slot name="error" />
      </template>
    </q-input>

    <!-- 外部帮助文本 -->
    <div v-if="helpText && !hasError" class="modern-input-help">
      {{ helpText }}
    </div>

    <!-- 字符计数 -->
    <div
      v-if="showCounter && maxlength"
      class="modern-input-counter"
      :class="{ 'counter-warning': counterWarning }"
    >
      {{ (modelValue || '').length }} / {{ maxlength }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';

type InputValue = string | number | null | undefined;

type ValidationRule =
  | string
  | boolean
  | ((val: InputValue) => boolean | string | Promise<boolean | string>);

interface Props {
  modelValue?: InputValue;
  label?: string;
  placeholder?: string;
  type?: string;
  variant?: 'outlined' | 'filled' | 'standout' | 'underline';
  prependIcon?: string;
  appendIcon?: string;
  appendIconClickable?: boolean;
  required?: boolean;
  readonly?: boolean;
  disable?: boolean;
  loading?: boolean;
  dense?: boolean;
  clearable?: boolean;
  showPasswordToggle?: boolean;
  rules?: ValidationRule[];
  lazyRules?: boolean;
  hint?: string;
  helpText?: string;
  showCounter?: boolean;
  maxlength?: number;
  iconColor?: string;
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text',
  variant: 'outlined',
  showPasswordToggle: false,
  clearable: false,
  lazyRules: false,
  showCounter: false,
  iconColor: 'primary',
});

const emit = defineEmits<{
  'update:modelValue': [value: InputValue];
  focus: [event: FocusEvent];
  blur: [event: FocusEvent];
  keyup: [event: KeyboardEvent];
  keydown: [event: KeyboardEvent];
  'append-click': [];
}>();

const focused = ref(false);
const showPassword = ref(false);
const inputId = ref('');

// 生成唯一ID
onMounted(() => {
  inputId.value = `modern-input-${Math.random().toString(36).substr(2, 9)}`;
});

// 计算输入类型
const computedType = computed(() => {
  if (props.type === 'password' && props.showPasswordToggle) {
    return showPassword.value ? 'text' : 'password';
  }
  return props.type;
});

// 检查是否有错误
const hasError = computed(() => {
  return false; // 需要集成表单验证逻辑
});

// 检查是否成功
const hasSuccess = computed(() => {
  return false; // 需要集成表单验证逻辑
});

// 字符计数警告
const counterWarning = computed(() => {
  if (!props.maxlength || !props.modelValue) return false;
  const length = props.modelValue.toString().length;
  return length > props.maxlength * 0.8;
});

// 处理焦点事件
const onFocus = (event: FocusEvent) => {
  focused.value = true;
  emit('focus', event);
};

const onBlur = (event: FocusEvent) => {
  focused.value = false;
  emit('blur', event);
};

// 切换密码可见性
const togglePasswordVisibility = () => {
  showPassword.value = !showPassword.value;
};

// 清除值
const clearValue = () => {
  emit('update:modelValue', '');
};
</script>

<style lang="scss" scoped>
@import 'src/css/quasar.variables';

// 🎨 现代化输入框包装器
// --------------------------------------------------

.modern-input-wrapper {
  position: relative;
  margin-bottom: 4px;
}

// 🏷️ 标签样式
// --------------------------------------------------

.modern-input-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--q-color-grey-8);
  margin-bottom: 8px;
  transition: color $transition-base;

  .body--dark & {
    color: var(--q-color-grey-3);
  }

  .required-mark {
    color: var(--q-negative);
    margin-left: 2px;
  }
}

// 📝 输入框样式
// --------------------------------------------------

.modern-input {
  :deep(.q-field__control) {
    border-radius: $border-radius-sm;
    transition: all $transition-base $ease-out-cubic;
    position: relative;

    &::before {
      content: '';
      position: absolute;
      inset: 0;
      border-radius: inherit;
      background: linear-gradient(
        135deg,
        transparent 0%,
        rgb(102 126 234 / 5%) 50%,
        transparent 100%
      );
      opacity: 0;
      transition: opacity $transition-base;
      pointer-events: none;
    }
  }

  // 聚焦状态
  &--focused {
    :deep(.q-field__control) {
      transform: translateY(-1px);
      box-shadow: 0 4px 12px rgb(102 126 234 / 15%);
    }

    :deep(.q-field__control::before) {
      opacity: 1;
    }
  }

  // 错误状态
  &--error {
    :deep(.q-field__control) {
      border-color: var(--q-negative) !important;
      box-shadow: 0 0 0 2px rgb(193 0 21 / 10%);
    }

    :deep(.q-field__label),
    :deep(.q-field__marginal) {
      color: var(--q-negative);
    }
  }

  // 成功状态
  &--success {
    :deep(.q-field__control) {
      border-color: var(--q-positive) !important;
      box-shadow: 0 0 0 2px rgb(33 186 69 / 10%);
    }

    :deep(.q-field__label),
    :deep(.q-field__marginal) {
      color: var(--q-positive);
    }
  }

  // 描边变体
  &--outlined {
    :deep(.q-field__control) {
      background: rgb(255 255 255 / 80%);
      border: 2px solid rgb(0 0 0 / 10%);

      .body--dark & {
        background: rgb(255 255 255 / 5%);
        border-color: rgb(255 255 255 / 20%);
      }
    }

    :deep(.q-field--focused .q-field__control) {
      border-color: var(--q-primary);
      box-shadow: 0 0 0 3px rgb(102 126 234 / 10%);
    }
  }

  // 填充变体
  &--filled {
    :deep(.q-field__control) {
      background: rgb(102 126 234 / 5%);
      border: none;
      border-bottom: 2px solid rgb(102 126 234 / 20%);
      border-radius: $border-radius-sm $border-radius-sm 0 0;

      .body--dark & {
        background: rgb(255 255 255 / 5%);
      }
    }

    :deep(.q-field--focused .q-field__control) {
      border-bottom-color: var(--q-primary);
      background: rgb(102 126 234 / 8%);
    }
  }

  // 突出变体
  &--standout {
    :deep(.q-field__control) {
      background: rgb(0 0 0 / 5%);
      border: none;
      border-radius: $border-radius-sm;

      .body--dark & {
        background: rgb(255 255 255 / 5%);
      }
    }

    :deep(.q-field--focused .q-field__control) {
      background: var(--q-primary);
      color: white;
      box-shadow: $shadow-md;
    }

    :deep(.q-field--focused .q-field__native),
    :deep(.q-field--focused .q-field__prefix),
    :deep(.q-field--focused .q-field__suffix) {
      color: white;
    }
  }

  // 下划线变体
  &--underline {
    :deep(.q-field__control) {
      background: transparent;
      border: none;
      border-bottom: 1px solid rgb(0 0 0 / 20%);
      border-radius: 0;

      .body--dark & {
        border-bottom-color: rgb(255 255 255 / 30%);
      }
    }

    :deep(.q-field--focused .q-field__control) {
      border-bottom: 2px solid var(--q-primary);
      box-shadow: none;
    }
  }

  // 加载状态
  :deep(.q-field--loading .q-field__control) {
    opacity: 0.7;
    pointer-events: none;
  }

  // 禁用状态
  :deep(.q-field--disabled .q-field__control) {
    opacity: 0.6;
    background: rgb(0 0 0 / 2%) !important;

    .body--dark & {
      background: rgb(255 255 255 / 2%) !important;
    }
  }
}

// 🆘 帮助文本
// --------------------------------------------------

.modern-input-help {
  font-size: 0.75rem;
  color: var(--q-color-grey-6);
  margin-top: 6px;
  line-height: 1.4;

  .body--dark & {
    color: var(--q-color-grey-4);
  }
}

// 🔢 字符计数器
// --------------------------------------------------

.modern-input-counter {
  position: absolute;
  right: 8px;
  bottom: -20px;
  font-size: 0.75rem;
  color: var(--q-color-grey-5);
  transition: color $transition-base;

  &.counter-warning {
    color: var(--q-warning);
    font-weight: 600;
  }
}

// 📱 响应式优化
// --------------------------------------------------

@media (width <= 768px) {
  .modern-input-label {
    font-size: 0.8125rem;
    margin-bottom: 6px;
  }

  .modern-input-help {
    font-size: 0.6875rem;
  }

  .modern-input-counter {
    bottom: -18px;
    font-size: 0.6875rem;
  }
}

// 🌙 深色模式增强
// --------------------------------------------------

.body--dark {
  .modern-input {
    &--focused :deep(.q-field__control) {
      box-shadow: 0 4px 12px rgb(0 0 0 / 30%);
    }
  }
}
</style>
