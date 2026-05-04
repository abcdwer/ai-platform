'use client';

import { create } from 'zustand';

export interface WorkflowNode {
  id: string;
  type: string;
  position: { x: number; y: number };
  data: {
    label: string;
    config: Record<string, any>;
  };
}

export interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  sourceHandle?: string;
  targetHandle?: string;
  label?: string;
}

export interface Workflow {
  id: string;
  name: string;
  description?: string;
  version: number;
  status: 'draft' | 'published' | 'archived';
  graph_data?: {
    nodes: WorkflowNode[];
    edges: WorkflowEdge[];
  };
  created_at: string;
  updated_at: string;
}

export interface Execution {
  id: string;
  workflow_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  trigger_type: 'manual' | 'api' | 'schedule' | 'event';
  inputs?: Record<string, any>;
  outputs?: Record<string, any>;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  node_executions?: NodeExecution[];
}

export interface NodeExecution {
  id: string;
  execution_id: string;
  node_id: string;
  node_type: string;
  node_name?: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  inputs?: Record<string, any>;
  outputs?: Record<string, any>;
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
  error_message?: string;
  retry_count: number;
}

interface WorkflowState {
  // Current workflow being edited
  currentWorkflow: Workflow | null;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  
  // Selection
  selectedNode: WorkflowNode | null;
  
  // Execution
  currentExecution: Execution | null;
  isExecuting: boolean;
  
  // UI state
  showConfigPanel: boolean;
  showNodePanel: boolean;
  
  // History for undo/redo
  history: Array<{ nodes: WorkflowNode[]; edges: WorkflowEdge[] }>;
  historyIndex: number;
  
  // Actions
  setCurrentWorkflow: (workflow: Workflow | null) => void;
  setNodes: (nodes: WorkflowNode[]) => void;
  setEdges: (edges: WorkflowEdge[]) => void;
  addNode: (node: WorkflowNode) => void;
  updateNode: (nodeId: string, data: Partial<WorkflowNode['data']>) => void;
  removeNode: (nodeId: string) => void;
  addEdge: (edge: WorkflowEdge) => void;
  removeEdge: (edgeId: string) => void;
  setSelectedNode: (node: WorkflowNode | null) => void;
  setCurrentExecution: (execution: Execution | null) => void;
  setIsExecuting: (isExecuting: boolean) => void;
  setShowConfigPanel: (show: boolean) => void;
  setShowNodePanel: (show: boolean) => void;
  saveToHistory: () => void;
  undo: () => void;
  redo: () => void;
  resetWorkflow: () => void;
  
  // API helpers
  loadWorkflow: (workflow: Workflow) => void;
  getGraphData: () => { nodes: WorkflowNode[]; edges: WorkflowEdge[] };
}

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  // Initial state
  currentWorkflow: null,
  nodes: [],
  edges: [],
  selectedNode: null,
  currentExecution: null,
  isExecuting: false,
  showConfigPanel: false,
  showNodePanel: true,
  history: [],
  historyIndex: -1,
  
  // Actions
  setCurrentWorkflow: (workflow) => set({ currentWorkflow: workflow }),
  
  setNodes: (nodes) => set({ nodes }),
  
  setEdges: (edges) => set({ edges }),
  
  addNode: (node) => {
    set((state) => {
      state.nodes.push(node);
    });
    get().saveToHistory();
  },
  
  updateNode: (nodeId, data) => {
    set((state) => {
      const node = state.nodes.find((n) => n.id === nodeId);
      if (node) {
        node.data = { ...node.data, ...data };
      }
    });
  },
  
  removeNode: (nodeId) => {
    set((state) => {
      state.nodes = state.nodes.filter((n) => n.id !== nodeId);
      state.edges = state.edges.filter(
        (e) => e.source !== nodeId && e.target !== nodeId
      );
      if (state.selectedNode?.id === nodeId) {
        state.selectedNode = null;
      }
    });
    get().saveToHistory();
  },
  
  addEdge: (edge) => {
    set((state) => {
      // Prevent duplicate edges
      const exists = state.edges.some(
        (e) =>
          e.source === edge.source &&
          e.target === edge.target &&
          e.sourceHandle === edge.sourceHandle
      );
      if (!exists) {
        state.edges.push(edge);
      }
    });
    get().saveToHistory();
  },
  
  removeEdge: (edgeId) => {
    set((state) => {
      state.edges = state.edges.filter((e) => e.id !== edgeId);
    });
    get().saveToHistory();
  },
  
  setSelectedNode: (node) => set({ selectedNode: node, showConfigPanel: !!node }),
  
  setCurrentExecution: (execution) => set({ currentExecution: execution }),
  
  setIsExecuting: (isExecuting) => set({ isExecuting }),
  
  setShowConfigPanel: (show) => set({ showConfigPanel: show }),
  
  setShowNodePanel: (show) => set({ showNodePanel: show }),
  
  saveToHistory: () => {
    const { nodes, edges, history, historyIndex } = get();
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push({
      nodes: JSON.parse(JSON.stringify(nodes)),
      edges: JSON.parse(JSON.stringify(edges)),
    });
    
    // Limit history size
    if (newHistory.length > 50) {
      newHistory.shift();
    }
    
    set({
      history: newHistory,
      historyIndex: newHistory.length - 1,
    });
  },
  
  undo: () => {
    const { history, historyIndex } = get();
    if (historyIndex > 0) {
      const prevState = history[historyIndex - 1];
      set({
        nodes: JSON.parse(JSON.stringify(prevState.nodes)),
        edges: JSON.parse(JSON.stringify(prevState.edges)),
        historyIndex: historyIndex - 1,
      });
    }
  },
  
  redo: () => {
    const { history, historyIndex } = get();
    if (historyIndex < history.length - 1) {
      const nextState = history[historyIndex + 1];
      set({
        nodes: JSON.parse(JSON.stringify(nextState.nodes)),
        edges: JSON.parse(JSON.stringify(nextState.edges)),
        historyIndex: historyIndex + 1,
      });
    }
  },
  
  resetWorkflow: () => {
    set({
      currentWorkflow: null,
      nodes: [],
      edges: [],
      selectedNode: null,
      currentExecution: null,
      isExecuting: false,
      history: [],
      historyIndex: -1,
    });
  },
  
  loadWorkflow: (workflow) => {
    const nodes = workflow.graph_data?.nodes || [];
    const edges = workflow.graph_data?.edges || [];
    set({
      currentWorkflow: workflow,
      nodes,
      edges,
      history: [{ nodes, edges }],
      historyIndex: 0,
    });
  },
  
  getGraphData: () => {
    const { nodes, edges } = get();
    return { nodes, edges };
  },
}));

// Node type definitions with metadata
export const NODE_TYPES_CONFIG: Record<string, {
  label: string;
  color: string;
  icon: string;
  category: 'basic' | 'ai' | 'tool';
  description: string;
}> = {
  start: {
    label: 'Start',
    color: '#22c55e',
    icon: 'Play',
    category: 'basic',
    description: 'Workflow entry point',
  },
  end: {
    label: 'End',
    color: '#ef4444',
    icon: 'Square',
    category: 'basic',
    description: 'Workflow exit point',
  },
  llm: {
    label: 'LLM',
    color: '#8b5cf6',
    icon: 'Brain',
    category: 'ai',
    description: 'Call a language model',
  },
  code: {
    label: 'Code',
    color: '#f97316',
    icon: 'Code',
    category: 'basic',
    description: 'Execute code',
  },
  condition: {
    label: 'Condition',
    color: '#eab308',
    icon: 'GitBranch',
    category: 'basic',
    description: 'Branch based on condition',
  },
  loop: {
    label: 'Loop',
    color: '#06b6d4',
    icon: 'Repeat',
    category: 'basic',
    description: 'Iterate over items',
  },
  delay: {
    label: 'Delay',
    color: '#6b7280',
    icon: 'Clock',
    category: 'basic',
    description: 'Wait for a duration',
  },
  http: {
    label: 'HTTP Request',
    color: '#14b8a6',
    icon: 'Globe',
    category: 'basic',
    description: 'Make HTTP requests',
  },
  transform: {
    label: 'Transform',
    color: '#ec4899',
    icon: 'Shuffle',
    category: 'basic',
    description: 'Transform data',
  },
  merge: {
    label: 'Merge',
    color: '#64748b',
    icon: 'GitMerge',
    category: 'basic',
    description: 'Merge branches',
  },
  knowledge: {
    label: 'Knowledge Base',
    color: '#3b82f6',
    icon: 'BookOpen',
    category: 'ai',
    description: 'Query knowledge base',
  },
  agent: {
    label: 'Agent',
    color: '#a855f7',
    icon: 'Bot',
    category: 'ai',
    description: 'Call another agent',
  },
  text_splitter: {
    label: 'Text Splitter',
    color: '#6366f1',
    icon: 'Scissors',
    category: 'ai',
    description: 'Split text into chunks',
  },
  embedding: {
    label: 'Embedding',
    color: '#8b5cf6',
    icon: 'Hash',
    category: 'ai',
    description: 'Generate embeddings',
  },
  web_search: {
    label: 'Web Search',
    color: '#0ea5e9',
    icon: 'Search',
    category: 'tool',
    description: 'Search the web',
  },
  file_read: {
    label: 'File Read',
    color: '#84cc16',
    icon: 'FileText',
    category: 'tool',
    description: 'Read from file',
  },
  file_write: {
    label: 'File Write',
    color: '#22d3ee',
    icon: 'Save',
    category: 'tool',
    description: 'Write to file',
  },
  send_email: {
    label: 'Send Email',
    color: '#f43f5e',
    icon: 'Mail',
    category: 'tool',
    description: 'Send an email',
  },
  notification: {
    label: 'Notification',
    color: '#a3e635',
    icon: 'Bell',
    category: 'tool',
    description: 'Send notification',
  },
};
