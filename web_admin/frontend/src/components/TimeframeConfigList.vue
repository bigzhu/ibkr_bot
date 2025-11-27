<template>
  <div class="timeframe-config-list">
    <!-- 加载状态 -->
    <LoadingState
      v-if="isLoading"
      class="q-pa-md"
      message="加载时间周期配置..."
    />

    <!-- 配置列表 -->
    <div v-else-if="configs.length > 0" class="configs-container">
      <!-- 配置表格 -->
      <q-table
        :rows="configs"
        :columns="columns"
        row-key="id"
        dense
        flat
        :hide-pagination="true"
        :rows-per-page-options="[0]"
        table-class="table-auto"
        class="timeframe-config-table"
      >
        <!-- 时间周期列 -->
        <template v-slot:body-cell-kline_timeframe="props">
          <q-td
            :props="props"
            :class="{ 'disabled-cell': !props.row.is_active }"
            class="text-right"
          >
            <div :class="{ 'disabled-chip': !props.row.is_active }">
              <TimeframeChip :timeframe="props.value" />
            </div>
          </q-td>
        </template>



        <!-- 状态列 -->
        <template v-slot:body-cell-is_active="props">
          <q-td
            :props="props"
            :class="{ 'disabled-cell': !props.row.is_active }"
            class="text-right"
          >
            <q-toggle
              :model-value="props.value"
              @update:model-value="toggleConfigStatus(props.row)"
              :loading="props.row.isToggling"
              color="positive"
              size="sm"
            />
            <span class="q-ml-xs text-caption">
              {{ props.value ? '启用' : '禁用' }}
            </span>
          </q-td>
        </template>

        <!-- 买入信号值列 -->
        <template v-slot:body-cell-demark_buy="props">
          <TableCell :props="props" :is-active="props.row.is_active">
            <q-input
              :model-value="props.value"
              @update:model-value="updateBuySignalValue(props.row, $event)"
              @blur="saveConfig(props.row)"
              type="number"
              dense
              min="1"
              max="100"
              borderless
              input-class="text-right"
              class="signal-input"
            />
          </TableCell>
        </template>

        <!-- 卖出信号值列 -->
        <template v-slot:body-cell-demark_sell="props">
          <TableCell :props="props" :is-active="props.row.is_active">
            <q-input
              :model-value="props.value"
              @update:model-value="updateSellSignalValue(props.row, $event)"
              @blur="saveConfig(props.row)"
              type="number"
              dense
              min="1"
              max="100"
              borderless
              input-class="text-right"
              class="signal-input"
            />
          </TableCell>
        </template>





        <!-- 利润百分比列 -->
        <template v-slot:body-cell-minimum_profit_percentage="props">
          <TableCell :props="props" :is-active="props.row.is_active">
            <PercentageInput
              :model-value="props.value"
              @update:model-value="updateMinimumProfitPercentage(props.row, $event)"
              @blur="saveConfig(props.row)"
              :disabled="!props.row.is_active"
            />
          </TableCell>
        </template>


        <!-- 监控延迟列 -->
        <template v-slot:body-cell-monitor_delay="props">
          <TableCell :props="props" :is-active="props.row.is_active">
            <MonitorDelayInput
              :model-value="props.value"
              @update:model-value="updateMonitorDelay(props.row, $event)"
              @blur="saveConfig(props.row)"
              :disabled="!props.row.is_active"
            />
          </TableCell>
        </template>

        <!-- 操作模式列 -->
        <template v-slot:body-cell-oper_mode="props">
          <TableCell :props="props" :is-active="props.row.is_active">
            <q-select
              :model-value="props.value"
              @update:model-value="updateOperMode(props.row, $event)"
              :options="operModeOptions"
              emit-value
              map-options
              dense
              borderless
              class="oper-mode-select"
            />
          </TableCell>
        </template>
      </q-table>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-state q-pa-lg text-center">
      <q-icon name="schedule" size="3rem" color="grey-4" class="q-mb-md" />
      <div class="text-h6 text-grey-6 q-mb-sm">暂无时间周期配置</div>
      <div class="text-body2 text-grey-5">该交易对还没有配置任何时间周期参数</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import PercentageInput from './PercentageInput.vue';
import MonitorDelayInput from './MonitorDelayInput.vue';
import TableCell from './TableCell.vue';
import TimeframeChip from './TimeframeChip.vue';
import LoadingState from './LoadingState.vue';
import { useQuasar } from 'quasar';
import { apiService } from 'src/services';
import type { TimeframeConfigSummary, TimeframeConfigUpdatePayload } from 'src/services';
import { useSymbolsStore } from 'src/stores/symbols-store';

// Props 定义
interface Props {
  symbol: string;
  expanded?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  expanded: false,
});

// Emits 定义
const emit = defineEmits<{
  configUpdated: [symbol: string];
}>();

const $q = useQuasar();
const symbolsStore = useSymbolsStore();

// 响应式数据
const isLoading = ref(false);

interface TimeframeConfig extends Required<Omit<TimeframeConfigSummary, 'oper_mode' | 'is_active'>> {
  oper_mode: string;
  isToggling: boolean;
  isSaving: boolean;
  is_active: boolean;
}

type NumericInput = string | number | null | undefined;

const configs = ref<TimeframeConfig[]>([]);

// 操作模式选项
const operModeOptions = [
  { label: '双向', value: 'all' },
  { label: '仅买入', value: 'buy_only' },
  { label: '仅卖出', value: 'sell_only' },
];

// 表格列定义
const columns = [
  {
    name: 'kline_timeframe',
    label: '时间周期',
    field: 'kline_timeframe',
    align: 'right',
    sortable: true,
    headerStyle: 'text-align: right',
  },

  {
    name: 'demark_buy',
    label: '买入信号值',
    field: 'demark_buy',
    align: 'right',
    sortable: true,
    headerStyle: 'text-align: right',
  },
  {
    name: 'demark_sell',
    label: '卖出信号值',
    field: 'demark_sell',
    align: 'right',
    sortable: true,
    headerStyle: 'text-align: right',
  },

  {
    name: 'minimum_profit_percentage',
    label: '利润百分比',
    field: 'minimum_profit_percentage',
    align: 'right',
    sortable: true,
    headerStyle: 'text-align: right',
  },

  {
    name: 'monitor_delay',
    label: '延迟',
    field: 'monitor_delay',
    align: 'right' as const,
    sortable: true,
    headerStyle: 'text-align: right',
  },
  {
    name: 'oper_mode',
    label: '操作模式',
    field: 'oper_mode',
    align: 'right',
    headerStyle: 'text-align: right',
  },
  {
    name: 'is_active',
    label: '状态',
    field: 'is_active',
    align: 'right',
    headerStyle: 'text-align: right',
  },
];

// 计算属性
// 加载配置数据
const toManagedConfig = (config: TimeframeConfigSummary): TimeframeConfig => ({
  id: config.id,
  kline_timeframe: config.kline_timeframe,
  demark_buy: config.demark_buy ?? 9,
  demark_sell: config.demark_sell ?? 9,
  minimum_profit_percentage: config.minimum_profit_percentage ?? 0,

  monitor_delay: config.monitor_delay ?? 0,
  oper_mode: config.oper_mode ?? 'all',
  is_active: Boolean(config.is_active),
  isToggling: false,
  isSaving: false,
});

const loadConfigs = async (forceRefresh = false) => {
  if (!props.symbol) return;

  isLoading.value = true;
  try {
    const configsData = await symbolsStore.fetchTimeframeConfigs(props.symbol, forceRefresh);
    configs.value = configsData.map(toManagedConfig);
  } catch (error) {
    console.error('Failed to load timeframe configs:', error);
    const message = apiService.handleError(error);
    $q.notify({
      type: 'negative',
      message: '加载时间周期配置失败',
      caption: message,
    });
  } finally {
    isLoading.value = false;
  }
};

const parseNumber = (value: NumericInput, defaultValue = 0): number => {
  if (value === null || value === undefined || value === '') {
    return defaultValue;
  }
  const parsed = typeof value === 'string' ? Number.parseFloat(value) : value;
  return Number.isNaN(parsed) ? defaultValue : parsed;
};

// 切换配置状态
const toggleConfigStatus = async (config: TimeframeConfig) => {
  if (config.isToggling || config.isSaving) {
    return;
  }

  config.isToggling = true;
  try {
    const nextStatus = !config.is_active;
    const result = await apiService.timeframeConfig.updateConfig(config.id, {
      is_active: nextStatus,
    });

    if (result.success) {
      config.is_active = nextStatus;
      symbolsStore.applyTimeframeConfigPatch(props.symbol, config.id, { is_active: nextStatus });
      emit('configUpdated', props.symbol);
      $q.notify({
        type: 'positive',
        message: `时间周期 ${config.kline_timeframe} ${config.is_active ? '已启用' : '已禁用'}`,
      });
    } else {
      throw new Error(result.message || 'Failed to update config');
    }
  } catch (error) {
    console.error('Failed to toggle config status:', error);
    const message = apiService.handleError(error);
    $q.notify({
      type: 'negative',
      message: '更新配置状态失败',
      caption: message,
    });
  } finally {
    config.isToggling = false;
  }
};

// 更新买入信号值
const updateBuySignalValue = (config: TimeframeConfig, value: NumericInput) => {
  const numericValue = parseNumber(value, config.demark_buy);
  if (numericValue >= 1 && numericValue <= 100) {
    config.demark_buy = Math.round(numericValue);
  }
};

// 更新卖出信号值
const updateSellSignalValue = (config: TimeframeConfig, value: NumericInput) => {
  const numericValue = parseNumber(value, config.demark_sell);
  if (numericValue >= 1 && numericValue <= 100) {
    config.demark_sell = Math.round(numericValue);
  }
};

// 移除每日最大百分比字段相关交互



// 更新利润百分比
const updateMinimumProfitPercentage = (config: TimeframeConfig, value: number) => {
  config.minimum_profit_percentage = value;
};



// 更新监控延迟
const updateMonitorDelay = (config: TimeframeConfig, value: NumericInput) => {
  const numericValue = parseNumber(value, config.monitor_delay);
  if (numericValue >= 0) {
    config.monitor_delay = numericValue;
  }
};

// 更新操作模式
const updateOperMode = (config: TimeframeConfig, value: string) => {
  config.oper_mode = value;
  // 操作模式改变后立即保存
  void saveConfig(config);
};

// 保存配置
const saveConfig = async (config: TimeframeConfig) => {
  if (config.isSaving || config.isToggling) {
    return;
  }

  config.isSaving = true;
  try {
    const payload: TimeframeConfigUpdatePayload = {
      demark_buy: config.demark_buy,
      demark_sell: config.demark_sell,
      minimum_profit_percentage: config.minimum_profit_percentage,

      monitor_delay: config.monitor_delay,
      oper_mode: config.oper_mode,
    };

    const result = await apiService.timeframeConfig.updateConfig(config.id, payload);

    if (result.success) {
      const patch: Partial<TimeframeConfigSummary> = {};
      if (payload.demark_buy !== undefined) patch.demark_buy = payload.demark_buy;
      if (payload.demark_sell !== undefined) patch.demark_sell = payload.demark_sell;

      if (payload.monitor_delay !== undefined) {
        patch.monitor_delay = payload.monitor_delay;
      }
      if (payload.oper_mode !== undefined) {
        patch.oper_mode = payload.oper_mode;
      }

      symbolsStore.applyTimeframeConfigPatch(props.symbol, config.id, patch);

      emit('configUpdated', props.symbol);
      $q.notify({
        type: 'positive',
        message: `配置已保存`,
        timeout: 1000,
      });
    } else {
      throw new Error(result.message || 'Failed to save config');
    }
  } catch (error) {
    console.error('Failed to save config:', error);
    const message = apiService.handleError(error);
    $q.notify({
      type: 'negative',
      message: '保存配置失败',
      caption: message,
    });
  } finally {
    config.isSaving = false;
  }
};

// 监听展开状态,展开时加载数据
watch(
  () => props.expanded,
  (expanded) => {
    if (expanded) {
      void loadConfigs();
    }
  },
);

// 监听交易对变化
watch(
  () => props.symbol,
  () => {
    if (props.expanded) {
      void loadConfigs();
    }
  },
);

// 组件挂载时如果已展开则加载数据
onMounted(() => {
  if (props.expanded) {
    void loadConfigs();
  }
});
</script>

<style lang="scss" scoped>
@import 'src/css/quasar.variables';

.timeframe-config-list {
  .timeframe-config-table {
    :deep(.q-table thead th) {
      background: $white-alpha-05;
      color: $text-muted;
      font-weight: 500;
    }

    :deep(.q-table tbody td) {
      border-color: $white-alpha-10;
    }

    :deep(.q-table tbody tr:hover) {
      background: $white-alpha-03;
    }

    :deep(.disabled-cell) {
      opacity: 0.4 !important;

      * {
        opacity: 0.6 !important;
      }
    }

    :deep(.disabled-chip) {
      opacity: 0.6 !important;
      filter: grayscale(30%);
    }

    // 右对齐列的排序图标应该在文字右边
    :deep(.q-table thead th.text-right) {
      .q-table__sort-icon {
        margin-left: 4px;
        margin-right: 0;
      }
    }
  }

  .oper-mode-select {
    :deep(.q-field__native) {
      justify-content: flex-end !important;
    }

    :deep(.ellipsis) {
      text-align: right !important;
      width: 100% !important;
    }
  }
}
</style>
