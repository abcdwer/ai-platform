'use client';

import { create } from 'zustand';
import type { ModelInfo, AvailableModels, ModelStatus } from '@/types';

interface ModelState {
  models: AvailableModels | null;
  modelStatus: {
    provider: string;
    status: string;
    error?: string;
    model_count: number;
  }[];
  isLoading: boolean;
  error: string | null;
  
  setModels: (models: AvailableModels) => void;
  setModelStatus: (status: ModelState['modelStatus']) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  
  loadModels: () => Promise<void>;
  checkHealth: () => Promise<void>;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const useModelStore = create<ModelState>((set, get) => ({
  models: null,
  modelStatus: [],
  isLoading: false,
  error: null,
  
  setModels: (models) => set({ models }),
  
  setModelStatus: (modelStatus) => set({ modelStatus }),
  
  setLoading: (loading) => set({ isLoading: loading }),
  
  setError: (error) => set({ error }),
  
  loadModels: async () => {
    try {
      set({ isLoading: true, error: null });
      const response = await fetch(`${API_BASE}/api/models`);
      if (!response.ok) throw new Error('Failed to load models');
      const data = await response.json();
      set({ models: data });
      
      // Also load status
      await get().checkHealth();
    } catch (error) {
      set({ error: (error as Error).message });
      // Provide demo data if API fails
      set({
        models: {
          ollama: [
            {
              id: 'llama2',
              name: 'Llama 2',
              provider: 'ollama',
              model_id: 'llama2',
              is_default: true,
              supports_streaming: true,
              supports_function_calling: false,
            },
            {
              id: 'mistral',
              name: 'Mistral',
              provider: 'ollama',
              model_id: 'mistral',
              is_default: false,
              supports_streaming: true,
              supports_function_calling: false,
            },
          ],
          openai: [
            {
              id: 'gpt-4-turbo-preview',
              name: 'GPT-4 Turbo',
              provider: 'openai',
              model_id: 'gpt-4-turbo-preview',
              is_default: false,
              supports_streaming: true,
              supports_function_calling: true,
            },
            {
              id: 'gpt-3.5-turbo',
              name: 'GPT-3.5 Turbo',
              provider: 'openai',
              model_id: 'gpt-3.5-turbo',
              is_default: false,
              supports_streaming: true,
              supports_function_calling: false,
            },
          ],
          all: [],
        },
        modelStatus: [
          { provider: 'ollama', status: 'online', model_count: 2 },
          { provider: 'openai', status: 'not_configured', error: 'API key not set', model_count: 0 },
        ],
      });
    } finally {
      set({ isLoading: false });
    }
  },
  
  checkHealth: async () => {
    try {
      const response = await fetch(`${API_BASE}/api/models/status`);
      if (!response.ok) throw new Error('Failed to check health');
      const data = await response.json();
      set({ modelStatus: data.providers || [] });
    } catch (error) {
      // Ignore health check errors
      console.warn('Health check failed:', error);
    }
  },
}));
