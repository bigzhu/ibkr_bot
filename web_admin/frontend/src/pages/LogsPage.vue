<template>
  <q-page class="modern-page">
    <!-- 页面头部 -->
    <PageHeader
      title="交易日志"
      subtitle="监控交易活动和系统运行状态"
      icon="description"
      class="gt-xs"
    />

    <!-- 最低 SELL 条件表格 -->
    <DataTableCard class="min-sell-card q-mb-sm" title="最低 SELL 条件" icon="trending_up">
      <template #actions>
        <ModernButton
          variant="ghost"
          icon="refresh"
          size="sm"
          @click="() => loadMinSellConditions(true)"
        >
          刷新数据
        </ModernButton>
      </template>

      <ModernTable
        :rows="minSellRows"
        :columns="minSellColumns"
        row-key="pair"
        :hide-pagination="true"
        :dense="true"
        class="min-sell-table"
      >
        <!-- 交易对列 -->
        <template v-slot:body-cell-pair="props">
          <q-td :props="props">
            <TradingPairIcon
              :symbol="props.value"
              :show-text="true"
              icon-size="18px"
              text-class="text-weight-medium"
            />
          </q-td>
        </template>

        <!-- 成本列 -->
        <template v-slot:body-cell-cost="props">
          <q-td :props="props">
            <div class="text-weight-medium">
              <CurrencySymbolDisplay
                v-if="Number(props.row.holding_qty) > 0 && Number(props.row.average_price) > 0"
                :symbol="props.row.pair"
                :value="props.value"
                currency-type="quote"
              />
              <span v-else class="text-grey-6">-</span>
            </div>
          </q-td>
        </template>

        <!-- 市价列 -->
        <template v-slot:body-cell-market_price="props">
          <q-td :props="props">
            <div class="market-price-cell">
              <PriceDisplay :value="props.value" :show-dollar="true" />
              <q-spinner
                size="14px"
                color="primary"
                class="q-ml-xs"
                v-if="isMarketPriceLoading(props.row.pair)"
              />
            </div>
          </q-td>
        </template>

        <!-- 持币盈亏列 -->
        <template v-slot:body-cell-holding_profit_loss="props">
          <q-td :props="props">
            <div class="text-weight-medium" :class="getProfitLossClass(props.value)">
              <CurrencySymbolDisplay
                v-if="parseNumeric(props.value) !== null"
                :symbol="props.row.pair"
                :value="props.value"
                currency-type="quote"
              />
              <span v-else class="text-grey-6">-</span>
            </div>
          </q-td>
        </template>

        <!-- 买价列 -->
        <template v-slot:body-cell-average_price="props">
          <q-td :props="props">
            <div>
              <PriceDisplay :value="props.value" :show-dollar="true" />
            </div>
          </q-td>
        </template>

        <!-- 最低买价列 -->
        <template v-slot:body-cell-min_buy_price="props">
          <q-td :props="props">
            <div class="min-buy-price-cell">
              <PriceDisplay :value="props.value" :show-dollar="true" />
              <span
                v-if="getMinBuyPriceChange(props.row) !== null"
                class="price-change-badge"
                :class="getMinBuyPriceChangeClass(props.row)"
              >
                ({{ getMinBuyPriceChange(props.row) }}%)
              </span>
            </div>
          </q-td>
        </template>

        <!-- 持币数量列 -->
        <template v-slot:body-cell-holding_qty="props">
          <q-td :props="props">
            <CurrencySymbolDisplay
              :symbol="props.row.pair"
              :value="props.value"
              currency-type="base"
            />
          </q-td>
        </template>

        <!-- 计价余额列 -->
        <template v-slot:body-cell-quote_balance="props">
          <q-td :props="props">
            <div class="text-weight-medium" :class="Number(props.value) === 0 ? 'text-grey-8' : ''">
              <CurrencySymbolDisplay
                v-if="Number(props.value) > 0"
                :symbol="props.row.pair"
                :value="props.value"
                currency-type="quote"
              />
              <span v-else>-</span>
            </div>
          </q-td>
        </template>

        <template v-slot:no-data>
          <EmptyStateDisplay
            type="orders"
            title="暂无未撮合的BUY订单"
            description="当前没有需要SELL的BUY订单余额"
            size="sm"
          />
        </template>
      </ModernTable>
    </DataTableCard>

    <!-- 筛选器 -->
    <FilterDrawer
      :filters="filters"
      :field-configs="filterConfigs"
      auto-apply
      @update:filters="filters = $event"
      @apply="handleFilterApply"
      @reset="handleFilterReset"
    >
      <!-- 自定义交易对显示 -->
      <template #field-symbols="{ option }">
        <TradingPairIcon
          :symbol="option"
          :show-text="true"
          icon-size="18px"
          text-class="text-weight-regular"
          container-class="symbol-checkbox-label"
        />
      </template>
    </FilterDrawer>

    <!-- 日志明细表格 -->
    <DataTableCard class="logs-card" icon="table_view">
      <template #title>
        <div class="card-title">
          日志明细
          <span class="text-caption text-grey-6 q-ml-sm">{{ currentTime }}</span>
        </div>
      </template>
      <template #actions>
        <TableHeaderActions
          show-websocket-status
          show-refresh
          :ws-state="wsState"
          :loading="isLoading"
          @websocket-reconnect="manualReconnect"
          @refresh="loadLogs"
        >
          <template #column-control>
            <TableColumnControl
              :all-columns="allColumns"
              :is-column-visible="isColumnVisible"
              :is-column-required="isColumnRequired"
              :toggle-column="toggleColumn"
              :move-column-up="moveColumnUp"
              :move-column-down="moveColumnDown"
              :reset-columns="resetColumns"
              show-label
            />
          </template>
        </TableHeaderActions>
      </template>

      <!-- WebSocket 错误提示 -->
      <q-banner v-if="wsState.error" class="bg-negative text-white q-mb-md" rounded>
        <template v-slot:avatar>
          <q-icon name="warning" color="white" />
        </template>
        <div>
          <div class="text-weight-medium">WebSocket 连接错误</div>
          <div class="text-caption">{{ wsState.error }}</div>
        </div>
        <template v-slot:action>
          <q-btn flat color="white" label="重试" @click="manualReconnect" />
          <q-btn flat color="white" icon="close" @click="wsState.error = null" />
        </template>
      </q-banner>

      <ModernTable
        :rows="logs"
        :columns="filteredColumns"
        row-key="id"
        :loading="isLoading"
        v-model:pagination="pagination"
        @request="onRequest"
        :server-side="true"
        :dense="true"
        :rows-per-page-options="[22, 44, 88, 176]"
        class="logs-table"
        table-class="logs-detail-table"
      >
            <!-- 自定义整行 -->
            <template v-slot:body="props">
              <q-tr :props="props" :class="getRowClass(props.row)">
                <q-td
                  v-for="col in props.cols"
                  :key="col.name"
                  :props="props"
                  :class="{ 'error-info-cell': col.name === 'error_info' }"
                >
                  <template v-if="col.name === 'id'">
                    <div class="text-weight-medium text-primary">
                      {{ col.value }}
                    </div>
                  </template>

                  <template v-else-if="col.name === 'kline_time'">
                    <div class="text-weight-medium">
                      {{ col.value ? formatKlineTime(col.value) : '-' }}
                    </div>
                  </template>

                  <template v-else-if="col.name === 'run_time'">
                    <div class="text-weight-medium">
                      {{ col.value ? formatRunTime(col.value) : '-' }}
                    </div>
                  </template>

                  <template v-else-if="col.name === 'symbol'">
                    <TradingPairIcon
                      :symbol="col.value"
                      :show-text="true"
                      icon-size="18px"
                      text-class="text-weight-medium"
                    />
                  </template>

                  <template v-else-if="col.name === 'timeframe'">
                    <TimeframeChip :timeframe="col.value" :order-side="props.row.order_side" />
                  </template>

                  <template v-else-if="col.name === 'signal_value'">
                    <SignalProgressBar
                      :signal-value="col.value"
                      :order-side="props.row.order_side"
                    />
                  </template>

                  <template v-else-if="col.name === 'order_id'">
                    <span v-if="col.value" class="text-weight-medium">{{ col.value }}</span>
                    <span v-else class="text-grey-8">-</span>
                  </template>

                  <template v-else-if="col.name === 'order_side'">
                    <OrderSideChip :side="props.row.order_side" />
                  </template>

                  <template v-else-if="col.name === 'order_price'">
                    <PriceDisplay :value="col.value" :show-dollar="true" />
                  </template>

                  <template v-else-if="col.name === 'order_qty'">
                    <CurrencyAmountDisplay
                      :value="col.value"
                      :symbol="props.row.symbol"
                      currency-type="base"
                      format-type="quantity"
                    />
                  </template>

                  <template v-else-if="col.name === 'profit_lock_qty'">
                    <CurrencyAmountDisplay
                      :value="col.value"
                      :symbol="props.row.symbol"
                      currency-type="base"
                      format-type="quantity"
                    />
                  </template>

                  <template v-else-if="col.name === 'trade_value'">
                    <div
                      class="text-weight-medium"
                      :class="[
                        getTradeValueColor(props.row),
                        { 'opacity-muted': props.row.trade_value_is_neutral },
                      ]"
                    >
                      {{ props.row.trade_value_display ?? '-' }}
                    </div>
                  </template>

                  <template v-else-if="col.name === 'from_price'">
                    <PriceDisplay :value="col.value" :show-dollar="true" />
                  </template>

                  <template v-else-if="col.name === 'user_balance'">
                    <CurrencyAmountDisplay
                      :value="col.value"
                      :symbol="props.row.symbol"
                      :order-side="props.row.order_side"
                      currency-type="auto"
                      format-type="currency"
                    />
                  </template>

                  <template v-else-if="col.name === 'demark_percentage_coefficient'">
                    <div class="text-weight-medium" :class="getValueColor(col.value)">
                      {{ col.value ? formatQuantity(col.value) : '-' }}
                    </div>
                  </template>

                  <template v-else-if="col.name === 'price_change_percentage'">
                    <PercentageChangeDisplay
                      :value="getAdjustedPriceChange(props.row.order_side, col.value)"
                    />
                  </template>

                  <template v-else-if="col.name === 'error_info'">
                    <div v-if="col.value" class="text-caption error-text">
                      {{ col.value }}
                    </div>
                    <span v-else class="text-grey-8 opacity-muted">-</span>
                  </template>

                  <!-- 默认显示 -->
                  <template v-else>
                    {{ col.value }}
                  </template>
                </q-td>
              </q-tr>
            </template>
      </ModernTable>
    </DataTableCard>

    <!-- 错误详情对话框 -->
  </q-page>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onActivated, onDeactivated, onMounted, onUnmounted, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { useQuasar } from 'quasar';
import { useTableColumns } from 'src/composables/useTableColumns';
import { useLoading } from 'src/composables/useLoading';
import TableColumnControl from 'src/components/TableColumnControl.vue';
import { formatQuantity } from 'src/utils/formatters';
import { formatDateTime as formatDateTimeUtil } from 'src/utils/datetime';
import DataTableCard from 'src/components/DataTableCard.vue';
import ModernButton from 'src/components/ModernButton.vue';
import ModernTable from 'src/components/ModernTable.vue';
import PageHeader from 'src/components/PageHeader.vue';
import TableHeaderActions from 'src/components/TableHeaderActions.vue';
import TradingPairIcon from 'src/components/TradingPairIcon.vue';
import FilterDrawer from 'src/components/FilterDrawer.vue';
import TimeframeChip from 'src/components/TimeframeChip.vue';
import CurrencyAmountDisplay from 'src/components/CurrencyAmountDisplay.vue';
import SignalProgressBar from 'src/components/SignalProgressBar.vue';

import PercentageChangeDisplay from 'src/components/PercentageChangeDisplay.vue';
import OrderSideChip from 'src/components/OrderSideChip.vue';
import PriceDisplay from 'src/components/PriceDisplay.vue';
import EmptyStateDisplay from 'src/components/EmptyStateDisplay.vue';
import CurrencySymbolDisplay from 'src/components/CurrencySymbolDisplay.vue';
import { useLogsStore } from 'src/stores/logs-store';
import type { TradingLog } from 'src/stores/logs-store';
import { useMinSellConditionsStore } from 'src/stores/min-sell-conditions-store';
import { useMarketPriceStore } from 'src/stores/market-price-store';
import { apiService } from 'src/services';

const $q = useQuasar();
const logsStore = useLogsStore();
const minSellConditionsStore = useMinSellConditionsStore();
const { conditions: minSellConditions } = storeToRefs(minSellConditionsStore);
const marketPriceStore = useMarketPriceStore();
const { prices: marketPrices, loading: marketPriceLoading } = storeToRefs(marketPriceStore);

// 使用加载管理
const { isLoading } = useLoading();

// WebSocket 连接状态
const wsState = reactive({
  connected: false,
  reconnecting: false,
  error: null as string | null,
  ws: null as WebSocket | null,
});
const isPageActive = ref(false);
const hasInitialLoad = ref(false);

let ignoreTableRequestsUntil = 0;

const scheduleTableRequestSkip = () => {
  ignoreTableRequestsUntil = Date.now() + 400;
};


// 最低SELL条件相关
const MARKET_PRICE_TTL_MS = 60 * 1000;
let lastMarketPricePairsKey = '';

const parseNumeric = (value: unknown): number | null => {
  if (value === null || value === undefined || value === '') {
    return null;
  }
  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : null;
  }
  const num = Number(value);
  return Number.isFinite(num) ? num : null;
};

const minSellRows = computed(() =>
  minSellConditions.value.map((condition) => {
    const pairKey =
      typeof condition.pair === 'string' ? condition.pair.trim().toUpperCase() : condition.pair;
    const cachedPrice =
      typeof pairKey === 'string' && marketPrices.value[pairKey]
        ? marketPrices.value[pairKey].value
        : undefined;
    const marketPrice =
      cachedPrice ??
      (typeof condition.market_price === 'string'
        ? condition.market_price
        : condition.market_price != null
          ? String(condition.market_price)
          : null);
    const holdingQtyValue =
      parseNumeric(condition.holding_qty) ?? parseNumeric(condition.quantity) ?? null;
    const marketPriceValue = parseNumeric(marketPrice);
    const costValue = parseNumeric(condition.cost);
    const marketValue =
      marketPriceValue !== null && holdingQtyValue !== null
        ? marketPriceValue * holdingQtyValue
        : null;
    const holdingProfitLoss =
      marketValue !== null && costValue !== null ? marketValue - costValue : null;

    return {
      ...condition,
      market_price: marketPrice,
      holding_profit_loss: holdingProfitLoss,
    };
  }),
);

// 最低SELL条件表格列定义
const toNumber = (value: unknown) => {
  const numeric = Number(value);
  return Number.isFinite(numeric) ? numeric : 0;
};

const numericSort = (a: unknown, b: unknown) => toNumber(a) - toNumber(b);

const getProfitLossClass = (value: unknown) => {
  const numeric = parseNumeric(value);
  if (numeric === null) {
    return 'text-grey-8';
  }
  if (numeric >= 0) {
    return 'text-positive';
  }
  return 'text-negative';
};

// 计算最低买价与市价的价差百分比
const getMinBuyPriceChange = (row: Record<string, unknown>): string | null => {
  const minBuyPrice = parseNumeric(row.min_buy_price);
  const marketPrice = parseNumeric(row.market_price);

  if (minBuyPrice === null || minBuyPrice === 0 || marketPrice === null || marketPrice === 0) {
    return null;
  }

  const changePercentage = ((marketPrice - minBuyPrice) / minBuyPrice) * 100;
  const sign = changePercentage >= 0 ? '+' : '';
  return `${sign}${changePercentage.toFixed(2)}`;
};

// 获取价差百分比的颜色类
const getMinBuyPriceChangeClass = (row: Record<string, unknown>): string => {
  const minBuyPrice = parseNumeric(row.min_buy_price);
  const marketPrice = parseNumeric(row.market_price);

  if (minBuyPrice === null || minBuyPrice === 0 || marketPrice === null || marketPrice === 0) {
    return '';
  }

  if (marketPrice > minBuyPrice) {
    return 'positive-change';
  } else if (marketPrice < minBuyPrice) {
    return 'negative-change';
  }
  return '';
};

const minSellColumns = [
  {
    name: 'timeframe',
    label: '周期',
    field: 'timeframe',
    align: 'left',
    sortable: true,
  },
  {
    name: 'pair',
    label: '交易对',
    field: 'pair',
    align: 'left',
    sortable: true,
    style: 'min-width: 100px; width: auto; white-space: nowrap;',
    headerStyle: 'min-width: 100px; width: auto; white-space: nowrap;',
  },
  {
    name: 'cost',
    label: '持币成本',
    field: 'cost',
    align: 'left',
    sortable: true,
    sort: numericSort,
  },
  {
    name: 'holding_qty',
    label: '持币数量',
    field: 'holding_qty',
    align: 'left',
    sortable: true,
    sort: numericSort,
  },
  {
    name: 'average_price',
    label: '持仓均价',
    field: 'average_price',
    align: 'left',
    sortable: true,
    sort: numericSort,
  },
  {
    name: 'min_buy_price',
    label: '最低买价',
    field: 'min_buy_price',
    align: 'left',
    sortable: true,
    sort: numericSort,
  },
  {
    name: 'market_price',
    label: '市价',
    field: 'market_price',
    align: 'left',
    classes: 'text-left',
    headerClasses: 'text-left',
    sortable: true,
    sort: numericSort,
  },
  {
    name: 'holding_profit_loss',
    label: '持币盈亏',
    field: 'holding_profit_loss',
    align: 'left',
    sortable: true,
    sort: numericSort,
  },
  {
    name: 'quote_balance',
    label: '计价余额',
    field: 'quote_balance',
    align: 'left',
    classes: 'text-left',
    headerClasses: 'text-left',
    sortable: true,
    sort: numericSort,
  },
];

const normalisePairKey = (pair: string) => pair.trim().toUpperCase();

const setMarketPriceLoading = (pair: string, value: boolean) => {
  const key = normalisePairKey(pair);
  if (!key) {
    return;
  }
  marketPriceStore.setLoading(key, value);
};

const updateMarketPrice = (pair: string, price: string | null) => {
  const key = normalisePairKey(pair);
  if (!key) {
    return;
  }
  marketPriceStore.setPrice(key, price ?? '0');
};

const isMarketPriceLoading = (pair: string) => marketPriceStore.isLoading(pair);

const fetchPairMarketPrice = async (pair: string): Promise<void> => {
  const symbol = normalisePairKey(pair);
  if (!symbol) {
    return;
  }

  setMarketPriceLoading(symbol, true);
  try {
    const response = await apiService.binanceFilledOrders.getMarketPrice(symbol);
    if (response.success && typeof response.market_price === 'string') {
      updateMarketPrice(symbol, response.market_price);
    } else if (response.success && response.market_price === null) {
      updateMarketPrice(symbol, null);
    } else {
      console.warn('获取市价失败', symbol, response.message);
    }
  } catch (error) {
    console.error('获取市价失败:', symbol, error);
  } finally {
    setMarketPriceLoading(symbol, false);
  }
};

const refreshMarketPrices = (force = false): void => {
  const pairs = minSellConditions.value
    .map((item) => (typeof item.pair === 'string' ? normalisePairKey(item.pair) : ''))
    .filter((pair): pair is string => pair.length > 0);
  const uniquePairs = Array.from(new Set(pairs));
  const key = uniquePairs.slice().sort().join('|');

  if (!force && key === lastMarketPricePairsKey) {
    const allFresh = uniquePairs.every((pair) =>
      marketPriceStore.isFresh(pair, MARKET_PRICE_TTL_MS),
    );
    if (allFresh) {
      return;
    }
  }

  if (uniquePairs.length === 0) {
    marketPriceLoading.value = {};
    lastMarketPricePairsKey = '';
    return;
  }

  const prevLoading = marketPriceLoading.value;
  marketPriceLoading.value = uniquePairs.reduce<Record<string, boolean>>((acc, pair) => {
    acc[pair] = prevLoading[pair] ?? false;
    return acc;
  }, {});

  lastMarketPricePairsKey = key;

  for (const pair of uniquePairs) {
    if (!force && marketPriceStore.isFresh(pair, MARKET_PRICE_TTL_MS)) {
      continue;
    }
    void fetchPairMarketPrice(pair);
  }
};

const { tradingLogs: logs } = storeToRefs(logsStore);
const symbolOptions = ref<string[]>([]);
const allSymbols = ref<string[]>([]); // 保存所有交易对,用于筛选

interface LogFilters {
  symbols: string[];
  timeframes: string[];
  hasOrderId: boolean;
  orderSide: string;
}

// 筛选器
const filters = ref<LogFilters>({
  symbols: [],
  timeframes: [],
  hasOrderId: false,
  orderSide: '',
});

// 选项配置
const timeframeOptions = [
  { label: '1分钟', value: '1m' },
  { label: '3分钟', value: '3m' },
  { label: '5分钟', value: '5m' },
  { label: '15分钟', value: '15m' },
  { label: '30分钟', value: '30m' },
  { label: '1小时', value: '1h' },
  { label: '4小时', value: '4h' },
];
const orderSideOptions = [
  { label: 'BUY', value: 'BUY' },
  { label: 'SELL', value: 'SELL' },
];

interface TradingLogApi {
  id: number;
  created_at: string;
  symbol: string;
  kline_timeframe?: string | null;
  demark?: number | string | null;
  side?: string | null;
  price?: number | string | null;
  qty?: number | string | null;
  profit_lock_qty?: number | string | null;
  order_id?: string | null;
  error?: string | null;
  kline_time?: string | null;
  run_time?: string | null;
  demark_percentage_coefficient?: number | string | null;
  from_price?: number | string | null;
  user_balance?: number | string | null;
  price_change_percentage?: number | string | null;
  action_type?: string | null;
  result?: string | null;
  status?: string | null;
}

interface TableRequestPayload {
  pagination: {
    page: number;
    rowsPerPage: number;
    sortBy?: string | null;
    descending?: boolean | null;
  };
}

interface TradingLogCreatedMessage {
  type: 'trading_log_created';
  data: {
    id: number;
    log: TradingLogApi;
  };
}

interface TradingLogUpdatedMessage {
  type: 'trading_log_updated';
  data: {
    id: number;
    updated_fields: Record<string, unknown>;
  };
}

interface GenericMessage {
  type: 'connection_established' | 'filters_updated' | 'pong';
}

interface ErrorMessage {
  type: 'error';
  data: {
    message: string;
  };
}

type WebSocketMessage = TradingLogCreatedMessage | TradingLogUpdatedMessage | GenericMessage | ErrorMessage;

// 筛选器配置
const filterConfigs = ref([
  {
    key: 'hasOrderId',
    type: 'checkbox',
    label: '挂单状态',
    props: {
      checkboxLabel: '仅显示已挂单记录',
    },
  },
  {
    key: 'orderSide',
    type: 'radio-group',
    label: '挂单方向',
    options: orderSideOptions,
  },
  {
    key: 'symbols',
    type: 'checkbox-group',
    label: '交易对',
    options: computed(() => allSymbols.value || []),
  },
  {
    key: 'timeframes',
    type: 'checkbox-group',
    label: '时间周期',
    options: timeframeOptions,
  },
]);

// 当前时间显示
const currentTime = ref('');
let timeInterval: ReturnType<typeof setInterval> | null = null;
const updateCurrentTime = () => {
  currentTime.value = formatDateTimeUtil(new Date(), {
    includeYear: true,
    includeSeconds: true,
  });
};

// 分页配置
const pagination = ref({
  sortBy: null as string | null,
  descending: true,
  page: 1,
  rowsPerPage: 44,
  rowsNumber: 0,
});

if (logsStore.tradingLogs.length > 0) {
  pagination.value.rowsNumber = Math.max(
    pagination.value.rowsNumber,
    logsStore.tradingLogs.length,
  );
}

// 原始列定义(用于重置)
const originalColumns = [
  {
    name: 'id',
    label: 'ID',
    field: 'id',
    align: 'center',
    sortable: true,
    style: 'min-width: 80px; width: auto;',
  },
  {
    name: 'run_time',
    label: '运行',
    field: 'run_time',
    align: 'center',
    sortable: false,
    required: true, // 必需列
  },
  {
    name: 'kline_time',
    label: 'K线时间',
    field: 'kline_time',
    align: 'center',
    sortable: true,
  },
  {
    name: 'symbol',
    label: '交易对',
    field: 'symbol',
    align: 'center',
    sortable: true,
    style: 'min-width: 100px; width: auto; white-space: nowrap;',
    headerStyle: 'min-width: 100px; width: auto; white-space: nowrap;',
  },
  {
    name: 'timeframe',
    label: '周期',
    field: 'timeframe',
    align: 'center',
    sortable: true,
  },
  {
    name: 'signal_value',
    label: '信号',
    field: 'signal_value',
    align: 'center',
    sortable: true,
  },
  {
    name: 'order_id',
    label: 'order_id',
    field: 'order_id',
    align: 'center',
    sortable: true,
  },
  {
    name: 'order_side',
    label: '方向',
    field: 'side',
    align: 'center',
    sortable: true,
  },
  {
    name: 'order_price',
    label: '挂单价格',
    field: 'order_price',
    align: 'center',
    sortable: true,
  },
  {
    name: 'order_qty',
    label: '挂单数量',
    field: 'order_qty',
    align: 'center',
    sortable: true,
  },
  {
    name: 'profit_lock_qty',
    label: '有利量',
    field: 'profit_lock_qty',
    align: 'center',
    sortable: true,
  },
  {
    name: 'trade_value',
    label: '价值',
    field: 'trade_value',
    align: 'center',
    sortable: false,
  },
  {
    name: 'from_price',
    label: '基准价格',
    field: 'from_price',
    align: 'center',
    sortable: true,
  },
  {
    name: 'user_balance',
    label: '余额',
    field: 'user_balance',
    align: 'center',
    sortable: true,
  },
  {
    name: 'demark_percentage_coefficient',
    label: '放大系数',
    field: 'demark_percentage_coefficient',
    align: 'center',
    sortable: true,
  },
  {
    name: 'price_change_percentage',
    label: '价格变化(%)',
    field: 'price_change_percentage',
    align: 'center',
    sortable: true,
  },
  {
    name: 'error_info',
    label: '错误',
    field: 'error_message',
    align: 'center',
    sortable: true,
  },
];

// 默认显示的列(按需求隐藏: ID, 周期, order_id, 放大系数)
const defaultVisibleColumns = [
  'run_time',
  'kline_time',
  'symbol',
  'signal_value',
  'order_side',
  'order_price',
  'order_qty',
  'profit_lock_qty',
  'trade_value',
  'from_price',
  'user_balance',
  'price_change_percentage',
  'error_info',
];

// 使用表格列管理组合式函数
// 升级存储key以应用新的默认列配置
const columnManager = useTableColumns(
  originalColumns,
  defaultVisibleColumns,
  'logs-table-columns-v2',
);

const {
  allColumns,
  filteredColumns,
  toggleColumn,
  moveColumnUp,
  moveColumnDown,
  resetColumns,
  isColumnVisible,
  isColumnRequired,
} = columnManager;

// 筛选器事件处理
const handleFilterApply = async () => {
  await searchLogs();
};

const handleFilterReset = async () => {
  await searchLogs();
};

// 获取表格行CSS类 - 使用 Quasar 原生颜色类为有order_id的行添加高亮效果,适配 dark 模式
const getRowClass = (row: TradingLog) => {
  // 检查order_id是否存在且不为空
  if (!row.order_id || row.order_id === '' || row.order_id === null) {
    return '';
  }

  // 根据订单类型返回不同的高亮样式类
  if (row.order_side === 'BUY') {
    return 'order-highlight-buy'; // 自定义绿色高亮
  } else if (row.order_side === 'SELL') {
    return 'order-highlight-sell'; // 自定义红色高亮,黑色带一点红
  }

  // 默认高亮(兼容没有明确方向的情况)
  return 'order-highlight-default'; // 自定义默认高亮
};

// 根据方向调整价格变化显示, BUY 时强制为负值
const getAdjustedPriceChange = (
  orderSide: string | null | undefined,
  rawValue: unknown,
): number | string | null | undefined => {
  if (rawValue === null || rawValue === undefined) {
    return rawValue;
  }

  if (rawValue === '') {
    return '';
  }

  const numericValue = typeof rawValue === 'number' ? rawValue : Number(rawValue);
  if (!Number.isFinite(numericValue)) {
    return typeof rawValue === 'string' ? rawValue : numericValue;
  }

  if (orderSide && orderSide.toUpperCase() === 'BUY') {
    return numericValue === 0 ? 0 : -Math.abs(numericValue);
  }

  return numericValue;
};

// 获取数值的统一颜色样式
const getValueColor = (value: unknown, numValue?: number) => {
  // 如果值为空/null/undefined,显示深灰色
  if (value === null || value === undefined || value === '') {
    return 'text-grey-8';
  }

  // 如果提供了数值,优先使用数值判断
  const resolvedNumber =
    numValue !== undefined
      ? numValue
      : typeof value === 'string'
        ? Number.parseFloat(value)
        : typeof value === 'number'
          ? value
          : null;

  if (resolvedNumber === null || Number.isNaN(resolvedNumber)) {
    return 'text-grey-8'; // 无效值显示深灰色
  }

  if (resolvedNumber === 0) {
    return 'text-grey-8'; // 零值显示深灰色
  }

  return ''; // 正常值不设置特殊颜色,使用默认样式
};

// 获取交易价值的颜色样式
const getTradeValueColor = (row: TradingLog) => {
  return row.trade_value_is_neutral ? 'text-grey-8' : '';
};


// 格式化运行时间 - 显示 MM/DD HH:mm
const formatRunTime = (timestamp: string | number) =>
  formatDateTimeUtil(timestamp as string | number | Date | null | undefined, {
    includeYear: false,
    includeSeconds: false,
    fallback: '-',
  });

// 格式化K线时间 - 显示与成交订单一致的日期时间
const formatKlineTime = (timestamp: string | number) =>
  formatDateTimeUtil(timestamp as string | number | Date | null | undefined, {
    includeYear: false,
    includeSeconds: false,
    assumeUtc: true,
    fallback: '-',
  });

// 检查日志是否符合当前筛选条件
const shouldIncludeLog = (log: TradingLog) => {
  const selectedSymbols = (filters.value.symbols || []).map((item) => item.toUpperCase());
  const selectedTimeframes = (filters.value.timeframes || []).map((item) => item.toLowerCase());
  const selectedOrderSide = filters.value.orderSide ? filters.value.orderSide.toUpperCase() : '';

  const logSymbol = (log.symbol || '').toUpperCase();
  const logTimeframe = (log.timeframe || '').toLowerCase();
  const logOrderSide = (log.order_side || '').toUpperCase();

  // 检查交易对筛选
  if (selectedSymbols.length > 0 && !selectedSymbols.includes(logSymbol)) {
    return false;
  }

  // 检查时间周期筛选
  if (selectedTimeframes.length > 0 && !selectedTimeframes.includes(logTimeframe)) {
    return false;
  }

  // 检查order_id筛选条件
  if (filters.value.hasOrderId) {
    const hasOrderId =
      log.order_id && log.order_id !== '' && log.order_id !== null && log.order_id !== undefined;
    if (!hasOrderId) {
      return false; // 勾选了"有order_id"但记录没有order_id
    }
  }

  // 检查挂单方向筛选
  if (selectedOrderSide && logOrderSide !== selectedOrderSide) {
    return false;
  }

  return true; // 所有条件都通过
};

const mapApiLogToTradingLog = (log: TradingLogApi): TradingLog => ({
  id: log.id,
  symbol: (log.symbol || '').toUpperCase(),
  action_type: log.action_type || log.side || 'UNKNOWN',
  result: log.result || log.status || 'unknown',
  created_at: log.created_at,
  timeframe: typeof log.kline_timeframe === 'string' ? log.kline_timeframe.toLowerCase() : null,
  signal_value: log.demark ?? null,
  order_side: typeof log.side === 'string' ? log.side.toUpperCase() : null,
  order_price: log.price ?? null,
  order_qty: log.qty ?? null,
  profit_lock_qty: log.profit_lock_qty ?? null,
  order_id: log.order_id ?? null,
  error_message: log.error ?? null,
  kline_time: log.kline_time ?? null,
  run_time: log.run_time ?? null,
  demark_percentage_coefficient: log.demark_percentage_coefficient ?? null,
  from_price: log.from_price ?? null,
  user_balance: log.user_balance ?? null,
  price_change_percentage: log.price_change_percentage ?? null,
});

// 加载日志数据
const loadLogs = async (): Promise<void> => {
  isLoading.value = true;
  try {
    const params: Record<string, string | number | boolean> = {
      page: pagination.value.page,
      limit: pagination.value.rowsPerPage,
      _t: Date.now(),
    };

    if (pagination.value.sortBy) {
      params.sort_by = pagination.value.sortBy;
      params.sort_desc = pagination.value.descending ? 'true' : 'false';
    }

    if (filters.value.symbols?.length) {
      params.symbol = filters.value.symbols.join(',');
    }
    if (filters.value.timeframes?.length) {
      params.timeframe = filters.value.timeframes.join(',');
    }
    if (filters.value.hasOrderId) {
      params.meets_conditions = 'true';
    }
    if (filters.value.orderSide) {
      params.order_side = filters.value.orderSide;
    }

    const result = await apiService.tradingLogs.list<TradingLogApi>(params);

    if (result.success) {
      const rawLogs = Array.isArray(result.data)
        ? result.data
        : Array.isArray(result.logs)
          ? result.logs
          : [];

      const transformedLogs = rawLogs.map(mapApiLogToTradingLog);
      logsStore.setTradingLogs(transformedLogs, pagination.value.rowsPerPage);

      const totalRecords = Number(result.total);
      if (Number.isFinite(totalRecords)) {
        pagination.value.rowsNumber = totalRecords;
      } else {
        pagination.value.rowsNumber = transformedLogs.length;
      }

      void Promise.allSettled([loadMinSellConditions(true)]);
    } else {
      const message = result.error || result.message || 'Failed to load logs';
      throw new Error(message);
    }
  } catch (error) {
    console.error('Failed to load logs:', error);
    const message = apiService.handleError(error);
    $q.notify({
      type: 'negative',
      message: '加载日志失败',
      caption: message,
    });
  } finally {
    isLoading.value = false;
  }
};

// WebSocket筛选更新防抖
let filtersDebounceTimer: ReturnType<typeof setTimeout> | null = null;

// 加载最低SELL条件数据
const loadMinSellConditions = async (forceRefresh = false) => {
  try {
    await minSellConditionsStore.fetchConditions(forceRefresh);
    refreshMarketPrices(true);
  } catch (error) {
    console.error('Failed to load min sell conditions:', error);
    $q.notify({
      type: 'negative',
      message: '加载最低SELL条件失败',
      caption: error instanceof Error ? error.message : '未知错误',
    });
  }
};

// 搜索日志
const searchLogs = async () => {
  // 应用筛选器重新加载数据
  await loadLogs();

  $q.notify({
    type: 'positive',
    message: '日志搜索完成',
  });
};

// 加载交易对选项
const loadSymbolOptions = async () => {
  try {
    const result = await apiService.tradingLogs.symbols();

    if (result.success && Array.isArray(result.data)) {
      allSymbols.value = result.data;
      symbolOptions.value = result.data;
    } else {
      throw new Error(result.error || result.message || 'Failed to load symbols');
    }
  } catch (error) {
    console.error('加载交易对选项失败:', error);
    // 失败时使用空数组,避免显示不存在的交易对
    allSymbols.value = [];
    symbolOptions.value = [];

    // 通知用户加载失败
    $q.notify({
      type: 'negative',
      message: '加载交易对选项失败',
      caption: apiService.handleError(error),
      timeout: 3000,
    });
  }
};

// 表格请求处理
const onRequest = (props: TableRequestPayload) => {
  const { page, rowsPerPage, sortBy, descending } = props.pagination;

  pagination.value.page = page;
  pagination.value.rowsPerPage = rowsPerPage;
  pagination.value.sortBy = sortBy;
  pagination.value.descending = descending;

  if (Date.now() < ignoreTableRequestsUntil) {
    return;
  }

  void loadLogs();
};

const hasActiveFilters = (candidate: LogFilters): boolean => {
  return Object.values(candidate).some((value) => {
    if (Array.isArray(value)) {
      return value.length > 0;
    }
    if (typeof value === 'boolean') {
      return value;
    }
    return value !== '';
  });
};

const sendFiltersToWebSocket = (nextFilters: LogFilters) => {
  if (!isPageActive.value) {
    return;
  }

  const socket = wsState.ws;
  if (!socket || socket.readyState !== WebSocket.OPEN) {
    return;
  }

  socket.send(
    JSON.stringify({
      type: 'set_filters',
      filters: nextFilters,
    }),
  );
};

const scheduleFilterUpdate = (delay = 300) => {
  if (!isPageActive.value) {
    return;
  }

  if (filtersDebounceTimer) {
    clearTimeout(filtersDebounceTimer);
  }

  filtersDebounceTimer = setTimeout(() => {
    filtersDebounceTimer = null;
    sendFiltersToWebSocket(filters.value);
  }, delay);
};

const flushFilterUpdate = () => {
  if (filtersDebounceTimer) {
    clearTimeout(filtersDebounceTimer);
    filtersDebounceTimer = null;
  }
  sendFiltersToWebSocket(filters.value);
};

// WebSocket 实时连接
let reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
let reconnectAttempts = 0;
const maxReconnectAttempts = 5;

const setupWebSocket = () => {
  if (!isPageActive.value) {
    return;
  }

  if (wsState.ws) {
    wsState.ws.close();
  }

  try {
    const ws = new WebSocket(
      `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/logs`,
    );
    wsState.ws = ws;
    wsState.reconnecting = false;
    wsState.error = null;

    ws.onopen = () => {
      wsState.connected = true;
      wsState.reconnecting = false;
      reconnectAttempts = 0;

      // 发送当前筛选条件
      if (hasActiveFilters(filters.value)) {
        flushFilterUpdate();
      }

      // 发送心跳
      const heartbeat = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'ping' }));
        } else {
          clearInterval(heartbeat);
        }
      }, 30000); // 30秒心跳
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WebSocketMessage;
        handleWebSocketMessage(data);
      } catch (error) {
        console.error('❌ 解析 WebSocket 消息失败:', error, 'Raw data:', event.data);
      }
    };

    ws.onclose = (event) => {
      wsState.connected = false;
      wsState.ws = null;

      // 如果不是主动关闭,尝试重连
      if (event.code !== 1000 && reconnectAttempts < maxReconnectAttempts) {
        attemptReconnect();
      }
    };

    ws.onerror = (error) => {
      console.error('❌ WebSocket 错误:', error);
      wsState.error = '连接错误';
      wsState.connected = false;
    };
  } catch (error) {
    console.error('❌ 创建 WebSocket 连接失败:', error);
    wsState.error = '连接失败';
    attemptReconnect();
  }
};

const attemptReconnect = () => {
  if (!isPageActive.value) {
    return;
  }

  if (reconnectAttempts >= maxReconnectAttempts) {
    wsState.error = '重连失败,请刷新页面';
    return;
  }

  wsState.reconnecting = true;
  reconnectAttempts++;

  const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000); // 指数退避,最大30秒

  reconnectTimeout = setTimeout(() => {
    setupWebSocket();
  }, delay);
};

const handleWebSocketMessage = (message: WebSocketMessage) => {
  switch (message.type) {
    case 'connection_established':
    case 'filters_updated':
    case 'pong':
      return;

    case 'trading_log_created': {
      const newLog = mapApiLogToTradingLog(message.data.log);
      if (message.data.id !== undefined) {
        newLog.id = message.data.id;
      }
      if (!newLog.created_at) {
        newLog.created_at = message.timestamp || new Date().toISOString();
      }

      if (shouldIncludeLog(newLog)) {
        scheduleTableRequestSkip();
        logsStore.prependTradingLog(newLog, pagination.value.rowsPerPage);
      }

      return;
    }

    case 'trading_log_updated': {
      const mappedFields: Partial<TradingLog> = {};
      for (const [key, value] of Object.entries(message.data.updated_fields)) {
        switch (key) {
          case 'kline_timeframe':
            mappedFields.timeframe = value as TradingLog['timeframe'];
            break;
          case 'demark':
            mappedFields.signal_value = value as TradingLog['signal_value'];
            break;
          case 'side':
            mappedFields.order_side = value as TradingLog['order_side'];
            mappedFields.action_type = value as TradingLog['action_type'];
            break;
          case 'price':
            mappedFields.order_price = value as TradingLog['order_price'];
            break;
          case 'qty':
            mappedFields.order_qty = value as TradingLog['order_qty'];
            break;
          case 'error':
            mappedFields.error_message = value as TradingLog['error_message'];
            break;
          default:
            (mappedFields as Record<string, unknown>)[key] = value;
        }
      }

      const updated = logsStore.updateTradingLogEntry(message.data.id, mappedFields);
      if (!updated) {
        console.warn('⚠️ 未找到待更新的日志 ID:', message.data.id);
      } else {
        scheduleTableRequestSkip();
      }

      return;
    }

    case 'error':
      console.error('❌ 服务端错误:', message.data.message);
      wsState.error = message.data.message;
      return;

    default:
      console.warn('⚠️ 未知消息类型:', (message as { type: string }).type);
  }
};

const closeWebSocket = () => {
  if (reconnectTimeout) {
    clearTimeout(reconnectTimeout);
    reconnectTimeout = null;
  }

  if (wsState.ws) {
    wsState.ws.close(1000, '用户关闭');
    wsState.ws = null;
  }

  wsState.connected = false;
  wsState.reconnecting = false;
  reconnectAttempts = 0;
};

const manualReconnect = () => {
  if (!isPageActive.value) {
    return;
  }
  closeWebSocket();
  reconnectAttempts = 0;
  setupWebSocket();
};

const activatePage = () => {
  if (isPageActive.value) {
    return;
  }

  isPageActive.value = true;
  updateCurrentTime();

  if (!timeInterval) {
    timeInterval = setInterval(updateCurrentTime, 1000);
  }

  setupWebSocket();
  void loadMinSellConditions();
};

const deactivatePage = () => {
  if (!isPageActive.value) {
    return;
  }

  isPageActive.value = false;
  closeWebSocket();

  if (timeInterval) {
    clearInterval(timeInterval);
    timeInterval = null;
  }

  if (filtersDebounceTimer) {
    clearTimeout(filtersDebounceTimer);
    filtersDebounceTimer = null;
  }

  ignoreTableRequestsUntil = 0;
};

onMounted(() => {
  const initialMinSellPromise = loadMinSellConditions(true).catch(() => undefined);
  void loadSymbolOptions();

  void loadLogs()
    .catch(() => undefined)
    .finally(() => {
      hasInitialLoad.value = true;
      void initialMinSellPromise.finally(() => {
        activatePage();
      });
    });
});

onActivated(() => {
  const wasInactive = !isPageActive.value;
  activatePage();
  if (hasInitialLoad.value && wasInactive) {
    void loadLogs();
  }
});

onDeactivated(() => {
  deactivatePage();
});

onUnmounted(() => {
  deactivatePage();
});

// 监听筛选条件变化,更新 WebSocket 筛选
watch(
  () => filters.value,
  () => {
    scheduleFilterUpdate();
  },
  { deep: true },
);

// 组合式函数已自动管理列设置的保存,无需额外的 watch
</script>

<style lang="scss" scoped>
// 🎯 LogsPage特有样式 - 仅保留页面特殊需求
// --------------------------------------------------
// 其他样式已迁移到统一组件库: modern-pages.scss, components.scss, stat-cards.scss

// LogsPage特殊统计卡片样式
.stat-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 12px;

  &.success {
    background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
  }

  &.error {
    background: linear-gradient(135deg, #ff416c 0%, #ff4b2b 100%);
  }

  &.rate {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
  }

  &.warning {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  }

  &.info {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  }

  .q-card__section {
    min-height: auto;
  }

  .q-icon {
    min-width: auto;
  }

  @media (width <= 768px) {
    .q-card__section {
      padding: 6px;
    }

    // text-h6和text-caption字体大小已统一到app.scss
  }
}

.market-price-cell {
  display: inline-flex;
  align-items: center;
}

.min-buy-price-cell {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.price-change-badge {
  font-size: 0.85em;
  font-weight: 500;
  margin-left: 4px;
}

.positive-change {
  color: #21ba45;
}

.negative-change {
  color: #c10015;
}

// 🎯 LogsPage特有移动端样式
// --------------------------------------------------
// 通用字体样式(text-h5)和表格样式已统一到app.scss
// LogsPage需要更小的表格字体,使用compact-mobile类

// 确保交易日志表格支持水平滚动
.logs-table-card {
  // 覆盖 DataTableCard 内部 ModernCard 的 overflow: hidden
  :deep(.modern-card) {
    overflow: visible !important;
  }

  :deep(.modern-card__content) {
    overflow-x: auto !important;
    padding: 0 !important; // 移除padding以免影响滚动
  }

  // 为按钮区域恢复padding
  .row.items-center.q-gutter-sm.q-mb-md {
    padding: 24px 24px 0;
  }

  :deep(.modern-table-container) {
    overflow-x: auto !important;
  }

  :deep(.q-table__container) {
    overflow-x: auto !important;
  }

  :deep(.q-table__table) {
    min-width: max-content !important;
    width: auto !important;
  }
}

// 宽表格样式已迁移到通用样式 (modern-pages.scss)

// 错误信息文本样式
.error-text {
  overflow-wrap: anywhere;
  white-space: pre-wrap;
  max-width: 300px;
  line-height: 1.4;
}

// 5个统计卡片的响应式布局
@media (width >= 1024px) {
  .col-lg-2-4 {
    flex: 0 0 20%;
    max-width: 20%;
  }
}
</style>
