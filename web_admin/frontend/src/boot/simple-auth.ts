import { boot } from 'quasar/wrappers';

export default boot(({ router }) => {
  // 简化的认证守卫
  router.beforeEach((to) => {
    // 对于测试,允许所有路由访问
    if (to.path === '/login') {
      return '/'; // 重定向到主页
    }
    return true;
  });
});
