<template>
  <q-page class="modern-page">
    <!-- 页面头部 -->
    <PageHeader
      title="成交订单"
      subtitle="显示 filled_orders 表的数据"
      icon="receipt_long"
      glow-type="default"
    >
      <template #actions>
        <ModernButton
          icon="refresh"
          variant="outline"
          size="sm"
          :loading="loading"
          @click="() => loadOrders(true)"
        >
          刷新
        </ModernButton>
      </template>
    </PageHeader>

    <!-- 统计卡片 -->
    <StatsCardsRow :cards="statsCards" :columns="3" />

    <!-- 筛选器 -->
    <FilterDrawer
      :filters="filters"
      :field-configs="filterConfigs"
      @update:filters="updateFilters"
      @apply="handleFilterApply"
      @reset="handleFilterReset"
    />

    <!-- 数据表格 -->
    <DataTableCard class="orders-card" title="订单数据" icon="table_chart">
      <template #actions>
        <TableColumnControl
          :all-columns="allColumns"
          :is-column-visible="isColumnVisible"
          :is-column-required="isColumnRequired"
          :toggle-column="toggleColumn"
          :move-column-up="moveColumnUp"
          :move-column-down="moveColumnDown"
          :reset-columns="resetColumns"
        />
      </template>

      <ModernTable
        :rows="orders"
        :columns="filteredColumns"
        :loading="loading"
        row-key="id"
        :pagination="pagination"
        @request="onRequest"
        server-pagination
        :dense="true"
        :rows-per-page-options="[20, 50, 100, 200, 500, 1000]"
        class="filled-orders-table"
      >
            <!-- 交易对列 -->
            <template v-slot:body-cell-pair="props">
              <component :is="renderDefaultPairCell" v-bind="props" />
            </template>

            <!-- 方向列 -->
            <template v-slot:body-cell-side="props">
              <q-td :props="props">
                <OrderSideChip :side="props.value" />
              </q-td>
            </template>

            <!-- 状态列 -->
            <template v-slot:body-cell-status="props">
              <q-td :props="props">
                <OrderStatusBadge :status="props.value" />
              </q-td>
            </template>

            <!-- 订单类型列 -->
            <template v-slot:body-cell-order_type="props">
              <q-td :props="props">
                <q-chip dense outline>
                  {{ props.value === 'LIMIT' ? '限价单' : props.value }}
                </q-chip>
              </q-td>
            </template>

            <!-- 时间列格式化 -->
            <template v-slot:body-cell-time="props">
              <component :is="renderCompletedTimeCell" v-bind="props" />
            </template>

            <template v-slot:body-cell-date_utc="props">
              <component :is="renderCreatedTimeCell" v-bind="props" />
            </template>

            <template v-slot:body-cell-kline_time="props">
              <component :is="renderTimeCellWithFormatter" v-bind="props" />
            </template>

            <!-- 数量和金额格式化 -->
            <template v-slot:body-cell-order_amount="props">
              <component :is="renderOrderAmountCell" v-bind="props" />
            </template>

            <template v-slot:body-cell-executed="props">
              <component :is="renderExecutedAmountCell" v-bind="props" />
            </template>

            <template v-slot:body-cell-average_price="props">
              <q-td :props="props">
                <div class="text-weight-medium">
                  {{ props.value ?? '-' }}
                </div>
              </q-td>
            </template>

            <template v-slot:body-cell-trading_total="props">
              <component :is="renderTradingTotalCell" v-bind="props" />
            </template>

            <template v-slot:body-cell-unmatched_qty="props">
              <q-td :props="props">
                <div
                  class="text-weight-medium"
                  :class="
                    Number(props.value || 0) > 0 ? 'text-warning' : getValueColor(props.value)
                  "
                >
                  {{ props.value ? formatQuantity(props.value) : '-' }}
                </div>
              </q-td>
            </template>

            <!-- 利润列 -->
            <template v-slot:body-cell-profit="props">
              <component :is="renderProfitAmountCell" v-bind="props" />
            </template>

            <!-- 手续费列 -->
            <template v-slot:body-cell-commission="props">
              <component :is="renderCommissionAmountCell" v-bind="props" />
            </template>

            <!-- 周期列 -->
            <template v-slot:body-cell-client_order_id="props">
              <q-td :props="props">
                <TimeframeChip
                  :timeframe="props.value ? props.value.replace(/_1$/, '') : null"
                  :order-side="props.row.side"
                />
              </q-td>
            </template>

            <!-- 无数据时的显示 -->
            <template #no-data>
              <EmptyStateDisplay
                type="orders"
                title="暂无成交订单数据"
                description="当前没有符合条件的成交订单记录"
                size="md"
              >
                <template #actions>
                  <ModernButton
                    icon="refresh"
                    variant="gradient"
                    size="sm"
                    :loading="loading"
                    @click="() => loadOrders(true)"
                  >
                    刷新数据
                  </ModernButton>
                </template>
              </EmptyStateDisplay>
            </template>
      </ModernTable>
    </DataTableCard>
  </q-page>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue';
import { useQuasar } from 'quasar';
import { formatQuantity } from 'src/utils/formatters';
import { formatDateTime as formatDateTimeUtil } from 'src/utils/datetime';
import { createStatsCards } from 'src/utils/stats-cards';
import { useTableColumns } from 'src/composables/useTableColumns';
import { useTableCellRenderers } from 'src/composables/useTableCellRenderers';
import PageHeader from 'src/components/PageHeader.vue';
import DataTableCard from 'src/components/DataTableCard.vue';
import ModernButton from 'src/components/ModernButton.vue';
import ModernTable from 'src/components/ModernTable.vue';
import StatsCardsRow from 'src/components/StatsCardsRow.vue';
import TableColumnControl from 'src/components/TableColumnControl.vue';
import OrderSideChip from 'src/components/OrderSideChip.vue';
import OrderStatusBadge from 'src/components/OrderStatusBadge.vue';
import TimeframeChip from 'src/components/TimeframeChip.vue';
import EmptyStateDisplay from 'src/components/EmptyStateDisplay.vue';
import FilterDrawer from 'src/components/FilterDrawer.vue';
import { useFilledOrdersStore } from 'src/stores/filled-orders-store';
import { storeToRefs } from 'pinia';
import type { FilledOrdersQuery } from 'src/stores/filled-orders-store';
import { useApiRequest } from 'src/composables/useApiRequest';
import { api } from 'src/services';

const $q = useQuasar();
const filledOrdersStore = useFilledOrdersStore();

// 响应式数据 - 依赖 Pinia store
const {
  ordersForCurrentPage: orders,
  stats,
  pagination,
  loadingOrders,
} = storeToRefs(filledOrdersStore);

const loading = computed(() => loadingOrders.value);

const resolvedStats = computed(() => {
  const current = stats.value;
  if (!current) {
    return {
      total_orders: 0,
      unmatched_count: 0,
      matched_count: 0,
    };
  }
  return current;
});

const { renderPairCell, renderPriceCell, renderQuantityCell, renderAmountCell, renderTimeCell } =
  useTableCellRenderers();
type TableSlotProps = Parameters<typeof renderPairCell>[0];

const renderDefaultPairCell = (props: TableSlotProps) => renderPairCell(props);

const renderOrderAmountCell = (props: TableSlotProps) => renderQuantityCell(props);
const renderExecutedAmountCell = renderOrderAmountCell;

const renderTradingTotalCell = (props: TableSlotProps) =>
  renderPriceCell(props, { type: 'amount', showDollar: true });

const renderProfitAmountCell = (props: TableSlotProps) => renderAmountCell(props, { type: 'income' });
const renderCommissionAmountCell = (props: TableSlotProps) =>
  renderAmountCell(props, { type: 'expense' });

const formatFilledOrderTime = (rawValue: unknown) =>
  formatDateTimeUtil(rawValue as string | number | Date | null | undefined, {
    includeYear: false,
    includeSeconds: false,
    assumeUtc: true,
  });

const renderTimeCellWithFormatter = (props: TableSlotProps) =>
  renderTimeCell(props, { formatter: formatFilledOrderTime });
const renderCompletedTimeCell = renderTimeCellWithFormatter;
const renderCreatedTimeCell = renderTimeCellWithFormatter;

// 统计卡片
const statsCards = computed(() =>
  createStatsCards(
    [
      {
        value: resolvedStats.value.total_orders,
        label: '总订单数',
        icon: 'receipt',
        iconType: 'total',
      },
      {
        value: resolvedStats.value.unmatched_count,
        label: '未完全撮合',
        icon: 'schedule',
        iconType: 'warning',
      },
      {
        value: resolvedStats.value.matched_count,
        label: '完全撮合',
        icon: 'check_circle',
        iconType: 'success',
      },
    ],
    { preset: 'gradient' },
  ),
);

// 过滤器
const filters = reactive({
  symbol: '',
  side: '',
});

// 交易对选项
const symbolOptions = ref<Array<{ label: string; value: string }>>([]);

// 筛选器配置
const filterConfigs = ref([
  {
    key: 'symbol',
    type: 'select',
    label: '交易对',
    options: computed(() => symbolOptions.value || []),
    props: {
      optionLabel: 'label',
      optionValue: 'value',
    },
  },
  {
    key: 'side',
    type: 'select',
    label: '方向',
    options: [
      { label: 'BUY', value: 'BUY' },
      { label: 'SELL', value: 'SELL' },
    ],
    props: {
      optionLabel: 'label',
      optionValue: 'value',
    },
  },
]);

const { execute: fetchOrdersTask } = useApiRequest(
  async (overrides: Partial<FilledOrdersQuery> = {}, forceRefresh = false) => {
    await filledOrdersStore.fetchOrders(overrides, forceRefresh);
  },
  {
    notifySuccess: false,
    notifyError: false,
    onError: (error) => notifyError('加载成交订单失败', error),
  },
);

const { execute: fetchStatsTask } = useApiRequest(
  async (forceRefresh = false) => {
    await filledOrdersStore.fetchStats(forceRefresh);
  },
  {
    notifySuccess: false,
    notifyError: false,
    onError: (error) => notifyError('加载撮合统计失败', error),
  },
);

// 原始表格列定义
const originalColumns = [
  { name: 'id', label: 'ID', field: 'id', sortable: true, align: 'left' },
  { name: 'kline_time', label: 'K线时间', field: 'kline_time', sortable: true, align: 'left' },
  { name: 'time', label: '完成时间', field: 'time', sortable: true, align: 'left' },
  { name: 'date_utc', label: '创建时间', field: 'date_utc', sortable: true, align: 'left' },
  { name: 'pair', label: '交易对', field: 'pair', sortable: true, align: 'left' },
  { name: 'side', label: '方向', field: 'side', sortable: true, align: 'left' },
  { name: 'order_type', label: '类型', field: 'order_type', sortable: true, align: 'left' },
  { name: 'status', label: '状态', field: 'status', sortable: true, align: 'left' },
  {
    name: 'order_amount',
    label: '挂单数量',
    field: 'order_amount',
    sortable: true,
    align: 'left',
  },
  { name: 'executed', label: '成交数量', field: 'executed', sortable: true, align: 'left' },
  {
    name: 'average_price',
    label: '成交价格',
    field: 'average_price',
    sortable: true,
    align: 'left',
  },
  {
    name: 'trading_total',
    label: '成交总额',
    field: 'trading_total',
    sortable: true,
    align: 'left',
  },
  {
    name: 'unmatched_qty',
    label: '未撮合数量',
    field: 'unmatched_qty',
    sortable: true,
    align: 'left',
  },
  { name: 'profit', label: '利润', field: 'profit', sortable: true, align: 'left' },
  { name: 'commission', label: '手续费', field: 'commission', sortable: true, align: 'left' },
  {
    name: 'client_order_id',
    label: '周期',
    field: 'client_order_id',
    sortable: true,
    align: 'left',
  },
];

// 默认显示的列
const defaultVisibleColumns = [
  'kline_time',
  'time',
  'pair',
  'side',
  'order_amount',
  'executed',
  'average_price',
  'trading_total',
  'profit',
];

// 使用表格列管理组合式函数
const columnManager = useTableColumns(
  originalColumns,
  defaultVisibleColumns,
  'filled-orders-columns',
);
const { allColumns, filteredColumns, isColumnVisible, isColumnRequired, toggleColumn, moveColumnUp, moveColumnDown, resetColumns } = columnManager;

// 工具函数
const extractErrorMessage = (error: unknown): string => {
  if (error instanceof Error) {
    return error.message;
  }
  if (typeof error === 'object' && error !== null && 'message' in error) {
    const message = (error as { message: unknown }).message;
    return typeof message === 'string' ? message : JSON.stringify(message);
  }
  return '未知错误';
};

const getValueColor = (value: unknown, numValue?: number) => {
  // 如果值为空/null/undefined,显示深灰色
  if (value === null || value === undefined || value === '') {
    return 'text-grey-8';
  }

  // 如果提供了数值,优先使用数值判断
  const numericCandidate =
    numValue !== undefined
      ? numValue
      : typeof value === 'string'
        ? Number.parseFloat(value)
        : typeof value === 'number'
          ? value
          : Number.NaN;

  if (Number.isNaN(numericCandidate)) {
    return 'text-grey-8'; // 无效值显示深灰色
  }

  if (numericCandidate === 0) {
    return 'text-grey-8'; // 零值显示深灰色
  }

  return ''; // 正常值不设置特殊颜色,使用默认样式
};

const notifyError = (message: string, error: unknown) => {
  const caption = extractErrorMessage(error);
  $q.notify({
    type: 'negative',
    message,
    caption,
    position: 'top',
  });
};

const fetchOrders = async (
  overrides: Partial<FilledOrdersQuery> = {},
  forceRefresh = false,
) => {
  await fetchOrdersTask(overrides, forceRefresh);
};

const loadOrders = async (forceRefresh = false) => {
  await fetchOrders({}, forceRefresh);
};

const loadStats = async (forceRefresh = false) => {
  await fetchStatsTask(forceRefresh);
};

// 获取交易对列表
const fetchSymbols = async () => {
  try {
    const response = await api.get<{ success: boolean; data: string[] }>(
      '/api/v1/filled-orders/symbols',
    );
    if (response.data?.success && Array.isArray(response.data.data)) {
      symbolOptions.value = response.data.data.map((symbol) => ({
        label: symbol,
        value: symbol,
      }));
    }
  } catch (error) {
    console.error('❌ 获取交易对列表失败:', error);
  }
};

// 筛选器事件处理
const updateFilters = (newFilters: Partial<typeof filters>) => {
  Object.assign(filters, newFilters);
};

const buildFilters = (): Partial<FilledOrdersQuery> => {
  const query: Partial<FilledOrdersQuery> = {
    page: 1,
  };

  if (filters.symbol) {
    query.symbol = filters.symbol;
  }

  if (filters.side) {
    query.side = filters.side;
  }

  return query;
};

const handleFilterApply = async () => {
  await fetchOrders(buildFilters(), true);
};

const handleFilterReset = async () => {
  filters.symbol = '';
  filters.side = '';
  await fetchOrders({ page: 1, symbol: undefined, side: undefined }, true);
};

// 表格事件处理
interface TableRequestPayload {
  pagination: {
    page: number;
    rowsPerPage: number;
    sortBy?: string | null;
    descending?: boolean | null;
  };
}

const onRequest = (props: TableRequestPayload) => {
  const { page, rowsPerPage, sortBy, descending } = props.pagination;
  const query: Partial<FilledOrdersQuery> = {
    page,
    rowsPerPage,
    sortBy: sortBy || pagination.value.sortBy,
    descending: descending ?? pagination.value.descending,
    symbol: filters.symbol || undefined,
    side: filters.side || undefined,
  };

  void fetchOrders(query, true);
};

// 组件挂载
onMounted(() => {
  void loadOrders();
  void loadStats();
  void fetchSymbols();
});
</script>

<style lang="scss" scoped>
@import 'src/css/quasar.variables';

.card-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--q-primary);
}

.card-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.orders-card {
  :deep(.q-table) {
    th {
      background-color: $white-alpha-03;
      font-weight: 600;
    }
  }
}
</style>
