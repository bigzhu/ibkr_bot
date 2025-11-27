import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import { Notify } from 'quasar';
import { apiService } from 'src/services';

export interface User {
  username: string;
  isAdmin: boolean;
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null);
  const token = ref<string | null>(localStorage.getItem('auth_token'));

  const isAuthenticated = computed(() => !!token.value && !!user.value);

  const login = async (username: string, password: string) => {
    try {
      const response = await apiService.auth.login({ username, password });

      if (response.success && response.token) {

        // 使用后端实际响应结构
        token.value = response.token;
        user.value = {
          username: username, // 使用输入的用户名,后端登录响应不包含 username
          isAdmin: true, // 默认为 admin,后端只有一个 admin 用户
        };


        // Save to localStorage
        localStorage.setItem('auth_token', token.value);
        localStorage.setItem('user_info', JSON.stringify(user.value));


        return { success: true };
      } else {
        return { success: false, message: response.message || '登录失败' };
      }
    } catch (error: unknown) {
      console.error('Login error:', error);
      return {
        success: false,
        message: apiService.handleError(error),
      };
    }
  };

  const logout = () => {
    user.value = null;
    token.value = null;
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_info');

    Notify.create({
      type: 'positive',
      message: '已成功退出登录',
      position: 'top',
    });
  };

  const checkAuth = async () => {
    const savedToken = localStorage.getItem('auth_token');
    const savedUser = localStorage.getItem('user_info');

    if (savedToken && savedUser) {
      token.value = savedToken;
      try {
        user.value = JSON.parse(savedUser);
      } catch {
        // If parsing fails, clear storage
        logout();
        return false;
      }

      // Verify token is still valid
      try {
        const verifyResponse = await apiService.auth.verify();
        if (verifyResponse.success && verifyResponse.username) {
          // 更新用户信息为后端返回的实际用户名
          user.value = {
            username: verifyResponse.username,
            isAdmin: true,
          };
          localStorage.setItem('user_info', JSON.stringify(user.value));
          return true;
        } else {
          // Token invalid, clear storage
          logout();
          return false;
        }
      } catch {
        // Token invalid, clear storage
        logout();
        return false;
      }
    }

    return false;
  };

  // Initialize auth state
  void checkAuth();

  return {
    user,
    token,
    isAuthenticated,
    login,
    logout,
    checkAuth,
  };
});
