// Authentication store for user management
'use client';

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  avatar_url?: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setUser: (user: User | null) => void;
  setToken: (token: string | null) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  
  // Auth methods
  login: (username: string, password: string) => Promise<boolean>;
  register: (data: RegisterData) => Promise<boolean>;
  logout: () => void;
  fetchUser: () => Promise<void>;
  updateProfile: (data: UpdateProfileData) => Promise<boolean>;
}

interface RegisterData {
  email: string;
  username: string;
  password: string;
  full_name?: string;
}

interface UpdateProfileData {
  email?: string;
  username?: string;
  full_name?: string;
  password?: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      
      setUser: (user) => set({ user, isAuthenticated: !!user }),
      setToken: (token) => set({ token, isAuthenticated: !!token }),
      setLoading: (loading) => set({ isLoading: loading }),
      setError: (error) => set({ error }),
      
      login: async (username, password) => {
        set({ isLoading: true, error: null });
        
        try {
          const formData = new URLSearchParams();
          formData.append('username', username);
          formData.append('password', password);
          
          const response = await fetch(`${API_BASE}/api/auth/login`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: formData.toString(),
          });
          
          if (!response.ok) {
            const data = await response.json();
            throw new Error(data.detail || 'Login failed');
          }
          
          const data = await response.json();
          set({ token: data.access_token });
          
          // Fetch user info
          await get().fetchUser();
          
          set({ isLoading: false });
          return true;
        } catch (error: any) {
          set({ error: error.message, isLoading: false });
          return false;
        }
      },
      
      register: async (data) => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await fetch(`${API_BASE}/api/auth/register`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
          });
          
          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Registration failed');
          }
          
          // Auto login after registration
          await get().login(data.username, data.password);
          
          set({ isLoading: false });
          return true;
        } catch (error: any) {
          set({ error: error.message, isLoading: false });
          return false;
        }
      },
      
      logout: () => {
        set({ user: null, token: null, isAuthenticated: false, error: null });
      },
      
      fetchUser: async () => {
        const { token } = get();
        if (!token) return;
        
        try {
          const response = await fetch(`${API_BASE}/api/auth/me`, {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          });
          
          if (!response.ok) {
            // Token might be expired
            if (response.status === 401) {
              get().logout();
            }
            return;
          }
          
          const user = await response.json();
          set({ user, isAuthenticated: true });
        } catch (error) {
          console.error('Failed to fetch user:', error);
        }
      },
      
      updateProfile: async (data) => {
        set({ isLoading: true, error: null });
        
        try {
          const { token } = get();
          const response = await fetch(`${API_BASE}/api/auth/me`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify(data),
          });
          
          if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Update failed');
          }
          
          const user = await response.json();
          set({ user, isLoading: false });
          return true;
        } catch (error: any) {
          set({ error: error.message, isLoading: false });
          return false;
        }
      },
    }),
    {
      name: 'auth-storage',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({ token: state.token }),
    }
  )
);

// Helper function to get auth headers
export function getAuthHeaders(): HeadersInit {
  if (typeof window === 'undefined') return {};
  
  const token = useAuthStore.getState().token;
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

// API fetch wrapper with auth
export async function authFetch(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const headers = {
    ...options.headers,
    ...getAuthHeaders(),
  };
  
  return fetch(url, { ...options, headers });
}
