<template>
  <router-view v-slot="{ Component, route }">
    <keep-alive :include="keepAliveComponents">
      <component :is="Component" :key="route.path" />
    </keep-alive>
  </router-view>
</template>

<script setup lang="ts">
import { ref } from 'vue';

// 配置需要缓存的组件
// 这些页面在切换时会保持状态,提高用户体验
const keepAliveComponents = ref([
  'SymbolsPage', // 交易对列表 - 缓存列表状态和筛选条件
  'ConfigPage', // 系统配置 - 缓存表单状态
  'LogsPage', // 日志页面 - 缓存日志数据
]);

// 不缓存的页面:
// - LoginPage: 登录页面不需要缓存,每次都应该是新的状态
// - ErrorNotFound: 错误页面不需要缓存
</script>
