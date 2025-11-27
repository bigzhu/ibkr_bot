<template>
  <div class="text-weight-medium" :class="getValueColor(value)">
    <div
      v-if="shouldShowAmount"
      class="flex items-center justify-center q-gutter-xs"
      :class="{ 'opacity-muted': isZeroAmount }"
    >
      <TradingPairIcon
        :symbol="displayCurrency"
        :show-text="false"
        icon-size="18px"
        :title="displayCurrency"
      />
      <span>{{ formattedAmount }}</span>
      <span class="text-caption">{{ displayCurrency }}</span>
    </div>
    <span v-else class="opacity-muted">-</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { formatQuantity, formatCurrency } from 'src/utils/formatters';
import TradingPairIcon from 'src/components/TradingPairIcon.vue';

interface Props {
  value: string | number | null | undefined;
  symbol?: string; // 完整交易对符号,用于提取币种
  orderSide?: string; // 订单方向,用于动态选择币种 (BUY=计价币种, SELL=基础币种)
  currencyType?: 'base' | 'quote' | 'auto'; // 币种类型: base=基础币种, quote=计价币种, auto=根据orderSide自动选择
  formatType?: 'quantity' | 'currency';
  currency?: string; // 直接指定币种,优先级最高
}

const props = withDefaults(defineProps<Props>(), {
  formatType: 'quantity',
  currencyType: 'base',
});

// 提取基础币种
const getBaseCurrency = (symbol: string) => {
  if (!symbol) return '';

  const quoteCurrencies = [
    'USDT',
    'USDC',
    'BUSD',
    'FDUSD',
    'TUSD',
    'BTC',
    'ETH',
    'BNB',
    'EUR',
    'JPY',
    'GBP',
    'TRY',
    'BRL',
    'AUD',
    'RUB',
    'ZAR',
    'PLN',
    'MXN',
  ];

  for (const quote of quoteCurrencies) {
    if (symbol.endsWith(quote)) {
      return symbol.slice(0, -quote.length);
    }
  }

  return symbol;
};

// 提取计价币种
const getQuoteCurrency = (symbol: string) => {
  if (!symbol) return '';

  const quoteCurrencies = [
    'USDT',
    'USDC',
    'BUSD',
    'FDUSD',
    'TUSD',
    'BTC',
    'ETH',
    'BNB',
    'EUR',
    'JPY',
    'GBP',
    'TRY',
    'BRL',
    'AUD',
    'RUB',
    'ZAR',
    'PLN',
    'MXN',
  ];

  for (const quote of quoteCurrencies) {
    if (symbol.endsWith(quote)) {
      return quote;
    }
  }

  return '';
};

// 计算显示的币种
const displayCurrency = computed(() => {
  // 如果直接指定了币种,优先使用
  if (props.currency) {
    return props.currency;
  }

  // 如果没有交易对符号,返回空
  if (!props.symbol) {
    return '';
  }

  // 根据币种类型选择
  if (props.currencyType === 'auto' && props.orderSide) {
    // 根据订单方向自动选择: BUY=计价币种, SELL=基础币种
    return props.orderSide === 'BUY'
      ? getQuoteCurrency(props.symbol)
      : getBaseCurrency(props.symbol);
  } else if (props.currencyType === 'quote') {
    return getQuoteCurrency(props.symbol);
  } else {
    // 默认返回基础币种
    return getBaseCurrency(props.symbol);
  }
});

// 计算是否应该显示金额
const shouldShowAmount = computed(() => {
  if (props.value === null || props.value === undefined || props.value === '') {
    return false;
  }

  const numValue = Number(props.value);
  return !Number.isNaN(numValue) && numValue >= 0; // 包括0值也显示,但用透明度区分
});

const isZeroAmount = computed(() => {
  if (!shouldShowAmount.value) {
    return false;
  }

  const numValue = Number(props.value);
  return !Number.isNaN(numValue) && numValue === 0;
});

// 格式化金额显示
const formattedAmount = computed(() => {
  if (!shouldShowAmount.value) return '-';

  if (props.formatType === 'currency') {
    return formatCurrency(props.value, displayCurrency.value);
  } else {
    return formatQuantity(props.value);
  }
});

// 获取数值颜色样式
const getValueColor = (value: Props['value']) => {
  if (value === null || value === undefined || value === '') {
    return 'text-grey-8';
  }

  const numericValue = typeof value === 'string' ? Number.parseFloat(value) : value;

  if (typeof numericValue !== 'number' || Number.isNaN(numericValue) || numericValue === 0) {
    return 'text-grey-8';
  }

  return '';
};
</script>
