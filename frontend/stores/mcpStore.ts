'use client';

import { create } from 'zustand';

export interface MCPServer {
  id: string;
  name: string;
  description?: string;
  transport_type: 'sse' | 'stdio' | 'http_stream';
  sse_url?: string;
  sse_endpoint?: string;
  stdio_command?: string;
  stdio_args?: string[];
  http_url?: string;
  auth_type?: string;
  timeout: number;
  max_retries: number;
  is_connected: boolean;
  last_connected_at?: string;
  connection_error?: string;
  created_at: string;
}

export interface MCPTool {
  id: string;
  server_id: string;
  name: string;
  description?: string;
  input_schema: {
    type: string;
    properties?: Record<string, any>;
    required?: string[];
  };
  category?: string;
  tags?: string[];
  is_discovered: boolean;
  total_calls: number;
  success_count: number;
  failure_count: number;
  success_rate: number;
  avg_execution_time_ms: number;
  discovered_at?: string;
  created_at: string;
}

export interface MCPLog {
  id: string;
  server_id: string;
  tool_id?: string;
  request_id: string;
  method: string;
  status_code?: number;
  success: boolean;
  latency_ms?: number;
  error_message?: string;
  created_at: string;
}

interface MCPState {
  // Servers
  servers: MCPServer[];
  currentServer: MCPServer | null;
  serversLoading: boolean;
  
  // Tools
  tools: MCPTool[];
  currentTool: MCPTool | null;
  
  // Logs
  logs: MCPLog[];
  logsLoading: boolean;
  
  // Actions
  loadServers: () => Promise<void>;
  getServer: (id: string) => Promise<MCPServer>;
  createServer: (data: Partial<MCPServer>) => Promise<MCPServer>;
  updateServer: (id: string, data: Partial<MCPServer>) => Promise<void>;
  deleteServer: (id: string) => Promise<void>;
  
  connectServer: (id: string) => Promise<void>;
  disconnectServer: (id: string) => Promise<void>;
  testConnection: (id: string) => Promise<{ success: boolean; message: string }>;
  
  loadServerTools: (serverId: string) => Promise<MCPTool[]>;
  getTool: (id: string) => Promise<MCPTool>;
  callTool: (id: string, parameters: Record<string, any>) => Promise<any>;
  
  loadLogs: (serverId?: string, toolId?: string) => Promise<void>;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const useMCPStore = create<MCPState>((set, get) => ({
  // Initial state
  servers: [],
  currentServer: null,
  serversLoading: false,
  
  tools: [],
  currentTool: null,
  
  logs: [],
  logsLoading: false,
  
  // Server actions
  loadServers: async () => {
    set({ serversLoading: true });
    try {
      const res = await fetch(`${API_BASE}/api/mcp/servers`);
      const data = await res.json();
      set({ servers: data.items, serversLoading: false });
    } catch (error) {
      console.error('Failed to load servers:', error);
      set({ serversLoading: false });
    }
  },
  
  getServer: async (id: string) => {
    const res = await fetch(`${API_BASE}/api/mcp/servers/${id}`);
    const server = await res.json();
    set({ currentServer: server });
    return server;
  },
  
  createServer: async (data: Partial<MCPServer>) => {
    const formData = new FormData();
    formData.append('name', data.name || '');
    formData.append('transport_type', data.transport_type || 'sse');
    if (data.description) formData.append('description', data.description);
    if (data.sse_url) formData.append('sse_url', data.sse_url);
    if (data.sse_endpoint) formData.append('sse_endpoint', data.sse_endpoint);
    if (data.stdio_command) formData.append('stdio_command', data.stdio_command);
    if (data.stdio_args) formData.append('stdio_args', JSON.stringify(data.stdio_args));
    if (data.http_url) formData.append('http_url', data.http_url);
    if (data.auth_type) formData.append('auth_type', data.auth_type);
    
    const res = await fetch(`${API_BASE}/api/mcp/servers`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) throw new Error('Failed to create server');
    const server = await res.json();
    set(state => ({ servers: [server, ...state.servers] }));
    return server;
  },
  
  updateServer: async (id: string, data: Partial<MCPServer>) => {
    const formData = new FormData();
    Object.entries(data).forEach(([key, value]) => {
      if (value !== undefined) {
        if (typeof value === 'object') {
          formData.append(key, JSON.stringify(value));
        } else {
          formData.append(key, String(value));
        }
      }
    });
    
    await fetch(`${API_BASE}/api/mcp/servers/${id}`, {
      method: 'PATCH',
      body: formData,
    });
    
    // Refresh server
    await get().getServer(id);
  },
  
  deleteServer: async (id: string) => {
    await fetch(`${API_BASE}/api/mcp/servers/${id}`, { method: 'DELETE' });
    set(state => ({ 
      servers: state.servers.filter(s => s.id !== id),
      currentServer: state.currentServer?.id === id ? null : state.currentServer,
    }));
  },
  
  // Connection actions
  connectServer: async (id: string) => {
    const res = await fetch(`${API_BASE}/api/mcp/servers/${id}/connect`, { method: 'POST' });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Failed to connect');
    set(state => ({
      servers: state.servers.map(s => s.id === id ? { ...s, is_connected: true } : s),
      currentServer: state.currentServer?.id === id ? { ...state.currentServer, is_connected: true } : state.currentServer,
    }));
  },
  
  disconnectServer: async (id: string) => {
    await fetch(`${API_BASE}/api/mcp/servers/${id}/disconnect`, { method: 'POST' });
    set(state => ({
      servers: state.servers.map(s => s.id === id ? { ...s, is_connected: false } : s),
      currentServer: state.currentServer?.id === id ? { ...state.currentServer, is_connected: false } : state.currentServer,
    }));
  },
  
  testConnection: async (id: string) => {
    const res = await fetch(`${API_BASE}/api/mcp/servers/${id}/test`, { method: 'POST' });
    return await res.json();
  },
  
  // Tool actions
  loadServerTools: async (serverId: string) => {
    const res = await fetch(`${API_BASE}/api/mcp/servers/${serverId}/tools`);
    const data = await res.json();
    set({ tools: data.items });
    return data.items;
  },
  
  getTool: async (id: string) => {
    const res = await fetch(`${API_BASE}/api/mcp/tools/${id}`);
    const tool = await res.json();
    set({ currentTool: tool });
    return tool;
  },
  
  callTool: async (id: string, parameters: Record<string, any>) => {
    const formData = new FormData();
    formData.append('parameters', JSON.stringify(parameters));
    
    const res = await fetch(`${API_BASE}/api/mcp/tools/${id}/call`, {
      method: 'POST',
      body: formData,
    });
    
    const result = await res.json();
    
    if (!result.success) {
      throw new Error(result.error || 'Tool call failed');
    }
    
    return result;
  },
  
  // Log actions
  loadLogs: async (serverId?: string, toolId?: string) => {
    set({ logsLoading: true });
    try {
      let url = `${API_BASE}/api/mcp/logs`;
      const params = new URLSearchParams();
      if (serverId) params.append('server_id', serverId);
      if (toolId) params.append('tool_id', toolId);
      if (params.toString()) url += `?${params.toString()}`;
      
      const res = await fetch(url);
      const data = await res.json();
      set({ logs: data.items, logsLoading: false });
    } catch (error) {
      console.error('Failed to load logs:', error);
      set({ logsLoading: false });
    }
  },
}));
