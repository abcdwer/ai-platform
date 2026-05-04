'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Plus, Search, MoreHorizontal, Play, Edit, Trash2, Copy, Archive, ChevronRight } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useToast } from '@/components/ui/use-toast';

interface Workflow {
  id: string;
  name: string;
  description?: string;
  version: number;
  status: 'draft' | 'published' | 'archived';
  created_at: string;
  updated_at: string;
}

export default function WorkflowsPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newWorkflowName, setNewWorkflowName] = useState('');
  const [newWorkflowDescription, setNewWorkflowDescription] = useState('');
  const [creating, setCreating] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  useEffect(() => {
    fetchWorkflows();
  }, []);

  const fetchWorkflows = async () => {
    try {
      const response = await fetch('/api/workflows');
      if (response.ok) {
        const data = await response.json();
        setWorkflows(data.items || []);
      }
    } catch (error) {
      console.error('Failed to fetch workflows:', error);
    } finally {
      setLoading(false);
    }
  };

  const createWorkflow = async () => {
    if (!newWorkflowName.trim()) return;

    setCreating(true);
    try {
      const response = await fetch('/api/workflows', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: newWorkflowName,
          description: newWorkflowDescription,
          graph_data: {
            nodes: [
              {
                id: 'start-1',
                type: 'start',
                position: { x: 100, y: 200 },
                data: { label: 'Start', config: { trigger: 'manual' } },
              },
              {
                id: 'end-1',
                type: 'end',
                position: { x: 500, y: 200 },
                data: { label: 'End', config: {} },
              },
            ],
            edges: [],
          },
        }),
      });

      if (response.ok) {
        const workflow = await response.json();
        toast({ title: 'Workflow created successfully' });
        setShowCreateDialog(false);
        setNewWorkflowName('');
        setNewWorkflowDescription('');
        router.push(`/workflows/${workflow.id}/edit`);
      } else {
        throw new Error('Failed to create workflow');
      }
    } catch (error) {
      toast({ title: 'Failed to create workflow', variant: 'destructive' });
    } finally {
      setCreating(false);
    }
  };

  const deleteWorkflow = async (id: string) => {
    setDeletingId(id);
    try {
      const response = await fetch(`/api/workflows/${id}`, { method: 'DELETE' });
      if (response.ok) {
        setWorkflows(workflows.filter((w) => w.id !== id));
        toast({ title: 'Workflow deleted' });
      }
    } catch (error) {
      toast({ title: 'Failed to delete workflow', variant: 'destructive' });
    } finally {
      setDeletingId(null);
    }
  };

  const duplicateWorkflow = async (workflow: Workflow) => {
    try {
      const response = await fetch('/api/workflows', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: `${workflow.name} (Copy)`,
          description: workflow.description,
          graph_data: {},
        }),
      });

      if (response.ok) {
        toast({ title: 'Workflow duplicated' });
        fetchWorkflows();
      }
    } catch (error) {
      toast({ title: 'Failed to duplicate workflow', variant: 'destructive' });
    }
  };

  const publishWorkflow = async (id: string) => {
    try {
      const response = await fetch(`/api/workflows/${id}/publish`, { method: 'POST' });
      if (response.ok) {
        toast({ title: 'Workflow published' });
        fetchWorkflows();
      }
    } catch (error) {
      toast({ title: 'Failed to publish workflow', variant: 'destructive' });
    }
  };

  const filteredWorkflows = workflows.filter(
    (w) =>
      w.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      w.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const statusColors = {
    draft: 'bg-yellow-500/10 text-yellow-600 border-yellow-500/20',
    published: 'bg-green-500/10 text-green-600 border-green-500/20',
    archived: 'bg-gray-500/10 text-gray-600 border-gray-500/20',
  };

  return (
    <div className="container mx-auto py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold">Workflows</h1>
          <p className="text-muted-foreground mt-1">
            Create and manage visual workflows for your AI tasks
          </p>
        </div>
        <Button onClick={() => setShowCreateDialog(true)}>
          <Plus className="w-4 h-4 mr-2" />
          New Workflow
        </Button>
      </div>

      {/* Search */}
      <div className="relative mb-6">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
        <Input
          placeholder="Search workflows..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10 max-w-md"
        />
      </div>

      {/* Workflow List */}
      {loading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader>
                <div className="h-6 bg-muted rounded w-1/2" />
                <div className="h-4 bg-muted rounded w-3/4 mt-2" />
              </CardHeader>
              <CardContent>
                <div className="h-4 bg-muted rounded w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      ) : filteredWorkflows.length === 0 ? (
        <Card className="text-center py-12">
          <CardContent>
            <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-muted flex items-center justify-center">
              <Play className="w-8 h-8 text-muted-foreground" />
            </div>
            <h3 className="text-lg font-semibold mb-2">No workflows yet</h3>
            <p className="text-muted-foreground mb-4">
              Create your first workflow to get started with visual automation.
            </p>
            <Button onClick={() => setShowCreateDialog(true)}>
              <Plus className="w-4 h-4 mr-2" />
              Create Workflow
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredWorkflows.map((workflow) => (
            <Card key={workflow.id} className="group hover:shadow-lg transition-shadow">
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <CardTitle className="truncate">{workflow.name}</CardTitle>
                    <CardDescription className="mt-1 line-clamp-2">
                      {workflow.description || 'No description'}
                    </CardDescription>
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity">
                        <MoreHorizontal className="w-4 h-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => router.push(`/workflows/${workflow.id}/edit`)}>
                        <Edit className="w-4 h-4 mr-2" />
                        Edit
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => router.push(`/workflows/${workflow.id}/executions`)}>
                        <Play className="w-4 h-4 mr-2" />
                        Executions
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => duplicateWorkflow(workflow)}>
                        <Copy className="w-4 h-4 mr-2" />
                        Duplicate
                      </DropdownMenuItem>
                      {workflow.status === 'draft' && (
                        <DropdownMenuItem onClick={() => publishWorkflow(workflow.id)}>
                          <Archive className="w-4 h-4 mr-2" />
                          Publish
                        </DropdownMenuItem>
                      )}
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        onClick={() => deleteWorkflow(workflow.id)}
                        className="text-destructive focus:text-destructive"
                        disabled={deletingId === workflow.id}
                      >
                        <Trash2 className="w-4 h-4 mr-2" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex items-center justify-between">
                  <Badge variant="outline" className={statusColors[workflow.status]}>
                    {workflow.status}
                  </Badge>
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span>v{workflow.version}</span>
                    <ChevronRight className="w-3 h-3" />
                  </div>
                </div>
                <div className="mt-4 flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1"
                    onClick={() => router.push(`/workflows/${workflow.id}/edit`)}
                  >
                    <Edit className="w-3 h-3 mr-1" />
                    Edit
                  </Button>
                  {workflow.status === 'published' && (
                    <Button
                      size="sm"
                      className="flex-1"
                      onClick={() => router.push(`/workflows/${workflow.id}/executions`)}
                    >
                      <Play className="w-3 h-3 mr-1" />
                      Run
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create Dialog */}
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Workflow</DialogTitle>
            <DialogDescription>
              Create a new workflow to automate your AI tasks.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <label htmlFor="name" className="text-sm font-medium">
                Name
              </label>
              <Input
                id="name"
                value={newWorkflowName}
                onChange={(e) => setNewWorkflowName(e.target.value)}
                placeholder="My Workflow"
              />
            </div>
            <div className="space-y-2">
              <label htmlFor="description" className="text-sm font-medium">
                Description (optional)
              </label>
              <Input
                id="description"
                value={newWorkflowDescription}
                onChange={(e) => setNewWorkflowDescription(e.target.value)}
                placeholder="Describe what this workflow does..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateDialog(false)}>
              Cancel
            </Button>
            <Button onClick={createWorkflow} disabled={!newWorkflowName.trim() || creating}>
              {creating ? 'Creating...' : 'Create'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
