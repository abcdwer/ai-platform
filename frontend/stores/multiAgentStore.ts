'use client';

import { create } from 'zustand';
import type {
  AgentGroup,
  AgentGroupCreate,
  AgentGroupUpdate,
  AgentMember,
  AgentMemberCreate,
  AgentMemberUpdate,
  CollaborationSession,
  AgentMessage,
  SessionExecuteRequest,
  SessionExecuteResponse,
  CollaborationMode,
  ModeConfig,
} from '@/types/multi-agent';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface MultiAgentState {
  // Groups
  groups: AgentGroup[];
  currentGroup: AgentGroup | null;
  isLoadingGroups: boolean;
  groupsError: string | null;
  
  // Sessions
  sessions: CollaborationSession[];
  currentSession: CollaborationSession | null;
  isLoadingSessions: boolean;
  
  // Execution
  isExecuting: boolean;
  executionError: string | null;
  
  // Messages
  messages: AgentMessage[];
  
  // UI State
  showCreateDialog: boolean;
  showMemberDialog: boolean;
  editingMember: AgentMember | null;
  
  // Actions - Groups
  loadGroups: () => Promise<void>;
  createGroup: (data: AgentGroupCreate) => Promise<AgentGroup | null>;
  updateGroup: (id: string, data: AgentGroupUpdate) => Promise<AgentGroup | null>;
  deleteGroup: (id: string) => Promise<boolean>;
  setCurrentGroup: (group: AgentGroup | null) => void;
  
  // Actions - Members
  addMember: (groupId: string, data: AgentMemberCreate) => Promise<AgentMember | null>;
  updateMember: (groupId: string, memberId: string, data: AgentMemberUpdate) => Promise<AgentMember | null>;
  deleteMember: (groupId: string, memberId: string) => Promise<boolean>;
  reorderMembers: (groupId: string, memberOrders: { id: string; order: number }[]) => Promise<boolean>;
  
  // Actions - Sessions
  loadSessions: (groupId: string) => Promise<void>;
  getSession: (sessionId: string) => Promise<CollaborationSession | null>;
  setCurrentSession: (session: CollaborationSession | null) => void;
  
  // Actions - Execution
  executeSession: (groupId: string, request: SessionExecuteRequest) => Promise<SessionExecuteResponse | null>;
  stopSession: (sessionId: string) => Promise<boolean>;
  pauseSession: (sessionId: string) => Promise<boolean>;
  resumeSession: (sessionId: string) => Promise<boolean>;
  
  // Actions - Messages
  loadMessages: (sessionId: string) => Promise<void>;
  clearMessages: () => void;
  
  // Actions - UI
  setShowCreateDialog: (show: boolean) => void;
  setShowMemberDialog: (show: boolean) => void;
  setEditingMember: (member: AgentMember | null) => void;
  
  // Helpers
  setError: (error: string | null) => void;
}

export const useMultiAgentStore = create<MultiAgentState>((set, get) => ({
  // Initial state
  groups: [],
  currentGroup: null,
  isLoadingGroups: false,
  groupsError: null,
  
  sessions: [],
  currentSession: null,
  isLoadingSessions: false,
  
  isExecuting: false,
  executionError: null,
  
  messages: [],
  
  showCreateDialog: false,
  showMemberDialog: false,
  editingMember: null,
  
  // ============== Groups ==============
  
  loadGroups: async () => {
    try {
      set({ isLoadingGroups: true, groupsError: null });
      const response = await fetch(`${API_BASE}/api/multi-agent/groups`);
      
      if (!response.ok) {
        // Return demo data for testing
        set({
          groups: getDemoGroups(),
          isLoadingGroups: false,
        });
        return;
      }
      
      const data = await response.json();
      set({ groups: data.items || [], isLoadingGroups: false });
    } catch (error) {
      set({
        groupsError: (error as Error).message,
        isLoadingGroups: false,
        groups: getDemoGroups(),
      });
    }
  },
  
  createGroup: async (data: AgentGroupCreate) => {
    try {
      set({ groupsError: null });
      const response = await fetch(`${API_BASE}/api/multi-agent/groups`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      
      if (!response.ok) throw new Error('Failed to create group');
      
      const group = await response.json();
      set((state) => ({ groups: [group, ...state.groups] }));
      return group;
    } catch (error) {
      set({ groupsError: (error as Error).message });
      return null;
    }
  },
  
  updateGroup: async (id: string, data: AgentGroupUpdate) => {
    try {
      set({ groupsError: null });
      const response = await fetch(`${API_BASE}/api/multi-agent/groups/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      
      if (!response.ok) throw new Error('Failed to update group');
      
      const group = await response.json();
      set((state) => ({
        groups: state.groups.map((g) => (g.id === id ? group : g)),
        currentGroup: state.currentGroup?.id === id ? group : state.currentGroup,
      }));
      return group;
    } catch (error) {
      set({ groupsError: (error as Error).message });
      return null;
    }
  },
  
  deleteGroup: async (id: string) => {
    try {
      set({ groupsError: null });
      const response = await fetch(`${API_BASE}/api/multi-agent/groups/${id}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) throw new Error('Failed to delete group');
      
      set((state) => ({
        groups: state.groups.filter((g) => g.id !== id),
        currentGroup: state.currentGroup?.id === id ? null : state.currentGroup,
      }));
      return true;
    } catch (error) {
      set({ groupsError: (error as Error).message });
      return false;
    }
  },
  
  setCurrentGroup: (group) => set({ currentGroup: group }),
  
  // ============== Members ==============
  
  addMember: async (groupId: string, data: AgentMemberCreate) => {
    try {
      set({ groupsError: null });
      const response = await fetch(`${API_BASE}/api/multi-agent/groups/${groupId}/members`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });
      
      if (!response.ok) throw new Error('Failed to add member');
      
      const member = await response.json();
      
      // Update current group
      set((state) => {
        if (!state.currentGroup || state.currentGroup.id !== groupId) return state;
        return {
          currentGroup: {
            ...state.currentGroup,
            members: [...(state.currentGroup.members || []), member],
          },
        };
      });
      
      return member;
    } catch (error) {
      set({ groupsError: (error as Error).message });
      return null;
    }
  },
  
  updateMember: async (groupId: string, memberId: string, data: AgentMemberUpdate) => {
    try {
      set({ groupsError: null });
      const response = await fetch(
        `${API_BASE}/api/multi-agent/groups/${groupId}/members/${memberId}`,
        {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data),
        }
      );
      
      if (!response.ok) throw new Error('Failed to update member');
      
      const member = await response.json();
      
      // Update current group
      set((state) => {
        if (!state.currentGroup || state.currentGroup.id !== groupId) return state;
        return {
          currentGroup: {
            ...state.currentGroup,
            members: state.currentGroup.members?.map((m) =>
              m.id === memberId ? member : m
            ),
          },
        };
      });
      
      return member;
    } catch (error) {
      set({ groupsError: (error as Error).message });
      return null;
    }
  },
  
  deleteMember: async (groupId: string, memberId: string) => {
    try {
      set({ groupsError: null });
      const response = await fetch(
        `${API_BASE}/api/multi-agent/groups/${groupId}/members/${memberId}`,
        { method: 'DELETE' }
      );
      
      if (!response.ok) throw new Error('Failed to delete member');
      
      // Update current group
      set((state) => {
        if (!state.currentGroup || state.currentGroup.id !== groupId) return state;
        return {
          currentGroup: {
            ...state.currentGroup,
            members: state.currentGroup.members?.filter((m) => m.id !== memberId),
          },
        };
      });
      
      return true;
    } catch (error) {
      set({ groupsError: (error as Error).message });
      return false;
    }
  },
  
  reorderMembers: async (groupId: string, memberOrders: { id: string; order: number }[]) => {
    try {
      set({ groupsError: null });
      const response = await fetch(
        `${API_BASE}/api/multi-agent/groups/${groupId}/members/reorder`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(memberOrders),
        }
      );
      
      if (!response.ok) throw new Error('Failed to reorder members');
      return true;
    } catch (error) {
      set({ groupsError: (error as Error).message });
      return false;
    }
  },
  
  // ============== Sessions ==============
  
  loadSessions: async (groupId: string) => {
    try {
      set({ isLoadingSessions: true });
      const response = await fetch(
        `${API_BASE}/api/multi-agent/groups/${groupId}/sessions`
      );
      
      if (!response.ok) throw new Error('Failed to load sessions');
      
      const data = await response.json();
      set({ sessions: data.items || [], isLoadingSessions: false });
    } catch (error) {
      set({ isLoadingSessions: false });
    }
  },
  
  getSession: async (sessionId: string) => {
    try {
      const response = await fetch(
        `${API_BASE}/api/multi-agent/sessions/${sessionId}`
      );
      
      if (!response.ok) throw new Error('Failed to get session');
      
      const session = await response.json();
      return session;
    } catch (error) {
      return null;
    }
  },
  
  setCurrentSession: (session) => set({ currentSession: session }),
  
  // ============== Execution ==============
  
  executeSession: async (groupId: string, request: SessionExecuteRequest) => {
    try {
      set({ isExecuting: true, executionError: null });
      
      const response = await fetch(
        `${API_BASE}/api/multi-agent/groups/${groupId}/execute`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(request),
        }
      );
      
      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Execution failed');
      }
      
      const result: SessionExecuteResponse = await response.json();
      
      // Update messages
      set((state) => ({
        messages: [...state.messages, ...result.messages],
        isExecuting: false,
      }));
      
      return result;
    } catch (error) {
      set({
        executionError: (error as Error).message,
        isExecuting: false,
      });
      return null;
    }
  },
  
  stopSession: async (sessionId: string) => {
    try {
      const response = await fetch(
        `${API_BASE}/api/multi-agent/sessions/${sessionId}/stop`,
        { method: 'POST' }
      );
      
      return response.ok;
    } catch {
      return false;
    }
  },
  
  pauseSession: async (sessionId: string) => {
    try {
      const response = await fetch(
        `${API_BASE}/api/multi-agent/sessions/${sessionId}/pause`,
        { method: 'POST' }
      );
      
      return response.ok;
    } catch {
      return false;
    }
  },
  
  resumeSession: async (sessionId: string) => {
    try {
      const response = await fetch(
        `${API_BASE}/api/multi-agent/sessions/${sessionId}/resume`,
        { method: 'POST' }
      );
      
      return response.ok;
    } catch {
      return false;
    }
  },
  
  // ============== Messages ==============
  
  loadMessages: async (sessionId: string) => {
    try {
      const response = await fetch(
        `${API_BASE}/api/multi-agent/sessions/${sessionId}/messages`
      );
      
      if (!response.ok) throw new Error('Failed to load messages');
      
      const messages: AgentMessage[] = await response.json();
      set({ messages });
    } catch {
      // Ignore errors
    }
  },
  
  clearMessages: () => set({ messages: [] }),
  
  // ============== UI ==============
  
  setShowCreateDialog: (show) => set({ showCreateDialog: show }),
  setShowMemberDialog: (show) => set({ showMemberDialog: show }),
  setEditingMember: (member) => set({ editingMember: member }),
  setError: (error) => set({ groupsError: error }),
}));

// Demo data for testing
function getDemoGroups(): AgentGroup[] {
  return [
    {
      id: 'group-1',
      user_id: 'user-1',
      name: 'Code Review Team',
      description: 'Multi-agent team for code review and refactoring suggestions',
      mode: 'sequential',
      mode_config: {},
      default_model: 'llama2',
      default_provider: 'ollama',
      enable_orchestrator: true,
      max_iterations: 5,
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      members: [
        {
          id: 'member-1',
          group_id: 'group-1',
          name: 'Code Analyzer',
          role: 'member',
          system_prompt: 'You analyze code for bugs, security issues, and performance problems.',
          execution_order: 0,
          temperature: 0.3,
          max_tokens: 2048,
          tools: [],
          color: '#3b82f6',
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: 'member-2',
          group_id: 'group-1',
          name: 'Refactoring Advisor',
          role: 'member',
          system_prompt: 'You suggest refactoring improvements and best practices.',
          execution_order: 1,
          temperature: 0.5,
          max_tokens: 2048,
          tools: [],
          color: '#10b981',
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
    },
    {
      id: 'group-2',
      user_id: 'user-1',
      name: 'Debate Panel',
      description: 'Agents debate topics with pro/con positions',
      mode: 'debate',
      mode_config: { rounds: 3, allow_rebuttal: true },
      default_model: 'llama2',
      default_provider: 'ollama',
      enable_orchestrator: true,
      max_iterations: 10,
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      members: [
        {
          id: 'member-3',
          group_id: 'group-2',
          name: 'Pro Speaker',
          role: 'supporter',
          system_prompt: 'You argue in favor of the given proposition. Be logical and persuasive.',
          execution_order: 0,
          temperature: 0.7,
          max_tokens: 2048,
          tools: [],
          color: '#10b981',
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: 'member-4',
          group_id: 'group-2',
          name: 'Con Speaker',
          role: 'opponent',
          system_prompt: 'You argue against the given proposition. Be logical and persuasive.',
          execution_order: 1,
          temperature: 0.7,
          max_tokens: 2048,
          tools: [],
          color: '#ef4444',
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: 'member-5',
          group_id: 'group-2',
          name: 'Judge',
          role: 'judge',
          system_prompt: 'You evaluate the debate and make a fair judgment based on the arguments presented.',
          execution_order: 2,
          temperature: 0.3,
          max_tokens: 2048,
          tools: [],
          color: '#f59e0b',
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
    },
    {
      id: 'group-3',
      user_id: 'user-1',
      name: 'Research Team',
      description: 'Parallel research agents that gather and synthesize information',
      mode: 'parallel',
      mode_config: { max_parallel: 3, aggregation_method: 'merge' },
      default_model: 'llama2',
      default_provider: 'ollama',
      enable_orchestrator: true,
      max_iterations: 3,
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      members: [
        {
          id: 'member-6',
          group_id: 'group-3',
          name: 'Web Researcher',
          role: 'member',
          system_prompt: 'You search for information on the web about the given topic.',
          execution_order: 0,
          temperature: 0.4,
          max_tokens: 2048,
          tools: [],
          color: '#8b5cf6',
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
        {
          id: 'member-7',
          group_id: 'group-3',
          name: 'Academic Researcher',
          role: 'member',
          system_prompt: 'You find academic papers and scholarly sources.',
          execution_order: 1,
          temperature: 0.4,
          max_tokens: 2048,
          tools: [],
          color: '#06b6d4',
          is_active: true,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        },
      ],
    },
  ];
}
