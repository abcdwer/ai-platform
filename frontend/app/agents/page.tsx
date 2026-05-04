'use client';

import { useEffect, useState } from 'react';
import { Sidebar } from '@/components/sidebar';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useAgentStore, useModelStore } from '@/stores';
import { Plus, Bot, Trash2, Edit, Loader2, MessageSquare, Settings, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Agent } from '@/types';

export default function AgentsPage() {
  const { agents, isLoading, error, loadAgents, deleteAgent } = useAgentStore();
  const { models } = useModelStore();
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingAgent, setEditingAgent] = useState<Agent | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    system_prompt: '',
    model_provider: 'ollama',
    model: 'llama2',
    temperature: 0.7,
    max_tokens: 2048,
    top_p: 0.9,
    is_active: true,
    is_public: false,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    loadAgents();
  }, [loadAgents]);

  const handleOpenCreate = () => {
    setEditingAgent(null);
    setFormData({
      name: '',
      description: '',
      system_prompt: '',
      model_provider: 'ollama',
      model: 'llama2',
      temperature: 0.7,
      max_tokens: 2048,
      top_p: 0.9,
      is_active: true,
      is_public: false,
    });
    setIsDialogOpen(true);
  };

  const handleOpenEdit = (agent: Agent) => {
    setEditingAgent(agent);
    setFormData({
      name: agent.name,
      description: agent.description || '',
      system_prompt: agent.system_prompt,
      model_provider: agent.model_provider,
      model: agent.model,
      temperature: agent.temperature,
      max_tokens: agent.max_tokens,
      top_p: agent.top_p || 0.9,
      is_active: agent.is_active,
      is_public: agent.is_public,
    });
    setIsDialogOpen(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    
    try {
      const url = editingAgent 
        ? `/api/agents/${editingAgent.id}`
        : '/api/agents';
      const method = editingAgent ? 'PUT' : 'POST';
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}${url}`, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      
      if (!response.ok) throw new Error('Failed to save agent');
      
      await loadAgents();
      setIsDialogOpen(false);
    } catch (error) {
      console.error('Failed to save agent:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (confirm('Are you sure you want to delete this agent?')) {
      try {
        await deleteAgent(id);
      } catch (error) {
        console.error('Failed to delete agent:', error);
      }
    }
  };

  return (
    <div className="flex h-screen">
      <Sidebar />
      
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-10">
          <div className="container mx-auto px-6 py-4 flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Agents</h1>
              <p className="text-muted-foreground">
                Create and manage AI agents with custom prompts and tools
              </p>
            </div>
            <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
              <DialogTrigger asChild>
                <Button onClick={handleOpenCreate}>
                  <Plus className="h-4 w-4 mr-2" />
                  Create Agent
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
                <form onSubmit={handleSubmit} className="flex flex-col h-full">
                  <DialogHeader>
                    <DialogTitle>{editingAgent ? 'Edit Agent' : 'Create New Agent'}</DialogTitle>
                    <DialogDescription>
                      Configure your AI agent with custom prompts, model, and settings.
                    </DialogDescription>
                  </DialogHeader>
                  
                  <ScrollArea className="flex-1 my-4">
                    <div className="space-y-4 px-1">
                      <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <label className="text-sm font-medium">Name</label>
                          <Input
                            placeholder="My Agent"
                            value={formData.name}
                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                            required
                          />
                        </div>
                        <div className="space-y-2">
                          <label className="text-sm font-medium">Model Provider</label>
                          <Select
                            value={formData.model_provider}
                            onValueChange={(value) => setFormData({ ...formData, model_provider: value })}
                          >
                            <SelectTrigger>
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="ollama">Ollama (Local)</SelectItem>
                              <SelectItem value="openai">OpenAI</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                      
                      <div className="space-y-2">
                        <label className="text-sm font-medium">Description</label>
                        <Input
                          placeholder="A brief description of what this agent does"
                          value={formData.description}
                          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                        />
                      </div>
                      
                      <div className="space-y-2">
                        <label className="text-sm font-medium">System Prompt</label>
                        <Textarea
                          placeholder="You are a helpful AI assistant that..."
                          value={formData.system_prompt}
                          onChange={(e) => setFormData({ ...formData, system_prompt: e.target.value })}
                          rows={4}
                          required
                        />
                      </div>
                      
                      <div className="grid grid-cols-3 gap-4">
                        <div className="space-y-2">
                          <label className="text-sm font-medium">Temperature</label>
                          <Input
                            type="number"
                            step="0.1"
                            min="0"
                            max="2"
                            value={formData.temperature}
                            onChange={(e) => setFormData({ ...formData, temperature: parseFloat(e.target.value) })}
                          />
                        </div>
                        <div className="space-y-2">
                          <label className="text-sm font-medium">Max Tokens</label>
                          <Input
                            type="number"
                            min="1"
                            value={formData.max_tokens}
                            onChange={(e) => setFormData({ ...formData, max_tokens: parseInt(e.target.value) })}
                          />
                        </div>
                        <div className="space-y-2">
                          <label className="text-sm font-medium">Top P</label>
                          <Input
                            type="number"
                            step="0.1"
                            min="0"
                            max="1"
                            value={formData.top_p}
                            onChange={(e) => setFormData({ ...formData, top_p: parseFloat(e.target.value) })}
                          />
                        </div>
                      </div>
                    </div>
                  </ScrollArea>
                  
                  <DialogFooter className="flex-shrink-0">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => setIsDialogOpen(false)}
                    >
                      Cancel
                    </Button>
                    <Button type="submit" disabled={isSubmitting}>
                      {isSubmitting && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                      {editingAgent ? 'Save Changes' : 'Create Agent'}
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        </header>

        {/* Agent List */}
        <div className="flex-1 overflow-y-auto p-6">
          {isLoading ? (
            <div className="flex items-center justify-center h-full">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          ) : agents.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground">
              <Bot className="w-16 h-16 mb-4 opacity-50" />
              <h2 className="text-xl font-medium mb-2">No agents yet</h2>
              <p className="text-sm max-w-md mb-4">
                Create your first agent to get started with custom AI assistants.
              </p>
              <Button onClick={handleOpenCreate}>
                <Plus className="h-4 w-4 mr-2" />
                Create Agent
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {agents.map((agent) => (
                <AgentCard
                  key={agent.id}
                  agent={agent}
                  onEdit={() => handleOpenEdit(agent)}
                  onDelete={() => handleDelete(agent.id)}
                />
              ))}
            </div>
          )}
          
          {error && (
            <div className="mt-4 p-4 text-sm text-destructive bg-destructive/10 rounded-md">
              {error}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

interface AgentCardProps {
  agent: Agent;
  onEdit: () => void;
  onDelete: () => void;
}

function AgentCard({ agent, onEdit, onDelete }: AgentCardProps) {
  return (
    <Card className="hover:border-primary/50 transition-all group">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
              <Bot className="h-5 w-5 text-primary" />
            </div>
            <div>
              <CardTitle className="text-base">{agent.name}</CardTitle>
              <CardDescription className="text-xs">
                {agent.model_provider}/{agent.model}
              </CardDescription>
            </div>
          </div>
          <Badge variant={agent.is_active ? 'default' : 'secondary'} className="text-xs">
            {agent.is_active ? 'Active' : 'Inactive'}
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        {agent.description && (
          <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
            {agent.description}
          </p>
        )}
        
        <div className="flex flex-wrap gap-2 mb-4">
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <Zap className="h-3 w-3" />
            Temp: {agent.temperature}
          </div>
          <div className="flex items-center gap-1 text-xs text-muted-foreground">
            <MessageSquare className="h-3 w-3" />
            Max: {agent.max_tokens}
          </div>
        </div>
        
        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
          <Button variant="outline" size="sm" className="flex-1" onClick={onEdit}>
            <Edit className="h-3 w-3 mr-1" />
            Edit
          </Button>
          <Button variant="outline" size="sm" className="text-destructive hover:text-destructive" onClick={onDelete}>
            <Trash2 className="h-3 w-3" />
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
