/**
 * 精确数学计算工具
 * 解决 JavaScript 浮点数精度问题
 */

/**
 * 将数字转换为整数进行计算,避免浮点精度问题
 * @param {number} num 数字
 * @returns {Object} {value: 整数值, decimals: 小数位数}
 */
function toInteger(num) {
  const str = num.toString();
  const decimalIndex = str.indexOf('.');

  if (decimalIndex === -1) {
    return { value: num, decimals: 0 };
  }

  const decimals = str.length - decimalIndex - 1;
  const value = parseInt(str.replace('.', ''));

  return { value, decimals };
}

/**
 * 精确加法
 * @param {string|number} a 加数
 * @param {string|number} b 加数
 * @returns {number} 精确结果
 */
export function preciseAdd(a, b) {
  const numA = parseFloat(a) || 0;
  const numB = parseFloat(b) || 0;

  const intA = toInteger(numA);
  const intB = toInteger(numB);

  // 统一小数位数
  const maxDecimals = Math.max(intA.decimals, intB.decimals);
  const factorA = Math.pow(10, maxDecimals - intA.decimals);
  const factorB = Math.pow(10, maxDecimals - intB.decimals);

  const result = (intA.value * factorA + intB.value * factorB) / Math.pow(10, maxDecimals);

  return result;
}

/**
 * 精确减法
 * @param {string|number} a 被减数
 * @param {string|number} b 减数
 * @returns {number} 精确结果
 */
export function preciseSubtract(a, b) {
  const numA = parseFloat(a) || 0;
  const numB = parseFloat(b) || 0;

  const intA = toInteger(numA);
  const intB = toInteger(numB);

  // 统一小数位数
  const maxDecimals = Math.max(intA.decimals, intB.decimals);
  const factorA = Math.pow(10, maxDecimals - intA.decimals);
  const factorB = Math.pow(10, maxDecimals - intB.decimals);

  const result = (intA.value * factorA - intB.value * factorB) / Math.pow(10, maxDecimals);

  return result;
}

/**
 * 精确乘法
 * @param {string|number} a 乘数
 * @param {string|number} b 乘数
 * @returns {number} 精确结果
 */
export function preciseMultiply(a, b) {
  const numA = parseFloat(a) || 0;
  const numB = parseFloat(b) || 0;

  const intA = toInteger(numA);
  const intB = toInteger(numB);

  const result = (intA.value * intB.value) / Math.pow(10, intA.decimals + intB.decimals);

  return result;
}

/**
 * 精确除法
 * @param {string|number} a 被除数
 * @param {string|number} b 除数
 * @returns {number} 精确结果
 */
export function preciseDivide(a, b) {
  const numA = parseFloat(a) || 0;
  const numB = parseFloat(b) || 0;

  if (numB === 0) {
    throw new Error('Division by zero');
  }

  const intA = toInteger(numA);
  const intB = toInteger(numB);

  // 扩大被除数精度以保证除法精度
  const precision = 10;
  const factor = Math.pow(10, precision);

  const result =
    (intA.value * factor * Math.pow(10, intB.decimals)) /
    (intB.value * Math.pow(10, intA.decimals)) /
    factor;

  return result;
}

/**
 * 计算净利润 (总利润 - 手续费)
 * @param {string|number} profit 总利润
 * @param {string|number} commission 手续费
 * @returns {number} 精确的净利润
 */
export function calculateNetProfit(profit, commission) {
  return preciseSubtract(profit, commission);
}

/**
 * 精确求和
 * @param {Array<string|number>} numbers 数字数组
 * @returns {number} 精确的总和
 */
export function preciseSum(numbers) {
  return numbers.reduce((sum, num) => preciseAdd(sum, num), 0);
}
