import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import axios from 'axios';
import { AuthStore, LoginCredentials, RegisterData, User, ApiResponse } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      login: async (credentials: LoginCredentials) => {
        set({ isLoading: true, error: null });

        try {
          const response = await axios.post<ApiResponse<{ user: User; token: string }>>(
            `${API_BASE_URL}/auth/login`,
            credentials
          );

          const { user, token } = response.data.data;

          // Set token in axios defaults for future requests
          axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;

          set({
            user,
            token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.message || 'Login failed';
          set({
            error: errorMessage,
            isLoading: false,
            isAuthenticated: false,
          });
          throw new Error(errorMessage);
        }
      },

      register: async (data: RegisterData) => {
        set({ isLoading: true, error: null });

        try {
          const response = await axios.post<ApiResponse<{ user: User; token: string }>>(
            `${API_BASE_URL}/auth/register`,
            data
          );

          const { user, token } = response.data.data;

          // Set token in axios defaults for future requests
          axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;

          set({
            user,
            token,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.message || 'Registration failed';
          set({
            error: errorMessage,
            isLoading: false,
            isAuthenticated: false,
          });
          throw new Error(errorMessage);
        }
      },

      logout: () => {
        // Remove token from axios defaults
        delete axios.defaults.headers.common['Authorization'];

        set({
          user: null,
          token: null,
          isAuthenticated: false,
          error: null,
        });
      },

      refreshToken: async () => {
        const { token } = get();

        if (!token) {
          throw new Error('No token available');
        }

        set({ isLoading: true, error: null });

        try {
          const response = await axios.post<ApiResponse<{ token: string }>>(
            `${API_BASE_URL}/auth/refresh`,
            {},
            {
              headers: { Authorization: `Bearer ${token}` },
            }
          );

          const newToken = response.data.data.token;

          // Update token in axios defaults
          axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;

          set({
            token: newToken,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          const errorMessage = error.response?.data?.message || 'Token refresh failed';
          set({
            error: errorMessage,
            isLoading: false,
          });

          // If refresh fails, logout user
          get().logout();
          throw new Error(errorMessage);
        }
      },

      setUser: (user: User | null) => {
        set({ user });
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },

      setError: (error: string | null) => {
        set({ error });
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
        isAuthenticated: state.isAuthenticated,
      }),
      onRehydrateStorage: () => (state) => {
        if (state?.token) {
          // Restore token in axios defaults when store rehydrates
          axios.defaults.headers.common['Authorization'] = `Bearer ${state.token}`;
        }
      },
    }
  )
);

// Setup axios interceptor for automatic token refresh
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        await useAuthStore.getState().refreshToken();
        return axios(originalRequest);
      } catch (refreshError) {
        useAuthStore.getState().logout();
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);