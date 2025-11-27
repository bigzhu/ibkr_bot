import { onMounted, onUnmounted, onActivated, onDeactivated, ref } from 'vue';
import { useQuasar } from 'quasar';
import { useRouter } from 'vue-router';

interface PageLifecycleOptions {
  /** 数据加载函数 */
  loadData: () => Promise<void>;
  /** 刷新间隔 (毫秒),默认30秒 */
  refreshInterval?: number;
  /** 是否需要认证检查,默认true */
  requireAuth?: boolean;
  /** 页面名称,用于日志输出 */
  pageName?: string;
  /** 是否启用网络同步监听,默认false */
  enableNetworkSync?: boolean;
}

/**
 * 页面生命周期管理组合式函数
 * 统一处理:认证检查,数据加载,后台刷新,事件监听,资源清理
 */
export function usePageLifecycle(options: PageLifecycleOptions) {
  const {
    loadData,
    refreshInterval = 30 * 1000, // 默认30秒
    requireAuth = true,
    pageName = '页面',
    enableNetworkSync = false,
  } = options;

  const $q = useQuasar();
  const router = useRouter();

  // 定时器和事件监听器引用
  let refreshTimer: number | null = null;
  let visibilityListener: (() => void) | null = null;
  let networkSyncListener: ((event: CustomEvent) => void) | null = null;

  // 加载状态
  const isLoading = ref(false);

  /**
   * 带错误处理的数据加载函数
   */
  const safeLoadData = async () => {
    try {
      isLoading.value = true;
      await loadData();
    } catch (error) {
      console.error(`${pageName}数据加载失败:`, error);
      $q.notify({
        type: 'warning',
        message: `${pageName}数据加载失败,请检查网络连接`,
        position: 'top',
        timeout: 3000,
      });
    } finally {
      isLoading.value = false;
    }
  };

  /**
   * 智能数据加载函数 - 只在必要时重新加载
   */
  const smartLoadData = async () => {
    // 如果正在加载中,跳过
    if (isLoading.value) {
      return;
    }

    await safeLoadData();
  };

  /**
   * 启动定时器
   */
  const startTimer = () => {
    if (refreshTimer) clearInterval(refreshTimer);

    // 只有当refreshInterval大于0时才启动定时器
    if (refreshInterval > 0) {
      refreshTimer = window.setInterval(() => {
        if (!document.hidden) {
          void smartLoadData();
        }
      }, refreshInterval);
    }
  };

  /**
   * 设置后台刷新机制
   */
  const setupBackgroundRefresh = () => {
    // 1. 页面可见性变化监听
    visibilityListener = () => {
      if (!document.hidden) {
        // 只在页面重新可见时启动定时器,不立即刷新数据
        startTimer();
      } else {
        if (refreshTimer) {
          clearInterval(refreshTimer);
          refreshTimer = null;
        }
      }
    };

    // 2. 网络数据同步监听(可选)
    if (enableNetworkSync) {
      networkSyncListener = () => {
        void smartLoadData();
      };
    }

    // 添加事件监听器
    document.addEventListener('visibilitychange', visibilityListener);

    if (networkSyncListener) {
      window.addEventListener('network-data-sync', networkSyncListener as EventListener);
    }

    // 启动定时器
    startTimer();
  };

  /**
   * 清理所有资源
   */
  const cleanup = () => {
    // 清理定时器
    if (refreshTimer) {
      clearInterval(refreshTimer);
      refreshTimer = null;
    }

    // 清理事件监听器
    if (visibilityListener) {
      document.removeEventListener('visibilitychange', visibilityListener);
      visibilityListener = null;
    }

    if (networkSyncListener) {
      window.removeEventListener('network-data-sync', networkSyncListener as EventListener);
      networkSyncListener = null;
    }
  };

  /**
   * 认证检查
   */
  const checkAuth = (): boolean => {
    if (!requireAuth) return true;

    const token = localStorage.getItem('auth_token');
    if (!token) {
      $q.notify({
        type: 'negative',
        message: '请先登录',
        position: 'top',
      });
      void router.push('/login');
      return false;
    }
    return true;
  };

  /**
   * 页面初始化
   */
  const initialize = async () => {
    // 认证检查
    if (!checkAuth()) return;

    // 初始数据加载
    await safeLoadData();

    // 设置后台刷新机制
    setupBackgroundRefresh();

  };

  // 页面挂载时初始化
  onMounted(() => {
    void initialize();
  });

  // KeepAlive: 页面激活/失活时控制后台刷新
  onActivated(() => {
    // 页面重新可见或被激活时,重启定时器但不强制刷新
    startTimer();
  });

  onDeactivated(() => {
    // 页面失活时,停止定时器,避免在后台继续拉取数据
    if (refreshTimer) {
      clearInterval(refreshTimer);
      refreshTimer = null;
    }
  });

  // 页面卸载时清理资源
  onUnmounted(() => {
    cleanup();
  });

  return {
    /** 是否正在加载数据 */
    isLoading,
    /** 手动刷新数据 */
    refreshData: safeLoadData,
    /** 手动启动定时器 */
    startTimer,
    /** 手动停止定时器 */
    stopTimer: () => {
      if (refreshTimer) {
        clearInterval(refreshTimer);
        refreshTimer = null;
      }
    },
    /** 手动清理资源 */
    cleanup,
  };
}
