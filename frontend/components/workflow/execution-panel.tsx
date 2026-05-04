'use client';

import React, { useEffect, useState } from 'react';
import { useWorkflowStore, Workflow } from '@/stores/workflowStore';
import { Play, Square, CheckCircle, XCircle, Clock, Loader2, ChevronDown, ChevronUp, Eye } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';

interface ExecutionPanelProps {
  workflowId: string;
}

export function ExecutionPanel({ workflowId }: ExecutionPanelProps) {
  const { currentExecution, isExecuting, setCurrentExecution, setIsExecuting } = useWorkflowStore();
  const [showPanel, setShowPanel] = useState(false);
  const [logs, setLogs] = useState<Array<{ timestamp: string; level: string; message: string }>>([]);

  const executeWorkflow = async () => {
    try {
      setIsExecuting(true);
      setShowPanel(true);
      setLogs([]);

      // Start execution
      const response = await fetch(`/api/workflows/${workflowId}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ inputs: {} }),
      });

      if (!response.ok) {
        throw new Error('Failed to start workflow');
      }

      const result = await response.json();
      setCurrentExecution({
        id: result.execution_id,
        workflow_id: workflowId,
        status: 'running',
        trigger_type: 'manual',
      });

      addLog('info', `Workflow execution started: ${result.execution_id}`);

      // Poll for execution status
      pollExecutionStatus(result.execution_id);
    } catch (error) {
      console.error('Execution error:', error);
      addLog('error', `Execution failed: ${error}`);
      setIsExecuting(false);
    }
  };

  const pollExecutionStatus = async (executionId: string) => {
    const poll = async () => {
      try {
        const response = await fetch(`/api/workflows/${workflowId}/executions/${executionId}`);
        if (!response.ok) {
          throw new Error('Failed to get execution status');
        }

        const execution = await response.json();
        setCurrentExecution(execution);

        // Update logs from node executions
        if (execution.node_executions) {
          execution.node_executions.forEach((node: any) => {
            if (node.status === 'completed') {
              addLog('success', `${node.node_type} node completed`);
            } else if (node.status === 'failed') {
              addLog('error', `${node.node_type} node failed: ${node.error_message}`);
            }
          });
        }

        if (execution.status === 'completed') {
          addLog('success', 'Workflow completed successfully');
          setIsExecuting(false);
          return;
        }

        if (execution.status === 'failed') {
          addLog('error', `Workflow failed: ${execution.error_message}`);
          setIsExecuting(false);
          return;
        }

        if (execution.status === 'cancelled') {
          addLog('warning', 'Workflow was cancelled');
          setIsExecuting(false);
          return;
        }

        // Continue polling
        setTimeout(poll, 1000);
      } catch (error) {
        console.error('Poll error:', error);
        setTimeout(poll, 2000);
      }
    };

    poll();
  };

  const cancelExecution = async () => {
    if (!currentExecution) return;

    try {
      await fetch(`/api/workflows/${workflowId}/executions/${currentExecution.id}/cancel`, {
        method: 'POST',
      });
      addLog('warning', 'Execution cancelled');
      setIsExecuting(false);
    } catch (error) {
      console.error('Cancel error:', error);
    }
  };

  const addLog = (level: string, message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs((prev) => [...prev, { timestamp, level, message }]);
  };

  return (
    <div className="absolute bottom-4 right-4 z-10 w-96">
      {/* Toggle Button */}
      <button
        onClick={() => setShowPanel(!showPanel)}
        className={cn(
          'w-full flex items-center justify-between px-4 py-2 bg-card border rounded-lg shadow-lg transition-colors',
          isExecuting ? 'border-primary' : ''
        )}
      >
        <div className="flex items-center gap-2">
          {isExecuting ? (
            <Loader2 className="w-4 h-4 animate-spin text-primary" />
          ) : currentExecution?.status === 'completed' ? (
            <CheckCircle className="w-4 h-4 text-green-500" />
          ) : currentExecution?.status === 'failed' ? (
            <XCircle className="w-4 h-4 text-red-500" />
          ) : (
            <Clock className="w-4 h-4 text-muted-foreground" />
          )}
          <span className="font-medium text-sm">
            {isExecuting ? 'Running...' : currentExecution?.status || 'Execution'}
          </span>
        </div>
        {showPanel ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
      </button>

      {/* Execution Panel */}
      {showPanel && (
        <div className="mt-2 bg-card border rounded-lg shadow-lg">
          {/* Actions */}
          <div className="flex gap-2 p-3 border-b">
            {!isExecuting && (
              <Button onClick={executeWorkflow} size="sm" className="flex-1">
                <Play className="w-4 h-4 mr-1" />
                Run
              </Button>
            )}
            {isExecuting && (
              <Button onClick={cancelExecution} size="sm" variant="destructive" className="flex-1">
                <Square className="w-4 h-4 mr-1" />
                Cancel
              </Button>
            )}
            {currentExecution && (
              <Button
                onClick={() => window.location.href = `/workflows/${workflowId}/executions`}
                size="sm"
                variant="outline"
                className="flex-1"
              >
                <Eye className="w-4 h-4 mr-1" />
                Details
              </Button>
            )}
          </div>

          {/* Tabs */}
          <Tabs defaultValue="logs" className="w-full">
            <TabsList className="w-full grid grid-cols-2">
              <TabsTrigger value="logs">Logs</TabsTrigger>
              <TabsTrigger value="nodes">Nodes</TabsTrigger>
            </TabsList>

            <TabsContent value="logs" className="h-64">
              <ScrollArea className="h-full p-3">
                {logs.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-8">
                    No logs yet. Run the workflow to see execution logs.
                  </p>
                ) : (
                  <div className="space-y-1 font-mono text-xs">
                    {logs.map((log, i) => (
                      <div key={i} className="flex gap-2">
                        <span className="text-muted-foreground">{log.timestamp}</span>
                        <span className={cn(
                          log.level === 'error' && 'text-red-500',
                          log.level === 'success' && 'text-green-500',
                          log.level === 'warning' && 'text-yellow-500',
                          log.level === 'info' && 'text-blue-500',
                        )}>
                          [{log.level.toUpperCase()}]
                        </span>
                        <span className="text-foreground">{log.message}</span>
                      </div>
                    ))}
                  </div>
                )}
              </ScrollArea>
            </TabsContent>

            <TabsContent value="nodes" className="h-64">
              <ScrollArea className="h-full p-3">
                {currentExecution?.node_executions ? (
                  <div className="space-y-2">
                    {currentExecution.node_executions.map((node) => (
                      <div
                        key={node.id}
                        className={cn(
                          'flex items-center justify-between p-2 rounded border',
                          node.status === 'completed' && 'border-green-500 bg-green-500/10',
                          node.status === 'failed' && 'border-red-500 bg-red-500/10',
                          node.status === 'running' && 'border-blue-500 bg-blue-500/10 animate-pulse',
                          node.status === 'pending' && 'border-gray-500 bg-gray-500/10',
                        )}
                      >
                        <div>
                          <div className="text-sm font-medium">{node.node_name || node.node_type}</div>
                          <div className="text-xs text-muted-foreground">{node.node_id}</div>
                        </div>
                        <div className="flex items-center gap-2">
                          {node.status === 'completed' && (
                            <CheckCircle className="w-4 h-4 text-green-500" />
                          )}
                          {node.status === 'failed' && (
                            <XCircle className="w-4 h-4 text-red-500" />
                          )}
                          {node.status === 'running' && (
                            <Loader2 className="w-4 h-4 animate-spin text-blue-500" />
                          )}
                          {node.duration_ms && (
                            <span className="text-xs text-muted-foreground">
                              {node.duration_ms}ms
                            </span>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground text-center py-8">
                    No execution data yet.
                  </p>
                )}
              </ScrollArea>
            </TabsContent>
          </Tabs>
        </div>
      )}
    </div>
  );
}
