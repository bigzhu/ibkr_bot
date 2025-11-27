import type { NumberLike } from './http';

export const toNumber = (value: NumberLike): number => {
  if (typeof value === 'number') {
    return Number.isFinite(value) ? value : 0;
  }
  if (typeof value === 'string') {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : 0;
  }
  return 0;
};

export const toBoolean = (value: unknown): boolean => value === true || value === 1;

