'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Play, Clock, CheckCircle, XCircle, Loader2, ChevronRight, Eye, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';

interface Workflow {
  id: string;
  name: string;
  status: string;
}

interface NodeExecution {
  id: string;
  node_id: string;
  node_type: string;
  node_name?: string;
  status: string;
  inputs?: any;
  outputs?: any;
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
  error_message?: string;
}

interface Execution {
  id: string;
  workflow_id: string;
  status: string;
  trigger_type: string;
  inputs?: any;
  outputs?: any;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  node_executions?: NodeExecution[];
}

export default function ExecutionsPage() {
  const router = useRouter();
  const params = useParams();
  const workflowId = params.id as string;

  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [executions, setExecutions] = useState<Execution[]>([]);
  const [selectedExecution, setSelectedExecution] = useState<Execution | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, [workflowId]);

  const fetchData = async () => {
    try {
      const [wfRes, execRes] = await Promise.all([
        fetch(`/api/workflows/${workflowId}`),
        fetch(`/api/workflows/${workflowId}/executions`),
      ]);

      if (wfRes.ok) {
        setWorkflow(await wfRes.json());
      }

      if (execRes.ok) {
        const data = await execRes.json();
        setExecutions(data.items || []);
      }
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchExecutionDetails = async (executionId: string) => {
    try {
      const response = await fetch(`/api/workflows/${workflowId}/executions/${executionId}`);
      if (response.ok) {
        setSelectedExecution(await response.json());
      }
    } catch (error) {
      console.error('Failed to fetch execution details:', error);
    }
  };

  const runWorkflow = async () => {
    try {
      const response = await fetch(`/api/workflows/${workflowId}/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ inputs: {} }),
      });

      if (response.ok) {
        fetchData();
      }
    } catch (error) {
      console.error('Failed to run workflow:', error);
    }
  };

  const statusConfig = {
    pending: { color: 'bg-gray-500', icon: Clock, label: 'Pending' },
    running: { color: 'bg-blue-500', icon: Loader2, label: 'Running' },
    completed: { color: 'bg-green-500', icon: CheckCircle, label: 'Completed' },
    failed: { color: 'bg-red-500', icon: XCircle, label: 'Failed' },
    cancelled: { color: 'bg-yellow-500', icon: Clock, label: 'Cancelled' },
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString();
  };

  const formatDuration = (start?: string, end?: string) => {
    if (!start || !end) return '-';
    const startTime = new Date(start).getTime();
    const endTime = new Date(end).getTime();
    const duration = endTime - startTime;
    if (duration < 1000) return `${duration}ms`;
    if (duration < 60000) return `${(duration / 1000).toFixed(1)}s`;
    return `${(duration / 60000).toFixed(1)}m`;
  };

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="container mx-auto py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div className="flex items-center gap-4">
          <Link href="/workflows">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="w-4 h-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-2xl font-bold">{workflow?.name || 'Workflow'} - Executions</h1>
            <p className="text-muted-foreground">View workflow execution history</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={fetchData}>
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>
          {workflow?.status === 'published' && (
            <Button onClick={runWorkflow}>
              <Play className="w-4 h-4 mr-2" />
              Run Now
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6 h-[calc(100vh-200px)]">
        {/* Execution List */}
        <Card className="col-span-1 flex flex-col">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">Executions</CardTitle>
            <CardDescription>
              {executions.length} execution{executions.length !== 1 ? 's' : ''}
            </CardDescription>
          </CardHeader>
          <CardContent className="flex-1 p-0">
            <ScrollArea className="h-full">
              {executions.length === 0 ? (
                <div className="text-center py-12 px-4">
                  <Clock className="w-12 h-12 mx-auto mb-4 text-muted-foreground" />
                  <p className="text-muted-foreground">No executions yet</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Run the workflow to see execution history
                  </p>
                </div>
              ) : (
                <div className="space-y-1 p-2">
                  {executions.map((execution) => {
                    const config = statusConfig[execution.status as keyof typeof statusConfig] || statusConfig.pending;
                    const Icon = config.icon;
                    
                    return (
                      <button
                        key={execution.id}
                        onClick={() => fetchExecutionDetails(execution.id)}
                        className={cn(
                          'w-full text-left p-3 rounded-lg border transition-colors',
                          selectedExecution?.id === execution.id
                            ? 'bg-accent border-primary'
                            : 'hover:bg-accent/50 border-transparent'
                        )}
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <Icon className={cn('w-4 h-4', execution.status === 'running' && 'animate-spin', execution.status === 'completed' && 'text-green-500', execution.status === 'failed' && 'text-red-500')} />
                          <span className="font-medium text-sm capitalize">{execution.status}</span>
                          <Badge variant="outline" className="ml-auto text-xs">
                            {execution.trigger_type}
                          </Badge>
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {formatDate(execution.started_at)}
                        </div>
                        {execution.duration_ms && (
                          <div className="text-xs text-muted-foreground mt-1">
                            Duration: {formatDuration(execution.started_at, execution.completed_at)}
                          </div>
                        )}
                      </button>
                    );
                  })}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Execution Details */}
        <Card className="col-span-2 flex flex-col">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">Execution Details</CardTitle>
            <CardDescription>
              {selectedExecution ? (
                <span>ID: {selectedExecution.id.slice(0, 8)}...</span>
              ) : (
                'Select an execution to view details'
              )}
            </CardDescription>
          </CardHeader>
          <CardContent className="flex-1 p-0">
            {!selectedExecution ? (
              <div className="flex items-center justify-center h-full text-muted-foreground">
                <div className="text-center">
                  <Eye className="w-12 h-12 mx-auto mb-4" />
                  <p>Select an execution to view details</p>
                </div>
              </div>
            ) : (
              <Tabs defaultValue="overview" className="h-full flex flex-col">
                <TabsList className="mx-4">
                  <TabsTrigger value="overview">Overview</TabsTrigger>
                  <TabsTrigger value="nodes">Node Executions</TabsTrigger>
                  <TabsTrigger value="inputs">Inputs</TabsTrigger>
                  <TabsTrigger value="outputs">Outputs</TabsTrigger>
                </TabsList>

                <ScrollArea className="flex-1 p-4">
                  <TabsContent value="overview" className="mt-0 space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium text-muted-foreground">Status</label>
                        <div className="flex items-center gap-2 mt-1">
                          {React.createElement(statusConfig[selectedExecution.status as keyof typeof statusConfig]?.icon || Clock, {
                            className: cn('w-5 h-5', selectedExecution.status === 'completed' && 'text-green-500', selectedExecution.status === 'failed' && 'text-red-500'),
                          })}
                          <span className="capitalize">{selectedExecution.status}</span>
                        </div>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-muted-foreground">Trigger</label>
                        <p className="mt-1 capitalize">{selectedExecution.trigger_type}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-muted-foreground">Started</label>
                        <p className="mt-1">{formatDate(selectedExecution.started_at)}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-muted-foreground">Duration</label>
                        <p className="mt-1">{formatDuration(selectedExecution.started_at, selectedExecution.completed_at)}</p>
                      </div>
                    </div>

                    {selectedExecution.error_message && (
                      <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20">
                        <label className="text-sm font-medium text-red-600">Error</label>
                        <p className="mt-1 text-sm text-red-600/80">{selectedExecution.error_message}</p>
                      </div>
                    )}
                  </TabsContent>

                  <TabsContent value="nodes" className="mt-0 space-y-3">
                    {selectedExecution.node_executions?.length === 0 ? (
                      <p className="text-center text-muted-foreground py-8">No node executions recorded</p>
                    ) : (
                      selectedExecution.node_executions?.map((node) => {
                        const nodeConfig = statusConfig[node.status as keyof typeof statusConfig] || statusConfig.pending;
                        const NodeIcon = nodeConfig.icon;
                        
                        return (
                          <div
                            key={node.id}
                            className={cn(
                              'p-4 rounded-lg border',
                              node.status === 'completed' && 'border-green-500/20 bg-green-500/5',
                              node.status === 'failed' && 'border-red-500/20 bg-red-500/5',
                              node.status === 'running' && 'border-blue-500/20 bg-blue-500/5',
                              node.status === 'pending' && 'border-gray-500/20 bg-gray-500/5',
                            )}
                          >
                            <div className="flex items-center justify-between mb-2">
                              <div className="flex items-center gap-2">
                                <NodeIcon className={cn('w-4 h-4', node.status === 'running' && 'animate-spin')} />
                                <span className="font-medium">{node.node_name || node.node_type}</span>
                                <Badge variant="outline" className="text-xs">{node.node_type}</Badge>
                              </div>
                              <div className="flex items-center gap-3 text-sm text-muted-foreground">
                                {node.duration_ms && <span>{node.duration_ms}ms</span>}
                                <span className="capitalize">{node.status}</span>
                              </div>
                            </div>
                            <div className="text-xs text-muted-foreground">
                              Node ID: {node.node_id}
                            </div>
                            {node.error_message && (
                              <div className="mt-2 text-sm text-red-600">
                                {node.error_message}
                              </div>
                            )}
                          </div>
                        );
                      })
                    )}
                  </TabsContent>

                  <TabsContent value="inputs" className="mt-0">
                    <pre className="p-4 rounded-lg bg-muted overflow-auto text-sm">
                      {JSON.stringify(selectedExecution.inputs || {}, null, 2)}
                    </pre>
                  </TabsContent>

                  <TabsContent value="outputs" className="mt-0">
                    {selectedExecution.outputs ? (
                      <pre className="p-4 rounded-lg bg-muted overflow-auto text-sm">
                        {JSON.stringify(selectedExecution.outputs, null, 2)}
                      </pre>
                    ) : (
                      <p className="text-center text-muted-foreground py-8">
                        No outputs available
                      </p>
                    )}
                  </TabsContent>
                </ScrollArea>
              </Tabs>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
