/**
 * Quasar 缓存系统启动文件
 * 注册全局缓存管理器并设置自动清理机制
 */

import { boot } from 'quasar/wrappers';
import { cacheManager } from 'src/utils/cache-manager';

export default boot(({ app }) => {
  // 全局注入缓存管理器
  app.config.globalProperties.$cache = cacheManager;
  app.provide('cache', cacheManager);

  // 应用启动时清理过期缓存
  const cleanup = cacheManager.cleanup();
  if (cleanup.removed > 0) {
    console.info(`🧹 已清理 ${cleanup.removed} 条过期缓存`);
  }
  if (cleanup.errors.length > 0) {
    console.warn('缓存清理错误:', cleanup.errors);
  }

  // 设置定期清理(每5分钟清理一次过期缓存)
  const cleanupInterval = setInterval(
    () => {
      const result = cacheManager.cleanup();
      if (result.removed > 0) {
        console.info(`🧹 定时清理缓存: ${result.removed} 条过期数据已移除`);
      }
    },
    5 * 60 * 1000,
  );

  // 页面卸载时清理定时器
  window.addEventListener('beforeunload', () => {
    clearInterval(cleanupInterval);
  });

  // 网络状态监听
  // 内存不足时清理缓存
  if ('memory' in performance) {
    let lastCleanupTime = 0;
    const checkMemory = () => {
      const memInfo = (
        performance as { memory?: { usedJSHeapSize: number; totalJSHeapSize: number } }
      ).memory;
      if (memInfo) {
        const usedMemory = memInfo.usedJSHeapSize / memInfo.totalJSHeapSize;
        const now = Date.now();

        // 只有当内存使用率超过90%且距离上次清理超过5分钟时才清理
        if (usedMemory > 0.9 && now - lastCleanupTime > 5 * 60 * 1000) {
          cacheManager.cleanup();
          lastCleanupTime = now;
        }
      }
    };

    // 每3分钟检查一次内存使用情况,降低检查频率
    setInterval(checkMemory, 3 * 60 * 1000);
  }

  // 开发环境下暴露缓存管理器到 window 对象
  if (process.env.NODE_ENV === 'development') {
    try {
      (
        window as Window & {
          __CACHE_MANAGER__?: typeof cacheManager;
          __CLEAR_ALL_CACHE__?: () => void;
        }
      ).__CACHE_MANAGER__ = cacheManager;
      // 添加全局清理函数
      (window as Window & { __CLEAR_ALL_CACHE__?: () => void }).__CLEAR_ALL_CACHE__ = () => {
        cacheManager.clear();
        window.location.reload();
      };

      // 打印缓存统计信息
      const stats = cacheManager.getStats();
      if (typeof console !== 'undefined' && console.log) {
        console.log('当前缓存统计信息:', stats);
      }
    } catch {
      // 忽略开发环境错误
    }
  }
});

// 类型声明增强
declare module '@vue/runtime-core' {
  interface ComponentCustomProperties {
    $cache: typeof cacheManager;
  }
}

// 导出缓存相关工具函数
export const useCacheManager = () => cacheManager;

// 网络状态感知的缓存获取函数
export const getWithNetworkFallback = async <T>(
  key: string,
  fetcher: () => Promise<T>,
  options?: { ttl?: number; prefix?: string },
): Promise<T> => {
  try {
    // 如果在线,尝试获取最新数据
    if (navigator.onLine) {
      return await cacheManager.getOrFetch(key, fetcher, options);
    }

    // 如果离线,优先使用缓存
    const cached = cacheManager.get<T>(key, options);
    if (cached !== null) {
      return cached;
    }

    // 如果没有缓存且离线,抛出错误
    throw new Error('网络离线且无缓存数据');
  } catch (error) {
    // 网络请求失败时,尝试使用缓存
    const cached = cacheManager.get<T>(key, options);
    if (cached !== null) {
      console.warn('网络请求失败,使用缓存数据:', error);
      return cached;
    }
    throw error;
  }
};

// 批量预加载缓存
export const preloadCache = async <T>(
  preloadTasks: Array<{
    key: string;
    fetcher: () => Promise<T>;
    options?: { ttl?: number; prefix?: string };
  }>,
) => {
  const results = await Promise.allSettled(
    preloadTasks.map((task) => cacheManager.getOrFetch(task.key, task.fetcher, task.options)),
  );

  const successful = results.filter((r) => r.status === 'fulfilled').length;
  const failed = results.filter((r) => r.status === 'rejected').length;

  console.log(`📦 预加载完成: ${successful} 成功, ${failed} 失败`);

  return results;
};
