<template>
  <q-btn-dropdown flat dense icon="view_column" :label="showLabel ? '列显示' : ''" class="q-mr-xs">
    <q-list dense class="min-width-dropdown">
      <q-item-label header>
        <div class="row items-center justify-between">
          <span>显示列</span>
          <q-btn flat dense size="xs" icon="refresh" @click="resetColumns" class="q-ml-sm">
            <q-tooltip>重置为默认</q-tooltip>
          </q-btn>
        </div>
      </q-item-label>

      <q-separator />

      <template v-for="(column, index) in allColumns" :key="column.name">
        <q-item dense>
          <q-item-section avatar>
            <q-checkbox
              :model-value="isColumnVisible(column.name)"
              @update:model-value="toggleColumn(column.name)"
              :disable="isColumnRequired(column.name)"
              dense
            />
          </q-item-section>

          <q-item-section>
            <q-item-label>{{ column.label }}</q-item-label>
            <q-item-label v-if="isColumnRequired(column.name)" caption class="text-grey-6">
              必需列
            </q-item-label>
          </q-item-section>

          <q-item-section side>
            <div class="row q-gutter-xs">
              <q-btn
                flat
                dense
                size="xs"
                icon="keyboard_arrow_up"
                :disable="index === 0"
                @click.stop="moveColumnUp(index)"
              >
                <q-tooltip>上移</q-tooltip>
              </q-btn>
              <q-btn
                flat
                dense
                size="xs"
                icon="keyboard_arrow_down"
                :disable="index === allColumns.length - 1"
                @click.stop="moveColumnDown(index)"
              >
                <q-tooltip>下移</q-tooltip>
              </q-btn>
            </div>
          </q-item-section>
        </q-item>
      </template>
    </q-list>
  </q-btn-dropdown>
</template>

<script setup lang="ts">
interface TableColumn {
  name: string;
  label: string;
  field?: string | ((row: Record<string, unknown>) => unknown);
  align?: 'left' | 'center' | 'right';
  sortable?: boolean;
}

interface Props {
  allColumns: TableColumn[];
  isColumnVisible: (name: string) => boolean;
  isColumnRequired: (name: string) => boolean;
  toggleColumn: (name: string) => boolean;
  moveColumnUp: (index: number) => void;
  moveColumnDown: (index: number) => void;
  resetColumns: () => void;
  showLabel?: boolean;
}

defineProps<Props>();
</script>
