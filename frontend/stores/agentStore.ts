'use client';

import { create } from 'zustand';
import type { Agent } from '@/types';

interface AgentState {
  agents: Agent[];
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setAgents: (agents: Agent[]) => void;
  addAgent: (agent: Agent) => void;
  updateAgent: (id: string, updates: Partial<Agent>) => void;
  deleteAgent: (id: string) => Promise<void>;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  loadAgents: () => Promise<void>;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const useAgentStore = create<AgentState>((set, get) => ({
  agents: [],
  isLoading: false,
  error: null,
  
  setAgents: (agents) => set({ agents }),
  
  addAgent: (agent) => set((state) => ({
    agents: [...state.agents, agent]
  })),
  
  updateAgent: (id, updates) => set((state) => ({
    agents: state.agents.map((a) =>
      a.id === id ? { ...a, ...updates } : a
    )
  })),
  
  deleteAgent: async (id) => {
    try {
      const response = await fetch(`${API_BASE}/api/agents/${id}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error('Failed to delete agent');
      
      set((state) => ({
        agents: state.agents.filter((a) => a.id !== id)
      }));
    } catch (error) {
      set({ error: (error as Error).message });
      throw error;
    }
  },
  
  setLoading: (loading) => set({ isLoading: loading }),
  
  setError: (error) => set({ error }),
  
  loadAgents: async () => {
    try {
      set({ isLoading: true, error: null });
      const response = await fetch(`${API_BASE}/api/agents`);
      if (!response.ok) throw new Error('Failed to load agents');
      const data = await response.json();
      set({ agents: data.items || [] });
    } catch (error) {
      set({ error: (error as Error).message });
      // Provide demo agents for testing
      set({
        agents: [
          {
            id: 'agent-1',
            user_id: 'user-1',
            name: 'Code Assistant',
            description: 'Expert in coding, debugging, and software architecture',
            system_prompt: 'You are a helpful coding assistant. You help users write, debug, and understand code.',
            model: 'llama2',
            model_provider: 'ollama',
            temperature: 0.7,
            max_tokens: 2048,
            is_active: true,
            is_public: true,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          },
          {
            id: 'agent-2',
            user_id: 'user-1',
            name: 'Writing Assistant',
            description: 'Helps with writing tasks like emails, articles, and creative writing',
            system_prompt: 'You are a professional writing assistant. You help users craft well-written content.',
            model: 'llama2',
            model_provider: 'ollama',
            temperature: 0.8,
            max_tokens: 2048,
            is_active: true,
            is_public: true,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          },
          {
            id: 'agent-3',
            user_id: 'user-1',
            name: 'Research Analyst',
            description: 'Specialized in data analysis and research',
            system_prompt: 'You are a research analyst. You help users analyze data and conduct research.',
            model: 'llama2',
            model_provider: 'ollama',
            temperature: 0.5,
            max_tokens: 2048,
            is_active: true,
            is_public: true,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          }
        ]
      });
    } finally {
      set({ isLoading: false });
    }
  },
}));
