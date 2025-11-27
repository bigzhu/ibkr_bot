import { onActivated, onDeactivated, onMounted, onUnmounted, readonly, ref } from 'vue';
import type { Ref } from 'vue';

export interface BackgroundRefreshOptions {
  /** 异步刷新函数 */
  refresh: () => Promise<void> | void;
  /** 定时刷新间隔(毫秒),默认5分钟,<=0则不启用定时器 */
  interval?: number;
  /** 挂载时是否立即刷新,默认true */
  immediate?: boolean;
  /** KeepAlive 激活时是否立即刷新,默认true */
  immediateOnActivate?: boolean;
  /** 页面重新可见时是否立即刷新,默认true */
  runOnVisibilityGain?: boolean;
  /** 窗口获得焦点时是否刷新,默认true */
  runOnFocus?: boolean;
  /** 是否允许刷新,返回false时会跳过刷新 */
  enabled?: () => boolean;
}

export interface BackgroundRefreshHandle {
  /** 当前是否正在刷新 */
  isRefreshing: Readonly<Ref<boolean>>;
  /** 手动触发刷新 */
  refreshNow: () => Promise<void>;
  /** 手动启动定时器(会自动附加事件监听) */
  start: () => void;
  /** 暂停定时刷新 */
  stop: () => void;
}

const DEFAULT_INTERVAL = 5 * 60 * 1000; // 5分钟

export function useBackgroundRefresh(options: BackgroundRefreshOptions): BackgroundRefreshHandle {
  const {
    refresh,
    interval = DEFAULT_INTERVAL,
    immediate = true,
    immediateOnActivate = true,
    runOnVisibilityGain = true,
    runOnFocus = true,
    enabled,
  } = options;

  const hasWindow = typeof window !== 'undefined';
  const hasDocument = typeof document !== 'undefined';

  const isRefreshing = ref(false);
  let timer: number | null = null;
  let listenersAttached = false;

  const shouldRefresh = () => {
    if (enabled && !enabled()) {
      return false;
    }
    return true;
  };

  const runRefresh = async () => {
    if (!shouldRefresh()) {
      return;
    }
    if (isRefreshing.value) {
      return;
    }

    isRefreshing.value = true;
    try {
      await refresh();
    } finally {
      isRefreshing.value = false;
    }
  };

  const stopTimer = () => {
    if (!hasWindow) {
      return;
    }
    if (timer !== null) {
      window.clearInterval(timer);
      timer = null;
    }
  };

  const startTimer = () => {
    if (!hasWindow) {
      return;
    }
    if (interval <= 0 || timer !== null) {
      return;
    }
    timer = window.setInterval(() => {
      void runRefresh();
    }, interval);
  };

  const handleVisibilityChange = () => {
    if (!hasDocument) {
      return;
    }
    if (document.hidden) {
      stopTimer();
      return;
    }

    if (runOnVisibilityGain) {
      void runRefresh();
    }
    startTimer();
  };

  const handleFocus = () => {
    if (!runOnFocus) {
      return;
    }
    void runRefresh();
  };

  const attachListeners = () => {
    if (listenersAttached) {
      return;
    }
    if (hasDocument) {
      document.addEventListener('visibilitychange', handleVisibilityChange);
    }
    if (hasWindow && runOnFocus) {
      window.addEventListener('focus', handleFocus);
    }
    listenersAttached = true;
  };

  const detachListeners = () => {
    if (!listenersAttached) {
      return;
    }
    if (hasDocument) {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    }
    if (hasWindow && runOnFocus) {
      window.removeEventListener('focus', handleFocus);
    }
    listenersAttached = false;
  };

  const start = () => {
    attachListeners();
    startTimer();
  };

  const stop = () => {
    stopTimer();
  };

  onMounted(() => {
    if (!hasWindow) {
      return;
    }
    start();
    if (immediate) {
      void runRefresh();
    }
  });

  onActivated(() => {
    if (!hasWindow) {
      return;
    }
    startTimer();
    if (immediateOnActivate) {
      void runRefresh();
    }
  });

  onDeactivated(() => {
    stopTimer();
  });

  onUnmounted(() => {
    stopTimer();
    detachListeners();
  });

  return {
    isRefreshing: readonly(isRefreshing),
    refreshNow: async () => {
      await runRefresh();
    },
    start,
    stop,
  };
}
