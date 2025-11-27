/**
 * 统一的数值格式化工具函数
 * 只保留两个核心函数:金额格式化和货币格式化
 */

// 交易对精度缓存已移除,避免未使用变量的警告

// 常见资产精度配置
const COMMON_ASSET_PRECISION = {
  BTC: 8,
  ETH: 6,
  BNB: 5,
  ADA: 4,
  DOT: 4,
  SOL: 4,
  MATIC: 4,
  AVAX: 4,
  ATOM: 4,
  USDT: 2,
  USDC: 2,
  BUSD: 2,
  DAI: 2,
  TUSD: 2,
};

/**
 * 获取资产精度
 * @param {string} asset - 资产名称(如 BTC, ETH)
 * @returns {number} 精度位数
 */
const getAssetPrecision = (asset) => {
  if (!asset) return 8;
  return COMMON_ASSET_PRECISION[asset.toUpperCase()] || 8;
};

/**
 * 金额格式化 - 用于价值/价格显示,固定保留2位小数
 * 适用于:成交总额,成交价格等以法币计价的数值
 * @param {string|number} value - 数值
 * @returns {string} 格式化后的金额字符串(保留2位小数)
 */
export const formatAmount = (value) => {
  if (!value && value !== 0) return '0';

  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return '0';

  // 直接格式化为4位小数,不使用千分位分隔符
  return num.toFixed(4);
};

/**
 * 资产数量格式化 - 根据资产类型动态保留小数位数
 * 适用于:BTC,ETH等加密货币数量显示
 * @param {string|number} value - 数值
 * @param {string} asset - 资产名称(如BTC,ETH,ADA),可选,默认使用8位精度
 * @returns {string} 格式化后的货币字符串
 */
export const formatCurrency = (value, asset = '') => {
  if (!value && value !== 0) return '0';

  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return '0';

  let precision = 8; // 默认精度

  // 如果传入了资产名称,获取对应精度
  if (asset && typeof asset === 'string' && asset.length > 0) {
    precision = getAssetPrecision(asset);
  }

  // 直接格式化,不使用千分位分隔符
  const formatted = num.toFixed(precision);

  // 去除末尾的0,但保留整数部分
  // 特殊处理:如果是纯0,直接返回'0'
  if (formatted === '0') return '0';
  return formatted.replace(/\.?0+$/, '');
};

/**
 * 数量格式化 - 保留最多6位小数并去除末尾的0
 * 适用于:订单数量,撮合数量,利润,手续费等金额数值
 * @param {string|number} value - 数值
 * @returns {string} 格式化后的数量字符串
 */
export const formatQuantity = (value) => {
  if (!value && value !== 0) return '0';

  const num = typeof value === 'string' ? parseFloat(value) : value;
  if (isNaN(num)) return '0';

  // 保留最多6位小数
  const fixed = num.toFixed(6);

  // 去除末尾的0和可能的末尾小数点
  return fixed.replace(/\.?0+$/, '');
};

/**
 * 根据交易对获取基础资产名称
 * @param {string} symbol - 交易对符号(如BTCUSDT,ADAUSDC)
 * @returns {string} 基础资产名称
 */
export const getBaseAssetFromSymbol = (symbol) => {
  if (!symbol || typeof symbol !== 'string') return '';

  const upperSymbol = symbol.toUpperCase();

  // 按计价货币优先级尝试分离
  const quoteAssets = ['USDT', 'USDC', 'BUSD', 'DAI', 'TUSD', 'BTC', 'ETH', 'BNB'];
  for (const quote of quoteAssets) {
    if (upperSymbol.endsWith(quote)) {
      return upperSymbol.substring(0, upperSymbol.length - quote.length);
    }
  }

  return '';
};
