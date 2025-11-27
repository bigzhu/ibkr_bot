<template>
  <q-page class="modern-page">
    <!-- 页面头部 -->
    <PageHeader
      title="交易对管理"
      subtitle="管理和监控所有交易对的状态,配置和信号强度"
      icon="currency_exchange"
      glow-type="pulse"
    >
      <template #actions>
        <ModernButton
          variant="outline"
          icon="percent"
          size="lg"
          @click="openBulkUpdateDialog"
        >
          批量修改
        </ModernButton>
        <ModernButton variant="gradient" icon="add" size="lg" @click="showAddDialog = true">
          添加交易对
        </ModernButton>
      </template>
    </PageHeader>

    <!-- 搜索和筛选卡片 -->
    <SymbolsFilterCard
      :search="searchQuery"
      :status="statusFilter"
      :status-options="statusOptions"
      @update:search="searchQuery = $event"
      @update:status="statusFilter = $event"
    />

    <!-- 交易对统计 -->
    <StatsCardsRow :cards="symbolStatsCards" :columns="3" :hide-on-small="false" />

    <!-- 交易对列表 - 使用 Expansion Item -->
    <LoadingState
      v-if="isLoading"
      class="q-pa-lg"
      message="加载交易对数据..."
      size="lg"
    />

    <q-list v-else-if="filteredSymbols.length > 0" separator class="symbols-expansion-list">
      <SymbolListItem
        v-for="symbol in filteredSymbols"
        :key="symbol.id"
        :symbol="symbol"
        :expanded="expandedSymbols.includes(symbol.symbol)"
        :active-config-count="getActiveConfigsCount(symbol.symbol)"
        :inactive-config-count="getInactiveConfigsCount(symbol.symbol)"
        @expand="(expanded) => onSymbolExpand(symbol.symbol, expanded)"
        @toggle-status="toggleSymbolStatus"
        @delete="confirmDeleteSymbol"
        @config-updated="onConfigUpdated"
      />
    </q-list>

    <!-- 空状态 -->
    <EmptyStateDisplay
      v-else
      type="config"
      title="暂无交易对"
      description="还没有添加任何交易对,点击下方按钮添加第一个交易对"
      size="lg"
    >
      <template #actions>
        <ModernButton variant="gradient" icon="add" @click="showAddDialog = true">
          添加交易对
        </ModernButton>
      </template>
    </EmptyStateDisplay>

    <!-- 批量配置更新对话框 -->
    <UniversalDialog
      v-model="showBulkUpdateDialog"
      type="custom"
      title="批量修改配置"
      subtitle="统一设置所有交易对的信号阈值与百分比"
      icon="percent"
      icon-color="accent"
      :responsive="true"
    >
      <template #content>
        <div class="bulk-form q-pa-sm q-pt-md">
          <div class="row q-col-gutter-md">
            <div class="col-12 col-sm-4">
              <ModernInput
                v-model.number="bulkDemarkBuy"
                label="买入信号值"
                placeholder="如: 1"
                type="number"
                step="1"
                min="1"
                max="50"
                variant="filled"
                :rules="[
                  (val) => val !== null && val !== '' || '请输入买入信号值',
                  (val) => val >= 1 || '必须大于等于1',
                  (val) => val <= 50 || '必须小于等于50',
                ]"
                help-text="统一设置所有配置的 DeMark 买入信号阈值"
              />
            </div>
            <div class="col-12 col-sm-4">
              <ModernInput
                v-model.number="bulkDemarkSell"
                label="卖出信号值"
                placeholder="如: 1"
                type="number"
                step="1"
                min="1"
                max="50"
                variant="filled"
                :rules="[
                  (val) => val !== null && val !== '' || '请输入卖出信号值',
                  (val) => val >= 1 || '必须大于等于1',
                  (val) => val <= 50 || '必须小于等于50',
                ]"
                help-text="统一设置所有配置的 DeMark 卖出信号阈值"
              />
            </div>
            <div class="col-12 col-sm-4">
              <ModernInput
                v-model.number="bulkMinimumProfit"
                label="利润百分比"
                placeholder="如: 0.44"
                type="number"
                step="0.01"
                min="0"
                max="100"
                suffix="%"
                variant="filled"
                :rules="[
                  (val) => val !== null && val !== '' || '请输入利润百分比',
                  (val) => val >= 0 || '必须大于等于0',
                  (val) => val <= 100 || '必须小于等于100',
                ]"
                help-text="统一设置所有配置的利润百分比"
              />
            </div>
            <div class="col-12 col-sm-4">
              <ModernInput
                v-model.number="bulkMonitorDelay"
                label="监控延迟"
                placeholder="如: 1"
                type="number"
                step="0.1"
                min="0"
                max="60"
                suffix="秒"
                variant="filled"
                :rules="[
                  (val) => val !== null && val !== '' || '请输入监控延迟',
                  (val) => val >= 0 || '必须大于等于0',
                  (val) => val <= 60 || '必须小于等于60',
                ]"
                help-text="统一设置所有配置的监控延迟时间"
              />
            </div>
          </div>
        </div>
      </template>
      <template #actions>
        <ModernButton variant="ghost" @click="showBulkUpdateDialog = false"> 取消 </ModernButton>
        <ModernButton
          variant="gradient"
          icon="save"
          :loading="isBulkUpdating"
          @click="submitBulkUpdate"
        >
          确认更新
        </ModernButton>
      </template>
    </UniversalDialog>

    <!-- 添加配置对话框 -->
    <UniversalDialog
      v-model="showAddDialog"
      type="custom"
      title="添加交易对配置"
      subtitle="配置新的交易对进行自动化交易"
      icon="add_circle"
      icon-color="positive"
      :responsive="true"
    >
      <template #content>
        <q-form @submit="addSymbolConfig" class="add-form">
          <ModernInput
            v-model="newSymbol.symbol"
            label="交易对符号"
            placeholder="如: TRXUSDC, ADAUSDC"
            prepend-icon="currency_exchange"
            variant="filled"
            :rules="[
              (val) => !!val || '请输入交易对',
              (val) => (val && val.length >= 5) || '交易对名称至少5个字符',
              (val) => (val && val.length <= 12) || '交易对名称最多12个字符',
            ]"
            help-text="请输入标准的交易对格式,如 ADAUSDC"
          />
        </q-form>
      </template>
      <template #actions>
        <ModernButton variant="ghost" @click="showAddDialog = false"> 取消 </ModernButton>
        <ModernButton variant="gradient" icon="add" :loading="isAdding" @click="addSymbolConfig">
          添加交易对
        </ModernButton>
      </template>
    </UniversalDialog>

    <!-- 删除确认对话框 -->
    <UniversalDialog
      v-model="showDeleteDialog"
      type="confirm-delete"
      title="确认删除交易对"
      subtitle="此操作不可恢复,请谨慎操作"
      icon="warning"
      confirm-message="您即将删除交易对: "
      :confirm-target="deleteDialogSymbol?.symbol"
      :require-input-confirmation="true"
      :input-placeholder="`请输入 ${deleteDialogSymbol?.symbol} 确认删除`"
      input-help-text="为防止误删,请输入完整的交易对名称"
      confirm-text="确认删除"
      confirm-button-icon="delete_forever"
      @confirm="handleDeleteConfirm"
    />
  </q-page>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { storeToRefs } from 'pinia';
import ModernButton from 'src/components/ModernButton.vue';
import ModernInput from 'src/components/ModernInput.vue';
import LoadingState from 'src/components/LoadingState.vue';
import StatsCardsRow from 'src/components/StatsCardsRow.vue';
import UniversalDialog from 'src/components/UniversalDialog.vue';
import PageHeader from 'src/components/PageHeader.vue';
import EmptyStateDisplay from 'src/components/EmptyStateDisplay.vue';
import SymbolsFilterCard from 'src/components/SymbolsFilterCard.vue';
import SymbolListItem from 'src/components/SymbolListItem.vue';
import { createStatsCards } from 'src/utils/stats-cards';
import type { ManagedSymbol } from 'src/types/symbols';
import { usePageLifecycle } from 'src/composables/usePageLifecycle';
import { apiService } from 'src/services';
import type { TimeframeConfigSummary, TimeframeBulkUpdatePayload } from 'src/services';
import { useQuasar } from 'quasar';
import { useSymbolsStore } from 'src/stores/symbols-store';

defineOptions({
  name: 'SymbolsPage',
});

const $q = useQuasar();
const symbolsStore = useSymbolsStore();

const { symbols: storeSymbols, symbolStats, stats: storeStats, loading: storeLoading } =
  storeToRefs(symbolsStore);

const searchQuery = ref('');
const statusFilter = ref<boolean | ''>('');
const showAddDialog = ref(false);
const showBulkUpdateDialog = ref(false);
const bulkDemarkBuy = ref<number | null>(1);
const bulkDemarkSell = ref<number | null>(1);
const bulkMinimumProfit = ref<number | null>(0.44);
const bulkMonitorDelay = ref<number | null>(1);
const isBulkUpdating = ref(false);
const isAdding = ref(false);
const showDeleteDialog = ref(false);
const deleteDialogSymbol = ref<ManagedSymbol | null>(null);
const expandedSymbols = ref<string[]>([]);
const userCollapsedActiveSymbols = ref<string[]>([]);
const newSymbol = ref({ symbol: '' });

const statusOptions: Array<{ label: string; value: boolean }> = [
  { label: '活跃', value: true },
  { label: '暂停', value: false },
];

interface BulkDialogValues {
  demarkBuy: number | null;
  demarkSell: number | null;
  profit: number | null;
  monitorDelay: number | null;
}

const defaultBulkValues: BulkDialogValues = {
  demarkBuy: 1,
  demarkSell: 1,
  profit: 0.44,
  monitorDelay: 1,
};

const initialBulkValues = ref<BulkDialogValues>({ ...defaultBulkValues });

const filteredSymbols = computed((): ManagedSymbol[] => {
  let filtered = storeSymbols.value;

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    filtered = filtered.filter((symbol) => symbol.symbol.toLowerCase().includes(query));
  }

  if (statusFilter.value !== '') {
    filtered = filtered.filter((symbol) => symbol.is_active === statusFilter.value);
  }

  return filtered;
});

const activeSymbolsCount = computed(() => storeStats.value.active);
const pausedSymbolsCount = computed(() => storeStats.value.inactive);

const symbolStatsCards = computed(() =>
  createStatsCards(
    [
      {
        value: storeStats.value.total,
        label: '总交易对',
        icon: 'trending_up',
        iconType: 'total',
      },
      {
        value: activeSymbolsCount.value,
        label: '活跃交易对',
        icon: 'play_circle',
        iconType: 'success',
      },
      {
        value: pausedSymbolsCount.value,
        label: '暂停交易对',
        icon: 'pause_circle',
        iconType: 'warning',
      },
    ],
    { preset: 'gradient' },
  ),
);

const removeFromCollapsed = (symbol: string) => {
  if (!userCollapsedActiveSymbols.value.length) {
    return;
  }

  userCollapsedActiveSymbols.value = userCollapsedActiveSymbols.value.filter(
    (item) => item !== symbol,
  );
};

const isSymbolActive = (symbol: string): boolean => {
  return storeSymbols.value.some((item) => item.symbol === symbol && item.is_active);
};

const onSymbolExpand = (symbol: string, expanded: boolean) => {
  if (expanded) {
    if (!expandedSymbols.value.includes(symbol)) {
      expandedSymbols.value.push(symbol);
    }
    removeFromCollapsed(symbol);
  } else {
    const index = expandedSymbols.value.indexOf(symbol);
    if (index > -1) {
      expandedSymbols.value.splice(index, 1);
    }

    if (isSymbolActive(symbol) && !userCollapsedActiveSymbols.value.includes(symbol)) {
      userCollapsedActiveSymbols.value = [...userCollapsedActiveSymbols.value, symbol];
    }
  }
};

const executeDeleteSymbol = async (symbol: ManagedSymbol) => {
  symbol.isDeleting = true;
  try {
    await symbolsStore.deleteSymbol(symbol);
    $q.notify({
      type: 'positive',
      message: `交易对 ${symbol.symbol} 已删除`,
    });
  } catch (error) {
    console.error('删除交易对失败:', error);
    $q.notify({
      type: 'negative',
      message: `删除失败: ${error instanceof Error ? error.message : '未知错误'}`,
    });
  } finally {
    symbol.isDeleting = false;
  }
};

const onConfigUpdated = () => {
  // 缓存已在 TimeframeConfigList 内更新, 此处无需额外刷新
};

const getActiveConfigsCount = (symbolName: string): number => {
  return symbolStats.value[symbolName]?.active || 0;
};

const getInactiveConfigsCount = (symbolName: string): number => {
  return symbolStats.value[symbolName]?.inactive || 0;
};

const loadSymbols = async (forceRefresh = false) => {
  await symbolsStore.fetchSymbols(forceRefresh);
};

const toggleSymbolStatus = async (symbol: ManagedSymbol) => {
  try {
    await symbolsStore.toggleSymbolStatus(symbol);
    $q.notify({
      type: 'positive',
      message: `${symbol.symbol} 状态已${symbol.is_active ? '启用' : '暂停'}`,
    });
  } catch (error) {
    console.error('Failed to toggle symbol status:', error);
    $q.notify({
      type: 'negative',
      message: `状态切换失败: ${error instanceof Error ? error.message : '未知错误'}`,
    });
  }
};


const confirmDeleteSymbol = (symbol: ManagedSymbol) => {
  deleteDialogSymbol.value = symbol;
  showDeleteDialog.value = true;
};

const handleDeleteConfirm = async () => {
  const symbol = deleteDialogSymbol.value;
  if (!symbol) {
    return;
  }

  await executeDeleteSymbol(symbol);
};

const toBoolean = (value: boolean | number | null | undefined): boolean => value === true || value === 1;

const deriveCurrentBulkValues = async (): Promise<BulkDialogValues> => {
  const defaultResult: BulkDialogValues = { ...defaultBulkValues };

  const selectBulkValues = (
    configs: Array<Omit<TimeframeConfigSummary, 'is_active'> & { is_active: boolean }>,
  ):
    | BulkDialogValues
    | null => {
    if (!configs.length) {
      return null;
    }

    const activeConfig = configs.find((config) => config.is_active);
    const targetConfig = activeConfig ?? configs[0];
    const demarkBuy = Number(targetConfig.demark_buy ?? 1);
    const demarkSell = Number(targetConfig.demark_sell ?? 1);
    const profit = Number(targetConfig.minimum_profit_percentage);
    const monitorDelay = Number(targetConfig.monitor_delay ?? 1);

    if (
      Number.isNaN(demarkBuy)
      || Number.isNaN(demarkSell)
      || Number.isNaN(profit)
      || Number.isNaN(monitorDelay)
    ) {
      return null;
    }

    return {
      demarkBuy,
      demarkSell,
      profit,
      monitorDelay,
    };
  };

  const fetchSymbolBulkValues = async (
    symbolName: string | undefined,
  ): Promise<
    | BulkDialogValues
    | null
  > => {
    if (!symbolName) {
      return null;
    }

    try {
      const response = await apiService.timeframeConfig.getConfigsBySymbol(symbolName);
      if (!response.success || !Array.isArray(response.configs)) {
        console.warn(`获取 ${symbolName} 配置失败: ${response.message ?? '未知错误'}`);
        return null;
      }
      const normalized = response.configs.map((config) => ({
        ...config,
        is_active: toBoolean(config.is_active),
      }));
      return selectBulkValues(normalized);
    } catch (error) {
      console.error(`获取 ${symbolName} 批量配置失败:`, error);
      return null;
    }
  };

  const activeSymbol = storeSymbols.value.find((symbol) => symbol.is_active);
  const activeValues = await fetchSymbolBulkValues(activeSymbol?.symbol);
  if (activeValues) {
    return activeValues;
  }

  const firstSymbol = storeSymbols.value[0];
  const fallbackValues = await fetchSymbolBulkValues(firstSymbol?.symbol);
  if (fallbackValues) {
    return fallbackValues;
  }

  return defaultResult;
};

const openBulkUpdateDialog = async () => {
  const { demarkBuy, demarkSell, profit, monitorDelay } =
    await deriveCurrentBulkValues();
  bulkDemarkBuy.value = demarkBuy;
  bulkDemarkSell.value = demarkSell;
  bulkMinimumProfit.value = profit;
  bulkMonitorDelay.value = monitorDelay;
  initialBulkValues.value = {
    demarkBuy,
    demarkSell,
    profit,
    monitorDelay,
  };
  showBulkUpdateDialog.value = true;
};

const submitBulkUpdate = async () => {
  const demarkBuyRaw = bulkDemarkBuy.value;
  const demarkSellRaw = bulkDemarkSell.value;
  const profitRaw = bulkMinimumProfit.value;
  const monitorDelayRaw = bulkMonitorDelay.value;

  const payload: TimeframeBulkUpdatePayload = {};

  if (profitRaw !== null && profitRaw !== undefined) {
    if (Number.isNaN(profitRaw) || profitRaw < 0 || profitRaw > 100) {
      $q.notify({
        type: 'negative',
        message: '请输入有效的利润百分比(0-100)',
        position: 'top',
      });
      return;
    }
    if (initialBulkValues.value.profit !== profitRaw) {
      payload.minimum_profit_percentage = profitRaw;
    }
  }

  if (demarkBuyRaw !== null && demarkBuyRaw !== undefined) {
    if (Number.isNaN(demarkBuyRaw) || demarkBuyRaw < 1 || demarkBuyRaw > 50) {
      $q.notify({
        type: 'negative',
        message: '请输入有效的买入信号值(1-50)',
        position: 'top',
      });
      return;
    }
    if (initialBulkValues.value.demarkBuy !== demarkBuyRaw) {
      payload.demark_buy = demarkBuyRaw;
    }
  }

  if (demarkSellRaw !== null && demarkSellRaw !== undefined) {
    if (Number.isNaN(demarkSellRaw) || demarkSellRaw < 1 || demarkSellRaw > 50) {
      $q.notify({
        type: 'negative',
        message: '请输入有效的卖出信号值(1-50)',
        position: 'top',
      });
      return;
    }
    if (initialBulkValues.value.demarkSell !== demarkSellRaw) {
      payload.demark_sell = demarkSellRaw;
    }
  }

  if (monitorDelayRaw !== null && monitorDelayRaw !== undefined) {
    if (Number.isNaN(monitorDelayRaw) || monitorDelayRaw < 0 || monitorDelayRaw > 60) {
      $q.notify({
        type: 'negative',
        message: '请输入有效的监控延迟(0-60秒)',
        position: 'top',
      });
      return;
    }
    if (initialBulkValues.value.monitorDelay !== monitorDelayRaw) {
      payload.monitor_delay = monitorDelayRaw;
    }
  }

  if (Object.keys(payload).length === 0) {
    $q.notify({
      type: 'info',
      message: '未检测到需要更新的字段',
      position: 'top',
    });
    return;
  }

  isBulkUpdating.value = true;
  try {
    const response = await apiService.timeframeConfig.bulkUpdateMinimumProfit(payload);
    if (!response.success) {
      throw new Error(response.message || '批量更新失败');
    }

    symbolsStore.clearTimeframeConfigCache();
    await loadSymbols(true);

    const summaryParts: string[] = [];
    if (payload.demark_buy !== undefined) {
      summaryParts.push(`买入信号值已更新为 ${payload.demark_buy}`);
    }
    if (payload.demark_sell !== undefined) {
      summaryParts.push(`卖出信号值已更新为 ${payload.demark_sell}`);
    }
    if (payload.minimum_profit_percentage !== undefined) {
      summaryParts.push(`利润百分比已更新为 ${payload.minimum_profit_percentage}%`);
    }
    if (payload.monitor_delay !== undefined) {
      summaryParts.push(`监控延迟已更新为 ${payload.monitor_delay}秒`);
    }

    $q.notify({
      type: 'positive',
      message: response.message || summaryParts.join(', '),
      position: 'top',
    });

    showBulkUpdateDialog.value = false;
  } catch (error) {
    console.error('批量更新配置失败:', error);
    $q.notify({
      type: 'negative',
      message: `批量更新失败: ${error instanceof Error ? error.message : '未知错误'}`,
      position: 'top',
    });
  } finally {
    isBulkUpdating.value = false;
  }
};

const addSymbolConfig = async () => {
  if (!newSymbol.value.symbol) {
    return;
  }

  isAdding.value = true;
  try {
    await symbolsStore.addSymbol({
      symbol: newSymbol.value.symbol,
      description: `${newSymbol.value.symbol} 交易对`,
      max_fund: null,
    });

    $q.notify({
      type: 'positive',
      message: '交易对添加成功',
    });

    showAddDialog.value = false;
    newSymbol.value = { symbol: '' };
  } catch (error) {
    console.error('Failed to add symbol:', error);
    let errorMessage = '添加交易对失败';

    if (error?.response?.data?.detail) {
      if (Array.isArray(error.response.data.detail)) {
        const validationErrors = error.response.data.detail
          .map((err: { loc?: unknown[]; msg: string }) => `${err.loc?.join('.') || '字段'}: ${err.msg}`)
          .join('; ');
        errorMessage = `验证失败: ${validationErrors}`;
      } else {
        errorMessage = error.response.data.detail;
      }
    } else if (error instanceof Error && error.message) {
      errorMessage = error.message;
    }

    $q.notify({
      type: 'negative',
      message: errorMessage,
    });
  } finally {
    isAdding.value = false;
  }
};

const { isLoading: lifecycleLoading } = usePageLifecycle({
  loadData: () => loadSymbols(false),
  refreshInterval: 0,
  requireAuth: true,
  pageName: '交易对管理',
  enableNetworkSync: false,
});

const isLoading = computed(() => lifecycleLoading.value || storeLoading.value);

watch(
  storeSymbols,
  (symbols) => {
    const activeSymbols = symbols.filter((symbol) => symbol.is_active).map((symbol) => symbol.symbol);
    const activeSet = new Set(activeSymbols);

    // 清理不再活跃的手动折叠状态
    if (userCollapsedActiveSymbols.value.length) {
      userCollapsedActiveSymbols.value = userCollapsedActiveSymbols.value.filter((symbol) =>
        activeSet.has(symbol),
      );
    }

    const collapsedSet = new Set(userCollapsedActiveSymbols.value);

    const nextExpanded = new Set(
      expandedSymbols.value.filter((symbol) => symbols.some((item) => item.symbol === symbol)),
    );

    for (const symbol of activeSymbols) {
      if (collapsedSet.has(symbol)) {
        nextExpanded.delete(symbol);
      } else {
        nextExpanded.add(symbol);
      }
    }

    expandedSymbols.value = Array.from(nextExpanded);
  },
  { immediate: true, deep: true },
);
</script>
