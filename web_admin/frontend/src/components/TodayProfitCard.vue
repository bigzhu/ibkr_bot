<template>
  <ModernCard
    variant="gradient"
    class="stat-card clickable-card"
    @click="$router.push('/profit-analysis')"
  >
    <div class="stat-content">
      <div class="stat-icon warning-icon">
        <q-icon name="account_balance_wallet" />
      </div>
      <div class="stat-details">
        <div
          class="stat-number"
          :class="profitStore.todayProfit >= 0 ? 'text-positive' : 'text-negative'"
        >
          {{
            profitStore.dailyProfitsData.length > 0 ? formatProfit(profitStore.todayProfit) : '-'
          }}
        </div>
        <div class="stat-label">今日盈亏</div>
      </div>
    </div>
  </ModernCard>
</template>

<script setup lang="ts">
import { useProfitAnalysisStore } from 'src/stores/profit-analysis-store';
import ModernCard from 'src/components/ModernCard.vue';

const profitStore = useProfitAnalysisStore();

// 格式化利润 - 截断到小数点后两位
const formatProfit = (profit: number) => {
  // 舍弃多余小数位,不进行四舍五入
  const truncated = Math.trunc(profit * 100) / 100;
  const formatted = truncated.toFixed(2);
  return truncated >= 0 ? `+${formatted}` : formatted;
};
</script>

<style lang="scss" scoped>
// 可点击卡片的悬停效果
.clickable-card {
  cursor: pointer;
  transition: transform 0.2s ease;

  &:hover {
    transform: translateY(-2px);
  }
}
</style>
