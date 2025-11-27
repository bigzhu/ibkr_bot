import { h } from 'vue';
import { QTd } from 'quasar';
import TradingPairIcon from 'src/components/TradingPairIcon.vue';
import AmountDisplay from 'src/components/AmountDisplay.vue';
import PriceDisplay from 'src/components/PriceDisplay.vue';

type TableCellProps<RowData = Record<string, unknown>, Value = unknown> = Record<string, unknown> & {
  row: RowData;
  value: Value;
};

const createTableCell = (slotProps: TableCellProps, children: unknown[]) =>
  h(QTd, slotProps, {
    default: () => children,
  });

// 交易对单元格渲染器
export const renderPairCell = (
  props: TableCellProps<Record<string, unknown>, string>,
  options: { showText?: boolean; iconSize?: string; textClass?: string } = {},
) => {
  const { showText = true, iconSize = '20px', textClass = 'text-weight-medium' } = options;
  return createTableCell(props, [
    h(TradingPairIcon, {
      symbol: props.value,
      'show-text': showText,
      'icon-size': iconSize,
      'text-class': textClass,
    }),
  ]);
};

// 状态徽章单元格渲染器
export const renderStatusBadgeCell = (
  props: TableCellProps<Record<string, unknown>, string>,
  options: {
    getStatusColor?: (status: string) => string;
    getStatusLabel?: (status: string) => string;
  } = {},
) => {
  const { getStatusColor, getStatusLabel } = options;
  return createTableCell(props, [
    h('q-badge', {
      color: getStatusColor ? getStatusColor(props.value) : 'primary',
      label: getStatusLabel ? getStatusLabel(props.value) : props.value,
    }),
  ]);
};

// 方向/操作类型单元格渲染器 (BUY/SELL)
export const renderSideCell = (props: TableCellProps<Record<string, unknown>, string>) => {
  const isBuy = props.value === 'BUY';
  return createTableCell(props, [
    h('q-badge', {
      color: isBuy ? 'positive' : 'negative',
      label: props.value,
    }),
  ]);
};

// 基于 PriceDisplay 的价格/数量/金额单元格渲染器
export const renderPriceCell = (
  props: TableCellProps<Record<string, unknown>, string | number | null | undefined>,
  options: { type?: 'price' | 'amount' | 'quantity'; showDollar?: boolean } = {},
) => {
  const { type = 'price', showDollar = false } = options;
  return createTableCell(props, [
    h(PriceDisplay, {
      value: props.value,
      type,
      'show-dollar': showDollar,
    }),
  ]);
};

// 数量格式化单元格渲染器 (默认无美元符号)
export const renderQuantityCell = (
  props: TableCellProps<Record<string, unknown>, string | number | null | undefined>,
  options: { showDollar?: boolean } = {},
) => renderPriceCell(props, { type: 'quantity', ...options });

// 金额格式化单元格渲染器 (使用 AmountDisplay 控制颜色)
export const renderAmountCell = (
  props: TableCellProps<Record<string, unknown>, string | number | null | undefined>,
  options: { type?: 'normal' | 'income' | 'expense'; showDollar?: boolean } = {},
) => {
  const { type = 'normal', showDollar = true } = options;
  return createTableCell(props, [
    h(AmountDisplay, {
      value: props.value,
      type,
      'show-dollar': showDollar,
    }),
  ]);
};

// 利润单元格渲染器 (根据正负值显示收入/支出颜色)
export const renderProfitCell = (
  props: TableCellProps<Record<string, unknown>, string | number | null | undefined>,
  options: { showDollar?: boolean } = {},
) => {
  const profit = typeof props.value === 'string' ? Number.parseFloat(props.value) : props.value ?? 0;
  const isNumber = typeof profit === 'number' && !Number.isNaN(profit);
  const type: 'normal' | 'income' | 'expense' = !isNumber || profit === 0 ? 'normal' : profit > 0 ? 'income' : 'expense';

  return renderAmountCell(props, {
    type,
    showDollar: options.showDollar ?? true,
  });
};

// 时间格式化单元格渲染器 - 需要页面提供自己的formatDateTime函数
export const renderTimeCell = <Value>(
  props: TableCellProps<Record<string, unknown>, Value>,
  options: { formatter: (value: Value) => string },
) => {
  const { formatter } = options;
  const formattedTime = props.value !== null && props.value !== undefined ? formatter(props.value) : '';
  return createTableCell(props, [
    h(
      'span',
      {
        class: 'text-caption',
      },
      formattedTime,
    ),
  ]);
};

// 通用文本单元格渲染器 (带0值处理)
export const renderTextCell = (
  props: TableCellProps,
  options: { emptyText?: string; zeroColor?: string } = {},
) => {
  const { emptyText = 'N/A', zeroColor = '#9e9e9e' } = options;
  const displayValue = props.value || emptyText;
  const isZeroOrEmpty = !props.value || props.value === '0' || props.value === 0;

  return createTableCell(props, [
    h(
      'span',
      {
        class: 'text-weight-medium',
        style: { color: isZeroOrEmpty ? zeroColor : '' },
      },
      displayValue,
    ),
  ]);
};

// 可点击单元格渲染器
export const renderClickableCell = (
  props: TableCellProps,
  options: { onClick: (row: Record<string, unknown>) => void; formatter?: (value: unknown) => string },
) => {
  const { onClick, formatter } = options;
  const displayValue = formatter ? formatter(props.value) : props.value;

  return createTableCell(props, [
    h(
      'span',
      {
        class: 'cursor-pointer text-primary text-weight-medium',
        onClick: () => onClick(props.row),
      },
      displayValue,
    ),
  ]);
};

// 组合所有渲染器的 hook
export function useTableCellRenderers() {
  return {
    renderPairCell,
    renderPriceCell,
    renderStatusBadgeCell,
    renderSideCell,
    renderQuantityCell,
    renderAmountCell,
    renderProfitCell,
    renderTimeCell,
    renderTextCell,
    renderClickableCell,
  };
}
