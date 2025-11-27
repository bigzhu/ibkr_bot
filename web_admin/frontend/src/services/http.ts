import { api } from 'src/boot/axios';

export { api };

export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  message?: string;
}

export type NumberLike = string | number | null | undefined;

export const handleApiError = (error: unknown): string => {
  if (error && typeof error === 'object' && 'response' in error) {
    const resp = (error as { response?: { data?: { detail?: string; message?: string } } }).response;
    return resp?.data?.detail || resp?.data?.message || 'Unknown server error';
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'Unknown error';
};
