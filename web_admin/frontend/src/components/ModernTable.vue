<template>
  <div class="modern-table-container">
    <!-- 表格工具栏 -->
    <div v-if="$slots.toolbar || showToolbar" class="table-toolbar">
      <slot name="toolbar">
        <div class="toolbar-left">
          <div v-if="title" class="table-title">
            <q-icon v-if="icon" :name="icon" size="20px" color="primary" class="q-mr-sm" />
            {{ title }}
          </div>
          <div v-if="subtitle" class="table-subtitle">{{ subtitle }}</div>
        </div>
        <div class="toolbar-right">
          <slot name="actions" />
        </div>
      </slot>
    </div>

    <!-- 表格主体 -->
    <q-table
      :class="tableClasses"
      :table-class="tableClassAttr"
      :rows="rows"
      :columns="columns"
      :row-key="rowKey"
      :pagination="computedPagination"
      :loading="loading"
      :selection="selection"
      :selected="selected"
      :flat="flat"
      :bordered="false"
      v-bind="forwardedAttrs"
      @update:selected="$emit('update:selected', $event)"
      @update:pagination="$emit('update:pagination', $event)"
      @request="$emit('request', $event)"
    >
      <!-- 自定义加载状态 -->
      <template v-slot:loading>
        <q-inner-loading showing :color="loadingColor">
          <div class="loading-content">
            <LoadingSpinner variant="gear" size="md" />
            <div class="loading-text q-mt-md">{{ loadingText }}</div>
          </div>
        </q-inner-loading>
      </template>

      <!-- 无数据状态 -->
      <template v-slot:no-data="{ message }">
        <div class="no-data-container">
          <div class="no-data-content">
            <q-icon name="inbox" size="64px" color="grey-4" />
            <div class="no-data-title">{{ noDataTitle }}</div>
            <div class="no-data-message">{{ message || noDataMessage }}</div>
            <slot name="no-data-actions" />
          </div>
        </div>
      </template>

      <!-- 透传所有插槽 -->
      <template v-for="(_, slot) in $slots" v-slot:[slot]="scope" :key="slot">
        <slot :name="slot" v-bind="scope" />
      </template>
    </q-table>

    <!-- 表格底部信息 -->
    <div v-if="showSummary && rows.length > 0" class="table-summary">
      <slot name="summary">
        <div class="summary-text">
          共 {{ rows.length }} 条记录
          <template v-if="selected && selected.length > 0">
            ,已选择 {{ selected.length }} 项
          </template>
        </div>
      </slot>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, useAttrs } from 'vue';
import LoadingSpinner from './LoadingSpinner.vue';

type TableRecord = Record<string, unknown>;

interface PaginationConfig extends TableRecord {
  sortBy?: string;
  descending?: boolean;
  page?: number;
  rowsPerPage?: number;
  rowsNumber?: number;
  rowsPerPageOptions?: number[];
}

interface Props {
  // 表格基础属性
  rows: TableRecord[];
  columns: TableRecord[];
  rowKey: string;

  // 样式变体
  variant?: 'default' | 'modern' | 'minimal' | 'card';
  striped?: boolean;
  hoverable?: boolean;
  bordered?: boolean;
  dense?: boolean;
  flat?: boolean;

  // 工具栏
  title?: string;
  subtitle?: string;
  icon?: string;
  showToolbar?: boolean;

  // 分页
  pagination?: PaginationConfig | false;
  hidePagination?: boolean;

  // 选择
  selection?: 'single' | 'multiple';
  selected?: TableRecord[];

  // 状态
  loading?: boolean;
  loadingColor?: string;
  loadingText?: string;

  // 无数据
  noDataTitle?: string;
  noDataMessage?: string;

  // 底部摘要
  showSummary?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
  striped: false,
  hoverable: true,
  bordered: false,
  dense: false,
  flat: true,
  showToolbar: false,
  hidePagination: false,
  loadingColor: 'primary',
  loadingText: '加载中...',
  noDataTitle: '暂无数据',
  noDataMessage: '当前没有可显示的数据',
  showSummary: false,
});

const attrs = useAttrs();

defineEmits<{
  'update:selected': [selected: TableRecord[]];
  'update:pagination': [pagination: PaginationConfig];
  request: [payload: unknown];
}>();

// 计算分页配置
const computedPagination = computed<PaginationConfig | false>(() => {
  if (props.hidePagination) {
    return { rowsPerPage: 0 };
  }
  if (props.pagination === false) return false;

  return {
    rowsPerPage: 10,
    rowsPerPageOptions: [5, 10, 20, 50],
    ...(props.pagination ?? {}),
  };
});
const tableClasses = computed(() => {
  const extraClass = attrs.class as string | undefined;
  return [
    'modern-table',
    `modern-table--${props.variant}`,
    {
      'modern-table--striped': props.striped,
      'modern-table--hover': props.hoverable,
      'modern-table--bordered': props.bordered,
      'modern-table--compact': props.dense,
    },
    extraClass,
  ];
});

const tableClassAttr = computed(() => (attrs as Record<string, unknown>)['table-class']);

const forwardedAttrs = computed(() => {
  const result: Record<string, unknown> = {};
  Object.keys(attrs).forEach((key) => {
    if (key !== 'class' && key !== 'table-class') {
      result[key] = (attrs as Record<string, unknown>)[key];
    }
  });
  return result;
});
</script>

<style lang="scss" scoped>
@import 'src/css/quasar.variables';

// 🎨 现代化表格容器
// --------------------------------------------------

.modern-table-container {
  background: white;
  border-radius: $border-radius-md;
  border: 1px solid rgb(0 0 0 / 5%);
  overflow: hidden;

  .body--dark & {
    background: $dark-surface;
    border-color: rgb(255 255 255 / 10%);
  }
}

// 支持宽表格的水平滚动
.modern-table-container--scrollable {
  overflow-x: auto !important;
  overflow-y: hidden;
}

// 🔧 表格工具栏
// --------------------------------------------------

.table-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  background: rgb(0 0 0 / 2%);
  border-bottom: 1px solid rgb(0 0 0 / 5%);

  .body--dark & {
    background: rgb(255 255 255 / 2%);
    border-bottom-color: rgb(255 255 255 / 5%);
  }

  .toolbar-left {
    flex: 1;

    .table-title {
      font-size: 1.125rem;
      font-weight: 600;
      color: var(--q-color-grey-8);
      display: flex;
      align-items: center;
      margin-bottom: 4px;

      .body--dark & {
        color: var(--q-color-grey-2);
      }
    }

    .table-subtitle {
      font-size: 0.875rem;
      color: var(--q-color-grey-6);

      .body--dark & {
        color: var(--q-color-grey-4);
      }
    }
  }

  .toolbar-right {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

// 📊 表格主体样式
// --------------------------------------------------

.modern-table {
  :deep(.q-table__container) {
    border-radius: 0;
  }

  // ensure row-level highlights override hover/striped styles
  :deep(tbody tr.order-highlight-buy td),
  :deep(tbody tr.order-highlight-buy th) {
    background-color: rgb(46 125 50 / 28%) !important;

    &:hover {
      background-color: rgb(46 125 50 / 33%) !important;
    }

    .body--dark & {
      background-color: rgb(46 125 50 / 38%) !important;

      &:hover {
        background-color: rgb(46 125 50 / 44%) !important;
      }
    }
  }

  :deep(tbody tr.order-highlight-sell td),
  :deep(tbody tr.order-highlight-sell th) {
    background-color: rgb(198 40 40 / 28%) !important;

    &:hover {
      background-color: rgb(198 40 40 / 32%) !important;
    }

    .body--dark & {
      background-color: rgb(198 40 40 / 36%) !important;

      &:hover {
        background-color: rgb(198 40 40 / 42%) !important;
      }
    }
  }

  :deep(tbody tr.order-highlight-default td),
  :deep(tbody tr.order-highlight-default th) {
    background-color: rgb(96 125 139 / 26%) !important;

    &:hover {
      background-color: rgb(96 125 139 / 32%) !important;
    }

    .body--dark & {
      background-color: rgb(96 125 139 / 34%) !important;

      &:hover {
        background-color: rgb(96 125 139 / 40%) !important;
      }
    }
  }

  // 表头样式
  :deep(thead) {
    tr:first-child th {
      background: rgb(102 126 234 / 5%);
      color: var(--q-primary);
      font-weight: 600;
      font-size: 0.875rem;
      padding: 16px 12px;
      border-bottom: 2px solid rgb(102 126 234 / 10%);

      .body--dark & {
        background: rgb(102 126 234 / 10%);
        border-bottom-color: rgb(102 126 234 / 20%);
      }
    }
  }

  // 表格行样式
  :deep(tbody) {
    tr {
      transition: all $transition-fast $ease-out-cubic;
      border-bottom: 1px solid rgb(0 0 0 / 5%);

      .body--dark & {
        border-bottom-color: rgb(255 255 255 / 5%);
      }

      td {
        padding: 16px 12px;
        vertical-align: middle;
        border-bottom: none;
      }

      &:last-child {
        border-bottom: none;
      }
    }
  }

  // 悬浮效果
  &--hover :deep(tbody tr:hover) {
    background: rgb(102 126 234 / 3%);
    transform: scale(1.002);

    .body--dark & {
      background: rgb(102 126 234 / 8%);
    }
  }

  // 条纹效果
  &--striped :deep(tbody tr:nth-child(even)) {
    background: rgb(0 0 0 / 2%);

    .body--dark & {
      background: rgb(255 255 255 / 2%);
    }
  }

  // 边框效果
  &--bordered {
    :deep(td),
    :deep(th) {
      border-right: 1px solid rgb(0 0 0 / 5%);

      .body--dark & {
        border-right-color: rgb(255 255 255 / 5%);
      }

      &:last-child {
        border-right: none;
      }
    }
  }

  // 紧凑模式
  &--compact {
    :deep(th),
    :deep(td) {
      padding: 8px 12px;
    }
  }

  // 现代变体
  &--modern {
    :deep(thead tr:first-child th) {
      background: $gradient-primary;
      color: white;
      font-weight: 600;
    }

    :deep(tbody tr:hover) {
      background: rgb(102 126 234 / 5%);
      box-shadow: inset 0 0 0 1px rgb(102 126 234 / 10%);
    }
  }

  // 极简变体
  &--minimal {
    :deep(thead tr:first-child th) {
      background: transparent;
      border-bottom: 1px solid rgb(0 0 0 / 10%);
      color: var(--q-color-grey-7);
    }

    :deep(tbody tr) {
      border-bottom: 1px solid rgb(0 0 0 / 5%);
    }
  }

  // 卡片变体
  &--card {
    :deep(tbody tr) {
      margin-bottom: 8px;
      border-radius: $border-radius-sm;
      border: 1px solid rgb(0 0 0 / 5%);
      box-shadow: $shadow-sm;

      &:hover {
        box-shadow: $shadow-md;
      }
    }
  }
}

// 📡 加载状态
// --------------------------------------------------

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;

  .loading-text {
    color: var(--q-primary);
    font-weight: 500;
  }
}

// 📭 无数据状态
// --------------------------------------------------

.no-data-container {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;

  .no-data-content {
    text-align: center;

    .no-data-title {
      font-size: 1.125rem;
      font-weight: 600;
      color: var(--q-color-grey-7);
      margin: 16px 0 8px;

      .body--dark & {
        color: var(--q-color-grey-4);
      }
    }

    .no-data-message {
      color: var(--q-color-grey-5);
      margin-bottom: 16px;
    }
  }
}

// 📊 表格摘要
// --------------------------------------------------

.table-summary {
  padding: 12px 24px;
  background: rgb(0 0 0 / 2%);
  border-top: 1px solid rgb(0 0 0 / 5%);

  .body--dark & {
    background: rgb(255 255 255 / 2%);
    border-top-color: rgb(255 255 255 / 5%);
  }

  .summary-text {
    font-size: 0.875rem;
    color: var(--q-color-grey-6);

    .body--dark & {
      color: var(--q-color-grey-4);
    }
  }
}

// 📱 响应式优化
// --------------------------------------------------

@media (width <= 768px) {
  .table-toolbar {
    padding: 16px;
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;

    .toolbar-right {
      align-self: stretch;
      justify-content: flex-end;
    }
  }

  .modern-table {
    :deep(th),
    :deep(td) {
      padding: 12px 8px;
      font-size: 0.875rem;
    }

    :deep(thead tr:first-child th) {
      padding: 12px 8px;
    }
  }

  .table-summary {
    padding: 12px 16px;
  }
}

@media (width <= 480px) {
  .modern-table {
    :deep(th),
    :deep(td) {
      padding: 8px 6px;
      font-size: 0.8rem;
    }
  }
}
</style>
