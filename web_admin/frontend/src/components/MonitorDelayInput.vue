<template>
  <q-input
    :model-value="modelValue"
    @update:model-value="handleUpdate"
    @blur="$emit('blur')"
    type="number"
    dense
    min="0"
    step="0.1"
    suffix="s"
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
  if (!isNaN(numValue) && numValue >= 0) {
    emit('update:modelValue', numValue);
  }
};
</script>
