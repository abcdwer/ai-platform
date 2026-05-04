'use client';

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { Play, Square, Brain, Code, GitBranch, Repeat, Clock, Globe, Shuffle, GitMerge, BookOpen, Bot, Scissors, Hash, Search, FileText, Save, Mail, Bell } from 'lucide-react';
import { NODE_TYPES_CONFIG } from '@/stores/workflowStore';

// Icon mapping
const iconMap: Record<string, React.ComponentType<{ className?: string }>> = {
  Play,
  Square,
  Brain,
  Code,
  GitBranch,
  Repeat,
  Clock,
  Globe,
  Shuffle,
  GitMerge,
  BookOpen,
  Bot,
  Scissors,
  Hash,
  Search,
  FileText,
  Save,
  Mail,
  Bell,
};

// Base node component
const BaseNode = memo(({ 
  data, 
  type,
  selected,
  hasInput = true,
  hasOutput = true,
  dualOutput = false,
}: { 
  data: any; 
  type: string;
  selected?: boolean;
  hasInput?: boolean;
  hasOutput?: boolean;
  dualOutput?: boolean;
}) => {
  const config = NODE_TYPES_CONFIG[type] || { label: type, color: '#6b7280', icon: 'Square' };
  const Icon = iconMap[config.icon] || Square;
  
  return (
    <div
      className={`
        relative min-w-[180px] rounded-lg border-2 bg-card shadow-md
        transition-all duration-200
        ${selected ? 'ring-2 ring-primary shadow-lg scale-105' : ''}
      `}
      style={{ borderColor: config.color }}
    >
      {/* Input Handle */}
      {hasInput && (
        <Handle
          type="target"
          position={Position.Left}
          className="!w-3 !h-3 !bg-background border-2 !-left-1.5"
          style={{ borderColor: config.color }}
        />
      )}
      
      {/* Node Header */}
      <div
        className="flex items-center gap-2 px-3 py-2 rounded-t-md"
        style={{ backgroundColor: `${config.color}20` }}
      >
        <Icon className="w-4 h-4" style={{ color: config.color }} />
        <span className="font-medium text-sm">{config.label}</span>
      </div>
      
      {/* Node Body */}
      <div className="px-3 py-2">
        <div className="text-sm font-medium text-foreground truncate">
          {data.label || config.label}
        </div>
        {data.config && Object.keys(data.config).length > 0 && (
          <div className="mt-1 text-xs text-muted-foreground">
            {Object.keys(data.config).slice(0, 2).map(key => (
              <div key={key} className="truncate">
                {key}: {String(data.config[key]).slice(0, 20)}
              </div>
            ))}
          </div>
        )}
      </div>
      
      {/* Output Handle(s) */}
      {hasOutput && !dualOutput && (
        <Handle
          type="source"
          position={Position.Right}
          className="!w-3 !h-3 !bg-background border-2 !-right-1.5"
          style={{ borderColor: config.color }}
        />
      )}
      
      {dualOutput && (
        <>
          <Handle
            type="source"
            position={Position.Right}
            id="output-true"
            className="!w-3 !h-3 !bg-green-500 border-2 !-right-1.5 !top-1/3"
          />
          <Handle
            type="source"
            position={Position.Right}
            id="output-false"
            className="!w-3 !h-3 !bg-red-500 border-2 !-right-1.5 !top-2/3"
          />
        </>
      )}
    </div>
  );
});

BaseNode.displayName = 'BaseNode';

// Start Node
export const StartNode = memo((props: NodeProps) => {
  return <BaseNode {...props} type="start" hasInput={false} />;
});
StartNode.displayName = 'StartNode';

// End Node
export const EndNode = memo((props: NodeProps) => {
  return <BaseNode {...props} type="end" hasOutput={false} />;
});
EndNode.displayName = 'EndNode';

// LLM Node
export const LLMNode = memo((props: NodeProps) => {
  const { data } = props;
  return (
    <BaseNode {...props} type="llm">
      <div className="text-xs text-muted-foreground mt-1">
        Model: {data.config?.model || 'gpt-4'}
      </div>
    </BaseNode>
  );
});
LLMNode.displayName = 'LLMNode';

// Code Node
export const CodeNode = memo((props: NodeProps) => {
  return <BaseNode {...props} type="code" />;
});
CodeNode.displayName = 'CodeNode';

// Condition Node
export const ConditionNode = memo((props: NodeProps) => {
  return (
    <BaseNode {...props} type="condition" dualOutput>
      <div className="text-xs text-muted-foreground mt-1 px-3">
        <span className="text-green-600">True →</span>
        <span className="ml-2 text-red-600">False →</span>
      </div>
    </BaseNode>
  );
});
ConditionNode.displayName = 'ConditionNode';

// Loop Node
export const LoopNode = memo((props: NodeProps) => {
  return <BaseNode {...props} type="loop" />;
});
LoopNode.displayName = 'LoopNode';

// Delay Node
export const DelayNode = memo((props: NodeProps) => {
  const { data } = props;
  return (
    <BaseNode {...props} type="delay">
      <div className="text-xs text-muted-foreground mt-1">
        Wait: {data.config?.delay_value || 1} {data.config?.delay_type || 'seconds'}
      </div>
    </BaseNode>
  );
});
DelayNode.displayName = 'DelayNode';

// HTTP Node
export const HTTPNode = memo((props: NodeProps) => {
  const { data } = props;
  return (
    <BaseNode {...props} type="http">
      <div className="text-xs text-muted-foreground mt-1">
        {data.config?.method || 'GET'} {data.config?.url?.slice(0, 20) || ''}...
      </div>
    </BaseNode>
  );
});
HTTPNode.displayName = 'HTTPNode';

// Transform Node
export const TransformNode = memo((props: NodeProps) => {
  const { data } = props;
  return (
    <BaseNode {...props} type="transform">
      <div className="text-xs text-muted-foreground mt-1">
        {data.config?.transform_type || 'json_path'}
      </div>
    </BaseNode>
  );
});
TransformNode.displayName = 'TransformNode';

// Merge Node
export const MergeNode = memo((props: NodeProps) => {
  return <BaseNode {...props} type="merge" hasInput={false} />;
});
MergeNode.displayName = 'MergeNode';

// Knowledge Base Node
export const KnowledgeNode = memo((props: NodeProps) => {
  return <BaseNode {...props} type="knowledge" />;
});
KnowledgeNode.displayName = 'KnowledgeNode';

// Agent Node
export const AgentNode = memo((props: NodeProps) => {
  return <BaseNode {...props} type="agent" />;
});
AgentNode.displayName = 'AgentNode';

// Text Splitter Node
export const TextSplitterNode = memo((props: NodeProps) => {
  const { data } = props;
  return (
    <BaseNode {...props} type="text_splitter">
      <div className="text-xs text-muted-foreground mt-1">
        Size: {data.config?.chunk_size || 1000}
      </div>
    </BaseNode>
  );
});
TextSplitterNode.displayName = 'TextSplitterNode';

// Embedding Node
export const EmbeddingNode = memo((props: NodeProps) => {
  const { data } = props;
  return (
    <BaseNode {...props} type="embedding">
      <div className="text-xs text-muted-foreground mt-1">
        Model: {data.config?.model || 'text-embedding-ada-002'}
      </div>
    </BaseNode>
  );
});
EmbeddingNode.displayName = 'EmbeddingNode';

// Web Search Node
export const WebSearchNode = memo((props: NodeProps) => {
  return <BaseNode {...props} type="web_search" />;
});
WebSearchNode.displayName = 'WebSearchNode';

// File Read Node
export const FileReadNode = memo((props: NodeProps) => {
  const { data } = props;
  return (
    <BaseNode {...props} type="file_read">
      <div className="text-xs text-muted-foreground mt-1 truncate">
        {data.config?.file_path || 'No file selected'}
      </div>
    </BaseNode>
  );
});
FileReadNode.displayName = 'FileReadNode';

// File Write Node
export const FileWriteNode = memo((props: NodeProps) => {
  const { data } = props;
  return (
    <BaseNode {...props} type="file_write">
      <div className="text-xs text-muted-foreground mt-1 truncate">
        {data.config?.file_path || 'No file selected'}
      </div>
    </BaseNode>
  );
});
FileWriteNode.displayName = 'FileWriteNode';

// Send Email Node
export const SendEmailNode = memo((props: NodeProps) => {
  const { data } = props;
  return (
    <BaseNode {...props} type="send_email">
      <div className="text-xs text-muted-foreground mt-1 truncate">
        To: {data.config?.to || 'Not set'}
      </div>
    </BaseNode>
  );
});
SendEmailNode.displayName = 'SendEmailNode';

// Notification Node
export const NotificationNode = memo((props: NodeProps) => {
  return <BaseNode {...props} type="notification" />;
});
NotificationNode.displayName = 'NotificationNode';

// Export all node types
export const nodeTypes = {
  start: StartNode,
  end: EndNode,
  llm: LLMNode,
  code: CodeNode,
  condition: ConditionNode,
  loop: LoopNode,
  delay: DelayNode,
  http: HTTPNode,
  transform: TransformNode,
  merge: MergeNode,
  knowledge: KnowledgeNode,
  agent: AgentNode,
  text_splitter: TextSplitterNode,
  embedding: EmbeddingNode,
  web_search: WebSearchNode,
  file_read: FileReadNode,
  file_write: FileWriteNode,
  send_email: SendEmailNode,
  notification: NotificationNode,
};
