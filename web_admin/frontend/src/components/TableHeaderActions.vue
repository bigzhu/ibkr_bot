<template>
  <div class="header-actions">
    <!-- 自定义操作插槽 -->
    <slot name="custom-actions" />

    <!-- WebSocket 连接状态按钮 -->
    <q-btn
      v-if="showWebSocketStatus && wsState"
      :color="wsState.connected ? 'green-7' : wsState.reconnecting ? 'orange-7' : 'red-7'"
      :icon="
        wsState.connected
          ? 'radio_button_checked'
          : wsState.reconnecting
            ? 'sync'
            : 'radio_button_unchecked'
      "
      :class="{ 'animate-spin': wsState.reconnecting }"
      flat
      round
      size="sm"
      @click="wsState.connected ? null : handleWebSocketReconnect"
      :disable="wsState.connected || wsState.reconnecting"
    >
      <q-tooltip>
        {{
          wsState.connected
            ? '实时连接正常'
            : wsState.reconnecting
              ? '重连中,请稍候...'
              : '连接断开,点击重连'
        }}
      </q-tooltip>
    </q-btn>

    <!-- 刷新按钮 -->
    <q-btn
      v-if="showRefresh"
      color="info"
      icon="refresh"
      flat
      round
      size="sm"
      :loading="loading"
      @click="handleRefresh"
    >
      <q-tooltip>{{ refreshTooltip }}</q-tooltip>
    </q-btn>

    <!-- 同步按钮 -->
    <q-btn
      v-if="showSync"
      color="primary"
      icon="sync"
      flat
      round
      size="sm"
      :loading="syncLoading"
      @click="handleSync"
    >
      <q-tooltip>{{ syncTooltip }}</q-tooltip>
    </q-btn>

    <!-- 导出按钮 -->
    <q-btn
      v-if="showExport"
      color="secondary"
      icon="file_download"
      flat
      round
      size="sm"
      @click="handleExport"
    >
      <q-tooltip>{{ exportTooltip }}</q-tooltip>
    </q-btn>

    <!-- 清空按钮 -->
    <q-btn
      v-if="showClear"
      color="negative"
      icon="delete_sweep"
      flat
      round
      size="sm"
      @click="handleClear"
    >
      <q-tooltip>{{ clearTooltip }}</q-tooltip>
    </q-btn>

    <!-- 列控制组件插槽 -->
    <slot name="column-control" />
  </div>
</template>

<script setup lang="ts">
interface WebSocketState {
  connected: boolean;
  reconnecting: boolean;
  error?: string | null;
}

interface Props {
  /** 是否显示WebSocket连接状态 */
  showWebSocketStatus?: boolean;
  /** WebSocket状态对象 */
  wsState?: WebSocketState;
  /** 是否显示刷新按钮 */
  showRefresh?: boolean;
  /** 刷新按钮loading状态 */
  loading?: boolean;
  /** 刷新按钮tooltip */
  refreshTooltip?: string;
  /** 是否显示同步按钮 */
  showSync?: boolean;
  /** 同步按钮loading状态 */
  syncLoading?: boolean;
  /** 同步按钮tooltip */
  syncTooltip?: string;
  /** 是否显示导出按钮 */
  showExport?: boolean;
  /** 导出按钮tooltip */
  exportTooltip?: string;
  /** 是否显示清空按钮 */
  showClear?: boolean;
  /** 清空按钮tooltip */
  clearTooltip?: string;
}

withDefaults(defineProps<Props>(), {
  showWebSocketStatus: false,
  showRefresh: true,
  loading: false,
  refreshTooltip: '刷新数据',
  showSync: false,
  syncLoading: false,
  syncTooltip: '同步数据',
  showExport: false,
  exportTooltip: '导出数据',
  showClear: false,
  clearTooltip: '清空数据',
});

const emit = defineEmits<{
  refresh: [];
  sync: [];
  export: [];
  clear: [];
  'websocket-reconnect': [];
}>();

const handleRefresh = () => emit('refresh');
const handleSync = () => emit('sync');
const handleExport = () => emit('export');
const handleClear = () => emit('clear');
const handleWebSocketReconnect = () => emit('websocket-reconnect');
</script>

<style lang="scss" scoped>
.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
</style>
