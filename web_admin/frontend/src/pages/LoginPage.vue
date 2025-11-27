<template>
  <q-page class="login-page flex flex-center">
    <div class="login-container">
      <!-- 登录卡片 -->
      <ModernCard class="login-card" variant="glass" icon="login">
        <template #header>
          <div class="text-center">
            <!-- Logo -->
            <q-avatar size="80px" class="q-mb-md">
              <img :src="logoSvg" alt="BigZhu 交易机器人 Logo" />
            </q-avatar>

            <!-- 标题 -->
            <div class="text-h5 text-weight-bold text-primary q-mb-xs">BigZhu 交易机器人</div>
            <div class="text-subtitle2 text-grey-7">请登录以继续使用系统</div>
          </div>
        </template>

        <div class="q-pt-lg">
          <!-- 登录表单 -->
          <q-form @submit="handleLogin" class="q-gutter-md">
            <!-- 用户名输入 -->
            <ModernInput
              v-model="loginForm.username"
              type="text"
              label="用户名"
              prepend-icon="person"
              :rules="[(val) => !!val || '请输入用户名']"
              :disable="isLoading"
              autofocus
              variant="filled"
            />

            <!-- 密码输入 -->
            <ModernInput
              v-model="loginForm.password"
              :type="showPassword ? 'text' : 'password'"
              label="密码"
              prepend-icon="lock"
              :rules="[(val) => !!val || '请输入密码']"
              :disable="isLoading"
              variant="filled"
              @keyup.enter="handleLogin"
            >
              <template v-slot:append>
                <q-icon
                  :name="showPassword ? 'visibility_off' : 'visibility'"
                  class="cursor-pointer"
                  @click="showPassword = !showPassword"
                />
              </template>
            </ModernInput>

            <!-- 记住我选项 -->
            <q-checkbox
              v-model="loginForm.rememberMe"
              label="记住我"
              :disable="isLoading"
              class="text-primary"
            />

            <!-- 登录按钮 -->
            <ModernButton
              type="submit"
              variant="gradient"
              size="lg"
              class="full-width q-mt-lg"
              :loading="isLoading"
              :disable="!isFormValid"
              icon="login"
            >
              <template v-slot:loading>
                <LoadingSpinner size="sm" />
                登录中...
              </template>
              登录
            </ModernButton>
          </q-form>
        </div>

        <!-- 错误消息显示 -->
        <div v-if="errorMessage" class="q-pt-none">
          <q-banner class="text-white bg-negative" rounded>
            <template v-slot:avatar>
              <q-icon name="error" color="white" />
            </template>
            {{ errorMessage }}
          </q-banner>
        </div>

        <!-- 帮助信息已移除: 不在页面展示任何默认账号信息 -->
      </ModernCard>

      <!-- 版本信息 -->
      <div class="text-center q-mt-lg">
        <div class="text-caption text-grey-5">BigZhu Trading Bot v1.0.0</div>
        <div class="text-caption text-grey-5">© 2025 BigZhu Trading Team</div>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useQuasar } from 'quasar';
import { useAuthStore } from 'src/stores/auth-store';
import logoSvg from 'src/assets/logo.svg';
import ModernCard from 'src/components/ModernCard.vue';
import ModernInput from 'src/components/ModernInput.vue';
import ModernButton from 'src/components/ModernButton.vue';
import LoadingSpinner from 'src/components/LoadingSpinner.vue';

const router = useRouter();
const $q = useQuasar();
const authStore = useAuthStore();

// 响应式数据
const isLoading = ref(false);
const showPassword = ref(false);
const errorMessage = ref('');

const loginForm = ref({
  username: '',
  password: '',
  rememberMe: false,
});

// 表单验证
const isFormValid = computed(() => {
  return loginForm.value.username.trim() !== '' && loginForm.value.password.trim() !== '';
});

// 处理登录
const handleLogin = async () => {
  if (!isFormValid.value) return;

  isLoading.value = true;
  errorMessage.value = '';

  try {
    const result = await authStore.login(loginForm.value.username.trim(), loginForm.value.password);

    if (result.success) {
      $q.notify({
        type: 'positive',
        message: '登录成功!',
        position: 'top',
      });

      // 等待认证状态更新后跳转
      await new Promise((resolve) => setTimeout(resolve, 100));

      try {
        await router.push('/');
      } catch (navError) {
        console.error('Navigation error:', navError);
        // 如果路由跳转失败,尝试强制刷新到主页
        window.location.href = '/';
      }
    } else {
      errorMessage.value = result.message || '登录失败,请检查用户名和密码';
    }
  } catch (error: unknown) {
    console.error('Login error:', error);
    errorMessage.value = '登录过程中发生错误,请稍后重试';
  } finally {
    isLoading.value = false;
  }
};

// 移除开发环境自动填充,避免账号信息出现在界面
</script>

<style lang="scss" scoped>
@import 'src/css/quasar.variables';

.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: $spacing-lg;
  background: linear-gradient(135deg, var(--q-primary) 0%, #302b63 100%);
}

.login-container {
  width: 100%;
  max-width: 420px;
}

.login-card {
  @include glass-panel(rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.2), $border-radius-lg);

  padding: $spacing-xl;
  box-shadow: $shadow-lg;

  .q-card-section {
    padding: $spacing-lg;
  }

  .body--dark & {
    background: rgb(10 14 26 / 88%);
    border-color: $white-alpha-05;
  }
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: $spacing-md;
}

.login-actions {
  display: flex;
  flex-direction: column;
  gap: $spacing-sm;
  margin-top: $spacing-lg;
}

:deep(.q-field) {
  .q-field__control {
    @include glass-panel($white-alpha-08, $white-alpha-10, $border-radius-sm);

    &:hover {
      border-color: $white-alpha-15;
    }

    &:focus-within {
      border-color: var(--q-primary);
      background: $white-alpha-10;
    }
  }

  .q-field__native {
    color: $primary-dark;
  }

  .q-field__label {
    color: $text-subtle;
  }
}

:deep(.q-btn) {
  border-radius: $border-radius-sm;
  font-weight: 600;
  text-transform: none;
}

.login-footer {
  margin-top: $spacing-lg;
  text-align: center;
  font-size: $font-size-sm;
  color: $text-subtle;
}

@media (width <= 600px) {
  .login-page {
    padding: $spacing-md;
  }

  .login-card {
    padding: $spacing-lg;
  }
}

</style>
