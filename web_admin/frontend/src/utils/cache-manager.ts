/**
 * Quasar 原生缓存管理器
 * 基于 LocalStorage 和 SessionStorage API 实现智能缓存
 */

import { LocalStorage, SessionStorage, Notify } from 'quasar';

export interface CacheData<T = unknown> {
  data: T;
  timestamp: number;
  ttl: number;
  version?: string;
}

export interface CacheOptions {
  ttl?: number;
  persistent?: boolean;
  version?: string;
  notifyOnError?: boolean;
}

export class QuasarCacheManager {
  private readonly prefix = 'quasar-app-';
  private readonly defaultTTL = 5 * 60 * 1000; // 5分钟
  private readonly maxAge = 24 * 60 * 60 * 1000; // 24小时最大缓存时间

  /**
   * 设置缓存数据
   */
  set<T>(key: string, data: T, options: CacheOptions = {}): void {
    const { ttl = this.defaultTTL, persistent = true, version = '1.0' } = options;

    const cacheData: CacheData<T> = {
      data,
      timestamp: Date.now(),
      ttl,
      version,
    };

    const storage = persistent ? LocalStorage : SessionStorage;
    const cacheKey = this.getCacheKey(key);

    try {
      storage.set(cacheKey, cacheData);
    } catch (error) {
      console.warn(`Failed to set cache for key: ${key}`, error);
      if (options.notifyOnError) {
        Notify.create({
          type: 'warning',
          message: '缓存存储失败',
          position: 'top',
        });
      }
    }
  }

  /**
   * 获取缓存数据
   */
  get<T>(key: string, options: CacheOptions = {}): T | null {
    const { persistent = true } = options;
    const storage = persistent ? LocalStorage : SessionStorage;
    const cacheKey = this.getCacheKey(key);

    try {
      const cached: CacheData<T> | null = storage.getItem(cacheKey);

      if (!cached) {
        return null;
      }

      // 检查是否过期
      const isExpired = Date.now() - cached.timestamp > cached.ttl;
      const isStale = Date.now() - cached.timestamp > this.maxAge;

      if (isExpired || isStale) {
        this.remove(key, options);
        return null;
      }

      // 检查版本兼容性
      if (options.version && cached.version !== options.version) {
        this.remove(key, options);
        return null;
      }

      return cached.data;
    } catch (error) {
      console.warn(`Failed to get cache for key: ${key}`, error);
      return null;
    }
  }

  /**
   * 智能获取:优先会话缓存 -> 持久化缓存 -> 网络请求
   */
  async getOrFetch<T>(
    key: string,
    fetcher: () => Promise<T>,
    options: CacheOptions = {},
  ): Promise<T> {
    const { ttl = this.defaultTTL, persistent = true, notifyOnError = true } = options;

    // 1. 优先检查会话缓存(快速访问)
    let data = this.get<T>(key, { ...options, persistent: false });
    if (data !== null) {
      return data;
    }

    // 2. 检查持久化缓存
    if (persistent) {
      data = this.get<T>(key, { ...options, persistent: true });
      if (data !== null) {
        // 同时设置会话缓存以加快后续访问
        this.set(key, data, { ...options, persistent: false, ttl: Math.min(ttl, 60000) });
        return data;
      }
    }

    // 3. 网络获取
    try {
      data = await fetcher();

      // 缓存新数据
      if (persistent) {
        this.set(key, data, { ...options, persistent: true, ttl });
      }
      this.set(key, data, { ...options, persistent: false, ttl: Math.min(ttl, 60000) });

      return data;
    } catch (error) {
      if (notifyOnError) {
        Notify.create({
          type: 'negative',
          message: '数据获取失败',
          caption: error instanceof Error ? error.message : '未知错误',
          position: 'top',
          actions: [
            {
              label: '重试',
              color: 'white',
              handler: () => {
                void this.getOrFetch(key, fetcher, options);
              },
            },
          ],
        });
      }
      throw error;
    }
  }

  /**
   * 移除缓存数据
   */
  remove(key: string, options: CacheOptions = {}): void {
    const { persistent = true } = options;
    const cacheKey = this.getCacheKey(key);

    if (persistent) {
      LocalStorage.remove(cacheKey);
    }
    SessionStorage.remove(cacheKey);
  }

  /**
   * 检查缓存是否存在且未过期
   */
  has(key: string, options: CacheOptions = {}): boolean {
    return this.get(key, options) !== null;
  }

  /**
   * 获取缓存信息
   */
  getInfo(
    key: string,
    options: CacheOptions = {},
  ): {
    exists: boolean;
    isExpired: boolean;
    age: number;
    ttl: number;
  } | null {
    const { persistent = true } = options;
    const storage = persistent ? LocalStorage : SessionStorage;
    const cacheKey = this.getCacheKey(key);

    const cached: CacheData | null = storage.getItem(cacheKey);
    if (!cached) {
      return null;
    }

    const age = Date.now() - cached.timestamp;
    const isExpired = age > cached.ttl;

    return {
      exists: true,
      isExpired,
      age,
      ttl: cached.ttl,
    };
  }

  /**
   * 清理过期缓存
   */
  cleanup(): { removed: number; errors: string[] } {
    let removed = 0;
    const errors: string[] = [];

    try {
      // 清理 LocalStorage
      const localKeys = LocalStorage.getAllKeys();
      const prefixedKeys = localKeys.filter((key) => key.startsWith(this.prefix));

      for (const key of prefixedKeys) {
        try {
          const cached: CacheData | null = LocalStorage.getItem(key);
          if (cached) {
            const isExpired = Date.now() - cached.timestamp > cached.ttl;
            const isStale = Date.now() - cached.timestamp > this.maxAge;

            if (isExpired || isStale) {
              LocalStorage.remove(key);
              removed++;
            }
          }
        } catch (error) {
          errors.push(`Failed to cleanup ${key}: ${String(error)}`);
        }
      }

      // 清理 SessionStorage
      const sessionKeys = SessionStorage.getAllKeys();
      const sessionPrefixedKeys = sessionKeys.filter((key) => key.startsWith(this.prefix));

      for (const key of sessionPrefixedKeys) {
        try {
          const cached: CacheData | null = SessionStorage.getItem(key);
          if (cached) {
            const isExpired = Date.now() - cached.timestamp > cached.ttl;

            if (isExpired) {
              SessionStorage.remove(key);
              removed++;
            }
          }
        } catch (error) {
          errors.push(`Failed to cleanup session ${key}: ${String(error)}`);
        }
      }
    } catch (error) {
      errors.push(`Cleanup failed: ${String(error)}`);
    }

    return { removed, errors };
  }

  /**
   * 清空所有缓存
   */
  clear(): void {
    try {
      const localKeys = LocalStorage.getAllKeys();
      const sessionKeys = SessionStorage.getAllKeys();

      // 清理 LocalStorage 中的应用缓存
      localKeys
        .filter((key) => key.startsWith(this.prefix))
        .forEach((key) => LocalStorage.remove(key));

      // 清理 SessionStorage 中的应用缓存
      sessionKeys
        .filter((key) => key.startsWith(this.prefix))
        .forEach((key) => SessionStorage.remove(key));
    } catch (error) {
      console.warn('Failed to clear cache:', error);
    }
  }

  /**
   * 获取缓存统计信息
   */
  getStats(): {
    localCount: number;
    sessionCount: number;
    totalSize: number;
    oldestEntry: number | null;
    newestEntry: number | null;
  } {
    let localCount = 0;
    let sessionCount = 0;
    let totalSize = 0;
    let oldestEntry: number | null = null;
    let newestEntry: number | null = null;

    try {
      // 统计 LocalStorage
      const localKeys = LocalStorage.getAllKeys();
      const localPrefixedKeys = localKeys.filter((key) => key.startsWith(this.prefix));
      localCount = localPrefixedKeys.length;

      for (const key of localPrefixedKeys) {
        const cached: CacheData | null = LocalStorage.getItem(key);
        if (cached) {
          totalSize += JSON.stringify(cached).length;

          if (oldestEntry === null || cached.timestamp < oldestEntry) {
            oldestEntry = cached.timestamp;
          }
          if (newestEntry === null || cached.timestamp > newestEntry) {
            newestEntry = cached.timestamp;
          }
        }
      }

      // 统计 SessionStorage
      const sessionKeys = SessionStorage.getAllKeys();
      const sessionPrefixedKeys = sessionKeys.filter((key) => key.startsWith(this.prefix));
      sessionCount = sessionPrefixedKeys.length;

      for (const key of sessionPrefixedKeys) {
        const cached: CacheData | null = SessionStorage.getItem(key);
        if (cached) {
          totalSize += JSON.stringify(cached).length;

          if (oldestEntry === null || cached.timestamp < oldestEntry) {
            oldestEntry = cached.timestamp;
          }
          if (newestEntry === null || cached.timestamp > newestEntry) {
            newestEntry = cached.timestamp;
          }
        }
      }
    } catch (error) {
      console.warn('Failed to get cache stats:', error);
    }

    return {
      localCount,
      sessionCount,
      totalSize,
      oldestEntry,
      newestEntry,
    };
  }

  /**
   * 设置配置数据缓存(长期缓存,基于版本控制)
   */
  setConfigData<T>(key: string, data: T, version: string = '1.0'): void {
    const cacheData: CacheData<T> = {
      data,
      timestamp: Date.now(),
      ttl: 365 * 24 * 60 * 60 * 1000, // 1年(配置数据几乎永不过期)
      version,
    };

    const storage = LocalStorage; // 配置数据总是持久化
    const cacheKey = this.getCacheKey(key);

    try {
      storage.set(cacheKey, cacheData);
    } catch (error) {
      console.warn(`Failed to set config cache for key: ${key}`, error);
    }
  }

  /**
   * 获取配置数据缓存
   */
  getConfigData<T>(key: string, currentVersion: string = '1.0'): T | null {
    const storage = LocalStorage;
    const cacheKey = this.getCacheKey(key);

    try {
      const cached: CacheData<T> | null = storage.getItem(cacheKey);

      if (!cached) {
        return null;
      }

      // 配置数据主要基于版本控制,而不是时间过期
      const isVersionMismatch = cached.version !== currentVersion;
      const isStale = Date.now() - cached.timestamp > this.maxAge; // 仍然检查最大年龄

      if (isVersionMismatch || isStale) {
        this.remove(key, { persistent: true });
        return null;
      }

      return cached.data;
    } catch (error) {
      console.warn(`Failed to get config cache for key: ${key}`, error);
      return null;
    }
  }

  /**
   * 生成缓存键名
   */
  private getCacheKey(key: string): string {
    return `${this.prefix}${key}`;
  }
}

// 全局缓存管理器实例
export const cacheManager = new QuasarCacheManager();

// 预定义的缓存配置
export const CacheConfigs = {
  // 用户配置 - 长期缓存
  USER_CONFIG: {
    ttl: 30 * 60 * 1000, // 30分钟
    persistent: true,
    version: '1.0',
  },

  // 交易对列表 - 配置数据缓存(变更频率很低)
  SYMBOLS_LIST: {
    ttl: 30 * 24 * 60 * 60 * 1000, // 30天(配置数据,几乎不会变更)
    persistent: true,
    version: '1.0',
  },

  // 时间周期配置 - 配置数据缓存(变更频率很低)
  TIMEFRAME_CONFIGS: {
    ttl: 30 * 24 * 60 * 60 * 1000, // 30天(配置数据,几乎不会变更)
    persistent: true,
    version: '1.0',
  },

  // 实时数据 - 短期缓存
  REALTIME_DATA: {
    ttl: 1 * 60 * 1000, // 1分钟
    persistent: false,
    version: '1.0',
  },

  // 页面状态 - 会话级缓存
  PAGE_STATE: {
    ttl: 60 * 60 * 1000, // 1小时
    persistent: false,
    version: '1.0',
  },
};
