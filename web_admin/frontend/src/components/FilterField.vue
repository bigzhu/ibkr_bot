<template>
  <div class="filter-section">
    <label class="filter-label">{{ label }}</label>

    <!-- 下拉选择 -->
    <template v-if="type === 'select'">
      <q-select
        :model-value="modelValue"
        @update:model-value="handleUpdate"
        :options="options"
        :clearable="clearable"
        :filled="filled"
        :dense="dense"
        :emit-value="emitValue"
        :map-options="mapOptions"
        :option-label="optionLabel"
        :option-value="optionValue"
        :placeholder="placeholder"
        :class="fieldClass"
      />
    </template>

    <!-- 单个复选框 -->
    <template v-else-if="type === 'checkbox'">
      <q-checkbox
        :model-value="modelValue"
        @update:model-value="handleUpdate"
        :label="checkboxLabel"
        :color="checkboxColor"
        :dense="dense"
        :class="fieldClass"
      />
    </template>

    <!-- 多选复选框组 -->
    <template v-else-if="type === 'checkbox-group'">
      <div class="filter-checkbox-list">
        <q-checkbox
          v-for="option in options"
          :key="getOptionKey(option)"
          :model-value="modelValue"
          @update:model-value="handleUpdate"
          :val="getOptionValue(option)"
          :class="`filter-checkbox-item ${fieldClass}`"
        >
          <template #default>
            <slot name="option" :option="option">
              {{ getOptionLabel(option) }}
            </slot>
          </template>
        </q-checkbox>
      </div>
    </template>

    <!-- 单选按钮组 -->
    <template v-else-if="type === 'radio-group'">
      <q-option-group
        :model-value="modelValue"
        @update:model-value="handleUpdate"
        :options="options"
        :color="radioColor"
        type="radio"
        class="filter-radio-group"
      />
      <!-- 清除按钮 -->
      <q-btn
        v-if="modelValue && showClearButton"
        flat
        dense
        size="sm"
        icon="clear"
        color="grey-6"
        label="清除"
        class="q-mt-sm"
        @click="clearRadio"
      />
    </template>

    <!-- 文本输入 -->
    <template v-else-if="type === 'input'">
      <q-input
        :model-value="modelValue"
        @update:model-value="handleUpdate"
        :filled="filled"
        :dense="dense"
        :clearable="clearable"
        :placeholder="placeholder"
        :class="fieldClass"
      />
    </template>

    <!-- 日期选择 -->
    <template v-else-if="type === 'date'">
      <q-input
        :model-value="modelValue"
        @update:model-value="handleUpdate"
        type="date"
        :filled="filled"
        :dense="dense"
        :clearable="clearable"
        :min="minDate"
        :max="maxDate"
        :class="fieldClass"
      />
    </template>
  </div>
</template>

<script setup lang="ts">

type OptionPrimitive = string | number | boolean | null | undefined;

interface FilterOption {
  label?: string;
  value?: OptionPrimitive;
  [key: string]: unknown;
}

type OptionEntry = FilterOption | OptionPrimitive;
type FilterValue = OptionPrimitive | OptionPrimitive[] | Date;

interface Props {
  modelValue?: FilterValue;
  type: 'select' | 'checkbox' | 'checkbox-group' | 'radio-group' | 'input' | 'date';
  label: string;
  options?: OptionEntry[];

  // 通用属性
  clearable?: boolean;
  filled?: boolean;
  dense?: boolean;
  placeholder?: string;
  fieldClass?: string;

  // select 属性
  emitValue?: boolean;
  mapOptions?: boolean;
  optionLabel?: string;
  optionValue?: string;

  // checkbox 属性
  checkboxLabel?: string;
  checkboxColor?: string;

  // radio 属性
  radioColor?: string;
  showClearButton?: boolean;

  // date 属性
  minDate?: string;
  maxDate?: string;
}

const props = withDefaults(defineProps<Props>(), {
  clearable: true,
  filled: true,
  dense: true,
  emitValue: true,
  mapOptions: true,
  optionLabel: 'label',
  optionValue: 'value',
  checkboxColor: 'primary',
  radioColor: 'primary',
  showClearButton: true,
  fieldClass: '',
});

const emit = defineEmits<{
  'update:modelValue': [value: FilterValue];
  change: [value: FilterValue];
}>();

// 处理值变更
const handleUpdate = (value: FilterValue) => {
  emit('update:modelValue', value);
  emit('change', value);
};

// 清除单选按钮组
const clearRadio = () => {
  handleUpdate('');
};

// 获取选项的键值
const getOptionKey = (option: OptionEntry): string => {
  if (typeof option === 'string') return option;
  if (typeof option === 'number') return option.toString();
  if (typeof option === 'boolean') return option ? 'true' : 'false';

  const candidate =
    (option[props.optionValue] as OptionPrimitive | undefined) ?? option.value ?? option.label;
  return String(candidate ?? '');
};

// 获取选项的显示值
const getOptionLabel = (option: OptionEntry): OptionPrimitive => {
  if (typeof option === 'string' || typeof option === 'number' || typeof option === 'boolean') {
    return option;
  }
  return (
    (option[props.optionLabel] as OptionPrimitive | undefined) ?? option.label ?? option.value ?? ''
  );
};

// 获取选项的实际值
const getOptionValue = (option: OptionEntry): OptionPrimitive => {
  if (typeof option === 'string' || typeof option === 'number' || typeof option === 'boolean') {
    return option;
  }
  return (option[props.optionValue] as OptionPrimitive | undefined) ?? option.value ?? null;
};
</script>

<style lang="scss" scoped>
.filter-section {
  margin-bottom: 24px;

  &:last-child {
    margin-bottom: 0;
  }
}

.filter-label {
  display: block;
  margin-bottom: 8px;
  font-size: 0.875rem;
  color: rgb(255 255 255 / 70%);
  font-weight: 500;
}

.filter-radio-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-checkbox-list {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  padding-right: 8px;

  &::-webkit-scrollbar {
    width: 6px;
  }

  &::-webkit-scrollbar-track {
    background: rgb(255 255 255 / 5%);
    border-radius: 3px;
  }

  &::-webkit-scrollbar-thumb {
    background: rgb(255 255 255 / 20%);
    border-radius: 3px;

    &:hover {
      background: rgb(255 255 255 / 30%);
    }
  }
}

.filter-checkbox-item {
  margin: 0;
}
</style>
