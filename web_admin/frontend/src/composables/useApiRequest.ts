import { readonly, ref } from 'vue';
import { useQuasar } from 'quasar';

type MessageResolver<T> = string | ((payload: T) => string | undefined);

export interface UseApiRequestOptions<TResult> {
  notifySuccess?: boolean;
  notifyError?: boolean;
  successMessage?: MessageResolver<TResult>;
  errorMessage?: MessageResolver<unknown>;
  onSuccess?: (result: TResult) => void;
  onError?: (error: unknown) => void;
}

export function useApiRequest<TArgs extends unknown[], TResult>(
  task: (...args: TArgs) => Promise<TResult>,
  options: UseApiRequestOptions<TResult> = {},
) {
  const $q = useQuasar();
  const loading = ref(false);
  const data = ref<TResult | null>(null);
  const error = ref<unknown>(null);

  const execute = async (...args: TArgs): Promise<TResult> => {
    loading.value = true;
    error.value = null;

    try {
      const result = await task(...args);
      data.value = result;
      options.onSuccess?.(result);

      if (options.notifySuccess) {
        const message = resolveMessage(options.successMessage, result);
        if (message) {
          $q.notify({ type: 'positive', message, position: 'top' });
        }
      }

      return result;
    } catch (err) {
      error.value = err;
      options.onError?.(err);

      if (options.notifyError !== false) {
        const message = resolveMessage(options.errorMessage, err) ?? defaultErrorMessage(err);
        if (message) {
          $q.notify({ type: 'negative', message, position: 'top' });
        }
      }

      throw err;
    } finally {
      loading.value = false;
    }
  };

  return {
    execute,
    loading: readonly(loading),
    data: readonly(data),
    error: readonly(error),
  };
}

function resolveMessage<T>(input: MessageResolver<T> | undefined, payload: T) {
  if (!input) {
    return undefined;
  }

  if (typeof input === 'function') {
    return input(payload);
  }

  return input;
}

function defaultErrorMessage(error: unknown): string {
  if (error instanceof Error) {
    return error.message;
  }

  if (typeof error === 'string') {
    return error;
  }

  try {
    return JSON.stringify(error);
  } catch {
    return '请求失败,请稍后重试';
  }
}
