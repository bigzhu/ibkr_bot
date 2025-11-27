<template>
  <div class="currency-symbol-display">
    <TradingPairIcon
      v-if="showIcon"
      :symbol="baseCurrency"
      :show-text="false"
      icon-size="18px"
      :title="baseCurrency"
    />
    <span class="currency-text">{{ formatCurrency(value) }}</span>
    <span class="currency-code">{{ baseCurrency }}</span>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import TradingPairIcon from './TradingPairIcon.vue';
import { formatCurrency } from 'src/utils/formatters';

interface Props {
  /** 交易对符号,如 ADAUSDC */
  symbol: string;
  /** 数值金额 */
  value: string | number;
  /** 要显示的货币类型:base(基础货币) 或 quote(计价货币) */
  currencyType?: 'base' | 'quote';
  showIcon?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  currencyType: 'base',
  showIcon: true,
});

// 提取基础货币
const getBaseCurrency = (symbol: string): string => {
  if (!symbol) return '';

  // 常见的计价币种列表,按长度倒序排列以优先匹配长的后缀
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

  // 如果没有匹配到已知的计价币种,返回原始符号
  return symbol;
};

// 提取计价货币
const getQuoteCurrency = (symbol: string): string => {
  if (!symbol) return '';

  // 常见的计价币种列表,按长度倒序排列以优先匹配长的后缀
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

  // 如果没有匹配到已知的计价币种,返回空字符串
  return '';
};

// 根据类型选择要显示的货币
const baseCurrency = computed(() =>
  props.currencyType === 'base' ? getBaseCurrency(props.symbol) : getQuoteCurrency(props.symbol),
);
</script>

<style lang="scss" scoped>
.currency-symbol-display {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 4px;

  .currency-text {
    font-weight: 500;
  }

  .currency-code {
    font-weight: 500;
  }
}
</style>
