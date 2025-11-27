import { Notify } from 'quasar';

export interface NotificationOptions {
  message: string;
  timeout?: number;
  position?:
    | 'top'
    | 'bottom'
    | 'left'
    | 'right'
    | 'center'
    | 'top-left'
    | 'top-right'
    | 'bottom-left'
    | 'bottom-right';
  actions?: Array<{
    label?: string;
    icon?: string;
    color?: string;
    handler?: () => void;
  }>;
  caption?: string;
}

export const notifications = {
  success(options: string | NotificationOptions) {
    const config = typeof options === 'string' ? { message: options } : options;

    Notify.create({
      type: 'positive',
      message: config.message,
      position: config.position || 'top',
      timeout: config.timeout || 3000,
      actions: config.actions || [{ icon: 'close', color: 'white' }],
      caption: config.caption,
      multiLine: Boolean(config.caption),
    });
  },

  error(options: string | NotificationOptions) {
    const config = typeof options === 'string' ? { message: options } : options;

    Notify.create({
      type: 'negative',
      message: config.message,
      position: config.position || 'top',
      timeout: config.timeout || 5000,
      actions: config.actions || [{ icon: 'close', color: 'white' }],
      caption: config.caption,
      multiLine: Boolean(config.caption),
    });
  },

  warning(options: string | NotificationOptions) {
    const config = typeof options === 'string' ? { message: options } : options;

    Notify.create({
      type: 'warning',
      message: config.message,
      position: config.position || 'top',
      timeout: config.timeout || 4000,
      actions: config.actions || [{ icon: 'close', color: 'white' }],
      caption: config.caption,
      multiLine: Boolean(config.caption),
    });
  },

  info(options: string | NotificationOptions) {
    const config = typeof options === 'string' ? { message: options } : options;

    Notify.create({
      type: 'info',
      message: config.message,
      position: config.position || 'top',
      timeout: config.timeout || 3000,
      actions: config.actions || [{ icon: 'close', color: 'white' }],
      caption: config.caption,
      multiLine: Boolean(config.caption),
    });
  },

  // 带重试功能的错误通知
  errorWithRetry(message: string, retryHandler: () => void) {
    Notify.create({
      type: 'negative',
      message,
      position: 'top',
      timeout: 0, // 不自动消失
      actions: [
        {
          label: '重试',
          color: 'white',
          handler: () => retryHandler(),
        },
        {
          icon: 'close',
          color: 'white',
        },
      ],
    });
  },

  // 确认操作通知
  confirm(
    message: string,
    confirmHandler: () => void,
    cancelHandler?: () => void,
  ) {
    Notify.create({
      type: 'warning',
      message,
      position: 'top',
      timeout: 0,
      actions: [
        {
          label: '确认',
          color: 'white',
          handler: () => confirmHandler(),
        },
        {
          label: '取消',
          color: 'white',
          handler: cancelHandler ? () => cancelHandler() : undefined,
        },
      ],
    });
  },

  // 进度通知
  progress(message: string) {
    return Notify.create({
      type: 'ongoing',
      message,
      position: 'top',
      timeout: 0,
      spinner: true,
      actions: [],
    });
  },
};

// 导出为默认的通知方法,保持向后兼容
export const showSuccess = (options: string | NotificationOptions) => {
  notifications.success(options);
};

export const showError = (options: string | NotificationOptions) => {
  notifications.error(options);
};

export const showWarning = (options: string | NotificationOptions) => {
  notifications.warning(options);
};

export const showInfo = (options: string | NotificationOptions) => {
  notifications.info(options);
};
