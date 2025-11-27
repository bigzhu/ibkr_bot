/**
 * 网络状态管理 Boot 文件
 * 初始化网络状态监听和缓存策略调整
 */

import { boot } from 'quasar/wrappers';
import { networkManager } from 'src/utils/network-manager';

export default boot(({ app }) => {
  // 将网络管理器注入到全局属性中
  app.config.globalProperties.$networkManager = networkManager;

  // 提供网络管理器给整个应用
  app.provide('networkManager', networkManager);

  // 监听网络数据同步事件
  window.addEventListener('network-data-sync', () => {

    // 可以在这里触发全局的数据刷新逻辑
    // 例如:通知所有缓存的组件刷新数据
  });

  // 在应用卸载时清理资源
  app.config.globalProperties.$onBeforeUnmount = () => {
    networkManager.destroy();
  };
});

// 导出网络管理器供其他模块使用
export { networkManager };
