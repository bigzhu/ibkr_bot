<template>
  <div class="loading-state" :class="[`loading-state--${size}`]">
    <LoadingSpinner :variant="variant" :size="spinnerSize" />
    <div v-if="message" class="loading-state__message">{{ message }}</div>
    <slot />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import LoadingSpinner from './LoadingSpinner.vue';

type LoadingVariant = 'dots' | 'gear' | 'pulse' | 'wave' | 'cube';
type LoadingSize = 'sm' | 'md' | 'lg';

interface Props {
  message?: string;
  variant?: LoadingVariant;
  size?: LoadingSize;
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'dots' as LoadingVariant,
  size: 'md' as LoadingSize,
  message: '',
});

const spinnerSize = computed(() => props.size);
</script>

<style scoped lang="scss">
@import 'src/css/quasar.variables';

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: $spacing-xs;
  text-align: center;

  &--md {
    padding: $spacing-md;
  }

  &--lg {
    padding: $spacing-lg;
  }

  &__message {
    font-size: 0.875rem;
    color: var(--q-color-grey-7);
  }
}
</style>
