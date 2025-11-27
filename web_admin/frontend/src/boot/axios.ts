import { boot } from 'quasar/wrappers';
import axios, { type AxiosInstance } from 'axios';

declare module 'vue' {
  interface ComponentCustomProperties {
    $axios: AxiosInstance;
    $api: AxiosInstance;
  }
}

// Be careful when using SSR for cross-request state pollution
// due to creating a Singleton instance here;
// If any client changes this (global) instance, it might be a
// good idea to move this instance creation inside of the
// "export default () => {}" function below (which runs individually
// for each client)
const api = axios.create({
  baseURL: '/',
  timeout: 10000,
});

export default boot(({ app }) => {
  // for use inside Vue files (Options API) through this.$axios and this.$api

  app.config.globalProperties.$axios = axios;
  // ^ ^ ^ this will allow you to use this.$axios (for Vue Options API form)
  //       so you won't necessarily have to import axios in each vue file

  app.config.globalProperties.$api = api;
  // ^ ^ ^ this will allow you to use this.$api (for Vue Options API form)
  //       so you can easily perform requests against your app's API

  // Request interceptor
  api.interceptors.request.use(
    (config) => {
      // Add auth token from localStorage if available
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    },
    (error) => {
      return Promise.reject(new Error(error.message || 'Request failed'));
    },
  );

  // Response interceptor
  api.interceptors.response.use(
    (response) => response,
    (error) => {
      if (error.response?.status === 401) {
        // Token expired or invalid
        console.warn('🔒 认证token失效,自动退出登录');

        // 清理所有认证相关数据
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_info');

        // 清理所有缓存数据,防止显示过期数据
        const cacheKeys = ['symbols-list', 'dashboard-stats', 'dashboard-recent-logs'];
        cacheKeys.forEach((key) => {
          localStorage.removeItem(`quasar-app-${key}`);
          sessionStorage.removeItem(`quasar-app-${key}`);
        });

        // 显示错误提示
        if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
          // 只在非登录页面时显示提示
          const message = error.response?.data?.detail || '登录已过期,请重新登录';

          // 使用原生JS显示提示,因为Quasar可能还没初始化
          if (window.confirm(`${message}\n\n是否立即跳转到登录页面?`)) {
            window.location.href = '/login';
          } else {
            window.location.href = '/login'; // 强制跳转
          }
        }

        return Promise.reject(new Error('认证失败,请重新登录'));
      }

      // 其他HTTP错误
      const errorMessage =
        error.response?.data?.message ||
        error.response?.data?.detail ||
        error.message ||
        'API调用失败';

      console.error('API错误:', {
        status: error.response?.status,
        message: errorMessage,
        url: error.config?.url,
      });

      return Promise.reject(new Error(errorMessage));
    },
  );
});

export { api };
