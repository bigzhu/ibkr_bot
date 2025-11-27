<template>
  <q-expansion-item
    class="symbol-list-item"
    :class="{ 'symbol-list-item--paused': !symbol.is_active }"
    :label="symbol.symbol"
    :caption="`${symbol.is_active ? '活跃' : '暂停'}`"
    :header-class="[
      'symbol-list-item__header-container',
      !symbol.is_active && 'symbol-list-item__header-container--paused',
    ]"
    switch-toggle-side
    :model-value="expanded"
    @before-show="handleExpand(true)"
    @before-hide="handleExpand(false)"
  >
    <template #header>
      <div class="symbol-list-item__header row items-center full-width">
        <div class="col-auto">
          <TradingPairIcon
            :symbol="symbol.symbol"
            :show-text="true"
            icon-size="32px"
            text-class="text-h6 text-weight-bold"
          />
        </div>

        <div class="col q-ml-md">
          <div class="row items-center q-gutter-sm">
            <StatusIndicator
              :status="symbol.is_active ? 'success' : 'neutral'"
              :label="symbol.is_active ? '活跃' : '暂停'"
              :animated="symbol.is_active"
              variant="small"
            />
            <q-chip color="positive" text-color="white" size="sm">
              <q-icon name="play_circle" size="xs" class="q-mr-xs" />
              活跃: {{ activeConfigCountValue }}
            </q-chip>
            <q-chip color="negative" text-color="white" size="sm">
              <q-icon name="pause_circle" size="xs" class="q-mr-xs" />
              暂停: {{ inactiveConfigCountValue }}
            </q-chip>
          </div>
        </div>

        <div class="col-auto">
          <div class="row q-gutter-xs">
            <q-btn
              :icon="symbol.is_active ? 'pause' : 'play_arrow'"
              :color="symbol.is_active ? 'warning' : 'positive'"
              size="sm"
              round
              flat
              :loading="symbol.isToggling"
              @click.stop="emit('toggle-status', symbol)"
            >
              <q-tooltip>{{ symbol.is_active ? '暂停' : '启用' }}</q-tooltip>
            </q-btn>
            <q-btn
              icon="delete"
              color="negative"
              size="sm"
              round
              flat
              :loading="symbol.isDeleting"
              @click.stop="emit('delete', symbol)"
            >
              <q-tooltip>删除交易对</q-tooltip>
            </q-btn>
          </div>
        </div>
      </div>
    </template>

    <div class="symbol-list-item__body q-pa-md">
      <div class="symbol-list-item__timeframes">
        <TimeframeConfigList
          :symbol="symbol.symbol"
          :expanded="expanded"
          @config-updated="(payload) => emit('config-updated', payload)"
        />
      </div>
    </div>
  </q-expansion-item>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import TradingPairIcon from 'src/components/TradingPairIcon.vue';
import StatusIndicator from 'src/components/StatusIndicator.vue';
import TimeframeConfigList from 'src/components/TimeframeConfigList.vue';
import type { ManagedSymbol } from 'src/types/symbols';


const props = defineProps<{
  symbol: ManagedSymbol;
  expanded: boolean;
  activeConfigCount: number;
  inactiveConfigCount: number;
}>();

const emit = defineEmits<{
  (event: 'expand', expanded: boolean): void;
  (event: 'toggle-status', symbol: ManagedSymbol): void;
  (event: 'delete', symbol: ManagedSymbol): void;
  (event: 'config-updated', symbol: string): void;
}>();

const handleExpand = (shouldExpand: boolean) => {
  emit('expand', shouldExpand);
};

const activeConfigCountValue = computed(() => props.activeConfigCount);
const inactiveConfigCountValue = computed(() => props.inactiveConfigCount);
</script>

<style lang="scss" scoped>
@import 'src/css/quasar.variables';

.symbol-list-item {
  border-radius: $border-radius-md;
  margin-bottom: $spacing-sm;
  overflow: hidden;
  background: $white-alpha-02;
  border: 1px solid $white-alpha-08;
  transition: background $transition-base $ease-in-out-cubic,
    border-color $transition-base $ease-in-out-cubic;

  &--paused {
    opacity: 0.65;
  }

  &__header-container {
    &--paused {
      filter: grayscale(0.2);
    }
  }

  &__body {
    background: $white-alpha-02;
    border-top: 1px solid $white-alpha-05;
  }

  &__config {
    background: $white-alpha-05;
    border-radius: $border-radius-sm;
    padding: $spacing-sm $spacing-md;
    border: 1px solid $white-alpha-10;

    .text-weight-medium {
      color: $text-body;
      font-size: $font-size-sm;
    }

    @include mobile-flex-column {
      flex-direction: column;
      gap: 8px;
    }

    .q-ml-lg {
      margin-left: $spacing-lg;
    }

    @media (width <= 768px) {
      align-items: flex-start !important;

      .q-ml-lg {
        margin-left: 0 !important;
      }
    }
  }

  &__trapped-input {
    width: 100px;
  }

  &__signal {
    min-width: 60px;

    .signal-bar {
      margin: 4px 0;
    }

    .signal-value {
      font-size: 0.9rem;
      line-height: 1;
    }
  }
}

:deep(.q-expansion-item__container) {
  .q-expansion-item__toggle-icon {
    color: $text-muted;
  }
}
</style>
