import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  // Login page with layout
  {
    path: '/login',
    component: () => import('layouts/LoginLayout.vue'),
    meta: { requiresAuth: false },
    children: [
      {
        path: '',
        name: 'Login',
        component: () => import('pages/LoginPage.vue'),
      },
    ],
  },

  // Main app layout
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/logs',
      },
      {
        path: '/logs',
        name: 'Logs',
        component: () => import('pages/LogsPage.vue'),
      },
      {
        path: '/config',
        name: 'Config',
        component: () => import('pages/ConfigPage.vue'),
      },
      {
        path: '/symbols',
        name: 'Symbols',
        component: () => import('pages/SymbolsPage.vue'),
      },
      {
        path: '/filled-orders',
        name: 'FilledOrders',
        component: () => import('pages/FilledOrdersPage.vue'),
      },
      {
        path: '/profit-analysis',
        name: 'ProfitAnalysis',
        component: () => import('pages/ProfitAnalysisPage.vue'),
        meta: { quoteAsset: 'USDC' },
      },
      {
        path: '/profit-analysis-jpy',
        name: 'ProfitAnalysisJPY',
        component: () => import('pages/ProfitAnalysisPage.vue'),
        meta: { quoteAsset: 'JPY' },
      },
    ],
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('layouts/ErrorLayout.vue'),
    children: [
      {
        path: '',
        component: () => import('pages/ErrorNotFound.vue'),
      },
    ],
  },
];

export default routes;
