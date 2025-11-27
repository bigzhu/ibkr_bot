import { ref, computed } from 'vue';

export interface TableColumn {
  name: string;
  label: string;
  field: string | ((row: Record<string, unknown>) => unknown);
  align?: 'left' | 'center' | 'right';
  sortable?: boolean;
  required?: boolean;
  format?: (val: unknown, row: Record<string, unknown>) => string;
  style?: string | ((row: Record<string, unknown>) => string);
  classes?: string | ((row: Record<string, unknown>) => string);
  headerStyle?: string;
  headerClasses?: string;
}

export function useTableColumns(
  originalColumns: TableColumn[],
  defaultVisibleColumns: string[],
  storageKey: string,
) {
  // 所有可用的列
  const allColumns = ref([...originalColumns]);

  // 从 localStorage 加载已保存的列顺序和可见性
  const loadColumnSettings = () => {
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved) {
        const settings = JSON.parse(saved);
        if (settings.columnOrder && Array.isArray(settings.columnOrder)) {
          // 恢复列顺序
          const orderedColumns = settings.columnOrder
            .map((name: string) => originalColumns.find((col) => col.name === name))
            .filter(Boolean);

          // 添加任何新的列(可能在更新后添加的)
          const existingNames = new Set(settings.columnOrder);
          const newColumns = originalColumns.filter((col) => !existingNames.has(col.name));

          allColumns.value = [...orderedColumns, ...newColumns] as TableColumn[];
        }

        if (settings.visibleColumns && Array.isArray(settings.visibleColumns)) {
          return settings.visibleColumns;
        }
      }
    } catch (error) {
      console.warn('Failed to load column settings:', error);
    }
    return defaultVisibleColumns;
  };

  // 当前显示的列
  const visibleColumns = ref(loadColumnSettings());

  // 保存设置到 localStorage
  const saveColumnSettings = () => {
    try {
      const settings = {
        columnOrder: allColumns.value.map((col) => col.name),
        visibleColumns: visibleColumns.value,
      };
      localStorage.setItem(storageKey, JSON.stringify(settings));
    } catch (error) {
      console.warn('Failed to save column settings:', error);
    }
  };

  // 计算实际显示的列
  const filteredColumns = computed(() => {
    return allColumns.value.filter((col) => visibleColumns.value.includes(col.name));
  });

  // 切换列的显示/隐藏
  const toggleColumn = (columnName: string) => {
    const index = visibleColumns.value.indexOf(columnName);
    if (index > -1) {
      // 检查是否是必需的列
      const column = allColumns.value.find((col) => col.name === columnName);
      if (column?.required) {
        return false; // 不允许隐藏必需的列
      }
      visibleColumns.value.splice(index, 1);
    } else {
      visibleColumns.value.push(columnName);
    }
    saveColumnSettings();
    return true;
  };

  // 上移列
  const moveColumnUp = (index: number) => {
    if (index > 0) {
      const temp = allColumns.value[index];
      allColumns.value[index] = allColumns.value[index - 1];
      allColumns.value[index - 1] = temp;
      saveColumnSettings();
    }
  };

  // 下移列
  const moveColumnDown = (index: number) => {
    if (index < allColumns.value.length - 1) {
      const temp = allColumns.value[index];
      allColumns.value[index] = allColumns.value[index + 1];
      allColumns.value[index + 1] = temp;
      saveColumnSettings();
    }
  };

  // 重置为默认设置
  const resetColumns = () => {
    allColumns.value = [...originalColumns];
    visibleColumns.value = [...defaultVisibleColumns];
    saveColumnSettings();
  };

  // 是否显示某列
  const isColumnVisible = (columnName: string) => {
    return visibleColumns.value.includes(columnName);
  };

  // 是否为必需列
  const isColumnRequired = (columnName: string) => {
    const column = allColumns.value.find((col) => col.name === columnName);
    return Boolean(column?.required);
  };

  return {
    allColumns,
    visibleColumns,
    filteredColumns,
    toggleColumn,
    moveColumnUp,
    moveColumnDown,
    resetColumns,
    isColumnVisible,
    isColumnRequired,
    saveColumnSettings,
  };
}
