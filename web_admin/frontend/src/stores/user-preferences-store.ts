import { defineStore } from 'pinia';
import { ref } from 'vue';

// 用户偏好设置接口定义
export interface TablePreferences {
  [pageName: string]: {
    columnVisibility?: { [columnName: string]: boolean };
    sortBy?: string;
    sortOrder?: 'asc' | 'desc';
    rowsPerPage?: number;
    density?: 'compact' | 'comfortable' | 'spacious';
  };
}

export type FilterPreferences = Record<string, Record<string, unknown>>;

export interface InterfacePreferences {
  autoRefreshInterval: number;
  autoRefreshEnabled: boolean;
  showRefreshNotifications: boolean;
  compactMode: boolean;
  showPerformanceMetrics: boolean;
  defaultPage: string;
}

export interface DataPreferences {
  pricePrecision: number;
  quantityPrecision: number;
  percentagePrecision: number;
  showCurrencySymbol: boolean;
  timeFormat: string;
  defaultDateRange: number;
}

interface PreferencesSnapshot {
  theme: 'light' | 'dark';
  tablePreferences: TablePreferences;
  filterPreferences: FilterPreferences;
  interfacePreferences: InterfacePreferences;
  dataPreferences: DataPreferences;
  exportTime: string;
}

export const useUserPreferencesStore = defineStore(
  'user-preferences',
  () => {
    // 主题偏好
    const theme = ref<'light' | 'dark'>('light');

    // 表格偏好设置
    const tablePreferences = ref<TablePreferences>({
      dashboard: {
        rowsPerPage: 5,
        density: 'comfortable',
      },
      symbols: {
        rowsPerPage: 20,
        sortBy: 'symbol',
        sortOrder: 'asc',
      },
      binanceOrders: {
        rowsPerPage: 50,
        sortBy: 'time',
        sortOrder: 'desc',
      },
      profitAnalysis: {
        rowsPerPage: 100,
        density: 'compact',
      },
      logs: {
        rowsPerPage: 50,
        sortBy: 'created_at',
        sortOrder: 'desc',
      },
    });

    // 筛选条件偏好
    const filterPreferences = ref<FilterPreferences>({
      symbols: {
        searchQuery: '',
        statusFilter: '',
        showActiveOnly: false,
      },
      logs: {
        symbolFilter: '',
        actionTypeFilter: '',
        resultFilter: '',
        timeRangeFilter: 'today',
      },
      profitAnalysis: {
        selectedDate: '',
        symbolFilter: '',
        orderNoFilter: '',
      },
    });

    // 界面偏好设置
    const interfacePreferences = ref<InterfacePreferences>({
      // 自动刷新间隔(秒)
      autoRefreshInterval: 30,
      // 是否启用自动刷新
      autoRefreshEnabled: true,
      // 数据刷新提示
      showRefreshNotifications: true,
      // 紧凑模式
      compactMode: false,
      // 显示性能指标
      showPerformanceMetrics: false,
      // 默认页面
      defaultPage: '/dashboard',
    });

    // 数据显示偏好
    const dataPreferences = ref<DataPreferences>({
      // 数字显示精度
      pricePrecision: 2,
      quantityPrecision: 6,
      percentagePrecision: 2,
      // 货币符号显示
      showCurrencySymbol: true,
      // 时间格式
      timeFormat: 'zh-CN', // 'zh-CN', 'en-US', 'ISO'
      // 日期范围默认值
      defaultDateRange: 30, // 天数
    });

    // 方法 - 更新表格偏好
    const updateTablePreference = (
      pageName: string,
      preferences: Partial<TablePreferences[string]>,
    ) => {
      if (!tablePreferences.value[pageName]) {
        tablePreferences.value[pageName] = {};
      }
      Object.assign(tablePreferences.value[pageName], preferences);
    };

    // 方法 - 更新筛选偏好
    const updateFilterPreference = (pageName: string, filterName: string, value: unknown) => {
      if (!filterPreferences.value[pageName]) {
        filterPreferences.value[pageName] = {};
      }
      filterPreferences.value[pageName][filterName] = value;
    };

    // 方法 - 获取表格偏好
    const getTablePreference = (pageName: string, key?: string) => {
      const pagePrefs = tablePreferences.value[pageName];
      if (!pagePrefs) return undefined;
      return key ? pagePrefs[key as keyof typeof pagePrefs] : pagePrefs;
    };

    // 方法 - 获取筛选偏好
    const getFilterPreference = (pageName: string, filterName: string) => {
      return filterPreferences.value[pageName]?.[filterName];
    };

    // 方法 - 重置所有偏好
    const resetAllPreferences = () => {
      theme.value = 'light';
      tablePreferences.value = {};
      filterPreferences.value = {};
      interfacePreferences.value = {
        autoRefreshInterval: 30,
        autoRefreshEnabled: true,
        showRefreshNotifications: true,
        compactMode: false,
        showPerformanceMetrics: false,
        defaultPage: '/dashboard',
      };
      dataPreferences.value = {
        pricePrecision: 2,
        quantityPrecision: 6,
        percentagePrecision: 2,
        showCurrencySymbol: true,
        timeFormat: 'zh-CN',
        defaultDateRange: 30,
      };
    };

    // 方法 - 导出偏好设置(用于备份)
    const exportPreferences = (): PreferencesSnapshot => {
      return {
        theme: theme.value,
        tablePreferences: tablePreferences.value,
        filterPreferences: filterPreferences.value,
        interfacePreferences: interfacePreferences.value,
        dataPreferences: dataPreferences.value,
        exportTime: new Date().toISOString(),
      };
    };

    // 方法 - 导入偏好设置(用于恢复)
    const importPreferences = (preferences: Partial<PreferencesSnapshot>) => {
      if (preferences.theme) {
        theme.value = preferences.theme;
      }
      if (preferences.tablePreferences) {
        tablePreferences.value = { ...preferences.tablePreferences };
      }
      if (preferences.filterPreferences) {
        filterPreferences.value = { ...preferences.filterPreferences };
      }
      if (preferences.interfacePreferences) {
        interfacePreferences.value = { ...preferences.interfacePreferences };
      }
      if (preferences.dataPreferences) {
        dataPreferences.value = { ...preferences.dataPreferences };
      }
    };

    return {
      // 状态
      theme,
      tablePreferences,
      filterPreferences,
      interfacePreferences,
      dataPreferences,

      // 方法
      updateTablePreference,
      updateFilterPreference,
      getTablePreference,
      getFilterPreference,
      resetAllPreferences,
      exportPreferences,
      importPreferences,
    };
  },
  {
    persist: {
      key: 'user-preferences',
      storage: localStorage,
      // 持久化所有状态,但不持久化方法
      paths: [
        'theme',
        'tablePreferences',
        'filterPreferences',
        'interfacePreferences',
        'dataPreferences',
      ],
    },
  },
);
