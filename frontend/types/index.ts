// Agent types
export interface Agent {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  system_prompt: string;
  model: string;
  model_provider: string;
  tools?: ToolDefinition[];
  temperature: number;
  max_tokens: number;
  top_p?: number;
  is_active: boolean;
  is_public: boolean;
  created_at: string;
  updated_at: string;
}

export interface ToolDefinition {
  name: string;
  description: string;
  parameters: ToolParameters;
}

export interface ToolParameters {
  type: string;
  properties?: Record<string, ToolProperty>;
  required?: string[];
}

export interface ToolProperty {
  type: string;
  description?: string;
  enum?: string[];
}

// Model types
export interface ModelInfo {
  id: string;
  name: string;
  provider: string;
  model_id: string;
  is_default: boolean;
  supports_streaming: boolean;
  supports_function_calling: boolean;
}

export interface AvailableModels {
  ollama: ModelInfo[];
  openai: ModelInfo[];
  all: ModelInfo[];
}

export interface ModelStatus {
  provider: string;
  models: ModelInfo[];
  is_connected: boolean;
  error?: string;
}

// Conversation types
export interface Conversation {
  id: string;
  user_id: string;
  title: string;
  agent_id?: string;
  model: string;
  model_provider: string;
  is_pinned: boolean;
  is_archived: boolean;
  messages: Message[];
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  name?: string;
  tool_call_id?: string;
  tool_calls?: ToolCall[];
  tokens_used?: number;
  created_at: string;
}

export interface ToolCall {
  id: string;
  type: string;
  function: {
    name: string;
    arguments: string;
  };
}

// Chat types
export interface ChatRequest {
  conversation_id?: string;
  messages: { role: string; content: string }[];
  model?: string;
  model_provider?: string;
  agent_id?: string;
  temperature?: number;
  max_tokens?: number;
  stream: boolean;
  tools?: ToolDefinition[];
}

export interface ChatStreamChunk {
  type: 'message' | 'tool_call' | 'done' | 'error' | 'conversation_id' | 'title';
  content?: string;
  tool_call?: ToolCall;
  conversation_id?: string;
  finish_reason?: string;
  error?: string;
  title?: string;
}

// User types
export interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  avatar_url?: string;
  bio?: string;
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  updated_at: string;
  last_login?: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
  full_name?: string;
}

// API Response types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ApiError {
  detail: string;
  code?: string;
}

// Knowledge Base types
export interface KnowledgeBase {
  id: string;
  name: string;
  description?: string;
  embedding_model: string;
  embedding_provider: 'ollama' | 'openai';
  chunk_size: number;
  chunk_overlap: number;
  chunking_strategy: 'paragraph' | 'fixed' | 'semantic';
  top_k: number;
  similarity_threshold: number;
  tags?: string[];
  document_count: number;
  vector_count: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Document {
  id: string;
  knowledge_base_id: string;
  title: string;
  content_type: string;
  file_path?: string;
  file_size?: number;
  url?: string;
  status: 'uploading' | 'parsing' | 'embedding' | 'ready' | 'error';
  error_message?: string;
  chunk_count: number;
  metadata?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface SearchResult {
  content: string;
  document_id: string;
  document_title: string;
  chunk_index: number;
  score: number;
  metadata?: Record<string, unknown>;
}

export interface RAGSource {
  content: string;
  document_id: string;
  document_title: string;
  chunk_index: number;
  score: number;
}

export interface KnowledgeBaseListResponse {
  items: KnowledgeBase[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface DocumentListResponse {
  items: Document[];
  total: number;
}

// System Status types
export interface SystemStatus {
  status: 'online' | 'offline' | 'degraded';
  connected_models: number;
  active_agents: number;
  total_conversations: number;
  uptime: number;
}

// Search types
export interface SearchResult {
  id: string;
  type: 'conversation' | 'agent' | 'message';
  title: string;
  snippet: string;
  relevance: number;
  created_at: string;
}

// Onboarding types
export interface OnboardingData {
  welcome_message: string;
  checklist: ChecklistItem[];
  is_new_user: boolean;
}

export interface ChecklistItem {
  id: string;
  title: string;
  description: string;
  action: string;
  completed: boolean;
}
