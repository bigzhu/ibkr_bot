<template>
  <div
    class="trading-pair-icon flex items-center no-wrap"
    :class="[{ 'cursor-pointer': !isMobileDevice() }, containerClass]"
    @click="handleClick"
    :title="isMobileDevice() ? symbol : `点击访问币安交易页面: ${getBinanceFormat(symbol)}`"
  >
    <q-avatar :size="iconSize" class="q-mr-sm">
      <img
        :src="currentImageSrc"
        :alt="baseCurrency"
        class="coin-logo"
        @error="handleImageError"
        v-show="showImage"
      />
      <!-- 加载失败时显示币种首字母作为备选 -->
      <div
        v-show="!showImage"
        class="coin-logo-fallback text-weight-bold"
        :style="{ fontSize: getFallbackFontSize() }"
      >
        {{ baseCurrency.charAt(0).toUpperCase() }}
      </div>
    </q-avatar>
    <span v-if="showText" :class="textClass">
      {{ symbol }}
    </span>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';

// 检测是否为移动端设备
const isMobileDevice = () => {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
         window.innerWidth <= 768;
};

// Props 定义
interface Props {
  symbol: string;
  showText?: boolean;
  iconSize?: string;
  textClass?: string;
  containerClass?: string;
}

const props = withDefaults(defineProps<Props>(), {
  showText: true,
  iconSize: '24px',
  textClass: 'text-weight-medium',
  containerClass: '',
});

// 响应式状态
const currentImageSrc = ref('');
const currentSourceIndex = ref(0);
const showImage = ref(true);

// 从交易对中提取基础币种
const getBaseCurrency = (symbol: string) => {
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

  // 如果传入的就是单个币种(如USDC,BTC,ETH等),直接返回
  if (quoteCurrencies.includes(symbol.toUpperCase()) || symbol.length <= 5) {
    return symbol;
  }

  for (const quote of quoteCurrencies) {
    if (symbol.endsWith(quote)) {
      return symbol.slice(0, -quote.length);
    }
  }

  // 如果没有匹配到已知的计价币种,返回原始符号
  return symbol;
};

// 获取所有可能的图标源 - 优先使用已知可用的源
const getCoinLogoSources = (symbol: string): string[] => {
  if (!symbol) return [];

  const coinSymbol = symbol.toLowerCase();

  // 特殊处理币种映射和多个图标源
  const customIcons: Record<string, string[]> = {
    arb: [
      'https://assets.coingecko.com/coins/images/16547/small/photo_2023-03-29_21.47.00.jpeg?1680097073',
      'https://s2.coinmarketcap.com/static/img/coins/64x64/11841.png',
    ],
    pol: [
      'https://assets.coingecko.com/coins/images/4713/small/polygon.png',
      'https://s2.coinmarketcap.com/static/img/coins/64x64/3890.png',
      'https://cryptologos.cc/logos/polygon-matic-logo.png',
      'https://cdn.jsdelivr.net/gh/spothq/cryptocurrency-icons@master/32/color/matic.png',
    ],
    doge: [
      'https://assets.coingecko.com/coins/images/5/small/dogecoin.png',
      'https://s2.coinmarketcap.com/static/img/coins/64x64/74.png',
      'https://assets.coingecko.com/coins/images/5/large/dogecoin.png',
      'https://cdn.jsdelivr.net/gh/spothq/cryptocurrency-icons@master/32/color/doge.png',
    ],
    sui: [
      'https://assets.coingecko.com/coins/images/26375/small/sui-ocean-square.png',
      'https://s2.coinmarketcap.com/static/img/coins/64x64/20947.png',
      'https://cryptologos.cc/logos/sui-sui-logo.png',
    ],
    // 可以继续添加其他特殊币种
    apt: [
      'https://assets.coingecko.com/coins/images/26455/small/aptos_round.png',
      'https://s2.coinmarketcap.com/static/img/coins/64x64/21794.png',
    ],
    op: [
      'https://assets.coingecko.com/coins/images/25244/small/Optimism.png',
      'https://s2.coinmarketcap.com/static/img/coins/64x64/11840.png',
    ],
    near: [
      'https://assets.coingecko.com/coins/images/10365/small/near.jpg',
      'https://s2.coinmarketcap.com/static/img/coins/64x64/6535.png',
      'https://cdn.jsdelivr.net/gh/spothq/cryptocurrency-icons@master/32/color/near.png',
    ],
    sol: [
      'https://assets.coingecko.com/coins/images/4128/small/solana.png',
      'https://s2.coinmarketcap.com/static/img/coins/64x64/5426.png',
      'https://cdn.jsdelivr.net/gh/spothq/cryptocurrency-icons@master/32/color/sol.png',
    ],
    avax: [
      'https://assets.coingecko.com/coins/images/12559/small/Avalanche_Circle_RedWhite_Trans.png',
      'https://s2.coinmarketcap.com/static/img/coins/64x64/5805.png',
      'https://cdn.jsdelivr.net/gh/spothq/cryptocurrency-icons@master/32/color/avax.png',
    ],
    imx: [
      'https://assets.coingecko.com/coins/images/17233/small/immutableX-symbol-BLK-RGB.png',
      'https://s2.coinmarketcap.com/static/img/coins/64x64/10603.png',
    ],
    shib: [
      'https://assets.coingecko.com/coins/images/11939/small/shiba.png',
      'https://s2.coinmarketcap.com/static/img/coins/64x64/5994.png',
      'https://cdn.jsdelivr.net/gh/spothq/cryptocurrency-icons@master/32/color/shib.png',
    ],
    ftm: [
      'https://assets.coingecko.com/coins/images/4001/small/Fantom_round.png',
      'https://s2.coinmarketcap.com/static/img/coins/64x64/3513.png',
      'https://cdn.jsdelivr.net/gh/spothq/cryptocurrency-icons@master/32/color/ftm.png',
    ],
    sei: [
      'https://assets.coingecko.com/coins/images/28205/small/Sei_Logo_-_Transparent.png',
      'https://s2.coinmarketcap.com/static/img/coins/64x64/23149.png',
    ],
    pepe: [
      'https://assets.coingecko.com/coins/images/29850/small/pepe-token.jpeg',
      'https://s2.coinmarketcap.com/static/img/coins/64x64/24478.png',
    ],
    ton: [
      'https://assets.coingecko.com/coins/images/17980/small/ton_symbol.png',
      'https://s2.coinmarketcap.com/static/img/coins/64x64/11419.png',
    ],
    rune: [
      'https://assets.coingecko.com/coins/images/6595/small/thorchain.png',
      'https://s2.coinmarketcap.com/static/img/coins/64x64/4157.png',
      'https://cdn.jsdelivr.net/gh/spothq/cryptocurrency-icons@master/32/color/rune.png',
    ],
    inj: [
      'https://assets.coingecko.com/coins/images/12882/small/Secondary_Symbol.png',
      'https://s2.coinmarketcap.com/static/img/coins/64x64/7226.png',
    ],
  };

  // 如果有自定义图标,直接使用自定义配置
  if (customIcons[coinSymbol]) {
    return customIcons[coinSymbol];
  }

  return [
    // 方案1: 原有的可靠图标库 - 优先使用,大部分币种可用
    `https://cdn.jsdelivr.net/gh/spothq/cryptocurrency-icons@master/32/color/${coinSymbol}.png`,
    // 方案2: atomiclabs 图标库
    `https://raw.githubusercontent.com/atomiclabs/cryptocurrency-icons/master/32/color/${coinSymbol}.png`,
    // 方案3: Cryptologos - 支持多种格式
    `https://cryptologos.cc/logos/${coinSymbol}-${coinSymbol}-logo.png`,
    // 方案4: 通用加密货币图标 - 最后的备选
    `https://cdn.jsdelivr.net/gh/cryptocurrency-icons/cryptocurrency-icons@master/32/color/${coinSymbol}.png`,
  ];
};

// 计算属性
const baseCurrency = computed(() => getBaseCurrency(props.symbol));

// 获取备选文字大小
const getFallbackFontSize = () => {
  const size = parseInt(props.iconSize);
  return `${Math.max(8, Math.floor(size * 0.4))}px`;
};

// 尝试加载下一个图标源
const tryNextSource = () => {
  const sources = getCoinLogoSources(baseCurrency.value);

  if (currentSourceIndex.value < sources.length - 1) {
    currentSourceIndex.value++;
    currentImageSrc.value = sources[currentSourceIndex.value];
    showImage.value = true;
    console.log(`图标加载失败,尝试下一个源 (${currentSourceIndex.value + 1}/${sources.length}): ${currentImageSrc.value}`);
  } else {
    // 所有源都失败了,显示备选方案
    showImage.value = false;
    console.log(`所有图标源都失败,显示备选文字: ${baseCurrency.value}`);
  }
};

// 处理图片加载错误
const handleImageError = () => {
  tryNextSource();
};

// 初始化图标
const initializeIcon = () => {
  const sources = getCoinLogoSources(baseCurrency.value);
  if (sources.length > 0) {
    currentSourceIndex.value = 0;
    currentImageSrc.value = sources[0];
    showImage.value = true;
    console.log(`开始加载图标: ${baseCurrency.value}, 共${sources.length}个源`);
  } else {
    showImage.value = false;
    console.log(`没有找到图标源: ${baseCurrency.value}`);
  }
};

// 监听symbol变化,重新加载图标
watch(
  () => props.symbol,
  () => {
    initializeIcon();
  },
  { immediate: true },
);

// 币安链接相关函数
const getBinanceFormat = (symbol: string) => {
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
      const baseCurrency = symbol.slice(0, -quote.length);
      return `${baseCurrency}_${quote}`;
    }
  }

  // 如果没有匹配到已知的计价币种,返回原始符号
  return symbol;
};

const getBinanceTradeUrl = (symbol: string) => {
  const binanceFormat = getBinanceFormat(symbol);
  return `https://www.binance.com/zh-CN/trade/${binanceFormat}?type=spot`;
};

const handleClick = () => {
  // 在移动端不打开链接
  if (isMobileDevice()) {
    return;
  }

  const url = getBinanceTradeUrl(props.symbol);
  window.open(url, '_blank');
};
</script>

<style lang="scss" scoped>
.trading-pair-icon {
  transition: opacity 0.2s ease;

  &:hover {
    opacity: 0.8;
  }

  .coin-logo {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: 50%;
  }

  .coin-logo-fallback {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    user-select: none;
  }
}
</style>
