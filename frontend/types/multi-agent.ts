// Multi-Agent collaboration types

export type CollaborationMode = 'sequential' | 'parallel' | 'debate' | 'hierarchical' | 'round_robin';
export type SessionStatus = 'created' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';
export type MemberRole = 'leader' | 'member' | 'supporter' | 'opponent' | 'judge';
export type MessageType = 'user_input' | 'agent_output' | 'system' | 'reference';

// ============== Agent Member ==============

export interface AgentMember {
  id: string;
  group_id: string;
  name: string;
  role: MemberRole;
  system_prompt: string;
  execution_order: number;
  model?: string;
  model_provider?: string;
  temperature: number;
  max_tokens: number;
  tools: any[];
  icon?: string;
  color?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AgentMemberCreate {
  name: string;
  role: MemberRole;
  system_prompt?: string;
  execution_order?: number;
  model?: string;
  model_provider?: string;
  temperature?: number;
  max_tokens?: number;
  tools?: any[];
  icon?: string;
  color?: string;
}

export interface AgentMemberUpdate {
  name?: string;
  role?: MemberRole;
  system_prompt?: string;
  execution_order?: number;
  model?: string;
  model_provider?: string;
  temperature?: number;
  max_tokens?: number;
  tools?: any[];
  icon?: string;
  color?: string;
  is_active?: boolean;
}

// ============== Agent Group ==============

export interface ModeConfig {
  // For sequential
  stop_on_first_success?: boolean;
  
  // For parallel
  max_parallel?: number;
  aggregation_method?: 'merge' | 'vote' | 'first';
  
  // For debate
  rounds?: number;
  allow_rebuttal?: boolean;
  judge_model?: string;
  
  // For hierarchical
  max_depth?: number;
  delegate_threshold?: number;
  
  // For round_robin
  max_turns?: number;
  allow_skip?: boolean;
}

export interface AgentGroup {
  id: string;
  user_id: string;
  name: string;
  description?: string;
  mode: CollaborationMode;
  mode_config: ModeConfig;
  default_model: string;
  default_provider: string;
  enable_orchestrator: boolean;
  orchestrator_prompt?: string;
  max_iterations: number;
  termination_prompt?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  members?: AgentMember[];
}

export interface AgentGroupCreate {
  name: string;
  description?: string;
  mode: CollaborationMode;
  mode_config?: ModeConfig;
  default_model?: string;
  default_provider?: string;
  enable_orchestrator?: boolean;
  orchestrator_prompt?: string;
  max_iterations?: number;
  termination_prompt?: string;
  members?: AgentMemberCreate[];
}

export interface AgentGroupUpdate {
  name?: string;
  description?: string;
  mode?: CollaborationMode;
  mode_config?: ModeConfig;
  default_model?: string;
  default_provider?: string;
  enable_orchestrator?: boolean;
  orchestrator_prompt?: string;
  max_iterations?: number;
  termination_prompt?: string;
  is_active?: boolean;
}

// ============== Session ==============

export interface AgentMessage {
  id: string;
  session_id: string;
  member_id?: string;
  member_name?: string;
  member_color?: string;
  message_type: MessageType;
  content: string;
  turn: number;
  iteration: number;
  referenced_message_id?: string;
  tool_calls?: any[];
  tool_results?: any[];
  model_used?: string;
  tokens_used?: number;
  execution_time_ms?: number;
  created_at: string;
}

export interface CollaborationSession {
  id: string;
  group_id: string;
  user_id: string;
  status: SessionStatus;
  initial_input: string;
  context?: Record<string, any>;
  final_output?: string;
  summary?: string;
  current_turn: number;
  completed_iterations: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  messages?: AgentMessage[];
}

export interface SessionStart {
  initial_input: string;
  context?: Record<string, any>;
}

export interface SessionExecuteRequest {
  user_input?: string;
  continue_session?: boolean;
}

export interface SessionExecuteResponse {
  session_id: string;
  status: SessionStatus;
  current_turn: number;
  messages: AgentMessage[];
  final_output?: string;
  is_complete: boolean;
}

// ============== Mode Descriptions ==============

export const MODE_DESCRIPTIONS: Record<CollaborationMode, { title: string; description: string; icon: string }> = {
  sequential: {
    title: 'Sequential',
    description: 'Agents execute in a fixed order, each seeing the output of previous agents',
    icon: '→'
  },
  parallel: {
    title: 'Parallel',
    description: 'Multiple agents work simultaneously on the same task, results are aggregated',
    icon: '⚡'
  },
  debate: {
    title: 'Debate',
    description: 'Agents take pro/con positions and debate, with an optional judge',
    icon: '⚖️'
  },
  hierarchical: {
    title: 'Hierarchical',
    description: 'A leader agent coordinates subordinate agents through delegation',
    icon: '📋'
  },
  round_robin: {
    title: 'Round Robin',
    description: 'Agents take turns speaking in rotation until a conclusion is reached',
    icon: '🔄'
  }
};

export const MEMBER_ROLE_COLORS: Record<MemberRole, string> = {
  leader: '#8b5cf6',    // Purple
  member: '#3b82f6',    // Blue
  supporter: '#10b981', // Green
  opponent: '#ef4444',  // Red
  judge: '#f59e0b',     // Amber
};

export const MODE_COLORS: Record<CollaborationMode, string> = {
  sequential: '#3b82f6',
  parallel: '#8b5cf6',
  debate: '#ef4444',
  hierarchical: '#10b981',
  round_robin: '#f59e0b',
};
