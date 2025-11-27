<template>
  <ModernCard
    :title="title"
    :subtitle="subtitle"
    :icon="icon"
    :icon-size="iconSize"
    :icon-color="iconColor"
    :variant="variant"
    :hoverable="hoverable"
    :glass="glass"
    :elevated="elevated"
    :loading="loading"
    :loading-color="loadingColor"
  >
    <template #header>
      <div class="data-table-card__header">
        <div class="data-table-card__title">
          <slot name="title">
            <div v-if="title" class="card-title">{{ title }}</div>
            <div v-if="subtitle" class="card-subtitle">{{ subtitle }}</div>
          </slot>
        </div>
        <div v-if="$slots.actions" class="data-table-card__actions">
          <slot name="actions" />
        </div>
      </div>
    </template>

    <slot />

    <template v-if="$slots.footer" #footer>
      <slot name="footer" />
    </template>
  </ModernCard>
</template>

<script setup lang="ts">
import ModernCard from './ModernCard.vue';

type CardVariant = 'default' | 'gradient' | 'glass' | 'outlined';

interface Props {
  title?: string;
  subtitle?: string;
  icon?: string;
  iconSize?: string;
  iconColor?: string;
  variant?: CardVariant;
  hoverable?: boolean;
  glass?: boolean;
  elevated?: boolean;
  loading?: boolean;
  loadingColor?: string;
}

withDefaults(defineProps<Props>(), {
  variant: 'glass',
  iconSize: '24px',
  iconColor: 'primary',
  hoverable: true,
  glass: false,
  elevated: false,
  loading: false,
  loadingColor: 'primary',
});
</script>

<style scoped lang="scss">
@import 'src/css/quasar.variables';

.data-table-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: $spacing-sm;
  flex-wrap: wrap;
}

.data-table-card__title {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
  flex-wrap: wrap;
}

.data-table-card__actions {
  display: flex;
  align-items: center;
  gap: $spacing-sm;
}
</style>
