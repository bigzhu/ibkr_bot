export interface StatsCardConfig {
  value: number | string;
  label: string;
  icon: string;
  iconType?: 'total' | 'success' | 'warning' | 'info' | 'danger';
  variant?: 'gradient' | 'glass' | 'ghost' | 'solid';
}

export interface StatsCardPresetOptions {
  preset?: 'default' | 'gradient' | 'glass';
  defaultIconType?: StatsCardConfig['iconType'];
  defaultVariant?: StatsCardConfig['variant'];
}

const PRESET_VARIANTS: Record<'default' | 'gradient' | 'glass', StatsCardConfig['variant']> = {
  default: 'gradient',
  gradient: 'gradient',
  glass: 'glass',
};

const ICON_TYPE_FALLBACKS: StatsCardConfig['iconType'][] = ['total', 'info', 'success', 'warning', 'danger'];

export function createStatsCards(
  cards: Array<Partial<StatsCardConfig> & Pick<StatsCardConfig, 'value' | 'label' | 'icon'>>,
  options: StatsCardPresetOptions = {},
): StatsCardConfig[] {
  const { preset = 'default', defaultIconType, defaultVariant } = options;
  const variantFallback = defaultVariant ?? PRESET_VARIANTS[preset];
  const iconTypeFallback = defaultIconType ?? ICON_TYPE_FALLBACKS[0];

  return cards.map((card) => ({
    value: card.value,
    label: card.label,
    icon: card.icon,
    iconType: card.iconType ?? iconTypeFallback,
    variant: card.variant ?? variantFallback,
  }));
}

