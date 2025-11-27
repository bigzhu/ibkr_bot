<template>
  <q-input
    :model-value="modelValue"
    @update:model-value="handleUpdate"
    @blur="$emit('blur')"
    type="number"
    dense
    min="0"
    max="100"
    step="0.001"
    suffix="%"
    borderless
    input-class="text-right"
    class="signal-input"
    :disable="disabled"
  />
</template>

<script setup lang="ts">
interface Props {
  modelValue?: number | string;
  disabled?: boolean;
}

interface Emits {
  (e: 'update:modelValue', value: number): void;
  (e: 'blur'): void;
}

withDefaults(defineProps<Props>(), {
  disabled: false,
});

const emit = defineEmits<Emits>();

const handleUpdate = (value: string) => {
  const numValue = parseFloat(value);
  if (!isNaN(numValue) && numValue >= 0 && numValue <= 100) {
    emit('update:modelValue', numValue);
  }
};
</script>
