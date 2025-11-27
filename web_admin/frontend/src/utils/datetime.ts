type DateInput = string | number | Date | null | undefined;

interface NormalizeOptions {
  assumeUtc?: boolean;
}

const TIMEZONE_REGEX = /([zZ]|[+-]\d\d:?\d\d)$/;

function normalizeDateInput(value: DateInput, options: NormalizeOptions = {}): Date | null {
  const { assumeUtc = false } = options;

  if (value === null || value === undefined) {
    return null;
  }

  if (value instanceof Date) {
    return Number.isNaN(value.getTime()) ? null : value;
  }

  if (typeof value === 'number') {
    const ms = Math.abs(value) < 1e11 ? value * 1000 : value;
    const date = new Date(ms);
    return Number.isNaN(date.getTime()) ? null : date;
  }

  if (typeof value === 'string') {
    const trimmed = value.trim();
    if (!trimmed) {
      return null;
    }

    if (/^\d+$/.test(trimmed)) {
      return normalizeDateInput(Number.parseInt(trimmed, 10), options);
    }

    let normalized = trimmed.replace(' ', 'T');

    if (!TIMEZONE_REGEX.test(normalized) && assumeUtc) {
      normalized += 'Z';
    }

    const date = new Date(normalized);
    if (!Number.isNaN(date.getTime())) {
      return date;
    }

    const fallback = new Date(trimmed);
    return Number.isNaN(fallback.getTime()) ? null : fallback;
  }

  return null;
}

interface FormatDateTimeOptions {
  includeDate?: boolean;
  includeYear?: boolean;
  includeTime?: boolean;
  includeSeconds?: boolean;
  assumeUtc?: boolean;
  hour12?: boolean;
  fallback?: string;
}

export function formatDateTime(
  value: DateInput,
  {
    includeDate = true,
    includeYear = true,
    includeTime = true,
    includeSeconds = true,
    assumeUtc = false,
    hour12 = false,
    fallback = '-',
  }: FormatDateTimeOptions = {},
): string {
  if (!includeDate && !includeTime) {
    return fallback;
  }

  const date = normalizeDateInput(value, { assumeUtc });
  if (!date) {
    return fallback;
  }

  const options: Intl.DateTimeFormatOptions = { hour12 };

  if (includeDate) {
    if (includeYear) {
      options.year = 'numeric';
    }
    options.month = '2-digit';
    options.day = '2-digit';
  }

  if (includeTime) {
    options.hour = '2-digit';
    options.minute = '2-digit';
    if (includeSeconds) {
      options.second = '2-digit';
    }
  }

  return new Intl.DateTimeFormat('zh-CN', options).format(date);
}

interface FormatTimeOptions {
  includeSeconds?: boolean;
  assumeUtc?: boolean;
  hour12?: boolean;
  fallback?: string;
}

export function formatTime(
  value: DateInput,
  { includeSeconds = false, assumeUtc = false, hour12 = false, fallback = '-' }: FormatTimeOptions = {},
): string {
  return formatDateTime(value, {
    includeDate: false,
    includeYear: false,
    includeTime: true,
    includeSeconds,
    assumeUtc,
    hour12,
    fallback,
  });
}

interface FormatDateOptions {
  includeYear?: boolean;
  assumeUtc?: boolean;
  fallback?: string;
}

export function formatDate(
  value: DateInput,
  { includeYear = true, assumeUtc = false, fallback = '-' }: FormatDateOptions = {},
): string {
  return formatDateTime(value, {
    includeDate: true,
    includeYear,
    includeTime: false,
    assumeUtc,
    fallback,
  });
}

export function normalizeDate(value: DateInput, options?: NormalizeOptions): Date | null {
  return normalizeDateInput(value, options);
}

