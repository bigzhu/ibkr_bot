<template>
  <q-page class="modern-page">
    <!-- 页面头部 -->
    <PageHeader
      :title="pageTitle"
      subtitle="查看交易盈亏和手续费明细统计"
      icon="analytics"
      glow-type="default"
    />

    <!-- 筛选器 -->
    <FilterDrawer
      :filters="filters"
      :field-configs="filterConfigs"
      @update:filters="updateFilters"
      @apply="handleFilterApply"
      @reset="handleFilterReset"
    />

    <!-- 原过滤器卡片(已移除) -->

    <!-- 标签页 -->
    <ModernCard class="tabs-card q-mb-sm" variant="glass">
      <q-tabs
        v-model="activeTab"
        class="modern-tabs"
        align="left"
        @update:model-value="onTabChange"
        dense
        narrow-indicator
        active-color="primary"
        indicator-color="primary"
      >
        <q-tab name="sell-orders" icon="trending_up" label="盈亏清单" class="modern-tab" />
        <q-tab name="daily-profit" icon="calendar_today" label="每日盈亏" class="modern-tab" />
        <q-tab name="monthly-profit" icon="calendar_month" label="每月盈亏" class="modern-tab" />
        <q-tab
          name="symbol-daily-profit"
          icon="table_chart"
          label="交易对每日盈亏"
          class="modern-tab"
        />
        <q-tab name="symbol-profit" icon="donut_small" label="交易对盈亏" class="modern-tab" />
      </q-tabs>
    </ModernCard>

    <q-tab-panels v-model="activeTab" animated>
      <!-- SELL单明细 -->
      <q-tab-panel name="sell-orders" class="q-pa-none">
        <DataTableCard class="sell-orders-card" title="盈亏清单" icon="trending_up">
          <ModernTable
            :rows="sellOrdersData"
            :columns="sellOrderColumns"
            row-key="id"
            :loading="sellOrdersLoading || isInitializing"
            :pagination="sellOrderPagination"
            @request="onSellOrderRequest"
            server-pagination
            :dense="true"
          >
            <template v-slot:body-cell-order_no="props">
              <q-td :props="props" class="order-no-cell">
                <span class="text-mono text-body2" :title="props.value">{{
                  props.value || '-'
                }}</span>
              </q-td>
            </template>

            <template v-slot:body-cell-pair="props">
              <component :is="renderSellOrderPairCell" v-bind="props" />
            </template>

            <template v-slot:body-cell-timeframe="props">
              <q-td :props="props">
                <TimeframeChip
                  :timeframe="formatTimeframe(props.value)"
                  :order-side="props.row.side"
                />
              </q-td>
            </template>

            <template v-slot:body-cell-order_amount="props">
              <component :is="renderSellOrderQuantityCell" v-bind="props" />
            </template>

            <template v-slot:body-cell-average_price="props">
              <component :is="renderSellOrderAveragePriceCell" v-bind="props" />
            </template>

            <template v-slot:body-cell-trading_total="props">
              <component :is="renderSellOrderTradingTotalCell" v-bind="props" />
            </template>

            <template v-slot:body-cell-profit="props">
              <q-td :props="props">
                <span
                  class="cursor-pointer text-primary profit-cell"
                  @click="showMatchDetails(props.row.order_no)"
                  title="点击查看撮合详情"
                >
                  <AmountDisplay :value="props.value" />
                </span>
              </q-td>
            </template>

                        <template v-slot:body-cell-commission="props">
              <q-td :props="props">
                <AmountDisplay :value="parseFloat(props.value || 0) * 2" type="expense" />
              </q-td>
            </template>

            <template v-slot:body-cell-net_profit="props">
              <q-td :props="props">
                <AmountDisplay
                  :value="parseFloat(props.row.profit || 0) - parseFloat(props.row.commission || 0) * 2"
                  type="income"
                />
              </q-td>
            </template>

            <template v-slot:body-cell-time="props">
              <component :is="renderSellOrderTimeCell" v-bind="props" />
            </template>
          </ModernTable>
        </DataTableCard>
      </q-tab-panel>

      <!-- 每日盈亏 -->
      <q-tab-panel name="daily-profit" class="q-pa-none">
        <DataTableCard class="daily-profit-card" title="每日盈亏" icon="calendar_today">
          <template #actions>
            <div class="row items-center q-gutter-sm">
              <q-btn
                icon="content_copy"
                label="复制 Markdown"
                color="primary"
                size="sm"
                flat
                :disable="
                  profitStore.dailyProfitsLoading ||
                  dailyProfitsLoading ||
                  !filteredDailyProfits.length
                "
                @click="copyDailyProfitsMarkdown"
              />
              <q-btn
                icon="refresh"
                color="primary"
                size="sm"
                flat
                :loading="profitStore.dailyProfitsLoading || dailyProfitsLoading"
                @click="onRefreshDailyProfits"
              >
                刷新
              </q-btn>
            </div>
          </template>
          <ModernTable
            :rows="paginatedDailyProfits"
            :columns="dailyProfitColumns"
            row-key="date"
            :loading="profitStore.dailyProfitsLoading || dailyProfitsLoading || isInitializing"
            :pagination="{
              page: dailyProfitPagination.page,
              rowsPerPage: dailyProfitPagination.rowsPerPage,
              rowsNumber: filteredDailyProfits.length,
              rowsPerPageOptions: [0, 10, 20, 50]
            }"
            @request="onDailyProfitRequest"
            server-pagination
          >
            <template v-slot:body-cell-total_profit="props">
              <component :is="renderDailyTotalAmountCell" v-bind="props" />
            </template>

            <template v-slot:body-cell-total_commission="props">
              <component :is="renderDailyCommissionCell" v-bind="props" />
            </template>

            <template v-slot:body-cell-net_profit="props">
              <component :is="renderDailyNetProfitCell" v-bind="props" />
            </template>
          </ModernTable>
        </DataTableCard>
      </q-tab-panel>

      <!-- 每月盈亏 -->
      <q-tab-panel name="monthly-profit" class="q-pa-none">
        <DataTableCard class="monthly-profit-card" title="每月盈亏" icon="calendar_month">
          <template #actions>
            <div class="row items-center q-gutter-sm">
              <q-btn
                icon="content_copy"
                label="复制 Markdown"
                color="primary"
                size="sm"
                flat
                :disable="
                  profitStore.monthlyProfitsLoading ||
                  monthlyProfitsLoading ||
                  !filteredMonthlyProfits.length
                "
                @click="copyMonthlyProfitsMarkdown"
              />
              <q-btn
                icon="refresh"
                color="primary"
                size="sm"
                flat
                :loading="profitStore.monthlyProfitsLoading || monthlyProfitsLoading"
                @click="onRefreshMonthlyProfits"
              >
                刷新
              </q-btn>
            </div>
          </template>
          <ModernTable
            :rows="paginatedMonthlyProfits"
            :columns="monthlyProfitColumns"
            row-key="month"
            :loading="
              profitStore.monthlyProfitsLoading || monthlyProfitsLoading || isInitializing
            "
            :pagination="{
              page: monthlyProfitPagination.page,
              rowsPerPage: monthlyProfitPagination.rowsPerPage,
              rowsNumber: filteredMonthlyProfits.length,
              rowsPerPageOptions: [0, 10, 20, 50]
            }"
            @request="onMonthlyProfitRequest"
            server-pagination
          >
            <template v-slot:body-cell-total_profit="props">
              <component :is="renderDailyTotalAmountCell" v-bind="props" />
            </template>

            <template v-slot:body-cell-total_commission="props">
              <component :is="renderDailyCommissionCell" v-bind="props" />
            </template>

            <template v-slot:body-cell-net_profit="props">
              <component :is="renderDailyNetProfitCell" v-bind="props" />
            </template>
          </ModernTable>
        </DataTableCard>
      </q-tab-panel>

      <!-- 交易对汇总 -->
      <q-tab-panel name="symbol-profit" class="q-pa-none">
        <DataTableCard class="symbol-profit-card" title="交易对盈亏" icon="donut_small">
          <template #actions>
            <q-btn
              icon="content_copy"
              label="复制 Markdown"
              color="primary"
              size="sm"
              flat
              :disable="profitStore.symbolProfitsLoading || !profitStore.symbolProfitsData.length"
              @click="copySymbolProfitsMarkdown"
            />
          </template>
          <ModernTable
            :rows="paginatedSymbolProfits"
            :columns="symbolProfitColumns"
            row-key="symbol"
            :loading="profitStore.symbolProfitsLoading || isInitializing"
            :pagination="{
              page: symbolProfitPagination.page,
              rowsPerPage: symbolProfitPagination.rowsPerPage,
              rowsNumber: profitStore.symbolProfitsData.length,
              rowsPerPageOptions: [0, 10, 20, 50]
            }"
            @request="onSymbolProfitRequest"
            server-pagination
            :dense="true"
          >
            <template v-slot:body-cell-symbol="props">
              <component :is="renderSymbolProfitPairCell" v-bind="props" />
            </template>

            <template v-slot:body-cell-total_profit="props">
              <component :is="renderSymbolProfitTotalCell" v-bind="props" />
            </template>

            <template v-slot:body-cell-total_commission="props">
              <component :is="renderSymbolProfitCommissionCell" v-bind="props" />
            </template>

            <template v-slot:body-cell-net_profit="props">
              <component :is="renderSymbolProfitNetCell" v-bind="props" />
            </template>
          </ModernTable>
        </DataTableCard>
      </q-tab-panel>

      <!-- 交易对每日盈亏 -->
      <q-tab-panel name="symbol-daily-profit" class="q-pa-none">
        <DataTableCard class="symbol-daily-profit-card" title="交易对每日盈亏" icon="table_chart">
          <div class="symbol-daily-content-wrapper">
            <!-- 只有当 tab 处于激活状态时才渲染复杂内容 -->
            <template v-if="activeTab === 'symbol-daily-profit'">
              <LoadingState
                v-if="(profitStore.symbolDailyProfitsLoading || isInitializing) &&
                  groupedSymbolDailyProfits.length === 0"
                message="加载中..."
              />

              <EmptyStateDisplay
                v-else-if="groupedSymbolDailyProfits.length === 0"
                type="data"
                title="暂无盈亏数据"
                description="当前时间范围内没有可分析的盈亏数据"
                size="md"
              />

              <div v-else class="symbol-daily-content">
              <q-list separator class="symbol-daily-expansion-list">
                <q-expansion-item
                  v-for="dateGroup in paginatedGroupedSymbolDailyProfits"
                  :key="dateGroup.date"
                  :label="dateGroup.date"
                  :caption="`${dateGroup.totalSymbols}个交易对 | 净利润: $${formatAmountUtil(dateGroup.totalNetProfit)}`"
                  header-class="expansion-header"
                  expand-icon-class="expansion-icon"
                  :default-opened="false"
                >
                  <template v-slot:header>
                    <q-item-section avatar>
                      <q-avatar color="primary" text-color="white" size="40px">
                        <q-icon name="calendar_today" />
                      </q-avatar>
                    </q-item-section>

                    <q-item-section>
                      <q-item-label class="text-subtitle1 text-weight-medium">{{
                        dateGroup.date
                      }}</q-item-label>
                      <q-item-label caption class="text-grey-6">
                        {{ dateGroup.totalSymbols }}个交易对 • {{ dateGroup.totalOrders }}笔订单
                      </q-item-label>
                    </q-item-section>

                    <q-item-section side>
                      <div class="daily-summary">
                        <div class="summary-item">
                          <div class="summary-label">净利润</div>
                          <div>
                            <AmountDisplay :value="dateGroup.totalNetProfit" type="income" />
                          </div>
                        </div>
                      </div>
                    </q-item-section>
                  </template>

                  <!-- 交易对详情列表 -->
                  <div class="symbols-detail-container">
                    <q-list separator dense>
                      <q-item
                        v-for="symbol in dateGroup.symbols"
                        :key="symbol.symbol"
                        class="symbol-profit-item"
                      >
                        <q-item-section avatar>
                          <TradingPairIcon
                            :symbol="symbol.symbol"
                            :show-text="false"
                            icon-size="32px"
                          />
                        </q-item-section>

                        <q-item-section>
                          <q-item-label class="text-weight-medium">{{ symbol.symbol }}</q-item-label>
                          <q-item-label caption>{{ symbol.order_count }}笔订单</q-item-label>
                        </q-item-section>

                        <q-item-section side class="symbol-metrics">
                          <div class="metrics-grid">
                            <div class="text-center">
                              <div class="text-caption text-grey-6">总利润</div>
                              <div class="text-weight-medium text-mono">
                                ${{ formatAmountUtil(symbol.total_profit) }}
                              </div>
                            </div>
                            <div class="text-center">
                              <div class="text-caption text-grey-6">手续费</div>
                              <div class="text-weight-medium">
                                <AmountDisplay :value="symbol.total_commission" type="expense" />
                              </div>
                            </div>
                            <div class="text-center">
                              <div class="text-caption text-grey-6">净利润</div>
                              <div>
                                <AmountDisplay :value="symbol.net_profit" type="income" />
                              </div>
                            </div>
                          </div>
                        </q-item-section>
                      </q-item>
                    </q-list>
                  </div>
                </q-expansion-item>
              </q-list>

              <!-- 分页控件 -->
              <div
                v-if="
                  symbolDailyPagination.rowsPerPage > 0 &&
                  groupedSymbolDailyProfits.length > symbolDailyPagination.rowsPerPage
                "
                class="q-mt-md"
              >
                <q-pagination
                  v-model="symbolDailyPagination.page"
                  :max="Math.ceil(groupedSymbolDailyProfits.length / symbolDailyPagination.rowsPerPage)"
                  :max-pages="6"
                  boundary-links
                  direction-links
                  color="primary"
                  size="sm"
                />
              </div>

              <div
                v-if="profitStore.symbolDailyProfitsLoading"
                class="symbol-daily-loading-overlay"
              >
                <LoadingSpinner variant="dots" size="md" />
              </div>
            </div>
            </template>
          </div>
        </DataTableCard>
      </q-tab-panel>
    </q-tab-panels>

    <!-- 撮合详情对话框 -->
    <UniversalDialog
      v-model="showMatchDialog"
      type="custom"
      title="撮合详情"
      subtitle="查看订单的详细撮合记录和盈亏情况"
      icon="analytics"
      :responsive="true"
      :maximized="$q.screen.lt.md"
      :loading="matchDetailsLoading"
      loading-text="加载撮合详情中..."
      :show-actions="false"
      custom-class="match-details-dialog"
    >
      <template #content>
        <div v-if="matchDetails" class="match-details-content">
          <div class="q-mb-md">
            <div class="text-subtitle1">
              <span class="text-weight-medium">SELL单:</span> {{ currentOrderNo }}
            </div>
          </div>

          <!-- 汇总信息 -->
          <q-card flat bordered class="q-mb-md summary-card">
            <q-card-section class="q-pa-md">
              <div class="text-subtitle2 q-mb-md text-center">汇总信息</div>

              <!-- 移动端紧凑布局 -->
              <div v-if="$q.screen.lt.md" class="mobile-summary-grid">
                <div class="summary-item">
                  <div class="summary-icon">
                    <q-icon name="list_alt" />
                  </div>
                  <div class="summary-content">
                    <div class="summary-label">撮合笔数</div>
                    <div>{{ matchDetails.summary?.total_matches || 0 }}</div>
                  </div>
                </div>

                <div class="summary-item highlight">
                  <div class="summary-icon">
                    <q-icon name="trending_up" />
                  </div>
                  <div class="summary-content">
                    <div class="summary-label">净利润</div>
                    <div>
                      <AmountDisplay :value="matchDetails.summary?.net_profit || 0" type="income" />
                    </div>
                  </div>
                </div>

                <div class="summary-row">
                  <div class="summary-sub-item">
                    <div class="sub-label">总利润</div>
                    <div class="sub-value">
                      {{ formatAmountUtil(matchDetails.summary?.total_profit || 0) }}
                    </div>
                  </div>
                  <div class="summary-sub-item">
                    <div class="sub-label">总手续费</div>
                    <div class="sub-value">
                      <AmountDisplay :value="matchDetails.summary?.total_commission || 0" type="expense" />
                    </div>
                  </div>
                </div>
              </div>

              <!-- 桌面端标准布局 -->
              <div v-else class="desktop-summary-grid">
                <div class="desktop-summary-item">
                  <div class="text-caption text-grey-6">撮合笔数</div>
                  <div class="text-weight-medium">
                    {{ matchDetails.summary?.total_matches || 0 }}
                  </div>
                </div>
                <div class="desktop-summary-item">
                  <div class="text-caption text-grey-6">总利润</div>
                  <div class="text-weight-medium">
                    {{ formatAmountUtil(matchDetails.summary?.total_profit || 0) }}
                  </div>
                </div>
                <div class="desktop-summary-item">
                  <div class="text-caption text-grey-6">总手续费</div>
                  <div class="text-weight-medium">
                    <AmountDisplay :value="matchDetails.summary?.total_commission || 0" type="expense" />
                  </div>
                </div>
                <div class="desktop-summary-item">
                  <div class="text-caption text-grey-6">净利润</div>
                  <div class="text-weight-medium">
                    <AmountDisplay :value="matchDetails.summary?.net_profit || 0" type="income" />
                  </div>
                </div>
              </div>
            </q-card-section>
          </q-card>

          <!-- 详细撮合记录 -->
          <div class="text-subtitle2 q-mb-sm">详细记录</div>
          <div v-if="$q.screen.lt.md" class="mobile-match-list">
            <!-- 移动端优化的卡片式布局 -->
            <q-card
              v-for="(match, index) in matchDetails.matches"
              :key="match.id || index"
              flat
              bordered
              class="q-mb-md mobile-match-card"
            >
              <q-card-section class="q-pa-md">
                <!-- 卡片头部:订单号和索引 -->
                <div class="mobile-match-header q-mb-md">
                  <div class="text-weight-medium text-primary">第 {{ index + 1 }} 笔撮合</div>
                  <div class="text-caption text-grey-6">BUY单号: {{ match.buy_order_no }}</div>
                </div>

                <!-- 价格信息 -->
                <div class="mobile-price-section q-mb-md">
                  <div class="price-row">
                    <div class="price-item">
                      <div class="price-label">SELL价格</div>
                      <div class="price-value text-negative">
                        <PriceDisplay :value="match.sell_price" type="price" :show-dollar="true" />
                      </div>
                    </div>
                    <div class="price-separator">→</div>
                    <div class="price-item">
                      <div class="price-label">BUY价格</div>
                      <div class="price-value text-positive">
                        <PriceDisplay :value="match.buy_price" type="price" :show-dollar="true" />
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 数量和收益信息 -->
                <div class="mobile-info-grid">
                  <div class="info-item">
                    <q-icon name="inventory" class="info-icon" />
                    <div class="info-content">
                      <div class="text-caption text-grey-6">撮合数量</div>
                      <div class="text-weight-medium">{{ formatQuantity(match.matched_qty) }}</div>
                    </div>
                  </div>

                  <div class="info-item">
                    <q-icon name="trending_up" class="info-icon" />
                    <div class="info-content">
                      <div class="text-caption text-grey-6">单笔利润</div>
                      <div class="text-weight-bold">
                        {{ formatAmountUtil(match.profit) }}
                      </div>
                    </div>
                  </div>

                  <div class="info-item">
                    <q-icon name="account_balance" class="info-icon" />
                    <div class="info-content">
                      <div class="text-caption text-grey-6">手续费</div>
                      <div class="text-weight-medium">
                        <AmountDisplay :value="match.commission" type="expense" />
                      </div>
                    </div>
                  </div>

                  <div class="info-item highlight">
                    <q-icon name="paid" class="info-icon text-positive" />
                    <div class="info-content">
                      <div class="text-caption text-grey-6">净利润</div>
                      <div class="text-weight-bold">
                        <AmountDisplay :value="match.net_profit" type="income" />
                      </div>
                    </div>
                  </div>
                </div>
              </q-card-section>
            </q-card>
          </div>
          <q-table
            v-else
            :rows="matchDetails.matches || []"
            :columns="matchDetailsColumns"
            row-key="id"
            flat
            bordered
            dense
            :pagination="{ rowsPerPage: 0 }"
            class="match-details-table"
          >
            <template v-slot:body-cell-buy_order_no="props">
              <q-td :props="props">
                <span class="text-mono">{{ props.value }}</span>
              </q-td>
            </template>

            <template v-slot:body-cell-sell_price="props">
              <q-td :props="props">
                <PriceDisplay :value="props.value" type="price" :show-dollar="true" />
              </q-td>
            </template>

            <template v-slot:body-cell-buy_price="props">
              <q-td :props="props">
                <PriceDisplay :value="props.value" type="price" :show-dollar="true" />
              </q-td>
            </template>

            <template v-slot:body-cell-matched_qty="props">
              <q-td :props="props">
                {{ formatQuantity(props.value) }}
              </q-td>
            </template>

            <template v-slot:body-cell-profit="props">
              <q-td :props="props">
                <AmountDisplay :value="props.value" />
              </q-td>
            </template>

            <template v-slot:body-cell-net_profit="props">
              <q-td :props="props">
                <AmountDisplay :value="props.value" type="income" />
              </q-td>
            </template>
          </q-table>
        </div>

        <EmptyStateDisplay
          v-else-if="!matchDetailsLoading"
          type="data"
          title="暂无撮合详情"
          description="该订单暂无撮合详情数据"
          size="sm"
        />
      </template>
    </UniversalDialog>
  </q-page>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';
import { storeToRefs } from 'pinia';
import { api } from 'src/services';
import { useQuasar, copyToClipboard } from 'quasar';
import { formatAmount as formatAmountUtil, formatQuantity } from 'src/utils/formatters';
import { formatDateTime as formatDateTimeUtil } from 'src/utils/datetime';
import { calculateNetProfit, preciseSum } from 'src/utils/precision-math';
import TradingPairIcon from 'src/components/TradingPairIcon.vue';
import ModernCard from 'src/components/ModernCard.vue';
import DataTableCard from 'src/components/DataTableCard.vue';
import ModernTable from 'src/components/ModernTable.vue';
import FilterDrawer from 'src/components/FilterDrawer.vue';
import PageHeader from 'src/components/PageHeader.vue';
import UniversalDialog from 'src/components/UniversalDialog.vue';
import TimeframeChip from 'src/components/TimeframeChip.vue';
import LoadingSpinner from 'src/components/LoadingSpinner.vue';
import LoadingState from 'src/components/LoadingState.vue';
import EmptyStateDisplay from 'src/components/EmptyStateDisplay.vue';
import AmountDisplay from 'src/components/AmountDisplay.vue';
import PriceDisplay from 'src/components/PriceDisplay.vue';
import { useTableCellRenderers } from 'src/composables/useTableCellRenderers';
import {
  useProfitAnalysisStore,
  type DailyProfit,
  type MonthlyProfit,
  type SymbolDailyProfit,
} from 'src/stores/profit-analysis-store';
import { useSellOrdersStore } from 'src/stores/sell-orders-store';
import type { SellOrdersRequest, SellOrdersFilters } from 'src/stores/sell-orders-store';
import Decimal from 'decimal.js';
import { useApiRequest } from 'src/composables/useApiRequest';
import { useBackgroundRefresh } from 'src/composables/useBackgroundRefresh';

const $q = useQuasar();
const route = useRoute();
const currentQuoteAsset = computed(() => {
  const metaQuote = route.meta?.quoteAsset;
  if (typeof metaQuote === 'string' && metaQuote.length > 0) {
    return metaQuote.toUpperCase();
  }
  return 'USDC';
});
const pageTitle = computed(() =>
  currentQuoteAsset.value === 'USDC'
    ? '盈亏分析'
    : `盈亏分析 (${currentQuoteAsset.value})`,
);
const profitStore = useProfitAnalysisStore();
const sellOrdersStore = useSellOrdersStore();
const { renderPairCell, renderPriceCell, renderAmountCell, renderQuantityCell, renderTimeCell } =
  useTableCellRenderers();
type TableSlotProps = Parameters<typeof renderPairCell>[0];

const renderSellOrderPairCell = (props: TableSlotProps) => renderPairCell(props);
const renderSellOrderQuantityCell = (props: TableSlotProps) => renderQuantityCell(props);
const renderSellOrderAveragePriceCell = (props: TableSlotProps) =>
  renderPriceCell(props, { type: 'price', showDollar: true });
const renderSellOrderTradingTotalCell = (props: TableSlotProps) => renderAmountCell(props);
const formatSellOrderTime = (rawValue: unknown) =>
  formatDateTimeUtil(rawValue as string | number | Date | null | undefined, {
    assumeUtc: true,
    includeYear: true,
    includeSeconds: true,
    fallback: '',
  });

const renderSellOrderTimeCell = (props: TableSlotProps) =>
  renderTimeCell(props, { formatter: formatSellOrderTime });

const renderDailyTotalAmountCell = (props: TableSlotProps) => renderAmountCell(props);
const renderDailyCommissionCell = (props: TableSlotProps) => renderAmountCell(props, { type: 'expense' });
const renderDailyNetProfitCell = (props: TableSlotProps) => renderAmountCell(props, { type: 'income' });

const renderSymbolProfitPairCell = (props: TableSlotProps) =>
  renderPairCell(props, { iconSize: '24px' });
const renderSymbolProfitTotalCell = (props: TableSlotProps) => renderAmountCell(props);
const renderSymbolProfitCommissionCell = (props: TableSlotProps) =>
  renderAmountCell(props, { type: 'expense' });
const renderSymbolProfitNetCell = (props: TableSlotProps) => renderAmountCell(props, { type: 'income' });

// 响应式数据
const activeTab = ref('sell-orders');

// 过滤器
const filters = reactive({
  selectedDate: '',
  symbol: '',
  orderNo: '',
});

// 筛选器配置
const filterConfigs = ref([
  {
    key: 'selectedDate',
    type: 'date',
    label: '选择日期',
    props: {
      min: computed(() => earliestDate.value),
      max: computed(() => latestDate.value),
    },
  },
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
    key: 'orderNo',
    type: 'input',
    label: '订单号',
    props: {
      placeholder: '输入订单号搜索',
    },
  },
]);

// 数据 - 现在从store获取
// const sellOrders = ref([]); // 现在使用 profitStore.sellOrders
// const dailyProfits = ref([]); // 现在使用 profitStore.dailyProfits
// 删除本地 symbolProfits,现在使用 store 中的数据
const symbolOptions = ref<Array<{ label: string; value: string }>>([]);
const availableDatesSet = ref<Set<string>>(new Set());
const earliestDate = ref('');
const latestDate = ref('');

// 撮合详情相关
const showMatchDialog = ref(false);
interface SellOrderMatch {
  buy_order_no: string;
  sell_price: string;
  buy_price: string;
  matched_qty: string;
  profit: string;
  commission?: string;
  net_profit?: string;
}

interface MatchSummary {
  total_matches?: number;
  total_profit?: string;
  total_commission?: string;
  net_profit?: string;
  [key: string]: unknown;
}

interface MatchDetailsResponse {
  sell_order_no: string;
  matches: Array<{
    buy_order_no: string;
    sell_price: string;
    buy_price: string;
    matched_qty: string;
    profit: string;
  }>;
  summary?: MatchSummary;
}

interface MatchDetails extends MatchDetailsResponse {
  matches: SellOrderMatch[];
}

const matchDetails = ref<MatchDetails | null>(null);
const currentOrderNo = ref('');

const { execute: fetchMatchDetails, loading: matchDetailsLoading } = useApiRequest(
  async (orderNo: string) => {
    const response = await api.get<MatchDetailsResponse>(`/api/profit-analysis/order-matches/${orderNo}`);
    const payload = response.data;

    if (!payload || !payload.sell_order_no) {
      return null;
    }

    const processedMatches: SellOrderMatch[] = payload.matches.map((match) => {
      const sellPrice = new Decimal(match.sell_price);
      const matchedQty = new Decimal(match.matched_qty);
      const profit = new Decimal(match.profit);

      const commission = sellPrice.mul(matchedQty).mul(new Decimal('0.002'));
      const netProfit = profit.minus(commission);

      return {
        ...match,
        commission: commission.toFixed(8),
        net_profit: netProfit.toFixed(8),
      };
    });

    const totalProfit = processedMatches.reduce(
      (sum, match) => sum.plus(new Decimal(match.profit)),
      new Decimal('0'),
    );
    const totalCommission = processedMatches.reduce(
      (sum, match) => sum.plus(new Decimal(match.commission)),
      new Decimal('0'),
    );
    const totalNetProfit = totalProfit.minus(totalCommission);

    return {
      ...payload,
      matches: processedMatches,
      summary: {
        ...payload.summary,
        total_commission: totalCommission.toFixed(8),
        net_profit: totalNetProfit.toFixed(8),
      },
    } as MatchDetails;
  },
  {
    notifySuccess: false,
    notifyError: false,
    onError: (error) => {
      notifyError('加载撮合详情失败', error);
    },
  },
);

// 服务器端分页状态 - 使用 Pinia store
const { orders: sellOrdersData, loading: sellOrdersLoading, pagination: sellOrderPagination } =
  storeToRefs(sellOrdersStore);

const buildSellOrderFilters = (): SellOrdersFilters => {
  const filter: SellOrdersFilters = {};
  filter.quoteAsset = currentQuoteAsset.value;
  if (filters.symbol) {
    filter.symbol = filters.symbol;
  }
  if (filters.orderNo) {
    filter.orderNo = filters.orderNo;
  }
  if (filters.selectedDate) {
    filter.startDate = filters.selectedDate;
    filter.endDate = filters.selectedDate;
  }
  return filter;
};

const fetchSellOrders = async (
  overrides: Partial<SellOrdersRequest> = {},
  forceRefresh = false,
) => {
  const currentPagination = sellOrderPagination.value || {};
  const safePage =
    typeof currentPagination.page === 'number' && currentPagination.page > 0
      ? currentPagination.page
      : 1;
  const safeRowsPerPage =
    typeof currentPagination.rowsPerPage === 'number'
      ? currentPagination.rowsPerPage
      : 0;

  const request: SellOrdersRequest = {
    page: overrides.page ?? safePage,
    rowsPerPage: overrides.rowsPerPage ?? safeRowsPerPage,
    filters: overrides.filters ?? buildSellOrderFilters(),
  };
  if (!request.filters.quoteAsset) {
    request.filters.quoteAsset = currentQuoteAsset.value;
  }

  try {
    await sellOrdersStore.fetchSellOrders(request, forceRefresh);
  } catch (error) {
    console.error('❌ 获取盈亏清单失败:', error);
    $q.notify({
      type: 'negative',
      message: '加载盈亏清单失败',
      caption: error instanceof Error ? error.message : '未知错误',
      position: 'top',
    });
  }
};

// 表格列定义
const sellOrderColumns = [
  { name: 'time', label: '时间', field: 'time', align: 'left', sortable: true },
  {
    name: 'order_no',
    label: '订单号',
    field: 'order_no',
    align: 'left',
    sortable: true,
    style: 'width: 120px; max-width: 120px;',
  },
  { name: 'pair', label: '交易对', field: 'pair', align: 'left', sortable: true },
  {
    name: 'timeframe',
    label: '时间周期',
    field: 'client_order_id',
    align: 'left',
    sortable: true,
  },
  { name: 'order_amount', label: '数量', field: 'order_amount', align: 'left', sortable: true },
  {
    name: 'average_price',
    label: '成交价格',
    field: 'average_price',
    align: 'left',
    sortable: true,
  },
  {
    name: 'trading_total',
    label: '成交金额',
    field: 'trading_total',
    align: 'left',
    sortable: true,
  },
  { name: 'profit', label: '毛利', field: 'profit', align: 'left', sortable: true },
  { name: 'commission', label: '手续费', field: 'commission', align: 'left', sortable: true },
  { name: 'net_profit', label: '利润', field: 'net_profit', align: 'left', sortable: true },
];

const dailyProfitColumns = [
  { name: 'date', label: '日期', field: 'date', align: 'left', sortable: true },
  { name: 'order_count', label: '订单数', field: 'order_count', align: 'left', sortable: true },
  { name: 'total_profit', label: '总利润', field: 'total_profit', align: 'left', sortable: true },
  {
    name: 'total_commission',
    label: '总手续费',
    field: 'total_commission',
    align: 'left',
    sortable: true,
  },
  { name: 'net_profit', label: '到手利润', field: 'net_profit', align: 'left', sortable: true },
];

const monthlyProfitColumns = [
  { name: 'month', label: '月份', field: 'month', align: 'left', sortable: true },
  { name: 'order_count', label: '订单数', field: 'order_count', align: 'left', sortable: true },
  { name: 'total_profit', label: '总利润', field: 'total_profit', align: 'left', sortable: true },
  {
    name: 'total_commission',
    label: '总手续费',
    field: 'total_commission',
    align: 'left',
    sortable: true,
  },
  { name: 'net_profit', label: '到手利润', field: 'net_profit', align: 'left', sortable: true },
];

const symbolProfitColumns = [
  { name: 'symbol', label: '交易对', field: 'symbol', align: 'left', sortable: true },
  { name: 'order_count', label: '订单数', field: 'order_count', align: 'left', sortable: true },
  { name: 'total_profit', label: '总利润', field: 'total_profit', align: 'left', sortable: true },
  {
    name: 'total_commission',
    label: '总手续费',
    field: 'total_commission',
    align: 'left',
    sortable: true,
  },
  { name: 'net_profit', label: '到手利润', field: 'net_profit', align: 'left', sortable: true },
];

// 撮合详情表格列定义
const matchDetailsColumns = [
  { name: 'buy_order_no', label: 'BUY单号', field: 'buy_order_no', align: 'left' },
  { name: 'sell_price', label: 'SELL价格', field: 'sell_price', align: 'left' },
  { name: 'buy_price', label: 'BUY价格', field: 'buy_price', align: 'left' },
  { name: 'matched_qty', label: '撮合数量', field: 'matched_qty', align: 'left' },
  { name: 'profit', label: '单笔利润', field: 'profit', align: 'left' },
  { name: 'commission', label: '手续费', field: 'commission', align: 'left' },
  { name: 'net_profit', label: '净利润', field: 'net_profit', align: 'left' },
];

// 使用统一的格式化函数 formatAmount (金额) 和 formatCurrency (货币数量) (已从 src/utils/formatters 导入)

const formatTimeframe = (value: string | null | undefined) => {
  if (!value) return '-';
  // 去掉 _1 后缀
  return value.endsWith('_1') ? value.slice(0, -2) : value;
};

const loadData = async (forceRefresh = false) => {
  try {
    isInitializing.value = true;

    await fetchSellOrders({}, forceRefresh);

    const results = await Promise.allSettled([
      fetchDailyProfits(forceRefresh),
      fetchMonthlyProfits(forceRefresh),
      profitStore.fetchSymbolProfits(undefined, forceRefresh, currentQuoteAsset.value),
      profitStore.fetchSymbolDailyProfits(undefined, forceRefresh, currentQuoteAsset.value),
    ]);

    const symbolResult = results[2];
    if (symbolResult.status === 'fulfilled') {
      updateSymbolOptions();
    }
    const dailyResult = results[0];
    if (dailyResult.status === 'fulfilled') {
      updateAvailableDates();
    }
  } finally {
    isInitializing.value = false;
  }
};

// 删除原有的前端筛选逻辑,现在使用服务器端分页和筛选

// 删除原有的loadSellOrdersData函数,现在使用store

const updateSymbolOptions = () => {
  // 从后端交易对盈亏数据中提取交易对
  const uniqueSymbols = profitStore.symbolProfitsData.map((item) => item.symbol);
  symbolOptions.value = uniqueSymbols.map((symbol) => ({
    label: symbol,
    value: symbol,
  }));
};

const updateAvailableDates = () => {
  // 从后端每日盈亏数据中提取所有可用日期
  const uniqueDates = profitStore.dailyProfitsData.map((item) => item.date);

  // 设置可用日期集合
  availableDatesSet.value = new Set(uniqueDates);

  // 设置日期范围
  if (uniqueDates.length > 0) {
    uniqueDates.sort();
    earliestDate.value = uniqueDates[0];
    latestDate.value = uniqueDates[uniqueDates.length - 1];
  }
};

// 每日盈亏数据状态
const dailyProfitsData = ref<DailyProfit[]>([]);
const dailyProfitsLoading = ref(false);
const monthlyProfitsData = ref<MonthlyProfit[]>([]);
const monthlyProfitsLoading = ref(false);

// 初始化状态
const isInitializing = ref(true);

// 获取每日盈亏数据
const fetchDailyProfits = async (forceRefresh = false) => {
  dailyProfitsLoading.value = true;
  try {
    // 构建查询参数
    const params: { start_date?: string; end_date?: string; symbol?: string } = {};

    if (filters.selectedDate) {
      // 如果选择了具体日期,设置开始和结束日期为同一天
      params.start_date = filters.selectedDate;
      params.end_date = filters.selectedDate;
    }

    if (filters.symbol) {
      params.symbol = filters.symbol;
    }

    // 调用新的后端接口
    await profitStore.fetchDailyProfits(
      Object.keys(params).length > 0 ? params : undefined,
      forceRefresh,
      currentQuoteAsset.value,
    );
    dailyProfitsData.value = profitStore.dailyProfitsData;
  } catch (error) {
    console.error('❌ 获取每日盈亏数据失败:', error);
  } finally {
    dailyProfitsLoading.value = false;
  }
};

// 每日盈亏数据缓存,避免重复计算
const filteredDailyProfits = ref<DailyProfit[]>([]);

// 监听数据变化,更新每日盈亏缓存
watch(() => dailyProfitsData.value, (newData) => {
  filteredDailyProfits.value = newData;
}, { immediate: true });

const formatDateString = (date: Date): string => {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const fetchMonthlyProfits = async (forceRefresh = false) => {
  monthlyProfitsLoading.value = true;
  try {
    const params: { start_date?: string; end_date?: string; symbol?: string } = {};

    if (filters.selectedDate) {
      const [year, month, day] = filters.selectedDate.split('-').map((part) => Number.parseInt(part, 10));
      if (!Number.isNaN(year) && !Number.isNaN(month) && !Number.isNaN(day)) {
        const start = new Date(year, month - 1, 1);
        const end = new Date(year, month, 0);
        params.start_date = formatDateString(start);
        params.end_date = formatDateString(end);
      }
    }

    if (filters.symbol) {
      params.symbol = filters.symbol;
    }

    await profitStore.fetchMonthlyProfits(
      Object.keys(params).length > 0 ? params : undefined,
      forceRefresh,
      currentQuoteAsset.value,
    );
    monthlyProfitsData.value = profitStore.monthlyProfitsData;
  } catch (error) {
    console.error('❌ 获取每月盈亏数据失败:', error);
  } finally {
    monthlyProfitsLoading.value = false;
  }
};

// 每月盈亏数据缓存,避免重复计算
const filteredMonthlyProfits = ref<MonthlyProfit[]>([]);

// 监听数据变化,更新每月盈亏缓存
watch(() => monthlyProfitsData.value, (newData) => {
  filteredMonthlyProfits.value = newData;
}, { immediate: true });

const copyMonthlyProfitsMarkdown = async () => {
  if (!filteredMonthlyProfits.value.length) {
    $q.notify({
      type: 'warning',
      message: '暂无每月盈亏数据可复制',
      position: 'top',
    });
    return;
  }

  const headers = ['月份', '订单数', '总利润', '总手续费', '到手利润'];
  const rows = filteredMonthlyProfits.value.map((item) => [
    item.month,
    String(item.order_count),
    formatAmountUtil(item.total_profit),
    formatAmountUtil(item.total_commission),
    formatAmountUtil(item.net_profit),
  ]);

  const markdownTable = [
    `| ${headers.join(' | ')} |`,
    `| ${headers.map(() => '---').join(' | ')} |`,
    ...rows.map((cols) => `| ${cols.join(' | ')} |`),
  ].join('\n');

  try {
    await copyToClipboard(markdownTable);
    $q.notify({
      type: 'positive',
      message: '每月盈亏表格已复制',
      position: 'top',
    });
  } catch (error) {
    console.error('❌ 复制每月盈亏Markdown失败:', error);
    $q.notify({
      type: 'negative',
      message: '复制失败',
      caption: error instanceof Error ? error.message : '未知错误',
      position: 'top',
    });
  }
};

const copyDailyProfitsMarkdown = async () => {
  if (!filteredDailyProfits.value.length) {
    $q.notify({
      type: 'warning',
      message: '暂无每日盈亏数据可复制',
      position: 'top',
    });
    return;
  }

  const headers = ['日期', '订单数', '总利润', '总手续费', '到手利润'];
  const rows = filteredDailyProfits.value.map((item) => [
    item.date,
    String(item.order_count),
    formatAmountUtil(item.total_profit),
    formatAmountUtil(item.total_commission),
    formatAmountUtil(item.net_profit),
  ]);

  const markdownTable = [
    `| ${headers.join(' | ')} |`,
    `| ${headers.map(() => '---').join(' | ')} |`,
    ...rows.map((cols) => `| ${cols.join(' | ')} |`),
  ].join('\n');

  try {
    await copyToClipboard(markdownTable);
    $q.notify({
      type: 'positive',
      message: '每日盈亏表格已复制',
      position: 'top',
    });
  } catch (error) {
    console.error('❌ 复制每日盈亏Markdown失败:', error);
    $q.notify({
      type: 'negative',
      message: '复制失败',
      caption: error instanceof Error ? error.message : '未知错误',
      position: 'top',
    });
  }
};

const copySymbolProfitsMarkdown = async () => {
  const data = profitStore.symbolProfitsData;
  if (!data.length) {
    $q.notify({
      type: 'warning',
      message: '暂无交易对盈亏数据可复制',
      position: 'top',
    });
    return;
  }

  const headers = ['交易对', '订单数', '总利润', '总手续费', '到手利润'];
  const rows = data.map((item) => [
    item.symbol,
    String(item.order_count),
    formatAmountUtil(item.total_profit),
    formatAmountUtil(item.total_commission),
    formatAmountUtil(item.net_profit),
  ]);

  const markdownTable = [
    `| ${headers.join(' | ')} |`,
    `| ${headers.map(() => '---').join(' | ')} |`,
    ...rows.map((cols) => `| ${cols.join(' | ')} |`),
  ].join('\n');

  try {
    await copyToClipboard(markdownTable);
    $q.notify({
      type: 'positive',
      message: '交易对盈亏表格已复制',
      position: 'top',
    });
  } catch (error) {
    console.error('❌ 复制交易对盈亏Markdown失败:', error);
    $q.notify({
      type: 'negative',
      message: '复制失败',
      caption: error instanceof Error ? error.message : '未知错误',
      position: 'top',
    });
  }
};

// 按日期分组的交易对每日盈亏数据
interface GroupedSymbolDailyProfit {
  date: string;
  symbols: SymbolDailyProfit[];
  totalSymbols: number;
  totalOrders: number;
  totalProfit: number;
  totalCommission: number;
  totalNetProfit: number;
}

// 使用 ref 缓存计算结果,避免每次渲染都重新计算
const groupedSymbolDailyProfits = ref<GroupedSymbolDailyProfit[]>([]);

// 分页状态
const symbolDailyPagination = ref({
  page: 1,
  rowsPerPage: 0, // 0 表示显示全部
});

// 每日盈亏分页
const dailyProfitPagination = ref({
  page: 1,
  rowsPerPage: 0, // 默认显示全部
});

// 每月盈亏分页
const monthlyProfitPagination = ref({
  page: 1,
  rowsPerPage: 0, // 默认显示全部
});

// 交易对盈亏分页
const symbolProfitPagination = ref({
  page: 1,
  rowsPerPage: 0, // 默认显示全部
});

// 分页后的数据
const paginatedGroupedSymbolDailyProfits = computed(() => {
  const pageSize = symbolDailyPagination.value.rowsPerPage;
  if (!pageSize || pageSize <= 0) {
    return groupedSymbolDailyProfits.value;
  }
  const start = (symbolDailyPagination.value.page - 1) * pageSize;
  const end = start + pageSize;
  return groupedSymbolDailyProfits.value.slice(start, end);
});

const paginatedDailyProfits = computed(() => {
  const pageSize = dailyProfitPagination.value.rowsPerPage;
  if (!pageSize || pageSize <= 0) {
    return filteredDailyProfits.value;
  }
  const start = (dailyProfitPagination.value.page - 1) * pageSize;
  const end = start + pageSize;
  return filteredDailyProfits.value.slice(start, end);
});

const paginatedMonthlyProfits = computed(() => {
  const pageSize = monthlyProfitPagination.value.rowsPerPage;
  if (!pageSize || pageSize <= 0) {
    return filteredMonthlyProfits.value;
  }
  const start = (monthlyProfitPagination.value.page - 1) * pageSize;
  const end = start + pageSize;
  return filteredMonthlyProfits.value.slice(start, end);
});

const paginatedSymbolProfits = computed(() => {
  const pageSize = symbolProfitPagination.value.rowsPerPage;
  if (!pageSize || pageSize <= 0) {
    return profitStore.symbolProfitsData;
  }
  const start = (symbolProfitPagination.value.page - 1) * pageSize;
  const end = start + pageSize;
  return profitStore.symbolProfitsData.slice(start, end);
});

// 异步计算分组数据的函数,避免阻塞 UI
const computeGroupedSymbolDailyProfits = async () => {
  const data = profitStore.symbolDailyProfitsData;
  if (!data || data.length === 0) {
    groupedSymbolDailyProfits.value = [];
    return;
  }

  // 使用 requestIdleCallback 或 setTimeout 进行异步处理
  return new Promise<void>((resolve) => {
    const processData = () => {
      const groupedByDate = data.reduce<Record<string, SymbolDailyProfit[]>>((groups, item) => {
        if (!groups[item.date]) {
          groups[item.date] = [];
        }
        groups[item.date].push(item);
        return groups;
      }, {});

      const result = Object.keys(groupedByDate)
        .sort((a, b) => new Date(b).getTime() - new Date(a).getTime())
        .map((date) => {
          const symbols = groupedByDate[date];
          const totalOrders = symbols.reduce((sum, s) => sum + s.order_count, 0);
          const totalProfit = preciseSum(symbols.map((s) => s.total_profit ?? 0));
          const totalCommission = preciseSum(symbols.map((s) => s.total_commission ?? 0));
          const totalNetProfit = calculateNetProfit(totalProfit, totalCommission);

          symbols.sort(
            (a, b) =>
              (Number.parseFloat(String(b.net_profit)) || 0) -
              (Number.parseFloat(String(a.net_profit)) || 0),
          );

          return {
            date,
            symbols,
            totalSymbols: symbols.length,
            totalOrders,
            totalProfit,
            totalCommission,
            totalNetProfit,
          };
        });

      groupedSymbolDailyProfits.value = result;
      resolve();
    };

    // 使用 requestIdleCallback 进行异步处理,如果不支持则使用 setTimeout
    if (typeof requestIdleCallback !== 'undefined') {
      requestIdleCallback(processData);
    } else {
      setTimeout(processData, 0);
    }
  });
};

// 监听数据变化,更新分组计算
watch(() => profitStore.symbolDailyProfitsData, computeGroupedSymbolDailyProfits, { immediate: true });

const onRefreshDailyProfits = async () => {
  await fetchDailyProfits(true);
  updateAvailableDates();
};

const onRefreshMonthlyProfits = async () => {
  await fetchMonthlyProfits(true);
};

// 删除 updateSymbolProfits,现在使用后端数据

// 删除本地日期聚合函数,现在使用后端汇总

// 删除 processSymbolAggregation,现在使用后端汇总

// 筛选器事件处理
const updateFilters = (newFilters: Partial<typeof filters>) => {
  // 特殊处理日期变更
  if ('selectedDate' in newFilters) {
    const newDate = newFilters.selectedDate;
    if (newDate && !availableDatesSet.value.has(newDate)) {
      // 如果选择的日期没有数据,清除选择并提示
      newFilters.selectedDate = '';
      $q.notify({
        type: 'warning',
        message: '所选日期无交易数据,请选择其他日期',
        position: 'top',
      });
    }
  }
  Object.assign(filters, newFilters);
};

const handleFilterApply = async () => {
  console.log(`🔍 Applying filters for tab: ${activeTab.value}`);
  // 根据当前激活的 tab 来刷新对应的数据
  switch (activeTab.value) {
    case 'sell-orders':
      console.log('📋 Applying filters to sell orders...');
      await fetchSellOrders(
        {
          page: 1, // 应用筛选器时重置到第一页
          rowsPerPage: sellOrderPagination.value?.rowsPerPage ?? 0,
          filters: buildSellOrderFilters(),
        },
        true,
      );
      break;
    case 'daily-profit':
      await fetchDailyProfits(true);
      updateAvailableDates();
      break;
    case 'monthly-profit':
      await fetchMonthlyProfits(true);
      break;
    case 'symbol-profit':
      await profitStore.fetchSymbolProfits(undefined, true, currentQuoteAsset.value);
      updateSymbolOptions();
      break;
    case 'symbol-daily-profit':
      await profitStore.fetchSymbolDailyProfits(undefined, true, currentQuoteAsset.value);
      break;
    default:
      await loadData(true);
      break;
  }
};

const handleFilterReset = async () => {
  filters.selectedDate = '';
  filters.symbol = '';
  filters.orderNo = '';

  if (!isInitializing.value) {
    // 根据当前激活的 tab 来刷新对应的数据
    switch (activeTab.value) {
      case 'sell-orders':
        await fetchSellOrders(
          {
            page: 1, // 重置筛选器时重置到第一页
            rowsPerPage: sellOrderPagination.value?.rowsPerPage ?? 0,
            filters: buildSellOrderFilters(),
          },
          true,
        );
        break;
      case 'daily-profit':
        await fetchDailyProfits(true);
        updateAvailableDates();
        break;
      case 'monthly-profit':
        await fetchMonthlyProfits(true);
        break;
      case 'symbol-profit':
        await profitStore.fetchSymbolProfits(undefined, true, currentQuoteAsset.value);
        updateSymbolOptions();
        break;
      case 'symbol-daily-profit':
        await profitStore.fetchSymbolDailyProfits(undefined, true, currentQuoteAsset.value);
        break;
      default:
        await loadData(true);
        break;
    }
  }
};

// 显示撮合详情
const showMatchDetails = async (orderNo: string) => {
  if (!orderNo) {
    $q.notify({
      type: 'warning',
      message: '订单号无效',
      position: 'top',
    });
    return;
  }

  currentOrderNo.value = orderNo;
  showMatchDialog.value = true;
  matchDetails.value = null;

  const result = await fetchMatchDetails(orderNo);

  if (!result || result.matches.length === 0) {
    matchDetails.value = result;
    $q.notify({
      type: 'info',
      message: '该订单暂无撮合详情',
      position: 'top',
    });
    return;
  }

  matchDetails.value = result;
};

const onTabChange = (newTab: string) => {
  console.log(`🔄 Tab changed to: ${newTab}`);
  // tab 切换立即响应,不做任何阻塞操作
};

// 处理服务器端分页请求
interface TableRequestPayload {
  pagination: {
    page: number;
    rowsPerPage: number;
  };
}

const onSellOrderRequest = (props: TableRequestPayload) => {
  const { page, rowsPerPage } = props.pagination;
  void fetchSellOrders({ page, rowsPerPage }, true);
};

const onDailyProfitRequest = (props: TableRequestPayload) => {
  const { page, rowsPerPage } = props.pagination;
  dailyProfitPagination.value = { page, rowsPerPage };
};

const onMonthlyProfitRequest = (props: TableRequestPayload) => {
  const { page, rowsPerPage } = props.pagination;
  monthlyProfitPagination.value = { page, rowsPerPage };
};

const onSymbolProfitRequest = (props: TableRequestPayload) => {
  const { page, rowsPerPage } = props.pagination;
  symbolProfitPagination.value = { page, rowsPerPage };
};

watch(
  () => currentQuoteAsset.value,
  () => {
    filters.selectedDate = '';
    filters.symbol = '';
    filters.orderNo = '';
    symbolOptions.value = [];
    availableDatesSet.value = new Set<string>();
    earliestDate.value = '';
    latestDate.value = '';
    void loadData(true);
  },
  { immediate: false },
);

useBackgroundRefresh({
  refresh: async () => {
    await loadData(true);
  },
  interval: 5 * 60 * 1000,
  immediate: false,
});

// 监听 tab 变化,在动画完成后获取数据
watch(activeTab, (newTab) => {
  console.log(`🔄 Tab watcher triggered: ${newTab}`);

  // 使用 requestAnimationFrame 确保 tab 切换动画完成后再获取数据
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      console.log(`📋 Loading data for tab: ${newTab}`);
      switch (newTab) {
        case 'sell-orders':
          console.log('📋 Fetching sell orders with force refresh...');
          void fetchSellOrders(
            {
              page: 1,
              rowsPerPage: sellOrderPagination.value?.rowsPerPage ?? 0,
              filters: buildSellOrderFilters(),
            },
            true,
          );
          break;
        case 'daily-profit':
          void fetchDailyProfits(true).then(() => updateAvailableDates());
          break;
        case 'monthly-profit':
          void fetchMonthlyProfits(true);
          break;
        case 'symbol-profit':
          void profitStore
            .fetchSymbolProfits(undefined, true, currentQuoteAsset.value)
            .then(() => updateSymbolOptions());
          break;
        case 'symbol-daily-profit':
          void profitStore.fetchSymbolDailyProfits(undefined, true, currentQuoteAsset.value);
          break;
        default:
          void loadData(true);
          break;
      }
    });
  });
}, { immediate: false });

onMounted(async () => {
  // 进入页面时强制刷新数据
  await loadData(true);
});
</script>

<style lang="scss" scoped>
@import 'src/css/quasar.variables';

.filter-section {
  margin-bottom: $spacing-lg;

  &:last-child {
    margin-bottom: 0;
  }
}

.filter-label {
  display: block;
  margin-bottom: $spacing-xs;
  font-size: $font-size-sm;
  color: $text-muted;
  font-weight: 500;
}

.filter-input,
.filter-select {
  width: 100%;

  :deep(.q-field__control) {
    @include glass-panel($white-alpha-05, $white-alpha-10, $border-radius-sm);

    &:hover {
      border-color: $white-alpha-15;
    }

    &:focus-within {
      border-color: $primary;
      background: $white-alpha-08;
    }
  }
}

.filter-drawer-footer {
  padding: $spacing-md;

  @include glass-divider-top($white-alpha-10);

  .full-width {
    width: 100%;
  }
}

// 其他原有样式保持不变
.order-no-cell {
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.profit-cell {
  transition: all 0.3s ease;

  &:hover {
    text-decoration: underline;
    transform: scale(1.05);
  }
}

.match-dialog-card {
  max-height: 90vh;

  // 桌面端自适应宽度
  @media (width >= 600px) {
    width: auto;
    min-width: 600px;
    max-width: 1000px;
  }

  // 移动端全屏
  @media (width <= 599px) {
    width: 90vw;
    max-width: 90vw;
  }
}

.daily-summary {
  text-align: right;

  .summary-item {
    margin-bottom: 4px;

    .summary-label {
      font-size: 0.75rem;
      color: rgb(0 0 0 / 60%);
      margin-bottom: 2px;

      .body--dark & {
        color: $text-subtle;
      }
    }
  }

  @media (width <= 768px) {
    .summary-item {
      margin-bottom: 2px;

      .summary-label {
        font-size: 0.7rem;
      }
    }
  }
}

.summary-card {
  .mobile-summary-grid {
    display: flex;
    flex-direction: column;
    gap: $spacing-sm;

    .summary-item {
      display: flex;
      align-items: center;
      padding: $spacing-sm;
      background: $white-alpha-03;
      border-radius: $border-radius-sm;

      &.highlight {
        @include status-surface($positive);
      }

      .summary-icon {
        font-size: 1.5rem;
        margin-right: 12px;
        color: $text-subtle;
        flex-shrink: 0;

        .q-icon {
          font-size: inherit;
        }
      }

      .summary-content {
        flex: 1;

        .summary-label {
          font-size: 0.8rem;
          color: $text-muted;
          margin-bottom: 4px;
        }


      }
    }

    .summary-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: $white-alpha-02;
      border-radius: $border-radius-sm;
      padding: $spacing-sm;

      .summary-sub-item {
        flex: 1;
        text-align: center;

        .sub-label {
          font-size: 0.7rem;
          color: $text-subtle;
          margin-bottom: 4px;
        }

        .sub-value {
          font-size: 0.9rem;
          font-weight: 500;
          font-family: 'Roboto Mono', monospace;
        }
      }

      .summary-divider {
        font-size: 1rem;
        color: $text-subtle;
        margin: 0 12px;
        font-weight: bold;
      }
    }
  }

  .desktop-summary-grid {
    display: flex;
    gap: 24px;
    flex-wrap: nowrap;
    align-items: stretch;

    .desktop-summary-item {
      flex: 1;
      min-width: 0;
      display: flex;
      flex-direction: column;
      justify-content: center;
      text-align: center;
      padding: $spacing-md;
      background: $white-alpha-03;
      border-radius: $border-radius-sm;

      &.highlight {
        @include status-surface($positive);
      }
    }
  }
}

.mobile-match-card {
  background: $white-alpha-05;
  border-radius: $border-radius-md;
  transition: all 0.2s ease;

  &:hover {
    background: rgb(255 255 255 / 8%);
    transform: translateY(-2px);
  }

  .mobile-match-header {
    border-bottom: 1px solid $white-alpha-10;
    padding-bottom: 8px;

    .text-primary {
      font-size: 1rem;
    }
  }

  .mobile-price-section {
    .price-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: $white-alpha-03;
      border-radius: $border-radius-sm;
      padding: $spacing-sm;

      .price-item {
        flex: 1;
        text-align: center;

        .price-label {
          font-size: 0.75rem;
          color: $text-muted;
          margin-bottom: 4px;
        }

        .price-value {
          font-size: 1rem;
          font-weight: 600;
          font-family: 'Roboto Mono', monospace;
        }
      }

      .price-separator {
        font-size: 1.2rem;
        color: $primary;
        margin: 0 12px;
        font-weight: bold;
      }
    }
  }

  .mobile-info-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: $spacing-sm;

    .info-item {
      display: flex;
      align-items: center;
      padding: 8px;
      background: $white-alpha-02;
      border-radius: 6px;

      &.highlight {
        @include status-surface($positive);
      }

      .info-icon {
        font-size: 1.2rem;
        margin-right: 8px;
        color: $text-subtle;
        flex-shrink: 0;
      }

      .info-content {
        flex: 1;
        min-width: 0;
      }
    }
  }

  .text-mono {
    font-family: 'Roboto Mono', monospace;
  }
}

.match-details-table {
  :deep(.q-table__container) {
    background: transparent;
  }

  :deep(.q-table__middle) {
    max-height: 400px;
  }
}

// 📊 交易对每日盈亏展开面板样式
// --------------------------------------------------

.symbol-daily-content-wrapper {
  position: relative;
}

.symbol-daily-content {
  position: relative;
}

.symbol-daily-loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  background: rgb(255 255 255 / 65%);
  backdrop-filter: blur(6px);
  pointer-events: none;
  z-index: 1;

  .body--dark & {
    background: rgb(0 0 0 / 45%);
  }
}

.symbol-daily-expansion-list {
  .q-expansion-item {
    border-radius: $border-radius-md;
    margin-bottom: $spacing-sm;
    overflow: hidden;
    background: rgb(255 255 255 / 80%);
    backdrop-filter: blur(20px);
    border: 1px solid rgb(255 255 255 / 20%);

    .body--dark & {
      background: rgb(30 30 30 / 80%);
      border-color: $white-alpha-10;
    }

    .expansion-header {
      padding: $spacing-md $spacing-lg;
      border-radius: 12px 12px 0 0;

      &:hover {
        background: rgb(102 126 234 / 5%);
      }
  }
  }
}

.symbols-detail-container {
  background: $black-alpha-02;
  border-top: 1px solid $black-alpha-05;

  .body--dark & {
    background: $white-alpha-02;
    border-top-color: $white-alpha-05;
  }
}

.symbol-profit-item {
  padding: $spacing-md $spacing-lg;

  &:hover {
    background: rgb(102 126 234 / 3%);
  }

  .symbol-metrics {
    min-width: 300px;

    .metrics-grid {
      display: grid;
      grid-template-columns: 1fr 1fr 1fr;
      gap: 16px;
    }
  }
}

.no-data-container,
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
}

// 📱 移动端响应式
@media (width <= 768px) {
  .symbol-profit-item {
    padding: $spacing-sm $spacing-md;

    .symbol-metrics {
      min-width: auto;

      .metrics-grid {
        grid-template-columns: 1fr;
        gap: 8px;
      }
    }
  }

}
</style>
