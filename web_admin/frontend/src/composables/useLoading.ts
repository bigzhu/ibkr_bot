import { ref } from 'vue';
import { Loading } from 'quasar';

export interface LoadingOptions {
  message?: string;
  messageColor?: string;
  spinnerSize?: number;
  spinnerColor?: string;
  backgroundColor?: string;
  customClass?: string;
}

export function useLoading() {
  const isLoading = ref(false);

  // 显示全局加载
  const showGlobalLoading = (options?: LoadingOptions) => {
    Loading.show({
      message: options?.message || '加载中...',
      messageColor: options?.messageColor || 'white',
      spinnerSize: options?.spinnerSize || 80,
      spinnerColor: options?.spinnerColor || 'primary',
      backgroundColor: options?.backgroundColor || 'rgba(0,0,0,0.4)',
      customClass: options?.customClass,
    });
  };

  // 隐藏全局加载
  const hideGlobalLoading = () => {
    Loading.hide();
  };

  // 自动处理异步操作的加载状态
  const withLoading = async <T>(
    asyncOperation: () => Promise<T>,
    options?: LoadingOptions & {
      useGlobal?: boolean;
      errorHandler?: (error: unknown) => void;
    },
  ): Promise<T | undefined> => {
    try {
      if (options?.useGlobal) {
        showGlobalLoading(options);
      } else {
        isLoading.value = true;
      }

      const result = await asyncOperation();
      return result;
    } catch (error) {
      if (options?.errorHandler) {
        options.errorHandler(error);
      } else {
        console.error('Operation failed:', error);
      }
      return undefined;
    } finally {
      if (options?.useGlobal) {
        hideGlobalLoading();
      } else {
        isLoading.value = false;
      }
    }
  };

  // 批量加载状态管理
  const loadingStates = ref<Record<string, boolean>>({});

  const setLoading = (key: string, loading: boolean) => {
    loadingStates.value[key] = loading;
  };

  const isLoadingKey = (key: string) => {
    return Boolean(loadingStates.value[key]);
  };

  // 任意操作是否在加载中
  const isAnyLoading = () => {
    return isLoading.value || Object.values(loadingStates.value).some(Boolean);
  };

  return {
    isLoading,
    loadingStates,
    showGlobalLoading,
    hideGlobalLoading,
    withLoading,
    setLoading,
    isLoadingKey,
    isAnyLoading,
  };
}

// 创建一个全局的加载管理器
export const globalLoading = {
  show: (options?: LoadingOptions) => {
    Loading.show({
      message: options?.message || '加载中...',
      messageColor: options?.messageColor || 'white',
      spinnerSize: options?.spinnerSize || 80,
      spinnerColor: options?.spinnerColor || 'primary',
      backgroundColor: options?.backgroundColor || 'rgba(0,0,0,0.4)',
      customClass: options?.customClass,
    });
  },

  hide: () => {
    Loading.hide();
  },

  // 便捷的异步操作包装器
  async wrap<T>(asyncOperation: () => Promise<T>, message?: string): Promise<T | undefined> {
    try {
      globalLoading.show({ message });
      return await asyncOperation();
    } catch (error) {
      console.error('Global loading operation failed:', error);
      return undefined;
    } finally {
      globalLoading.hide();
    }
  },
};
