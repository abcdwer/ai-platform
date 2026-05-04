'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { ArrowLeft, Save, Play, Eye, Undo2, Redo2, Loader2, Share2, Download, Upload } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useToast } from '@/components/ui/use-toast';
import { useWorkflowStore, Workflow } from '@/stores/workflowStore';
import { WorkflowEditor, ExecutionPanel } from '@/components/workflow';
import { ExportWorkflowDialog, ImportWorkflowDialog } from '@/components/export-dialog';

export default function WorkflowEditPage() {
  const router = useRouter();
  const params = useParams();
  const { toast } = useToast();
  const workflowId = params.id as string;

  const {
    currentWorkflow,
    loadWorkflow,
    getGraphData,
    setCurrentWorkflow,
    resetWorkflow,
    history,
    historyIndex,
    undo,
    redo,
  } = useWorkflowStore();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);
  const [workflowName, setWorkflowName] = useState('');
  const [showExportDialog, setShowExportDialog] = useState(false);
  const [showImportDialog, setShowImportDialog] = useState(false);

  useEffect(() => {
    fetchWorkflow();
    return () => resetWorkflow();
  }, [workflowId]);

  const fetchWorkflow = async () => {
    try {
      const response = await fetch(`/api/workflows/${workflowId}`);
      if (response.ok) {
        const workflow = await response.json();
        setCurrentWorkflow(workflow);
        loadWorkflow(workflow);
        setWorkflowName(workflow.name);
      } else {
        toast({ title: 'Failed to load workflow', variant: 'destructive' });
        router.push('/workflows');
      }
    } catch (error) {
      console.error('Failed to fetch workflow:', error);
      toast({ title: 'Failed to load workflow', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  const saveWorkflow = async () => {
    if (!currentWorkflow) return;

    setSaving(true);
    try {
      const { nodes, edges } = getGraphData();
      const response = await fetch(`/api/workflows/${workflowId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: workflowName,
          graph_data: { nodes, edges },
        }),
      });

      if (response.ok) {
        const updated = await response.json();
        setCurrentWorkflow(updated);
        setHasChanges(false);
        toast({ title: 'Workflow saved' });
      } else {
        throw new Error('Failed to save');
      }
    } catch (error) {
      toast({ title: 'Failed to save workflow', variant: 'destructive' });
    } finally {
      setSaving(false);
    }
  };

  const handleExportWorkflow = async () => {
    const response = await fetch(`/api/workflows/${workflowId}/export`);
    if (!response.ok) throw new Error('Export failed');
    
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `workflow_${workflowName.replace(/\s+/g, '_')}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  const handleShareWorkflow = async () => {
    const response = await fetch(`/api/workflows/${workflowId}/share`);
    if (!response.ok) throw new Error('Share failed');
    
    const data = await response.json();
    
    // Copy share URL to clipboard
    await navigator.clipboard.writeText(`${window.location.origin}${data.share_url}`);
    
    return data;
  };

  const handleImportWorkflow = async (config: any) => {
    const workflowData = config.workflow || config;
    const response = await fetch('/api/workflows/import', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: `Imported: ${workflowData.name || 'Workflow'}`,
        description: workflowData.description || '',
        graph_data: workflowData.graph_data || { nodes: [], edges: [] },
      }),
    });
    
    if (!response.ok) throw new Error('Import failed');
    
    const newWorkflow = await response.json();
    toast({ title: 'Workflow imported', description: 'Redirecting to new workflow...' });
    router.push(`/workflows/${newWorkflow.id}/edit`);
  };

  // Track changes
  useEffect(() => {
    const unsubscribe = useWorkflowStore.subscribe((state) => {
      const currentGraph = { nodes: state.nodes, edges: state.edges };
      const savedGraph = state.currentWorkflow?.graph_data || { nodes: [], edges: [] };
      const changed = JSON.stringify(currentGraph) !== JSON.stringify(savedGraph);
      setHasChanges(changed);
    });

    return unsubscribe;
  }, []);

  const handleKeyDown = (e: KeyboardEvent) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 's') {
      e.preventDefault();
      saveWorkflow();
    }
    if ((e.metaKey || e.ctrlKey) && e.key === 'z') {
      e.preventDefault();
      if (e.shiftKey) {
        redo();
      } else {
        undo();
      }
    }
  };

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="flex items-center justify-between px-4 py-2 border-b bg-card">
        <div className="flex items-center gap-4">
          <Link href="/workflows">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="w-4 h-4" />
            </Button>
          </Link>
          <Input
            value={workflowName}
            onChange={(e) => {
              setWorkflowName(e.target.value);
              setHasChanges(true);
            }}
            className="font-semibold max-w-xs bg-transparent border-transparent hover:border-input focus:border-input"
          />
          {hasChanges && (
            <span className="text-xs text-muted-foreground">Unsaved changes</span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {/* Undo/Redo */}
          <Button
            variant="ghost"
            size="icon"
            onClick={undo}
            disabled={historyIndex <= 0}
            title="Undo (Ctrl+Z)"
          >
            <Undo2 className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={redo}
            disabled={historyIndex >= history.length - 1}
            title="Redo (Ctrl+Shift+Z)"
          >
            <Redo2 className="w-4 h-4" />
          </Button>

          <div className="w-px h-6 bg-border mx-2" />

          {/* Share & Export */}
          <Button variant="ghost" onClick={() => setShowExportDialog(true)} title="Share & Export">
            <Share2 className="w-4 h-4 mr-2" />
            Share
          </Button>
          <Button variant="ghost" onClick={() => setShowImportDialog(true)} title="Import">
            <Upload className="w-4 h-4" />
          </Button>

          <div className="w-px h-6 bg-border mx-2" />

          {/* Actions */}
          <Button variant="outline" onClick={() => router.push(`/workflows/${workflowId}/executions`)}>
            <Eye className="w-4 h-4 mr-2" />
            History
          </Button>
          <Button variant="outline" onClick={saveWorkflow} disabled={saving || !hasChanges}>
            <Save className="w-4 h-4 mr-2" />
            {saving ? 'Saving...' : 'Save'}
          </Button>
          {currentWorkflow?.status === 'published' && (
            <ExecutionPanel workflowId={workflowId} />
          )}
        </div>
      </header>

      {/* Editor */}
      <div className="flex-1 relative">
        <WorkflowEditor />
      </div>

      {/* Status Bar */}
      <footer className="flex items-center justify-between px-4 py-1 border-t bg-muted/50 text-xs text-muted-foreground">
        <div>
          {currentWorkflow && (
            <span>
              {currentWorkflow.status === 'published' ? (
                <span className="text-green-600">Published</span>
              ) : (
                <span className="text-yellow-600">Draft</span>
              )}
              {' • '}
              Version {currentWorkflow.version}
            </span>
          )}
        </div>
        <div>
          Use the node panel on the left to add nodes. Drag to connect them.
        </div>
      </footer>

      {/* Export & Share Dialog */}
      <ExportWorkflowDialog
        open={showExportDialog}
        onOpenChange={setShowExportDialog}
        workflowId={workflowId}
        workflowName={workflowName}
        onExport={handleExportWorkflow}
        onShare={handleShareWorkflow}
      />

      {/* Import Dialog */}
      <ImportWorkflowDialog
        open={showImportDialog}
        onOpenChange={setShowImportDialog}
        onImport={handleImportWorkflow}
      />
    </div>
  );
}
