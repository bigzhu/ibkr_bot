import { boot } from 'quasar/wrappers';

export default boot(({ router }) => {
  // Authentication guard
  router.beforeEach((to, from, next) => {
    // Simple token-based check for now
    const token = localStorage.getItem('auth_token');
    const isAuthenticated = !!token;

    // Public routes that don't require authentication
    const publicRoutes = ['/login'];
    const isPublicRoute = publicRoutes.includes(to.path);

    if (!isAuthenticated && !isPublicRoute) {
      next('/login');
    } else if (isAuthenticated && to.path === '/login') {
      next('/');
    } else {
      next();
    }
  });
});
