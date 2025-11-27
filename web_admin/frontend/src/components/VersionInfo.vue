<template>
  <div class="version-info">
    <q-chip :color="isDev ? 'orange' : 'primary'" text-color="white" size="sm" dense>
      <q-icon name="info" class="q-mr-xs" />
      {{ versionText }}
      <q-tooltip class="bg-dark text-white">
        <div class="q-pa-sm">
          <div><strong>版本:</strong> {{ appVersion }}</div>
          <div><strong>构建时间:</strong> {{ buildTime }}</div>
          <div><strong>Git:</strong> {{ gitHash }} ({{ gitBranch }})</div>
          <div><strong>环境:</strong> {{ isDev ? '开发版' : '生产版' }}</div>
        </div>
      </q-tooltip>
    </q-chip>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

// 从环境变量获取版本信息
const appVersion = process.env.APP_VERSION || '1.0.0';
const buildTime = process.env.BUILD_TIME || '未知';
const gitHash = process.env.GIT_HASH || 'dev';
const gitBranch = process.env.GIT_BRANCH || 'unknown';

// 判断是否为开发版本
const isDev = computed(() => {
  return (
    appVersion.includes('dev') ||
    appVersion.includes('build') ||
    gitHash === 'dev' ||
    gitBranch === 'develop'
  );
});

// 显示的版本文本
const versionText = computed(() => {
  return '殚精竭虑的作品';
});
</script>

<style lang="scss" scoped>
.version-info {
  display: inline-block;
}
</style>
