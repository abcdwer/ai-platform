'use client';

import React from 'react';
import { useWorkflowStore, NODE_TYPES_CONFIG, WorkflowNode } from '@/stores/workflowStore';
import { X, Trash2 } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';

export function NodeConfig() {
  const { selectedNode, showConfigPanel, setShowConfigPanel, updateNode, removeNode, setSelectedNode } = useWorkflowStore();

  if (!showConfigPanel || !selectedNode) {
    return null;
  }

  const config = NODE_TYPES_CONFIG[selectedNode.type] || { label: selectedNode.type };

  const handleClose = () => {
    setShowConfigPanel(false);
    setSelectedNode(null);
  };

  const handleUpdate = (key: string, value: any) => {
    const newConfig = { ...selectedNode.data.config, [key]: value };
    updateNode(selectedNode.id, { config: newConfig });
  };

  const handleLabelChange = (label: string) => {
    updateNode(selectedNode.id, { label });
  };

  const handleDelete = () => {
    removeNode(selectedNode.id);
    setSelectedNode(null);
    setShowConfigPanel(false);
  };

  return (
    <div className="absolute right-2 top-20 z-10 w-80 bg-card border rounded-lg shadow-lg">
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b">
        <div className="flex items-center gap-2">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: config.color }}
          />
          <span className="font-medium text-sm">{config.label} Configuration</span>
        </div>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="icon" onClick={handleDelete} className="h-8 w-8 text-destructive">
            <Trash2 className="w-4 h-4" />
          </Button>
          <button onClick={handleClose} className="p-1 hover:bg-accent rounded">
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Config Form */}
      <ScrollArea className="h-[calc(100vh-250px)]">
        <div className="p-4 space-y-4">
          {/* Label */}
          <div className="space-y-2">
            <Label htmlFor="label">Node Label</Label>
            <Input
              id="label"
              value={selectedNode.data.label}
              onChange={(e) => handleLabelChange(e.target.value)}
              placeholder="Enter node label"
            />
          </div>

          {/* Type-specific configs */}
          <NodeConfigFields
            nodeType={selectedNode.type}
            config={selectedNode.data.config}
            onUpdate={handleUpdate}
          />
        </div>
      </ScrollArea>
    </div>
  );
}

// Dynamic config fields based on node type
function NodeConfigFields({
  nodeType,
  config,
  onUpdate,
}: {
  nodeType: string;
  config: Record<string, any>;
  onUpdate: (key: string, value: any) => void;
}) {
  switch (nodeType) {
    case 'start':
      return (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Trigger Type</Label>
            <Select value={config.trigger || 'manual'} onValueChange={(v) => onUpdate('trigger', v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="manual">Manual</SelectItem>
                <SelectItem value="api">API</SelectItem>
                <SelectItem value="schedule">Schedule</SelectItem>
                <SelectItem value="event">Event</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      );

    case 'llm':
      return (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Provider</Label>
            <Select value={config.provider || 'openai'} onValueChange={(v) => onUpdate('provider', v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="openai">OpenAI</SelectItem>
                <SelectItem value="ollama">Ollama</SelectItem>
                <SelectItem value="anthropic">Anthropic</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Model</Label>
            <Input
              value={config.model || 'gpt-4'}
              onChange={(e) => onUpdate('model', e.target.value)}
              placeholder="gpt-4, claude-3, etc."
            />
          </div>
          <div className="space-y-2">
            <Label>System Prompt</Label>
            <Textarea
              value={config.system_prompt || ''}
              onChange={(e) => onUpdate('system_prompt', e.target.value)}
              placeholder="You are a helpful assistant..."
              rows={3}
            />
          </div>
          <div className="space-y-2">
            <Label>Prompt Template</Label>
            <Textarea
              value={config.prompt_template || '{{input}}'}
              onChange={(e) => onUpdate('prompt_template', e.target.value)}
              placeholder="Summarize: {{input}}"
              rows={3}
            />
            <p className="text-xs text-muted-foreground">
              Use {'{{input}}'} to reference input data. Use {'{{nodeId.field}}'} for other node outputs.
            </p>
          </div>
          <div className="space-y-2">
            <Label>Temperature: {config.temperature ?? 0.7}</Label>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={config.temperature ?? 0.7}
              onChange={(e) => onUpdate('temperature', parseFloat(e.target.value))}
              className="w-full"
            />
          </div>
          <div className="space-y-2">
            <Label>Max Tokens</Label>
            <Input
              type="number"
              value={config.max_tokens || 4096}
              onChange={(e) => onUpdate('max_tokens', parseInt(e.target.value))}
            />
          </div>
        </div>
      );

    case 'code':
      return (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Language</Label>
            <Select value={config.language || 'python'} onValueChange={(v) => onUpdate('language', v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="python">Python</SelectItem>
                <SelectItem value="javascript">JavaScript</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Code</Label>
            <Textarea
              value={config.code || ''}
              onChange={(e) => onUpdate('code', e.target.value)}
              placeholder="# Process input&#10;result = input&#10;return result"
              rows={10}
              className="font-mono text-sm"
            />
            <p className="text-xs text-muted-foreground">
              Available variables: input, context, variables. Return value becomes node output.
            </p>
          </div>
          <div className="space-y-2">
            <Label>Timeout (seconds)</Label>
            <Input
              type="number"
              value={config.timeout || 30}
              onChange={(e) => onUpdate('timeout', parseInt(e.target.value))}
            />
          </div>
        </div>
      );

    case 'condition':
      return (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Condition Type</Label>
            <Select value={config.condition_type || 'expression'} onValueChange={(v) => onUpdate('condition_type', v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="expression">Expression</SelectItem>
                <SelectItem value="threshold">Threshold</SelectItem>
              </SelectContent>
            </Select>
          </div>
          {config.condition_type === 'expression' ? (
            <div className="space-y-2">
              <Label>Expression</Label>
              <Input
                value={config.expression || '{{input}} == true'}
                onChange={(e) => onUpdate('expression', e.target.value)}
                placeholder="{{input}} > 0"
              />
              <p className="text-xs text-muted-foreground">
                Supports: ==, !=, {'>'}, {'<'}, {'>='}, {'<='}, and, or, not
              </p>
            </div>
          ) : (
            <>
              <div className="space-y-2">
                <Label>Comparison</Label>
                <Select value={config.threshold_comparison || '>'} onValueChange={(v) => onUpdate('threshold_comparison', v)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value=">">{'>'} Greater than</SelectItem>
                    <SelectItem value="<">{'<'} Less than</SelectItem>
                    <SelectItem value=">=">{'>='} Greater or equal</SelectItem>
                    <SelectItem value="<=">{'<='} Less or equal</SelectItem>
                    <SelectItem value="==">== Equal</SelectItem>
                    <SelectItem value="!=">!= Not equal</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Threshold Value</Label>
                <Input
                  type="number"
                  value={config.threshold_value || 0}
                  onChange={(e) => onUpdate('threshold_value', parseFloat(e.target.value))}
                />
              </div>
            </>
          )}
        </div>
      );

    case 'loop':
      return (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Loop Type</Label>
            <Select value={config.loop_type || 'count'} onValueChange={(v) => onUpdate('loop_type', v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="count">Fixed Count</SelectItem>
                <SelectItem value="while">While Condition</SelectItem>
                <SelectItem value="for_each">For Each</SelectItem>
              </SelectContent>
            </Select>
          </div>
          {config.loop_type === 'count' && (
            <div className="space-y-2">
              <Label>Iterations</Label>
              <Input
                type="number"
                value={config.iterations || 10}
                onChange={(e) => onUpdate('iterations', parseInt(e.target.value))}
              />
            </div>
          )}
          {config.loop_type === 'while' && (
            <div className="space-y-2">
              <Label>While Condition</Label>
              <Input
                value={config.while_condition || '{{count}} < 10'}
                onChange={(e) => onUpdate('while_condition', e.target.value)}
                placeholder="{{count}} < 10"
              />
            </div>
          )}
          {config.loop_type === 'for_each' && (
            <div className="space-y-2">
              <Label>Items Variable</Label>
              <Input
                value={config.items_variable || '{{input}}'}
                onChange={(e) => onUpdate('items_variable', e.target.value)}
                placeholder="{{input}}"
              />
            </div>
          )}
          <div className="space-y-2">
            <Label>Max Iterations</Label>
            <Input
              type="number"
              value={config.max_iterations || 100}
              onChange={(e) => onUpdate('max_iterations', parseInt(e.target.value))}
            />
          </div>
        </div>
      );

    case 'delay':
      return (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Delay Type</Label>
            <Select value={config.delay_type || 'seconds'} onValueChange={(v) => onUpdate('delay_type', v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="seconds">Seconds</SelectItem>
                <SelectItem value="minutes">Minutes</SelectItem>
                <SelectItem value="hours">Hours</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Delay Value</Label>
            <Input
              type="number"
              value={config.delay_value || 1}
              onChange={(e) => onUpdate('delay_value', parseInt(e.target.value))}
            />
          </div>
        </div>
      );

    case 'http':
      return (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Method</Label>
            <Select value={config.method || 'GET'} onValueChange={(v) => onUpdate('method', v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="GET">GET</SelectItem>
                <SelectItem value="POST">POST</SelectItem>
                <SelectItem value="PUT">PUT</SelectItem>
                <SelectItem value="DELETE">DELETE</SelectItem>
                <SelectItem value="PATCH">PATCH</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>URL</Label>
            <Input
              value={config.url || ''}
              onChange={(e) => onUpdate('url', e.target.value)}
              placeholder="https://api.example.com/endpoint"
            />
          </div>
          <div className="space-y-2">
            <Label>Headers (JSON)</Label>
            <Textarea
              value={JSON.stringify(config.headers || {}, null, 2)}
              onChange={(e) => {
                try {
                  onUpdate('headers', JSON.parse(e.target.value));
                } catch {}
              }}
              placeholder='{"Authorization": "Bearer {{api_key}}"}'
              rows={3}
            />
          </div>
          <div className="space-y-2">
            <Label>Body</Label>
            <Textarea
              value={typeof config.body === 'string' ? config.body : JSON.stringify(config.body || {}, null, 2)}
              onChange={(e) => {
                try {
                  onUpdate('body', JSON.parse(e.target.value));
                } catch {
                  onUpdate('body', e.target.value);
                }
              }}
              placeholder='{"key": "value"}'
              rows={3}
            />
          </div>
          <div className="space-y-2">
            <Label>Timeout (seconds)</Label>
            <Input
              type="number"
              value={config.timeout || 30}
              onChange={(e) => onUpdate('timeout', parseInt(e.target.value))}
            />
          </div>
        </div>
      );

    case 'transform':
      return (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Transform Type</Label>
            <Select value={config.transform_type || 'json_path'} onValueChange={(v) => onUpdate('transform_type', v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="json_path">JSON Path</SelectItem>
                <SelectItem value="template">Template</SelectItem>
                <SelectItem value="join">Join</SelectItem>
                <SelectItem value="split">Split</SelectItem>
              </SelectContent>
            </Select>
          </div>
          {config.transform_type === 'json_path' && (
            <div className="space-y-2">
              <Label>JSON Path</Label>
              <Input
                value={config.json_path || '$.data'}
                onChange={(e) => onUpdate('json_path', e.target.value)}
                placeholder="$.data or $[0].name"
              />
            </div>
          )}
          {config.transform_type === 'template' && (
            <div className="space-y-2">
              <Label>Template</Label>
              <Textarea
                value={config.template || '{{input}}'}
                onChange={(e) => onUpdate('template', e.target.value)}
                placeholder="Hello {{name}}!"
                rows={3}
              />
            </div>
          )}
          {config.transform_type === 'join' && (
            <div className="space-y-2">
              <Label>Delimiter</Label>
              <Input
                value={config.delimiter || ', '}
                onChange={(e) => onUpdate('delimiter', e.target.value)}
                placeholder=", "
              />
            </div>
          )}
          {config.transform_type === 'split' && (
            <div className="space-y-2">
              <Label>Separator</Label>
              <Input
                value={config.separator || ','}
                onChange={(e) => onUpdate('separator', e.target.value)}
                placeholder=","
              />
            </div>
          )}
        </div>
      );

    case 'knowledge':
      return (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Query Template</Label>
            <Textarea
              value={config.query_template || '{{input}}'}
              onChange={(e) => onUpdate('query_template', e.target.value)}
              placeholder="Find information about: {{input}}"
              rows={3}
            />
          </div>
          <div className="space-y-2">
            <Label>Top K Results</Label>
            <Input
              type="number"
              value={config.top_k || 5}
              onChange={(e) => onUpdate('top_k', parseInt(e.target.value))}
            />
          </div>
          <div className="space-y-2">
            <Label>Similarity Threshold: {config.similarity_threshold ?? 0.7}</Label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.1"
              value={config.similarity_threshold ?? 0.7}
              onChange={(e) => onUpdate('similarity_threshold', parseFloat(e.target.value))}
              className="w-full"
            />
          </div>
        </div>
      );

    case 'text_splitter':
      return (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Split Type</Label>
            <Select value={config.split_type || 'character'} onValueChange={(v) => onUpdate('split_type', v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="character">Character</SelectItem>
                <SelectItem value="token">Token</SelectItem>
                <SelectItem value="sentence">Sentence</SelectItem>
                <SelectItem value="paragraph">Paragraph</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Chunk Size</Label>
            <Input
              type="number"
              value={config.chunk_size || 1000}
              onChange={(e) => onUpdate('chunk_size', parseInt(e.target.value))}
            />
          </div>
          <div className="space-y-2">
            <Label>Chunk Overlap</Label>
            <Input
              type="number"
              value={config.chunk_overlap || 200}
              onChange={(e) => onUpdate('chunk_overlap', parseInt(e.target.value))}
            />
          </div>
        </div>
      );

    case 'embedding':
      return (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Provider</Label>
            <Select value={config.provider || 'openai'} onValueChange={(v) => onUpdate('provider', v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="openai">OpenAI</SelectItem>
                <SelectItem value="ollama">Ollama</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Model</Label>
            <Input
              value={config.model || 'text-embedding-ada-002'}
              onChange={(e) => onUpdate('model', e.target.value)}
              placeholder="text-embedding-ada-002"
            />
          </div>
          <div className="space-y-2">
            <Label>Batch Size</Label>
            <Input
              type="number"
              value={config.batch_size || 100}
              onChange={(e) => onUpdate('batch_size', parseInt(e.target.value))}
            />
          </div>
        </div>
      );

    case 'web_search':
      return (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Search Engine</Label>
            <Select value={config.search_engine || 'google'} onValueChange={(v) => onUpdate('search_engine', v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="google">Google</SelectItem>
                <SelectItem value="bing">Bing</SelectItem>
                <SelectItem value="duckduckgo">DuckDuckGo</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Query Template</Label>
            <Input
              value={config.query_template || '{{input}}'}
              onChange={(e) => onUpdate('query_template', e.target.value)}
              placeholder="{{input}}"
            />
          </div>
          <div className="space-y-2">
            <Label>Number of Results</Label>
            <Input
              type="number"
              value={config.num_results || 10}
              onChange={(e) => onUpdate('num_results', parseInt(e.target.value))}
            />
          </div>
        </div>
      );

    case 'file_read':
    case 'file_write':
      return (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>File Path</Label>
            <Input
              value={config.file_path || ''}
              onChange={(e) => onUpdate('file_path', e.target.value)}
              placeholder="/path/to/file.txt"
            />
          </div>
          {nodeType === 'file_write' && (
            <div className="space-y-2">
              <Label>Content Template</Label>
              <Textarea
                value={config.content_template || '{{input}}'}
                onChange={(e) => onUpdate('content_template', e.target.value)}
                placeholder="{{input}}"
                rows={3}
              />
            </div>
          )}
          <div className="space-y-2">
            <Label>Encoding</Label>
            <Input
              value={config.encoding || 'utf-8'}
              onChange={(e) => onUpdate('encoding', e.target.value)}
            />
          </div>
        </div>
      );

    case 'send_email':
      return (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>To</Label>
            <Input
              value={config.to || ''}
              onChange={(e) => onUpdate('to', e.target.value)}
              placeholder="recipient@example.com"
            />
          </div>
          <div className="space-y-2">
            <Label>Subject</Label>
            <Input
              value={config.subject || 'Workflow Notification'}
              onChange={(e) => onUpdate('subject', e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label>Body Template</Label>
            <Textarea
              value={config.body_template || '{{input}}'}
              onChange={(e) => onUpdate('body_template', e.target.value)}
              placeholder="Email content..."
              rows={5}
            />
          </div>
        </div>
      );

    case 'notification':
      return (
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Notification Type</Label>
            <Select value={config.notification_type || 'log'} onValueChange={(v) => onUpdate('notification_type', v)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="log">Log</SelectItem>
                <SelectItem value="webhook">Webhook</SelectItem>
              </SelectContent>
            </Select>
          </div>
          {config.notification_type === 'webhook' && (
            <div className="space-y-2">
              <Label>Webhook URL</Label>
              <Input
                value={config.webhook_url || ''}
                onChange={(e) => onUpdate('webhook_url', e.target.value)}
                placeholder="https://hooks.example.com/..."
              />
            </div>
          )}
          <div className="space-y-2">
            <Label>Message Template</Label>
            <Textarea
              value={config.message_template || '{{input}}'}
              onChange={(e) => onUpdate('message_template', e.target.value)}
              placeholder="{{input}}"
              rows={3}
            />
          </div>
        </div>
      );

    default:
      return (
        <div className="text-sm text-muted-foreground">
          No configuration options available for this node type.
        </div>
      );
  }
}
