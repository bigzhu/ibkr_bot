import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useAuthStore = defineStore('auth', () => {
  const isAuthenticated = ref(true); // 简化测试,默认已认证
  const user = ref({
    username: 'admin',
    email: 'admin@example.com',
  });

  const login = (credentials: { username: string; password: string }): Promise<{
    success: boolean;
    message?: string;
  }> => {
    // 简化登录逻辑
    if (credentials.username === 'admin' && credentials.password === 'password') {
      isAuthenticated.value = true;
      return Promise.resolve({ success: true });
    }
    return Promise.resolve({ success: false, message: '用户名或密码错误' });
  };

  const logout = () => {
    isAuthenticated.value = false;
    user.value = null;
  };

  return {
    isAuthenticated,
    user,
    login,
    logout,
  };
});
