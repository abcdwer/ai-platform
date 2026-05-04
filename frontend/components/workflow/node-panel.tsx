'use client';

import React from 'react';
import { useWorkflowStore, NODE_TYPES_CONFIG } from '@/stores/workflowStore';
import { Play, Square, Brain, Code, GitBranch, Repeat, Clock, Globe, Shuffle, GitMerge, BookOpen, Bot, Scissors, Hash, Search, FileText, Save, Mail, Bell, ChevronRight } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';

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

const categories = [
  { key: 'basic', label: 'Basic', color: 'bg-gray-100 dark:bg-gray-800' },
  { key: 'ai', label: 'AI', color: 'bg-purple-100 dark:bg-purple-900' },
  { key: 'tool', label: 'Tools', color: 'bg-blue-100 dark:bg-blue-900' },
];

export function NodePanel() {
  const { showNodePanel, setShowNodePanel, addNode, nodes } = useWorkflowStore();

  const onDragStart = (event: React.DragEvent, nodeType: string) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  const handleAddNode = (nodeType: string) => {
    const config = NODE_TYPES_CONFIG[nodeType];
    const newNode = {
      id: `${nodeType}-${Date.now()}`,
      type: nodeType,
      position: { x: 250 + Math.random() * 100, y: 100 + nodes.length * 50 },
      data: {
        label: config?.label || nodeType,
        config: getDefaultConfig(nodeType),
      },
    };
    addNode(newNode);
  };

  const getDefaultConfig = (nodeType: string): Record<string, any> => {
    switch (nodeType) {
      case 'start':
        return { trigger: 'manual' };
      case 'llm':
        return { model: 'gpt-4', provider: 'openai', prompt_template: '{{input}}', temperature: 0.7 };
      case 'code':
        return { language: 'python', code: '# Process input\nresult = input\nreturn result' };
      case 'condition':
        return { condition_type: 'expression', expression: '{{input}} == true' };
      case 'loop':
        return { loop_type: 'count', iterations: 10 };
      case 'delay':
        return { delay_type: 'seconds', delay_value: 1 };
      case 'http':
        return { method: 'GET', url: 'https://api.example.com' };
      case 'transform':
        return { transform_type: 'json_path', json_path: '$.data' };
      case 'knowledge':
        return { top_k: 5, similarity_threshold: 0.7 };
      case 'text_splitter':
        return { chunk_size: 1000, chunk_overlap: 200 };
      case 'embedding':
        return { model: 'text-embedding-ada-002' };
      case 'web_search':
        return { num_results: 10 };
      case 'file_read':
        return { file_path: '' };
      case 'file_write':
        return { file_path: '', content_template: '{{input}}' };
      case 'send_email':
        return { to: '', subject: 'Workflow Notification', body_template: '{{input}}' };
      case 'notification':
        return { notification_type: 'log', message_template: '{{input}}' };
      default:
        return {};
    }
  };

  if (!showNodePanel) {
    return (
      <button
        onClick={() => setShowNodePanel(true)}
        className="absolute left-2 top-20 z-10 p-2 bg-card border rounded-md shadow-md hover:bg-accent transition-colors"
      >
        <ChevronRight className="w-4 h-4" />
      </button>
    );
  }

  return (
    <div className="absolute left-2 top-20 z-10 w-64 bg-card border rounded-lg shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b">
        <span className="font-medium text-sm">Nodes</span>
        <button
          onClick={() => setShowNodePanel(false)}
          className="p-1 hover:bg-accent rounded"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>

      {/* Node List */}
      <ScrollArea className="h-[calc(100vh-200px)]">
        <div className="p-2 space-y-4">
          {categories.map((category) => {
            const nodesInCategory = Object.entries(NODE_TYPES_CONFIG).filter(
              ([, config]) => config.category === category.key
            );

            return (
              <div key={category.key}>
                <div className={cn('text-xs font-medium text-muted-foreground px-2 py-1 rounded', category.color)}>
                  {category.label}
                </div>
                <div className="mt-1 space-y-1">
                  {nodesInCategory.map(([type, config]) => {
                    const Icon = iconMap[config.icon] || Square;
                    return (
                      <div
                        key={type}
                        draggable
                        onDragStart={(e) => onDragStart(e, type)}
                        onClick={() => handleAddNode(type)}
                        className={cn(
                          'flex items-center gap-2 p-2 rounded-md cursor-grab active:cursor-grabbing',
                          'hover:bg-accent transition-colors group'
                        )}
                        style={{ borderLeftColor: config.color, borderLeftWidth: 3 }}
                      >
                        <Icon className="w-4 h-4" style={{ color: config.color }} />
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium truncate">{config.label}</div>
                          <div className="text-xs text-muted-foreground truncate">{config.description}</div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </ScrollArea>

      {/* Help Text */}
      <div className="p-3 border-t text-xs text-muted-foreground">
        Drag nodes to canvas or click to add
      </div>
    </div>
  );
}
