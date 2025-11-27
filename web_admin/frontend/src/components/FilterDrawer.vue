<template>
  <!-- 筛选器触发按钮 -->
  <div class="filter-trigger-wrapper q-mb-sm">
    <ModernButton variant="glass" icon="filter_list" size="sm" @click="drawerVisible = true">
      {{ triggerText }}
      <q-badge v-if="activeFilterCount > 0" color="primary" floating>
        {{ activeFilterCount }}
      </q-badge>
    </ModernButton>
  </div>

  <!-- 筛选器抽屉 -->
  <q-drawer
    v-model="drawerVisible"
    side="right"
    overlay
    bordered
    :width="width"
    class="filter-drawer"
    behavior="mobile"
  >
    <div class="filter-drawer-content">
      <!-- 抽屉头部 -->
      <div class="filter-drawer-header">
        <div class="header-icon">
          <q-icon name="filter_list" size="1.5rem" />
        </div>
        <div class="header-title">{{ title }}</div>
        <q-space />
        <q-btn icon="close" flat round dense @click="drawerVisible = false" />
      </div>

      <!-- 抽屉内容 -->
      <div class="filter-drawer-body">
        <FilterField
          v-for="config in fieldConfigs"
          :key="config.key"
          :type="config.type"
          :label="config.label"
          :options="config.options"
          :model-value="filters[config.key]"
          @update:model-value="updateFilter(config.key, $event)"
          v-bind="config.props || {}"
        >
          <!-- 传递插槽内容 -->
          <template v-if="$slots[`field-${config.key}`]" #option="{ option }">
            <slot :name="`field-${config.key}`" :option="option" />
          </template>
        </FilterField>
      </div>

      <!-- 抽屉底部 -->
      <div class="filter-drawer-footer">
        <ModernButton
          variant="gradient"
          icon="search"
          size="sm"
          @click="handleApply"
          :loading="loading"
          class="full-width q-mb-sm"
        >
          {{ applyText }}
        </ModernButton>
        <ModernButton
          variant="ghost"
          icon="refresh"
          size="sm"
          @click="handleReset"
          class="full-width"
        >
          {{ resetText }}
        </ModernButton>
      </div>
    </div>
  </q-drawer>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import ModernButton from './ModernButton.vue';
import FilterField from './FilterField.vue';

interface FilterOption {
  label?: string;
  value?: unknown;
  [key: string]: unknown;
}

type FilterValue = string | number | boolean | (string | number)[] | Date | null | undefined;

interface FilterFieldConfig {
  key: string;
  type: 'select' | 'checkbox' | 'checkbox-group' | 'radio-group' | 'input' | 'date';
  label: string;
  options?: FilterOption[];
  props?: Record<string, unknown>;
}

interface Props {
  // 筛选器数据
  filters: Record<string, FilterValue>;
  fieldConfigs: FilterFieldConfig[];

  // UI 文本
  title?: string;
  triggerText?: string;
  applyText?: string;
  resetText?: string;

  // 样式配置
  width?: number;

  // 状态
  loading?: boolean;

  // 自动应用
  autoApply?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  title: '筛选条件',
  triggerText: '筛选条件',
  applyText: '应用筛选',
  resetText: '重置条件',
  width: 320,
  loading: false,
  autoApply: false,
});

const emit = defineEmits<{
  'update:filters': [filters: Record<string, FilterValue>];
  apply: [filters: Record<string, FilterValue>];
  reset: [];
  change: [key: string, value: FilterValue];
}>();

// 抽屉显示状态
const drawerVisible = ref(false);

// 计算激活的筛选条件数量
const activeFilterCount = computed(() => {
  let count = 0;

  for (const config of props.fieldConfigs) {
    const value = props.filters[config.key];

    // 更严格的空值检查
    if (value === null || value === undefined) {
      continue;
    }

    // 数组类型(多选)- 只有非空数组才算激活
    if (Array.isArray(value)) {
      if (value.length > 0) {
        count++;
      }
    }
    // 布尔类型(复选框)- 只有true才算激活
    else if (typeof value === 'boolean') {
      if (value === true) {
        count++;
      }
    }
    // 字符串类型 - 只有非空字符串才算激活
    else if (typeof value === 'string') {
      if (value.trim() !== '') {
        count++;
      }
    }
    // 数字类型 - 非零认为激活
    else if (typeof value === 'number') {
      if (!Number.isNaN(value) && value !== 0) {
        count++;
      }
    }
    // 日期类型 - 只要有值就算激活
    else if (value instanceof Date) {
      count++;
    }
    // 其他类型 - 转换为字符串后检查
    else if (value) {
      const strValue = String(value).trim();
      if (strValue !== '' && strValue !== '0' && strValue !== 'false') {
        count++;
      }
    }
  }

  return count;
});

// 更新筛选器值
const updateFilter = (key: string, value: FilterValue) => {
  const updatedFilters: Record<string, FilterValue> = {
    ...props.filters,
    [key]: value,
  };

  emit('update:filters', updatedFilters);
  emit('change', key, value);

  // 自动应用
  if (props.autoApply) {
    emit('apply', updatedFilters);
  }
};

// 处理字段变更
// 应用筛选
const handleApply = () => {
  emit('apply', props.filters);
  drawerVisible.value = false;
};

// 重置筛选
const handleReset = () => {
  const resetFilters: Record<string, FilterValue> = {};

  // 根据字段配置初始化默认值
  for (const config of props.fieldConfigs) {
    switch (config.type) {
      case 'checkbox-group':
        resetFilters[config.key] = [];
        break;
      case 'checkbox':
        resetFilters[config.key] = false;
        break;
      default:
        resetFilters[config.key] = '';
    }
  }

  emit('update:filters', resetFilters);
  emit('reset');

  if (props.autoApply) {
    emit('apply', resetFilters);
  }

  drawerVisible.value = false;
};

// 暴露组件方法
defineExpose({
  open: () => {
    drawerVisible.value = true;
  },
  close: () => {
    drawerVisible.value = false;
  },
  toggle: () => {
    drawerVisible.value = !drawerVisible.value;
  },
});
</script>

<style lang="scss" scoped>
.filter-trigger-wrapper {
  display: flex;
  justify-content: flex-end;
  padding: 0 16px;
}

.filter-drawer {
  :deep(.q-drawer__content) {
    background: rgb(24 26 33 / 95%);
    backdrop-filter: blur(20px);
  }
}

.filter-drawer-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.filter-drawer-header {
  display: flex;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid rgb(255 255 255 / 10%);

  .header-icon {
    margin-right: 12px;
    color: var(--q-primary);
  }

  .header-title {
    font-size: 1.2rem;
    font-weight: 500;
  }
}

.filter-drawer-body {
  flex: 1;
  padding: 24px 16px;
  overflow-y: auto;
}

.filter-drawer-footer {
  padding: 16px;
  border-top: 1px solid rgb(255 255 255 / 10%);

  .full-width {
    width: 100%;
  }
}
</style>
