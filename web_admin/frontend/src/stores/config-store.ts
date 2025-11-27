import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { api } from 'src/services';

export interface BinanceConfig {
  api_key: string;
  secret_key: string;
  has_api_key: boolean;
  has_secret_key: boolean;
  is_configured: boolean;
  environment_name: string;
}

export interface SystemInfo {
  version: string;
  uptime: string;
  last_restart: string;
  python_version: string;
  dependencies: { [key: string]: string };
}

export const useConfigStore = defineStore(
  'config-store',
  () => {
    // 状态
    const binanceConfig = ref<BinanceConfig>({
      api_key: '',
      secret_key: '',
      has_api_key: false,
      has_secret_key: false,
      is_configured: false,
      environment_name: 'unknown',
    });

    const logLevel = ref<string>('INFO');
    const systemInfo = ref<SystemInfo>({
      version: 'v1.0.0',
      uptime: '0 days',
      last_restart: 'Unknown',
      python_version: '3.11+',
      dependencies: {},
    });

    const loading = ref(false);
    const lastFetchTime = ref<number>(0);
    const cacheTimeout = 5 * 60 * 1000; // 5分钟缓存

    // 计算属性
    const isConfigured = computed(() => binanceConfig.value.is_configured);
    const needsConfiguration = computed(
      () => !binanceConfig.value.has_api_key || !binanceConfig.value.has_secret_key,
    );

    // 方法 - 检查是否需要刷新
    const needsRefresh = (): boolean => {
      return Date.now() - lastFetchTime.value > cacheTimeout || !binanceConfig.value.api_key;
    };

    // 方法 - 获取Binance配置状态
    const fetchBinanceConfig = async (forceRefresh = false): Promise<void> => {
      if (!forceRefresh && !needsRefresh()) {
        return;
      }

      loading.value = true;
      try {
        const response = await api.get('/api/v1/config/binance/status');

        if (response.data?.success && response.data?.data) {
          binanceConfig.value = {
            api_key: response.data.data.api_key || '',
            secret_key: response.data.data.secret_key || '',
            has_api_key: response.data.data.has_api_key || false,
            has_secret_key: response.data.data.has_secret_key || false,
            is_configured: response.data.data.is_configured || false,
            environment_name: response.data.data.environment_name || 'unknown',
          };
          lastFetchTime.value = Date.now();
        } else {
          console.warn('⚠️ 获取Binance配置失败:', response.data);
        }
      } catch (error) {
        console.error('❌ 获取Binance配置出错:', error);
      } finally {
        loading.value = false;
      }
    };

    // 方法 - 获取日志级别
    const fetchLogLevel = async (): Promise<void> => {
      try {
        const response = await api.get('/api/v1/config/log-level');

        if (response.data?.success) {
          logLevel.value = response.data.log_level || 'INFO';
        } else {
          console.warn('⚠️ 获取日志级别失败:', response.data);
        }
      } catch (error) {
        console.error('❌ 获取日志级别出错:', error);
      }
    };

    // 方法 - 验证Binance API
    const validateBinanceAPI = async (config: { api_key: string; secret_key: string }) => {
      loading.value = true;
      try {
        const response = await api.post('/api/v1/config/binance/validate', config);
        return response.data;
      } catch (error) {
        console.error('❌ 验证Binance API出错:', error);
        throw error;
      } finally {
        loading.value = false;
      }
    };

    // 方法 - 保存Binance配置
    const saveBinanceConfig = async (config: { api_key: string; secret_key: string }) => {
      loading.value = true;
      try {
        const response = await api.post('/api/v1/config/binance/save', config);

        if (response.data?.success) {
          // 更新本地状态
          await fetchBinanceConfig(true); // 强制刷新配置状态
        }

        return response.data;
      } catch (error) {
        console.error('❌ 保存Binance配置出错:', error);
        throw error;
      } finally {
        loading.value = false;
      }
    };

    // 方法 - 更新日志级别
    const updateLogLevel = async (level: string) => {
      try {
        const response = await api.put('/api/v1/config/log-level', { log_level: level });

        if (response.data?.success) {
          logLevel.value = level;
        }

        return response.data;
      } catch (error) {
        console.error('❌ 更新日志级别出错:', error);
        throw error;
      }
    };

    // 方法 - 刷新所有配置
    const refreshAllConfig = async (): Promise<void> => {
      await Promise.all([fetchBinanceConfig(true), fetchLogLevel()]);
    };

    // 方法 - 清除敏感配置(用于登出时)
    const clearSensitiveData = () => {
      binanceConfig.value = {
        api_key: '',
        secret_key: '',
        has_api_key: false,
        has_secret_key: false,
        is_configured: false,
        environment_name: 'unknown',
      };
      lastFetchTime.value = 0;
    };

    return {
      // 状态
      binanceConfig,
      logLevel,
      systemInfo,
      loading,

      // 计算属性
      isConfigured,
      needsConfiguration,

      // 方法
      fetchBinanceConfig,
      fetchLogLevel,
      validateBinanceAPI,
      saveBinanceConfig,
      updateLogLevel,
      refreshAllConfig,
      clearSensitiveData,
      needsRefresh,
    };
  },
  {
    persist: {
      key: 'config-store',
      storage: localStorage,
      // 只持久化非敏感数据和状态信息
      paths: ['logLevel', 'systemInfo', 'lastFetchTime'],
    },
  },
);
