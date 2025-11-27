<template>
  <q-layout view="lHh Lpr lFf">
    <!-- 头部应用栏 - 现代化设计 -->
    <q-header elevated :class="headerClass">
      <q-toolbar class="modern-toolbar">
        <q-btn
          flat
          dense
          round
          icon="menu"
          aria-label="Menu"
          @click="toggleLeftDrawer"
          class="menu-btn q-mr-sm"
        />

        <!-- Logo区域 -->
        <div class="logo-section q-mr-md">
          <q-avatar class="logo-avatar" size="36px">
            <img :src="logoSvg" alt="BigZhu 交易机器人 Logo" />
          </q-avatar>
          <div class="logo-text">
            <div class="text-gradient logo-title">BigZhu</div>
            <div class="text-caption text-grey-4 mobile-hidden">交易机器人</div>
          </div>
        </div>

        <!-- 面包屑导航 - 桌面端 -->
        <div class="breadcrumb-section desktop-only q-ml-md">
          <q-icon name="folder" class="text-grey-4 q-mr-xs" size="18px" />
          <span class="text-h6 text-white">{{ currentPageTitle }}</span>
        </div>

        <!-- 移动端页面标题 -->
        <div class="mobile-only text-h6 text-white">
          {{ currentPageTitle }}
        </div>

        <q-space />

        <!-- 快捷操作区域 -->
        <div class="action-section q-gutter-sm">
          <!-- 用户菜单 -->
          <q-btn-dropdown
            flat
            rounded
            no-caps
            :label="getAuthStore().user?.username || 'Admin'"
            icon="account_circle"
            class="user-menu"
          >
            <q-list class="user-dropdown">
              <q-item clickable @click="toggleTheme" class="dropdown-item">
                <q-item-section avatar>
                  <q-icon
                    :name="isDark ? 'light_mode' : 'dark_mode'"
                    :color="isDark ? 'amber' : 'blue'"
                  />
                </q-item-section>
                <q-item-section>
                  <q-item-label>切换为{{ isDark ? '明亮' : '黑暗' }}主题</q-item-label>
                </q-item-section>
              </q-item>

              <q-separator inset />

              <q-item clickable @click="showUserProfile" class="dropdown-item">
                <q-item-section avatar>
                  <q-icon name="person" color="primary" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>用户资料</q-item-label>
                </q-item-section>
              </q-item>

              <q-item clickable @click="showSettings" class="dropdown-item">
                <q-item-section avatar>
                  <q-icon name="settings" color="grey-6" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>系统配置</q-item-label>
                </q-item-section>
              </q-item>

              <q-separator inset />

              <q-item clickable @click="handleLogout" class="dropdown-item logout-item">
                <q-item-section avatar>
                  <q-icon name="logout" color="negative" />
                </q-item-section>
                <q-item-section>
                  <q-item-label>退出登录</q-item-label>
                </q-item-section>
              </q-item>
            </q-list>
          </q-btn-dropdown>
        </div>
      </q-toolbar>
    </q-header>

    <!-- 左侧导航抽屉 - 现代化设计 -->
    <q-drawer
      v-model="leftDrawerOpen"
      :width="280"
      class="modern-drawer"
      :class="{ 'drawer-dark': isDark }"
    >
      <div class="drawer-content">
        <!-- 抽屉头部 -->
        <div class="drawer-header q-pa-md">
          <div class="flex items-center">
            <q-avatar class="logo-avatar-drawer" size="32px">
              <img :src="logoSvg" alt="Logo" />
            </q-avatar>
            <div class="q-ml-sm">
              <div class="text-weight-bold text-primary">BigZhu Bot</div>
              <div class="text-caption text-grey-6">殚精竭虑的作品</div>
            </div>
          </div>
        </div>

        <q-separator />

        <!-- 导航区域 -->
        <q-scroll-area class="drawer-navigation fit">
          <q-list class="navigation-list">
            <!-- 导航菜单项 -->
            <template v-for="nav in navigationList" :key="nav.title">
              <q-item
                clickable
                v-ripple
                :to="nav.link"
                exact-active-class="nav-item-active"
                class="nav-item"
              >
                <q-item-section avatar class="nav-icon-section">
                  <q-icon
                    :name="nav.icon"
                    size="20px"
                    :class="route.path === nav.link ? 'text-primary' : 'text-grey-6'"
                  />
                </q-item-section>
                <q-item-section class="nav-text-section">
                  <q-item-label
                    class="nav-title"
                    :class="
                      route.path === nav.link ? 'text-weight-bold text-primary' : 'text-grey-8'
                    "
                  >
                    {{ nav.title }}
                  </q-item-label>
                  <q-item-label caption v-if="nav.caption" class="nav-caption text-grey-5">
                    {{ nav.caption }}
                  </q-item-label>
                </q-item-section>

                <!-- 活跃指示器 -->
                <div v-if="route.path === nav.link" class="nav-active-indicator"></div>
              </q-item>
            </template>
          </q-list>
        </q-scroll-area>

        <!-- 抽屉底部 -->
        <div class="drawer-footer">
          <q-separator />

          <!-- 版本信息 -->
          <div class="version-info q-pa-sm text-center">
            <div class="text-caption text-grey-6">构建于 {{ buildTime }}</div>
          </div>
        </div>
      </div>
    </q-drawer>

    <!-- 主内容区域 -->
    <q-page-container>
      <!-- 页面加载指示器 -->
      <q-linear-progress v-if="isLoading" indeterminate color="primary" size="2px" />

      <router-view />
    </q-page-container>
  </q-layout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useQuasar } from 'quasar';
import { useAuthStore } from 'src/stores/auth-store';
import logoSvg from 'src/assets/logo.svg';
import { formatDateTime as formatDateTimeUtil } from 'src/utils/datetime';

const $q = useQuasar();
const router = useRouter();
const route = useRoute();

// Defensive store initialization - only access when needed
let authStore: ReturnType<typeof useAuthStore> | null = null;
const getAuthStore = () => {
  if (!authStore) {
    authStore = useAuthStore();
  }
  return authStore;
};

// 从localStorage读取菜单状态,默认为收起
const savedState = localStorage.getItem('leftDrawerOpen');
const leftDrawerOpen = ref(savedState === 'true');
const isLoading = ref(false);

// 版本信息
const buildTime = ref(
  formatDateTimeUtil(process.env.BUILD_TIME || new Date(), { includeSeconds: true }),
);

// 主题切换状态
const isDark = ref($q.dark.isActive);

// 切换主题
const toggleTheme = () => {
  $q.dark.toggle();
  isDark.value = $q.dark.isActive;

  // 保存主题选择到本地存储
  localStorage.setItem('theme-preference', $q.dark.isActive ? 'dark' : 'light');

  $q.notify({
    type: 'positive',
    message: `已切换为${$q.dark.isActive ? '黑暗' : '明亮'}主题`,
    position: 'top',
    timeout: 2000,
  });
};

// 导航菜单配置
const navigationList = [
  {
    title: '交易对管理',
    caption: '币种信息同步',
    icon: 'currency_exchange',
    link: '/symbols',
  },
  {
    title: '交易日志',
    caption: '历史记录查看',
    icon: 'history',
    link: '/logs',
  },
  {
    title: '成交订单',
    caption: '已成交订单查看',
    icon: 'receipt',
    link: '/filled-orders',
  },
  {
    title: '盈亏统计',
    caption: '交易盈亏分析和统计',
    icon: 'analytics',
    link: '/profit-analysis',
  },
  {
    title: '盈亏统计 (JPY)',
    caption: 'JPY 交易盈亏分析',
    icon: 'analytics',
    link: '/profit-analysis-jpy',
  },
];

// 当前页面标题
const currentPageTitle = computed(() => {
  if (route.path === '/config') {
    return '系统配置';
  }

  const currentNav = navigationList.find((nav) => nav.link === route.path);
  return currentNav?.title || '未知页面';
});

// 根据主题动态设置导航栏样式
const headerClass = computed(() => {
  if ($q.dark.isActive) {
    // Dark 模式下使用深色导航栏
    return 'header-dark text-white';
  } else {
    // Light 模式下使用主色调
    return 'bg-primary text-white';
  }
});

// 切换左侧抽屉
const toggleLeftDrawer = () => {
  leftDrawerOpen.value = !leftDrawerOpen.value;
};

// 监听菜单状态变化,保存到localStorage
watch(leftDrawerOpen, (newValue) => {
  localStorage.setItem('leftDrawerOpen', newValue.toString());
});

// 显示用户资料
const showUserProfile = () => {
  $q.dialog({
    title: '用户资料',
    message: `当前用户: ${getAuthStore().user?.username || 'Admin'}`,
    ok: '确定',
  });
};

// 显示系统设置
const showSettings = () => {
  void router.push('/config');
};

// 处理退出登录
const handleLogout = () => {
  $q.dialog({
    title: '确认退出',
    message: '确定要退出登录吗?',
    cancel: {
      label: '取消',
      color: 'grey',
      flat: true,
    },
    ok: {
      label: '退出登录',
      color: 'negative',
      unelevated: true,
    },
    persistent: true,
  }).onOk(() => {
    getAuthStore().logout();
    $q.notify({
      type: 'positive',
      message: '已安全退出登录',
      position: 'top',
    });
    void router.push('/login');
  });
};

// checkSystemStatus 函数已移除 - 不再需要系统状态检查

// statusInterval 已移除 - 不再需要系统状态定时检查

onMounted(() => {
  // 设置主题
  const savedTheme = localStorage.getItem('theme-preference');
  // 如果保存的主题不是'light',则默认为黑暗主题
  $q.dark.set(savedTheme !== 'light');
  isDark.value = $q.dark.isActive;
});
</script>

<style lang="scss" scoped>
@import 'src/css/quasar.variables';

// 🎨 现代化布局样式
// --------------------------------------------------


.q-layout {
  background: var(--q-color-grey-1);

  .body--dark & {
    background: $dark-page;
  }
}

// 🔝 头部工具栏样式
// --------------------------------------------------

.modern-toolbar {
  padding: 0 $spacing-md;
  min-height: 64px;
  background: $gradient-primary;
  backdrop-filter: $glass-backdrop;
  border-bottom: 1px solid $white-alpha-10;

  .menu-btn {
    transition: all $transition-base $ease-out-cubic;

    &:hover {
      transform: scale(1.1);
      background: $white-alpha-10;
    }
  }

  .logo-section {
    display: flex;
    align-items: center;

    .logo-avatar {
      border: 2px solid $white-alpha-20;
      transition: all $transition-base $ease-out-cubic;

      &:hover {
        transform: scale(1.05);
        border-color: $white-alpha-20;
      }
    }

    .logo-text {
      margin-left: 8px;

      .logo-title {
        font-size: 1.2rem;
        font-weight: 700;
        line-height: 1;
        text-shadow: 0 1px 2px $black-alpha-10;

        // 确保文字可见性的额外保护
        @supports not (background-clip: text) {
          color: white !important;
        }
      }
    }
  }

  .breadcrumb-section {
    display: flex;
    align-items: center;
    padding: $spacing-xs $spacing-sm;
    background: $white-alpha-10;
    border-radius: $border-radius-sm;
    backdrop-filter: $glass-backdrop;

    span {
      margin-left: 4px;
    }
  }

  .action-section {
    display: flex;
    align-items: center;
    gap: $spacing-xs;

    .network-indicator {
      transition: all $transition-base $ease-out-cubic;

      &:hover {
        transform: scale(1.1);
      }
    }

    .notification-btn {
      transition: all $transition-base $ease-out-cubic;

      &:hover {
        transform: scale(1.1);
        background: $white-alpha-10;
      }
    }

    .user-menu {
      padding: $spacing-sm $spacing-md;
      border-radius: $border-radius-xl;
      background: $white-alpha-10;
      border: 1px solid $white-alpha-20;
      transition: all $transition-base $ease-out-cubic;

      &:hover {
        background: $white-alpha-15;
        transform: translateY(-1px);
      }
    }
  }
}

// Dark 模式下的导航栏样式
:deep(.header-dark) {
  background: linear-gradient(135deg, $dark 0%, $dark-surface 100%) !important;
  border-bottom: 1px solid $white-alpha-10;
  box-shadow: 0 2px 12px rgb(0 0 0 / 40%) !important;
}

// 用户下拉菜单样式
:deep(.user-dropdown) {
  border-radius: $border-radius-md;
  overflow: hidden;
  box-shadow: $shadow-lg;
  min-width: $menu-width-md;

  .dropdown-item {
    padding: 12px 16px;
    transition: all $transition-fast $ease-out-cubic;

    &:hover {
      background: rgb(102 126 234 / 10%);
      transform: translateX(4px);
    }

    &.logout-item:hover {
      background: rgb(255 107 107 / 10%);
      color: var(--q-negative);
    }

    .q-item-section--avatar {
      min-width: 32px;
    }
  }
}

// 🗂️ 侧边抽屉样式
// --------------------------------------------------

.modern-drawer {
  border-right: 1px solid $black-alpha-05;
  background: white;

  .body--dark & {
    background: $dark-surface;
    border-right: 1px solid $dark-border;
  }

  .drawer-content {
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  .drawer-header {
    background: rgb(102 126 234 / 2%);
    border-bottom: 1px solid $black-alpha-05;

    .body--dark & {
      background: rgb(102 126 234 / 5%);
      border-bottom: 1px solid $dark-border;
    }

    .logo-avatar-drawer {
      border: 2px solid rgb(102 126 234 / 20%);
      transition: all $transition-base $ease-out-cubic;

      &:hover {
        transform: scale(1.05);
        border-color: var(--q-primary);
      }
    }
  }

  .drawer-navigation {
    flex: 1;
    padding: 8px 0;
  }

  .navigation-list {
    .nav-item {
      margin: 4px 12px;
      border-radius: $border-radius-sm;
      position: relative;
      transition: all $transition-base $ease-out-cubic;

      &:hover {
        background: rgb(102 126 234 / 5%);
        transform: translateX(2px);

        .body--dark & {
          background: rgb(102 126 234 / 10%);
        }
      }

      &.nav-item-active {
        background: rgb(102 126 234 / 10%);

        .body--dark & {
          background: rgb(102 126 234 / 20%);
        }
      }

      .nav-icon-section {
        min-width: 40px;
      }

      .nav-title {
        font-weight: 500;
        transition: all $transition-fast;
      }

      .nav-caption {
        font-size: 0.75rem;
        margin-top: 2px;
      }

      .nav-active-indicator {
        position: absolute;
        right: 0;
        top: 50%;
        transform: translateY(-50%);
        width: 3px;
        height: 24px;
        background: var(--q-primary);
        border-radius: 2px;
        animation: main-layout-nav-slide-in 0.3s $ease-out-cubic;
      }
    }
  }

  .drawer-footer {
    margin-top: auto;

    .version-info {
      background: $black-alpha-02;

      .body--dark & {
        background: rgb(255 255 255 / 2%);
      }
    }
  }
}

// 🎯 动画定义
// --------------------------------------------------

@keyframes main-layout-nav-slide-in {
  from {
    opacity: 0;
    transform: translateY(-50%) scaleY(0);
  }

  to {
    opacity: 1;
    transform: translateY(-50%) scaleY(1);
  }
}

// 📱 响应式优化
// --------------------------------------------------

@media (width <= 768px) {
  .desktop-only {
    display: none !important;
  }

  .mobile-hidden {
    display: none !important;
  }

  .modern-toolbar {
    padding: 0 12px;

    .logo-section .logo-text .logo-title {
      font-size: 1rem;
    }

    .action-section {
      gap: 2px;

      .user-menu {
        padding: 6px 12px;
      }
    }
  }

  .modern-drawer {
    .drawer-header {
      padding: 12px;
    }

    .navigation-list .nav-item {
      margin: 3px 8px;
    }
  }
}

@media (width >= 769px) {
  .mobile-only {
    display: none !important;
  }

  .desktop-hidden {
    display: none !important;
  }
}

// 🌙 深色模式特殊优化
// --------------------------------------------------

.body--dark {
  .modern-toolbar {
    .logo-section .logo-avatar {
      border-color: rgb(255 255 255 / 30%);
    }

    .breadcrumb-section {
      background: $white-alpha-05;
    }

    .action-section {
      .user-menu {
        background: $white-alpha-05;
        border-color: $white-alpha-10;

        &:hover {
          background: $white-alpha-10;
        }
      }
    }
  }
}
</style>
