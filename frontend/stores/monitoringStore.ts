// System monitoring store
'use client';

import { create } from 'zustand';

export interface ServiceHealth {
  name: string;
  status: 'online' | 'offline' | 'degraded';
  latency_ms?: number;
  error?: string;
}

export interface HealthCheckResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  services: Record<string, ServiceHealth>;
  uptime_seconds: number;
}

export interface RequestMetrics {
  total: number;
  by_endpoint: Record<string, number>;
  by_method: Record<string, number>;
  errors: number;
  error_rate_percent: number;
  avg_response_time_ms: number;
}

export interface Statistics {
  users: number;
  conversations: number;
  agents: number;
  knowledge_bases: number;
  documents: number;
  workflows: number;
  workflow_executions: number;
}

export interface MetricsResponse {
  timestamp: string;
  uptime_seconds: number;
  statistics: Statistics;
  requests: RequestMetrics;
}

interface MonitoringState {
  health: HealthCheckResponse | null;
  metrics: MetricsResponse | null;
  isLoading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  
  // Actions
  fetchHealth: () => Promise<void>;
  fetchMetrics: () => Promise<void>;
  fetchAll: () => Promise<void>;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const useMonitoringStore = create<MonitoringState>((set, get) => ({
  health: null,
  metrics: null,
  isLoading: false,
  error: null,
  lastUpdated: null,
  
  fetchHealth: async () => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await fetch(`${API_BASE}/api/health`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch health status');
      }
      
      const data = await response.json();
      
      set({
        health: data,
        isLoading: false,
        lastUpdated: new Date(),
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch health',
        isLoading: false,
      });
    }
  },
  
  fetchMetrics: async () => {
    set({ isLoading: true, error: null });
    
    try {
      const response = await fetch(`${API_BASE}/api/metrics`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch metrics');
      }
      
      const data = await response.json();
      
      set({
        metrics: data,
        isLoading: false,
        lastUpdated: new Date(),
      });
    } catch (error) {
      set({
        error: error instanceof Error ? error.message : 'Failed to fetch metrics',
        isLoading: false,
      });
    }
  },
  
  fetchAll: async () => {
    await Promise.all([get().fetchHealth(), get().fetchMetrics()]);
  },
}));
