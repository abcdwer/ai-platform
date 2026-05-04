// Theme store for managing theme state with Zustand
'use client';

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';

export type Theme = 'light' | 'dark' | 'system';

interface ThemeState {
  theme: Theme;
  resolvedTheme: 'light' | 'dark';
  setTheme: (theme: Theme) => void;
  getSystemTheme: () => 'light' | 'dark';
}

const getSystemTheme = (): 'light' | 'dark' => {
  if (typeof window === 'undefined') return 'light';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
};

const applyTheme = (theme: Theme): 'light' | 'dark' => {
  if (typeof document === 'undefined') return 'light';
  
  const root = document.documentElement;
  const resolved = theme === 'system' ? getSystemTheme() : theme;
  
  root.classList.remove('light', 'dark');
  root.classList.add(resolved);
  
  return resolved;
};

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      theme: 'system',
      resolvedTheme: 'light',
      
      setTheme: (newTheme: Theme) => {
        const resolved = applyTheme(newTheme);
        set({ theme: newTheme, resolvedTheme: resolved });
      },
      
      getSystemTheme,
    }),
    {
      name: 'ai-platform-theme',
      storage: createJSONStorage(() => localStorage),
      onRehydrateStorage: () => (state) => {
        if (state) {
          // Apply theme on rehydration
          const resolved = applyTheme(state.theme);
          state.resolvedTheme = resolved;
        }
      },
    }
  )
);

// Hook to initialize theme on mount (call in root layout)
export function useInitializeTheme() {
  const { theme, setTheme, resolvedTheme } = useThemeStore();
  
  // Initialize theme on mount
  if (typeof window !== 'undefined') {
    // Apply stored theme
    const stored = localStorage.getItem('ai-platform-theme');
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        if (parsed.state?.theme) {
          applyTheme(parsed.state.theme as Theme);
        }
      } catch {
        applyTheme(theme);
      }
    } else {
      applyTheme(theme);
    }
    
    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = () => {
      if (useThemeStore.getState().theme === 'system') {
        const newResolved = getSystemTheme();
        useThemeStore.setState({ resolvedTheme: newResolved });
        applyTheme('system');
      }
    };
    
    mediaQuery.addEventListener('change', handleChange);
    
    return () => {
      mediaQuery.removeEventListener('change', handleChange);
    };
  }
  
  return () => {};
}
