<template>
  <ModernCard class="symbols-filter-card q-mb-sm" variant="glass" icon="search">
    <template #header>
      <div class="symbols-filter-card__title">搜索与筛选</div>
    </template>

    <div class="row q-gutter-sm symbols-filter-card__controls">
      <div class="col-12 col-sm-4">
        <div class="symbols-filter-card__field">
          <label class="symbols-filter-card__label">搜索交易对</label>
          <ModernInput
            v-model="searchModel"
            placeholder="输入交易对名称..."
            prepend-icon="search"
            clearable
            variant="filled"
            class="symbols-filter-card__input"
          />
        </div>
      </div>

      <div class="col-12 col-sm-4">
        <div class="symbols-filter-card__field">
          <label class="symbols-filter-card__label">状态筛选</label>
          <q-select
            v-model="statusModel"
            filled
            :options="statusOptions"
            emit-value
            map-options
            clearable
            class="symbols-filter-card__input"
          />
        </div>
      </div>
    </div>
  </ModernCard>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import ModernCard from 'src/components/ModernCard.vue';
import ModernInput from 'src/components/ModernInput.vue';

interface StatusOption {
  label: string;
  value: boolean;
}

const props = defineProps<{
  search: string;
  status: boolean | '';
  statusOptions: StatusOption[];
}>();

const emit = defineEmits<{
  (event: 'update:search', value: string): void;
  (event: 'update:status', value: boolean | ''): void;
}>();

const searchModel = computed({
  get: () => props.search,
  set: (value: string) => emit('update:search', value),
});

const statusModel = computed({
  get: () => props.status,
  set: (value: boolean | '') => emit('update:status', value),
});
</script>

<style lang="scss" scoped>
@import 'src/css/quasar.variables';

.symbols-filter-card {
  &__title {
    font-size: $font-size-base;
    font-weight: 600;
    color: $text-heading;
  }

  &__controls {
    margin-top: $spacing-xs;
  }

  &__field {
    display: flex;
    flex-direction: column;
  }

  &__label {
    margin-bottom: $spacing-xs;
    font-size: $font-size-sm;
    color: $text-muted;
  }

  &__input {
    width: 100%;
  }
}
</style>
