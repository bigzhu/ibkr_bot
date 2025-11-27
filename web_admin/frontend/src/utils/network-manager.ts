/**
 * 网络状态管理器
 * 提供网络状态监听和缓存策略调整功能
 */

import type { Ref } from 'vue';
import { ref } from 'vue';
// import { cacheManager } from './cache-manager';

export interface NetworkState {
  isOnline: boolean;
  isSlowConnection: boolean;
  connectionType: string;
  effectiveType: string;
  downlink: number;
  rtt: number;
}

interface NavigatorConnection extends EventTarget {
  type?: string;
  effectiveType?: string;
  downlink?: number;
  rtt?: number;
  addEventListener(type: 'change', listener: () => void): void;
  removeEventListener(type: 'change', listener: () => void): void;
}

interface NavigatorWithConnection extends Navigator {
  connection?: NavigatorConnection;
  mozConnection?: NavigatorConnection;
  webkitConnection?: NavigatorConnection;
}

const getNavigatorConnection = (): NavigatorConnection | null => {
  const nav = navigator as NavigatorWithConnection;
  return nav.connection ?? nav.mozConnection ?? nav.webkitConnection ?? null;
};

class NetworkManager {
  private static instance: NetworkManager;

  // 网络状态
  public isOnline: Ref<boolean> = ref(navigator.onLine);
  public isSlowConnection: Ref<boolean> = ref(false);
  public connectionType: Ref<string> = ref('unknown');
  public effectiveType: Ref<string> = ref('4g');
  public downlink: Ref<number> = ref(10);
  public rtt: Ref<number> = ref(100);

  // 网络状态变化监听器
  private onlineHandler: (() => void) | null = null;
  private offlineHandler: (() => void) | null = null;
  private connectionChangeHandler: (() => void) | null = null;

  private constructor() {
    this.initNetworkMonitoring();
  }

  public static getInstance(): NetworkManager {
    if (!NetworkManager.instance) {
      NetworkManager.instance = new NetworkManager();
    }
    return NetworkManager.instance;
  }

  /**
   * 初始化网络监听
   */
  private initNetworkMonitoring() {
    // 基本在线/离线状态监听
    this.onlineHandler = () => {
      this.isOnline.value = true;
      this.handleOnlineStatus();
    };

    this.offlineHandler = () => {
      this.isOnline.value = false;
      this.handleOfflineStatus();
    };

    window.addEventListener('online', this.onlineHandler);
    window.addEventListener('offline', this.offlineHandler);

    // 网络连接信息监听(如果支持)
    const connection = getNavigatorConnection();
    if (connection) {
      this.updateConnectionInfo(connection);

      this.connectionChangeHandler = () => {
        const latestConnection = getNavigatorConnection();
        this.updateConnectionInfo(latestConnection);
        this.adjustCacheStrategy();
      };

      connection.addEventListener('change', this.connectionChangeHandler);
    }

    // 初始状态检查
    this.checkInitialNetworkState();
  }

  /**
   * 更新连接信息
   */
  private updateConnectionInfo(connection: NavigatorConnection | null) {
    if (connection) {
      this.connectionType.value = connection.type ?? 'unknown';
      this.effectiveType.value = connection.effectiveType ?? '4g';
      this.downlink.value = connection.downlink ?? 10;
      this.rtt.value = connection.rtt ?? 100;

      // 判断是否为慢速连接
      this.isSlowConnection.value =
        connection.effectiveType === 'slow-2g' ||
        connection.effectiveType === '2g' ||
        connection.downlink < 1.5 ||
        connection.rtt > 400;

    }
  }

  /**
   * 检查初始网络状态
   */
  private checkInitialNetworkState() {
    this.isOnline.value = navigator.onLine;

    this.updateConnectionInfo(getNavigatorConnection());

    this.adjustCacheStrategy();
  }

  /**
   * 处理在线状态
   */
  private handleOnlineStatus() {

    // 网络恢复时,可以触发数据同步
    this.triggerDataSync();
  }

  /**
   * 处理离线状态
   */
  private handleOfflineStatus() {

    // 离线时,依赖缓存数据
    // 可以在这里通知应用切换到离线模式
  }

  /**
   * 根据网络状态调整缓存策略
   */
  private adjustCacheStrategy() {
    if (this.isSlowConnection.value) {
      // 慢速网络时,延长缓存时间,减少API调用
      // 这里可以动态调整 CacheConfigs
    } else if (this.isOnline.value && !this.isSlowConnection.value) {
      // 快速网络时,使用正常的缓存策略
    }
  }

  /**
   * 触发数据同步
   */
  private triggerDataSync() {
    // 网络恢复时,可以触发关键数据的重新获取
    // 这里可以发送自定义事件,让各个组件监听并刷新数据

    const syncEvent = new CustomEvent('network-data-sync', {
      detail: {
        isOnline: this.isOnline.value,
        connectionType: this.connectionType.value,
      },
    });

    window.dispatchEvent(syncEvent);
  }

  /**
   * 获取当前网络状态
   */
  public getNetworkState(): NetworkState {
    return {
      isOnline: this.isOnline.value,
      isSlowConnection: this.isSlowConnection.value,
      connectionType: this.connectionType.value,
      effectiveType: this.effectiveType.value,
      downlink: this.downlink.value,
      rtt: this.rtt.value,
    };
  }

  /**
   * 检查是否应该使用缓存
   */
  public shouldUseCache(): boolean {
    // 离线时必须使用缓存
    if (!this.isOnline.value) {
      return true;
    }

    // 慢速网络时优先使用缓存
    if (this.isSlowConnection.value) {
      return true;
    }

    // 正常网络时根据具体情况决定
    return false;
  }

  /**
   * 获取推荐的缓存时间(毫秒)
   */
  public getRecommendedCacheTime(defaultTime: number): number {
    if (!this.isOnline.value) {
      // 离线时,缓存时间延长到最大
      return defaultTime * 10;
    }

    if (this.isSlowConnection.value) {
      // 慢速网络时,延长缓存时间
      return defaultTime * 3;
    }

    // 快速网络时,使用默认缓存时间
    return defaultTime;
  }

  /**
   * 清理资源
   */
  public destroy() {
    if (this.onlineHandler) {
      window.removeEventListener('online', this.onlineHandler);
      this.onlineHandler = null;
    }

    if (this.offlineHandler) {
      window.removeEventListener('offline', this.offlineHandler);
      this.offlineHandler = null;
    }

    if (this.connectionChangeHandler) {
      const connection = getNavigatorConnection();
      connection?.removeEventListener('change', this.connectionChangeHandler);
      this.connectionChangeHandler = null;
    }
  }
}

// 导出单例实例
export const networkManager = NetworkManager.getInstance();

// 导出用于组件中使用的响应式状态
export const useNetworkState = () => {
  const manager = NetworkManager.getInstance();

  return {
    isOnline: manager.isOnline,
    isSlowConnection: manager.isSlowConnection,
    connectionType: manager.connectionType,
    effectiveType: manager.effectiveType,
    downlink: manager.downlink,
    rtt: manager.rtt,
    getNetworkState: () => manager.getNetworkState(),
    shouldUseCache: () => manager.shouldUseCache(),
    getRecommendedCacheTime: (defaultTime: number) => manager.getRecommendedCacheTime(defaultTime),
  };
};
