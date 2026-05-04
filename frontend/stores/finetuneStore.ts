'use client';

import { create } from 'zustand';

export interface Dataset {
  id: string;
  name: string;
  description?: string;
  file_name: string;
  file_size: number;
  file_format: string;
  format_type: string;
  total_samples: number;
  total_tokens: number;
  avg_turns: number;
  is_validated: boolean;
  validation_errors?: any;
  train_ratio: number;
  validation_ratio: number;
  created_at: string;
}

export interface FinetuneJob {
  id: string;
  name: string;
  description?: string;
  dataset_id: string;
  base_model: string;
  status: 'pending' | 'queued' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';
  current_step: number;
  total_steps: number;
  current_epoch: number;
  total_epochs: number;
  current_loss?: number;
  best_loss?: number;
  learning_rate?: number;
  progress_pct: number;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export interface FinetuneModel {
  id: string;
  name: string;
  description?: string;
  job_id: string;
  base_model: string;
  adapter_path?: string;
  merged_path?: string;
  model_type: string;
  quantization?: string;
  final_loss?: number;
  final_perplexity?: number;
  file_size_mb?: number;
  is_deployed: boolean;
  deployment_status: string;
  deployment_endpoint?: string;
  created_at: string;
}

export interface TrainingConfig {
  mode: 'lora' | 'qlora' | 'full';
  base_model: string;
  training: {
    num_train_epochs: number;
    per_device_train_batch_size: number;
    per_device_eval_batch_size: number;
    learning_rate: number;
    weight_decay: number;
    warmup_ratio: number;
    optim: string;
    max_seq_length: number;
    fp16?: boolean;
    bf16?: boolean;
  };
  lora: {
    r: number;
    lora_alpha: number;
    lora_dropout: number;
    target_modules?: string[];
    bias: string;
  };
}

interface FinetuneState {
  // Datasets
  datasets: Dataset[];
  currentDataset: Dataset | null;
  datasetsLoading: boolean;
  
  // Jobs
  jobs: FinetuneJob[];
  currentJob: FinetuneJob | null;
  jobsLoading: boolean;
  
  // Models
  models: FinetuneModel[];
  currentModel: FinetuneModel | null;
  modelsLoading: boolean;
  
  // Metrics
  lossCurve: { steps: number[]; losses: number[] };
  trainingMetrics: any;
  
  // Actions
  loadDatasets: () => Promise<void>;
  getDataset: (id: string) => Promise<Dataset>;
  uploadDataset: (formData: FormData) => Promise<Dataset>;
  deleteDataset: (id: string) => Promise<void>;
  previewDataset: (id: string, limit?: number) => Promise<any[]>;
  
  loadJobs: (status?: string) => Promise<void>;
  getJob: (id: string) => Promise<FinetuneJob>;
  createJob: (name: string, datasetId: string, baseModel: string, config: TrainingConfig) => Promise<FinetuneJob>;
  startJob: (id: string) => Promise<void>;
  pauseJob: (id: string) => Promise<void>;
  resumeJob: (id: string) => Promise<void>;
  stopJob: (id: string) => Promise<void>;
  deleteJob: (id: string) => Promise<void>;
  
  loadModels: () => Promise<void>;
  getModel: (id: string) => Promise<FinetuneModel>;
  deployModel: (id: string) => Promise<void>;
  undeployModel: (id: string) => Promise<void>;
  deleteModel: (id: string) => Promise<void>;
  
  loadJobStatus: (id: string) => Promise<any>;
  subscribeToJobProgress: (id: string) => void;
  unsubscribeFromJobProgress: () => void;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

let eventSource: EventSource | null = null;

export const useFinetuneStore = create<FinetuneState>((set, get) => ({
  // Initial state
  datasets: [],
  currentDataset: null,
  datasetsLoading: false,
  
  jobs: [],
  currentJob: null,
  jobsLoading: false,
  
  models: [],
  currentModel: null,
  modelsLoading: false,
  
  lossCurve: { steps: [], losses: [] },
  trainingMetrics: null,
  
  // Dataset actions
  loadDatasets: async () => {
    set({ datasetsLoading: true });
    try {
      const res = await fetch(`${API_BASE}/api/finetune/datasets`);
      const data = await res.json();
      set({ datasets: data.items, datasetsLoading: false });
    } catch (error) {
      console.error('Failed to load datasets:', error);
      set({ datasetsLoading: false });
    }
  },
  
  getDataset: async (id: string) => {
    const res = await fetch(`${API_BASE}/api/finetune/datasets/${id}`);
    const dataset = await res.json();
    set({ currentDataset: dataset });
    return dataset;
  },
  
  uploadDataset: async (formData: FormData) => {
    const res = await fetch(`${API_BASE}/api/finetune/datasets/upload`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) throw new Error('Failed to upload dataset');
    const dataset = await res.json();
    set(state => ({ datasets: [dataset, ...state.datasets] }));
    return dataset;
  },
  
  deleteDataset: async (id: string) => {
    await fetch(`${API_BASE}/api/finetune/datasets/${id}`, { method: 'DELETE' });
    set(state => ({ datasets: state.datasets.filter(d => d.id !== id) }));
  },
  
  previewDataset: async (id: string, limit = 5) => {
    const res = await fetch(`${API_BASE}/api/finetune/datasets/${id}/preview?limit=${limit}`);
    const data = await res.json();
    return data.samples;
  },
  
  // Job actions
  loadJobs: async (status?: string) => {
    set({ jobsLoading: true });
    try {
      const url = status 
        ? `${API_BASE}/api/finetune/jobs?status=${status}`
        : `${API_BASE}/api/finetune/jobs`;
      const res = await fetch(url);
      const data = await res.json();
      set({ jobs: data.items, jobsLoading: false });
    } catch (error) {
      console.error('Failed to load jobs:', error);
      set({ jobsLoading: false });
    }
  },
  
  getJob: async (id: string) => {
    const res = await fetch(`${API_BASE}/api/finetune/jobs/${id}`);
    const data = await res.json();
    set({ 
      currentJob: data.job,
      lossCurve: data.loss_curve || { steps: [], losses: [] }
    });
    return data.job;
  },
  
  createJob: async (name, datasetId, baseModel, config) => {
    const formData = new FormData();
    formData.append('name', name);
    formData.append('dataset_id', datasetId);
    formData.append('base_model', baseModel);
    formData.append('config', JSON.stringify(config));
    
    const res = await fetch(`${API_BASE}/api/finetune/jobs`, {
      method: 'POST',
      body: formData,
    });
    if (!res.ok) throw new Error('Failed to create job');
    const job = await res.json();
    set(state => ({ jobs: [job, ...state.jobs] }));
    return job;
  },
  
  startJob: async (id: string) => {
    const res = await fetch(`${API_BASE}/api/finetune/jobs/${id}/start`, { method: 'POST' });
    const data = await res.json();
    set(state => ({
      jobs: state.jobs.map(j => j.id === id ? { ...j, status: data.status } : j)
    }));
  },
  
  pauseJob: async (id: string) => {
    const res = await fetch(`${API_BASE}/api/finetune/jobs/${id}/pause`, { method: 'POST' });
    const data = await res.json();
    set(state => ({
      jobs: state.jobs.map(j => j.id === id ? { ...j, status: 'paused' } : j)
    }));
  },
  
  resumeJob: async (id: string) => {
    const res = await fetch(`${API_BASE}/api/finetune/jobs/${id}/resume`, { method: 'POST' });
    const data = await res.json();
    set(state => ({
      jobs: state.jobs.map(j => j.id === id ? { ...j, status: 'running' } : j)
    }));
  },
  
  stopJob: async (id: string) => {
    await fetch(`${API_BASE}/api/finetune/jobs/${id}/stop`, { method: 'POST' });
    set(state => ({
      jobs: state.jobs.map(j => j.id === id ? { ...j, status: 'cancelled' } : j)
    }));
  },
  
  deleteJob: async (id: string) => {
    await fetch(`${API_BASE}/api/finetune/jobs/${id}`, { method: 'DELETE' });
    set(state => ({ jobs: state.jobs.filter(j => j.id !== id) }));
  },
  
  // Model actions
  loadModels: async () => {
    set({ modelsLoading: true });
    try {
      const res = await fetch(`${API_BASE}/api/finetune/models`);
      const data = await res.json();
      set({ models: data.items, modelsLoading: false });
    } catch (error) {
      console.error('Failed to load models:', error);
      set({ modelsLoading: false });
    }
  },
  
  getModel: async (id: string) => {
    const res = await fetch(`${API_BASE}/api/finetune/models/${id}`);
    const model = await res.json();
    set({ currentModel: model });
    return model;
  },
  
  deployModel: async (id: string) => {
    const res = await fetch(`${API_BASE}/api/finetune/models/${id}/deploy`, { method: 'POST' });
    const data = await res.json();
    set(state => ({
      models: state.models.map(m => m.id === id ? { ...m, is_deployed: true, deployment_status: data.deployment_status } : m)
    }));
  },
  
  undeployModel: async (id: string) => {
    const res = await fetch(`${API_BASE}/api/finetune/models/${id}/undeploy`, { method: 'POST' });
    set(state => ({
      models: state.models.map(m => m.id === id ? { ...m, is_deployed: false, deployment_status: 'not_deployed' } : m)
    }));
  },
  
  deleteModel: async (id: string) => {
    await fetch(`${API_BASE}/api/finetune/models/${id}`, { method: 'DELETE' });
    set(state => ({ models: state.models.filter(m => m.id !== id) }));
  },
  
  // Monitoring
  loadJobStatus: async (id: string) => {
    const res = await fetch(`${API_BASE}/api/finetune/jobs/${id}`);
    const data = await res.json();
    set(state => ({
      currentJob: data.job,
      lossCurve: data.loss_curve || state.lossCurve,
      trainingMetrics: data
    }));
    return data;
  },
  
  subscribeToJobProgress: (id: string) => {
    // Close existing connection
    if (eventSource) {
      eventSource.close();
    }
    
    eventSource = new EventSource(`${API_BASE}/api/finetune/jobs/${id}/stream`);
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'metrics') {
          const metrics = data.data;
          set(state => ({
            lossCurve: {
              steps: [...state.lossCurve.steps, metrics.step],
              losses: [...state.lossCurve.losses, metrics.loss],
            },
            currentJob: state.currentJob ? {
              ...state.currentJob,
              current_step: metrics.step,
              current_loss: metrics.loss,
              current_epoch: metrics.epoch,
            } : null,
          }));
        }
      } catch (e) {
        console.error('Failed to parse SSE data:', e);
      }
    };
    
    eventSource.onerror = () => {
      console.error('SSE connection error');
      eventSource?.close();
    };
  },
  
  unsubscribeFromJobProgress: () => {
    if (eventSource) {
      eventSource.close();
      eventSource = null;
    }
  },
}));
