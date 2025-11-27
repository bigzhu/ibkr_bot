import { api } from './http';

export interface LoginResponse {
  success: boolean;
  message: string;
  token: string | null;
}

export interface VerifyResponse {
  success: boolean;
  message: string;
  username?: string;
}

export interface ChangePasswordResponse {
  success: boolean;
  message: string;
}

export const authApi = {
  login: async (payload: { username: string; password: string }): Promise<LoginResponse> => {
    const response = await api.post('/api/v1/auth/login', payload);
    return response.data;
  },

  verify: async (): Promise<VerifyResponse> => {
    const response = await api.get('/api/v1/auth/verify');
    return response.data;
  },

  changePassword: async (payload: { old_password: string; new_password: string }): Promise<ChangePasswordResponse> => {
    const response = await api.post('/api/v1/auth/change-password', payload);
    return response.data;
  },
};
