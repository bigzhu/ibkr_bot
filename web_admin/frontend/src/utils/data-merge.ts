/**
 * Utility helpers for merging collections with a stable identifier.
 * These helpers allow stores to perform incremental updates without
 * clearing existing data, which helps the UI avoid flicker while keeping
 * the cached data fresh.
 */

export interface IdentifiableRecord {
  id: string | number;
}

export interface MergeOptions<T> {
  /** Optional comparer used to sort the merged collection */
  sort?: (a: T, b: T) => number;
  /** Maximum number of records to keep after merging */
  maxItems?: number;
  /**
   * When true, records that are not present in the incoming payload
   * will be dropped from the resulting collection.
   */
  pruneMissing?: boolean;
}

export function mergeById<T extends IdentifiableRecord>(
  existing: T[],
  incoming: T[],
  options: MergeOptions<T> = {},
): T[] {
  const map = new Map<string | number, T>();

  // Preserve existing records first
  for (const item of existing) {
    map.set(item.id, item);
  }

  // Apply incoming updates (upsert semantics)
  for (const item of incoming) {
    const previous = map.get(item.id);
    map.set(item.id, previous ? { ...previous, ...item } : item);
  }

  let merged = Array.from(map.values());

  if (options.pruneMissing) {
    const incomingIds = new Set(incoming.map((item) => item.id));
    merged = merged.filter((item) => incomingIds.has(item.id));
  }

  if (options.sort) {
    merged.sort(options.sort);
  }

  if (options.maxItems && options.maxItems > 0) {
    merged = merged.slice(0, options.maxItems);
  }

  return merged;
}
