/** @vitest-environment jsdom */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { act } from 'react-dom/test-utils';
import { useAuthStore, type User, type AuthState } from '@/stores/authStore';

// Mock fetch globally
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock crypto.randomUUID
Object.defineProperty(global, 'crypto', {
  value: {
    randomUUID: () => Math.random().toString(36).substring(2, 15),
  },
});

describe('AuthStore', () => {
  const mockUser: User = {
    id: 'test-user-id',
    email: 'test@example.com',
    username: 'testuser',
    full_name: 'Test User',
    is_active: true,
    is_superuser: false,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  const mockToken = 'mock-jwt-token';

  beforeEach(() => {
    // Reset store state
    useAuthStore.setState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
    vi.clearAllMocks();
  });

  it('has correct initial state', () => {
    const state = useAuthStore.getState();
    
    expect(state.user).toBeNull();
    expect(state.token).toBeNull();
    expect(state.isAuthenticated).toBe(false);
    expect(state.isLoading).toBe(false);
    expect(state.error).toBeNull();
  });

  it('can set user state', () => {
    const { setUser } = useAuthStore.getState();
    
    act(() => {
      setUser(mockUser);
    });
    
    const state = useAuthStore.getState();
    expect(state.user).toEqual(mockUser);
    expect(state.isAuthenticated).toBe(true);
  });

  it('can set token state', () => {
    const { setToken } = useAuthStore.getState();
    
    act(() => {
      setToken(mockToken);
    });
    
    const state = useAuthStore.getState();
    expect(state.token).toBe(mockToken);
    expect(state.isAuthenticated).toBe(true);
  });

  it('can set loading state', () => {
    const { setLoading } = useAuthStore.getState();
    
    act(() => {
      setLoading(true);
    });
    
    const state = useAuthStore.getState();
    expect(state.isLoading).toBe(true);
  });

  it('can set error state', () => {
    const { setError } = useAuthStore.getState();
    
    act(() => {
      setError('Test error message');
    });
    
    const state = useAuthStore.getState();
    expect(state.error).toBe('Test error message');
  });

  it('can clear user state', () => {
    // Set initial state
    useAuthStore.setState({
      user: mockUser,
      token: mockToken,
      isAuthenticated: true,
    });
    
    const { setUser } = useAuthStore.getState();
    
    act(() => {
      setUser(null);
    });
    
    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });

  it('can logout and clear all state', () => {
    // Set initial authenticated state
    useAuthStore.setState({
      user: mockUser,
      token: mockToken,
      isAuthenticated: true,
    });
    
    const { logout } = useAuthStore.getState();
    
    act(() => {
      logout();
    });
    
    const state = useAuthStore.getState();
    expect(state.user).toBeNull();
    expect(state.token).toBeNull();
    expect(state.isAuthenticated).toBe(false);
  });

  describe('login action', () => {
    it('sets loading state during login', async () => {
      mockFetch.mockImplementation(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ access_token: mockToken }),
        })
      );
      
      const { login, isLoading } = useAuthStore.getState();
      
      // Login should set loading to true immediately
      const loginPromise = login('testuser', 'password');
      
      // Check loading state is set
      expect(useAuthStore.getState().isLoading).toBe(true);
      
      await loginPromise;
    });

    it('handles login success', async () => {
      mockFetch.mockImplementation(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ access_token: mockToken }),
        })
      );
      
      const { login } = useAuthStore.getState();
      
      await act(async () => {
        await login('testuser', 'password');
      });
      
      const state = useAuthStore.getState();
      expect(state.token).toBe(mockToken);
      expect(state.isLoading).toBe(false);
      expect(state.error).toBeNull();
    });

    it('handles login failure', async () => {
      mockFetch.mockImplementation(() =>
        Promise.resolve({
          ok: false,
          json: () => Promise.resolve({ detail: 'Invalid credentials' }),
        })
      );
      
      const { login } = useAuthStore.getState();
      
      await act(async () => {
        await login('testuser', 'wrongpassword');
      });
      
      const state = useAuthStore.getState();
      expect(state.token).toBeNull();
      expect(state.error).toBe('Invalid credentials');
    });

    it('handles network error during login', async () => {
      mockFetch.mockImplementation(() =>
        Promise.reject(new Error('Network error'))
      );
      
      const { login } = useAuthStore.getState();
      
      await act(async () => {
        await login('testuser', 'password');
      });
      
      const state = useAuthStore.getState();
      expect(state.error).toBe('Network error');
    });
  });

  describe('register action', () => {
    it('handles register success', async () => {
      mockFetch.mockImplementation(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockUser),
        })
      );
      
      const { register } = useAuthStore.getState();
      
      await act(async () => {
        await register({
          email: 'new@example.com',
          username: 'newuser',
          password: 'password123',
        });
      });
      
      const state = useAuthStore.getState();
      expect(state.isLoading).toBe(false);
    });

    it('handles register failure with duplicate email', async () => {
      mockFetch.mockImplementation(() =>
        Promise.resolve({
          ok: false,
          json: () => Promise.resolve({ detail: 'Email already registered' }),
        })
      );
      
      const { register } = useAuthStore.getState();
      
      await act(async () => {
        await register({
          email: 'existing@example.com',
          username: 'newuser',
          password: 'password123',
        });
      });
      
      const state = useAuthStore.getState();
      expect(state.error).toBe('Email already registered');
    });
  });

  describe('fetchUser action', () => {
    it('fetches user data successfully', async () => {
      mockFetch.mockImplementation(() =>
        Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockUser),
        })
      );
      
      const { fetchUser } = useAuthStore.getState();
      
      await act(async () => {
        await fetchUser();
      });
      
      const state = useAuthStore.getState();
      expect(state.user).toEqual(mockUser);
    });

    it('handles fetch failure', async () => {
      mockFetch.mockImplementation(() =>
        Promise.resolve({
          ok: false,
          status: 401,
        })
      );
      
      const { fetchUser } = useAuthStore.getState();
      
      await act(async () => {
        await fetchUser();
      });
      
      const state = useAuthStore.getState();
      expect(state.user).toBeNull();
    });
  });
});
