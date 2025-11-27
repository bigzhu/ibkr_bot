<template>
  <q-page class="modern-page">
    <!-- 页面头部 -->
    <PageHeader
      title="系统配置"
      subtitle="管理交易系统的核心配置和安全设置"
      icon="settings"
      icon-size="3rem"
      glow-type="config"
      margin="xl"
    />

    <!-- 配置总览状态 -->
    <div class="config-overview q-mb-xl">
      <div class="overview-grid">
        <div
          class="overview-item"
          :class="{ 'item-success': systemInfo.database_status === 'connected' }"
        >
          <div class="item-icon">
            <q-icon name="storage" size="20px" />
          </div>
          <div class="item-content">
            <div class="item-label">数据库连接</div>
            <div class="item-status">
              {{ systemInfo.database_status === 'connected' ? '已连接' : '离线' }}
            </div>
          </div>
          <div class="item-indicator"></div>
        </div>

        <div
          class="overview-item"
          :class="{ 'item-success': apiConfig.api_key, 'item-warning': !apiConfig.api_key }"
        >
          <div class="item-icon">
            <q-icon name="api" size="20px" />
          </div>
          <div class="item-content">
            <div class="item-label">API 配置</div>
            <div class="item-status">{{ apiConfig.api_key ? '已配置' : '待配置' }}</div>
          </div>
          <div class="item-indicator"></div>
        </div>

        <div class="overview-item item-info">
          <div class="item-icon">
            <q-icon name="info" size="20px" />
          </div>
          <div class="item-content">
            <div class="item-label">系统版本</div>
            <div class="item-status">{{ systemInfo.version }}</div>
          </div>
          <div class="item-indicator"></div>
        </div>
      </div>
    </div>

    <!-- 配置面板区域 -->
    <div class="config-panels">
      <!-- API 配置面板 -->
      <div class="config-section">
        <q-card class="modern-card config-card api-config-card">
          <div class="card-header">
            <div class="header-left">
              <div class="section-icon">
                <q-icon name="api" size="24px" />
                <div class="icon-pulse"></div>
              </div>
              <div class="section-info">
                <h3 class="section-title">Binance API 配置</h3>
                <p class="section-description">配置您的 Binance 交易 API 密钥</p>
              </div>
            </div>
            <div class="header-actions">
              <q-btn
                flat
                round
                dense
                icon="help_outline"
                color="grey-6"
                size="sm"
                @click="showApiHelp"
              >
                <q-tooltip>API 配置帮助</q-tooltip>
              </q-btn>
            </div>
          </div>

          <div class="card-content">
            <q-form @submit="saveApiConfig" class="config-form">
              <!-- API Key 输入 -->
              <div class="form-group">
                <label class="form-label">API Key</label>
                <q-input
                  v-model="apiConfig.api_key"
                  outlined
                  dense
                  placeholder="请输入您的 Binance API Key"
                  :type="showApiKey ? 'text' : 'password'"
                  :rules="[(val) => !!val || '请输入 API Key']"
                  class="modern-input"
                >
                  <template v-slot:prepend>
                    <q-icon name="vpn_key" color="primary" />
                  </template>
                  <template v-slot:append>
                    <q-btn
                      flat
                      round
                      dense
                      :icon="showApiKey ? 'visibility_off' : 'visibility'"
                      @click="showApiKey = !showApiKey"
                      color="grey-6"
                      size="sm"
                    />
                  </template>
                </q-input>
              </div>

              <!-- API Secret 输入 -->
              <div class="form-group">
                <label class="form-label">API Secret</label>
                <q-input
                  v-model="apiConfig.secret_key"
                  outlined
                  dense
                  placeholder="请输入您的 Binance API Secret"
                  :type="showApiSecret ? 'text' : 'password'"
                  :rules="[(val) => !!val || '请输入 API Secret']"
                  class="modern-input"
                >
                  <template v-slot:prepend>
                    <q-icon name="security" color="primary" />
                  </template>
                  <template v-slot:append>
                    <q-btn
                      flat
                      round
                      dense
                      :icon="showApiSecret ? 'visibility_off' : 'visibility'"
                      @click="showApiSecret = !showApiSecret"
                      color="grey-6"
                      size="sm"
                    />
                  </template>
                </q-input>
              </div>

              <!-- 环境信息 -->
              <div class="form-group">
                <label class="form-label">交易环境</label>
                <div class="environment-info">
                  <div class="env-badge">
                    <q-icon name="public" size="18px" />
                    <span>Binance 主网 (Mainnet)</span>
                    <q-chip color="positive" text-color="white" size="xs" dense>
                      <q-icon name="check_circle" size="12px" />
                    </q-chip>
                  </div>
                  <div class="env-description">
                    系统配置为 Binance 主网交易环境,确保您的 API 密钥对应正确的环境
                  </div>
                </div>
              </div>

              <!-- 操作按钮 -->
              <div class="form-actions">
                <q-btn
                  type="submit"
                  unelevated
                  color="primary"
                  :loading="isSavingApi"
                  :disable="!apiConfig.api_key || !apiConfig.secret_key"
                  class="btn-gradient action-btn"
                  no-caps
                >
                  <q-icon name="save" size="18px" class="q-mr-sm" />
                  保存 API 配置
                </q-btn>
                <q-btn
                  unelevated
                  color="secondary"
                  :loading="isTestingConnection"
                  :disable="!apiConfig.api_key || !apiConfig.secret_key"
                  @click="testConnection"
                  class="action-btn"
                  no-caps
                >
                  <q-icon name="wifi_protected_setup" size="18px" class="q-mr-sm" />
                  测试连接
                </q-btn>
              </div>

              <!-- 安全提示 -->
              <div class="security-notice">
                <q-icon name="shield" color="warning" size="20px" />
                <div class="notice-content">
                  <div class="notice-title">安全提示</div>
                  <div class="notice-text">
                    您的 API 密钥将被安全加密存储.建议仅授予必要的交易权限,不要共享 API 密钥.
                  </div>
                </div>
              </div>
            </q-form>
          </div>
        </q-card>
      </div>

      <!-- 安全设置面板 -->
      <div class="config-section">
        <q-card class="modern-card config-card security-config-card">
          <div class="card-header">
            <div class="header-left">
              <div class="section-icon">
                <q-icon name="shield" size="24px" />
                <div class="icon-pulse"></div>
              </div>
              <div class="section-info">
                <h3 class="section-title">安全设置</h3>
                <p class="section-description">管理您的登录密码和安全选项</p>
              </div>
            </div>
          </div>

          <div class="card-content">
            <q-form @submit="changePassword" class="config-form">
              <!-- 当前密码 -->
              <div class="form-group">
                <label class="form-label">当前密码</label>
                <q-input
                  v-model="passwordConfig.current_password"
                  outlined
                  dense
                  placeholder="请输入当前登录密码"
                  :type="showCurrentPassword ? 'text' : 'password'"
                  :rules="[(val) => !!val || '请输入当前密码']"
                  class="modern-input"
                >
                  <template v-slot:prepend>
                    <q-icon name="lock_outline" color="primary" />
                  </template>
                  <template v-slot:append>
                    <q-btn
                      flat
                      round
                      dense
                      :icon="showCurrentPassword ? 'visibility_off' : 'visibility'"
                      @click="showCurrentPassword = !showCurrentPassword"
                      color="grey-6"
                      size="sm"
                    />
                  </template>
                </q-input>
              </div>

              <!-- 新密码 -->
              <div class="form-group">
                <label class="form-label">新密码</label>
                <q-input
                  v-model="passwordConfig.new_password"
                  outlined
                  dense
                  placeholder="请输入新密码 (至少6位)"
                  :type="showNewPassword ? 'text' : 'password'"
                  :rules="[
                    (val) => !!val || '请输入新密码',
                    (val) => val.length >= 6 || '新密码至少6位',
                  ]"
                  class="modern-input"
                >
                  <template v-slot:prepend>
                    <q-icon name="lock" color="primary" />
                  </template>
                  <template v-slot:append>
                    <q-btn
                      flat
                      round
                      dense
                      :icon="showNewPassword ? 'visibility_off' : 'visibility'"
                      @click="showNewPassword = !showNewPassword"
                      color="grey-6"
                      size="sm"
                    />
                  </template>
                </q-input>

                <!-- 密码强度指示器 -->
                <div class="password-strength" v-if="passwordConfig.new_password">
                  <div class="strength-label">密码强度:</div>
                  <div class="strength-bar">
                    <div
                      class="strength-indicator"
                      :class="getPasswordStrength(passwordConfig.new_password)"
                    ></div>
                  </div>
                  <div class="strength-text">
                    {{ getPasswordStrengthText(passwordConfig.new_password) }}
                  </div>
                </div>
              </div>

              <!-- 确认新密码 -->
              <div class="form-group">
                <label class="form-label">确认新密码</label>
                <q-input
                  v-model="passwordConfig.confirm_password"
                  outlined
                  dense
                  placeholder="请再次输入新密码进行确认"
                  :type="showConfirmPassword ? 'text' : 'password'"
                  :rules="[
                    (val) => !!val || '请确认新密码',
                    (val) => val.length >= 6 || '确认密码至少6位',
                    (val) => val === passwordConfig.new_password || '两次输入的密码不一致',
                  ]"
                  class="modern-input"
                >
                  <template v-slot:prepend>
                    <q-icon name="lock_reset" color="primary" />
                  </template>
                  <template v-slot:append>
                    <q-btn
                      flat
                      round
                      dense
                      :icon="showConfirmPassword ? 'visibility_off' : 'visibility'"
                      @click="showConfirmPassword = !showConfirmPassword"
                      color="grey-6"
                      size="sm"
                    />
                    <q-icon
                      v-if="
                        passwordConfig.confirm_password &&
                        passwordConfig.confirm_password === passwordConfig.new_password
                      "
                      name="check_circle"
                      color="positive"
                      size="sm"
                    />
                  </template>
                </q-input>
              </div>

              <!-- 操作按钮 -->
              <div class="form-actions">
                <q-btn
                  type="submit"
                  unelevated
                  color="warning"
                  :loading="isChangingPassword"
                  :disable="
                    !passwordConfig.current_password ||
                    !passwordConfig.new_password ||
                    !passwordConfig.confirm_password ||
                    passwordConfig.new_password !== passwordConfig.confirm_password
                  "
                  class="action-btn full-width"
                  no-caps
                >
                  <q-icon name="update" size="18px" class="q-mr-sm" />
                  修改密码
                </q-btn>
              </div>

              <!-- 安全警告 -->
              <div class="security-warning">
                <q-icon name="warning" color="orange" size="20px" />
                <div class="warning-content">
                  <div class="warning-title">重要提醒</div>
                  <div class="warning-text">
                    密码修改成功后将自动退出登录,请使用新密码重新登录系统.
                  </div>
                </div>
              </div>
            </q-form>
          </div>
        </q-card>
      </div>

      <!-- 日志配置面板 -->
      <div class="config-section">
        <q-card class="modern-card config-card log-config-card">
          <div class="card-header">
            <div class="header-left">
              <div class="section-icon">
                <q-icon name="description" size="24px" />
                <div class="icon-pulse"></div>
              </div>
              <div class="section-info">
                <h3 class="section-title">日志配置</h3>
                <p class="section-description">设置系统日志级别和存储选项</p>
              </div>
            </div>
          </div>

          <div class="card-content">
            <q-form @submit="saveLogConfig" class="config-form">
              <!-- 日志级别 -->
              <div class="form-group">
                <label class="form-label">日志级别</label>
                <q-select
                  v-model="logConfig.log_level"
                  outlined
                  dense
                  :options="logLevelOptions"
                  emit-value
                  map-options
                  class="modern-select"
                >
                  <template v-slot:prepend>
                    <q-icon name="tune" color="primary" />
                  </template>
                </q-select>
                <div class="form-hint">较低级别会记录更多详细信息,但可能影响性能</div>
              </div>

              <!-- 存储设置 -->
              <div class="form-row">
                <div class="form-group">
                  <label class="form-label">最大文件数</label>
                  <q-input
                    v-model.number="logConfig.max_log_files"
                    outlined
                    dense
                    type="number"
                    min="1"
                    max="500"
                    :rules="[(val) => (val > 0 && val <= 500) || '1-500之间']"
                    class="modern-input"
                  >
                    <template v-slot:prepend>
                      <q-icon name="folder" color="primary" />
                    </template>
                  </q-input>
                </div>

                <div class="form-group">
                  <label class="form-label">最大文件大小 (MB)</label>
                  <q-input
                    v-model.number="logConfig.max_file_size_mb"
                    outlined
                    dense
                    type="number"
                    min="1"
                    max="5000"
                    :rules="[(val) => (val > 0 && val <= 5000) || '1-5000之间']"
                    class="modern-input"
                  >
                    <template v-slot:prepend>
                      <q-icon name="storage" color="primary" />
                    </template>
                  </q-input>
                </div>
              </div>

              <!-- 高级选项 -->
              <div class="form-group">
                <div class="toggle-option">
                  <div class="toggle-info">
                    <div class="toggle-label">邮件告警</div>
                    <div class="toggle-description">关键错误时发送邮件通知</div>
                  </div>
                  <q-toggle v-model="logConfig.enable_email_alerts" color="warning" size="md" />
                </div>
              </div>

              <!-- 操作按钮 -->
              <div class="form-actions">
                <q-btn
                  type="submit"
                  unelevated
                  color="primary"
                  :loading="isSavingLog"
                  class="action-btn full-width"
                  no-caps
                >
                  <q-icon name="save" size="18px" class="q-mr-sm" />
                  保存日志配置
                </q-btn>
              </div>
            </q-form>
          </div>
        </q-card>
      </div>

      <!-- 系统状态面板 -->
      <div class="config-section">
        <q-card class="modern-card config-card system-status-card">
          <div class="card-header">
            <div class="header-left">
              <div class="section-icon">
                <q-icon name="monitor_heart" size="24px" />
                <div class="icon-pulse"></div>
              </div>
              <div class="section-info">
                <h3 class="section-title">系统状态</h3>
                <p class="section-description">实时系统运行状态和统计信息</p>
              </div>
            </div>
            <div class="header-actions">
              <q-btn
                flat
                round
                dense
                icon="refresh"
                color="primary"
                size="sm"
                :loading="isRefreshing"
                @click="refreshSystemInfo"
              >
                <q-tooltip>刷新状态</q-tooltip>
              </q-btn>
            </div>
          </div>

          <div class="card-content">
            <div class="status-grid">
              <div class="status-item">
                <div class="status-icon">
                  <q-icon name="code" color="info" size="24px" />
                </div>
                <div class="status-info">
                  <div class="status-label">系统版本</div>
                  <div class="status-value">{{ systemInfo.version }}</div>
                </div>
              </div>

              <div class="status-item">
                <div class="status-icon">
                  <q-icon
                    name="storage"
                    :color="systemInfo.database_status === 'connected' ? 'positive' : 'negative'"
                    size="24px"
                  />
                </div>
                <div class="status-info">
                  <div class="status-label">数据库状态</div>
                  <div class="status-value">
                    <q-chip
                      :color="systemInfo.database_status === 'connected' ? 'positive' : 'negative'"
                      text-color="white"
                      size="sm"
                      class="text-weight-bold"
                    >
                      <q-icon
                        :name="
                          systemInfo.database_status === 'connected' ? 'check_circle' : 'error'
                        "
                        size="14px"
                        class="q-mr-xs"
                      />
                      {{ systemInfo.database_status === 'connected' ? '已连接' : '断开' }}
                    </q-chip>
                  </div>
                </div>
              </div>

              <div class="status-item">
                <div class="status-icon">
                  <q-icon name="settings" color="primary" size="24px" />
                </div>
                <div class="status-info">
                  <div class="status-label">配置数量</div>
                  <div class="status-value">{{ systemInfo.config_count }} 个</div>
                </div>
              </div>

              <div class="status-item">
                <div class="status-icon">
                  <q-icon name="schedule" color="grey-6" size="24px" />
                </div>
                <div class="status-info">
                  <div class="status-label">最后更新</div>
                  <div class="status-value">{{ formatTime(systemInfo.last_update) }}</div>
                </div>
              </div>
            </div>

            <!-- 系统资源状态 -->
            <div class="resource-status">
              <div class="resource-title">系统资源</div>
              <div class="resource-metrics">
                <div class="resource-item">
                  <div class="resource-label">内存使用</div>
                  <div class="resource-bar">
                    <q-linear-progress
                      :value="0.35"
                      color="info"
                      track-color="grey-3"
                      size="6px"
                      rounded
                    />
                    <span class="resource-value">35%</span>
                  </div>
                </div>

                <div class="resource-item">
                  <div class="resource-label">磁盘空间</div>
                  <div class="resource-bar">
                    <q-linear-progress
                      :value="0.22"
                      color="positive"
                      track-color="grey-3"
                      size="6px"
                      rounded
                    />
                    <span class="resource-value">22%</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </q-card>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue';
import { useQuasar } from 'quasar';
import { useRouter } from 'vue-router';
import { apiService } from 'src/services';
import PageHeader from 'src/components/PageHeader.vue';
import { useBackgroundRefresh } from 'src/composables/useBackgroundRefresh';
import { useApiRequest } from 'src/composables/useApiRequest';
import { formatDateTime as formatDateTimeUtil } from 'src/utils/datetime';

const $q = useQuasar();
const router = useRouter();

// 响应式数据
const showApiKey = ref(false);
const showApiSecret = ref(false);
const showCurrentPassword = ref(false);
const showNewPassword = ref(false);
const showConfirmPassword = ref(false);

// API 配置
const apiConfig = ref({
  api_key: '',
  secret_key: '',
});

// 密码修改配置
const passwordConfig = ref({
  current_password: '',
  new_password: '',
  confirm_password: '',
});

// 日志配置
const logConfig = ref({
  log_level: 'INFO',
  max_log_files: 10,
  max_file_size_mb: 10,
  enable_email_alerts: false,
});

// 系统信息
const systemInfo = ref({
  version: 'v1.0.0',
  database_status: 'connected',
  config_count: 0,
  last_update: new Date(),
});

const logLevelOptions = [
  { label: 'DEBUG', value: 'DEBUG' },
  { label: 'INFO', value: 'INFO' },
  { label: 'WARNING', value: 'WARNING' },
  { label: 'ERROR', value: 'ERROR' },
];

const { execute: saveApiConfigRequest, loading: isSavingApi } = useApiRequest(
  async () => {
    const response = await apiService.config.saveBinanceConfig({
      api_key: apiConfig.value.api_key,
      secret_key: apiConfig.value.secret_key,
    });

    if (!response.success) {
      throw new Error(response.message || 'API 配置保存失败');
    }

    await loadConfigs();
    return response;
  },
  {
    notifySuccess: true,
    successMessage: (response) => response.message || 'API 配置保存成功',
    notifyError: true,
    errorMessage: (error) => `API 配置保存失败: ${apiService.handleError(error)}`,
  },
);

const { execute: saveLogConfigRequest, loading: isSavingLog } = useApiRequest(
  async () => {
    const response = await apiService.config.updateLogLevel(logConfig.value.log_level);

    if (!response.success) {
      throw new Error(response.message || '日志配置保存失败');
    }

    return response;
  },
  {
    notifySuccess: true,
    successMessage: (response) => response.message || '日志配置保存成功',
    notifyError: true,
    errorMessage: (error) => `日志配置保存失败: ${apiService.handleError(error)}`,
  },
);

const { execute: testConnectionRequest, loading: isTestingConnection } = useApiRequest(
  async () => {
    const response = await apiService.config.validateBinanceApi({
      api_key: apiConfig.value.api_key,
      secret_key: apiConfig.value.secret_key,
    });

    if (!response.success) {
      const details = response.error_details ? `: ${response.error_details}` : '';
      throw new Error(response.message ? `${response.message}${details}` : `API 连接测试失败${details}`);
    }

    return response;
  },
  {
    notifySuccess: true,
    successMessage: (response) => response.message || 'API 连接测试成功',
    notifyError: true,
    errorMessage: (error) => `API 连接测试失败: ${apiService.handleError(error)}`,
  },
);

let countdownTimer: ReturnType<typeof setInterval> | null = null;

const resetPasswordForm = () => {
  passwordConfig.value = {
    current_password: '',
    new_password: '',
    confirm_password: '',
  };
};

const clearCountdown = () => {
  if (countdownTimer) {
    clearInterval(countdownTimer);
    countdownTimer = null;
  }
};

const startLogoutCountdown = () => {
  clearCountdown();

  let countdown = 3;
  const countdownNotify = $q.notify({
    type: 'info',
    message: `${countdown} 秒后自动退出登录,请使用新密码重新登录`,
    timeout: 0,
    actions: [
      {
        label: '立即退出',
        color: 'white',
        handler: () => {
          clearCountdown();
          countdownNotify();
          performLogout();
        },
      },
    ],
  });

  countdownTimer = setInterval(() => {
    countdown -= 1;
    if (countdown > 0) {
      countdownNotify({
        message: `${countdown} 秒后自动退出登录,请使用新密码重新登录`,
      });
    } else {
      clearCountdown();
      countdownNotify();
      performLogout();
    }
  }, 1000);
};

const { execute: changePasswordRequest, loading: isChangingPassword } = useApiRequest(
  async (payload: { current_password: string; new_password: string; confirm_password: string }) => {
    const response = await apiService.auth.changePassword(payload);

    if (!response.success) {
      throw new Error(response.message || '密码修改失败');
    }

    return response;
  },
  {
    notifySuccess: false,
    notifyError: false,
    onSuccess: (response) => {
      $q.notify({
        type: 'positive',
        message: response.message || '密码修改成功',
        timeout: 3000,
      });
      resetPasswordForm();
      startLogoutCountdown();
    },
    onError: (error) => {
      $q.notify({
        type: 'negative',
        message: `密码修改失败: ${apiService.handleError(error)}`,
        position: 'top',
      });
    },
  },
);

const { execute: refreshSystemInfoRequest, loading: isRefreshing } = useApiRequest(
  async () => {
    await new Promise((resolve) => setTimeout(resolve, 1000));

    const info = {
      version: 'v1.0.0',
      database_status: 'connected',
      config_count: 8,
      last_update: new Date(),
    };

    systemInfo.value = info;
    return info;
  },
  {
    notifySuccess: true,
    successMessage: '系统状态已刷新',
    notifyError: true,
    errorMessage: (error) => `刷新系统状态失败: ${apiService.handleError(error)}`,
  },
);

// 密码强度计算
const getPasswordStrength = (password: string) => {
  let strength = 0;
  if (password.length >= 8) strength += 1;
  if (/[a-z]/.test(password)) strength += 1;
  if (/[A-Z]/.test(password)) strength += 1;
  if (/[0-9]/.test(password)) strength += 1;
  if (/[^A-Za-z0-9]/.test(password)) strength += 1;

  if (strength <= 2) return 'strength-weak';
  if (strength <= 3) return 'strength-medium';
  return 'strength-strong';
};

const getPasswordStrengthText = (password: string) => {
  const strength = getPasswordStrength(password);
  const texts = {
    'strength-weak': '弱',
    'strength-medium': '中等',
    'strength-strong': '强',
  };
  return texts[strength] || '弱';
};

// 显示 API 帮助
const showApiHelp = () => {
  $q.dialog({
    title: 'Binance API 配置帮助',
    message: `
配置步骤:
1. 登录 Binance 官网
2. 进入 API 管理页面
3. 创建新的 API 密钥
4. 设置权限:仅勾选"现货及杠杆交易"
5. 复制 API Key 和 Secret 到此处

安全提醒:
• 不要将 API 密钥分享给任何人
• 建议定期更换 API 密钥
• 仅授予必要的交易权限
    `,
    html: true,
    ok: '了解了',
  });
};

// 格式化时间
const formatTime = (timestamp: string | Date) =>
  formatDateTimeUtil(timestamp, { includeSeconds: true });

// 加载配置数据
const loadConfigs = async () => {
  try {
    // 加载Binance API配置状态
    const binanceResponse = await apiService.config.getBinanceStatus();
    if (binanceResponse.success) {
      apiConfig.value = {
        api_key: binanceResponse.data.api_key,
        secret_key: binanceResponse.data.secret_key,
      };
    }

    // 加载日志级别配置
    const logResponse = await apiService.config.getLogLevel();
    if (logResponse.success) {
      logConfig.value.log_level = logResponse.log_level;
    }

    // 其他日志配置暂时使用默认值,等待后端API实现
    logConfig.value = {
      ...logConfig.value,
      max_log_files: 10,
      max_file_size_mb: 10,
      enable_email_alerts: false,
    };
  } catch (error) {
    console.error('Failed to load configs:', error);
    $q.notify({
      type: 'negative',
      message: `加载配置失败: ${error instanceof Error ? error.message : '未知错误'}`,
      position: 'top',
    });
  }
};

// 保存 API 配置
const saveApiConfig = async () => {
  await saveApiConfigRequest();
};

// 保存日志配置
const saveLogConfig = async () => {
  await saveLogConfigRequest();
};

// 测试连接
const testConnection = async () => {
  await testConnectionRequest();
};

// 修改密码
const changePassword = async () => {
  if (passwordConfig.value.new_password !== passwordConfig.value.confirm_password) {
    $q.notify({
      type: 'negative',
      message: '两次输入的新密码不一致',
    });
    return;
  }

  await changePasswordRequest({ ...passwordConfig.value });
};

// 执行退出登录
const performLogout = () => {
  // 清除本地存储
  localStorage.removeItem('auth_token');
  localStorage.removeItem('user_info');

  // 清理相关缓存
  const cacheKeys = [
    'symbols-list',
    'dashboard-stats',
    'dashboard-recent-logs',
    'timeframe-configs',
  ];
  cacheKeys.forEach((key) => {
    localStorage.removeItem(`quasar-app-${key}`);
    sessionStorage.removeItem(`quasar-app-${key}`);
  });

  // 跳转到登录页
  void router.push('/login');
};

// 刷新系统信息
const refreshSystemInfo = async () => {
  await refreshSystemInfoRequest();
};

// 检查表单是否有用户输入
const hasUserInput = () => {
  // 检查API配置是否有用户输入的内容
  const hasApiInput =
    apiConfig.value.api_key.trim() !== '' || apiConfig.value.secret_key.trim() !== '';

  // 检查密码表单是否有用户输入
  const hasPasswordInput =
    passwordConfig.value.current_password.trim() !== '' ||
    passwordConfig.value.new_password.trim() !== '' ||
    passwordConfig.value.confirm_password.trim() !== '';

  return hasApiInput || hasPasswordInput;
};

useBackgroundRefresh({
  refresh: async () => {
    await loadConfigs();
  },
  interval: 10 * 60 * 1000,
  immediate: false,
  immediateOnActivate: false,
  runOnFocus: true,
  runOnVisibilityGain: true,
  enabled: () => !hasUserInput(),
});

onMounted(async () => {
  // 检查认证状态
  const token = localStorage.getItem('auth_token');
  if (!token) {
    $q.notify({
      type: 'negative',
      message: '请先登录',
      position: 'top',
    });
    void router.push('/login');
    return;
  }

  // 初始加载配置
  await loadConfigs();
});

onUnmounted(() => {
  clearCountdown();
});
</script>
