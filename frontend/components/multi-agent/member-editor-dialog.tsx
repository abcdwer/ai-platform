'use client';

import { useState } from 'react';
import { MemberRole, MEMBER_ROLE_COLORS } from '@/types/multi-agent';
import type { AgentMember, AgentMemberCreate, AgentMemberUpdate } from '@/types/multi-agent';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { 
  Dialog, 
  DialogContent, 
  DialogDescription, 
  DialogFooter, 
  DialogHeader, 
  DialogTitle,
} from '@/components/ui/dialog';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

const ROLE_DESCRIPTIONS: Record<MemberRole, string> = {
  leader: 'Coordinates and delegates tasks to other agents',
  member: 'Standard agent that participates in collaboration',
  supporter: 'Argues in favor (debate mode)',
  opponent: 'Argues against (debate mode)',
  judge: 'Evaluates and makes final decisions (debate mode)',
};

const PRESET_COLORS = [
  '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
  '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1',
];

interface MemberEditorDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  member: AgentMember | null;
  onSave: (data: AgentMemberCreate | AgentMemberUpdate) => Promise<void>;
}

export function MemberEditorDialog({
  open,
  onOpenChange,
  member,
  onSave,
}: MemberEditorDialogProps) {
  const [name, setName] = useState(member?.name || '');
  const [role, setRole] = useState<MemberRole>(member?.role || 'member');
  const [systemPrompt, setSystemPrompt] = useState(
    member?.system_prompt || 'You are a helpful AI assistant.'
  );
  const [model, setModel] = useState(member?.model || '');
  const [temperature, setTemperature] = useState(member?.temperature || 0.7);
  const [maxTokens, setMaxTokens] = useState(member?.max_tokens || 2048);
  const [color, setColor] = useState(member?.color || PRESET_COLORS[0]);
  const [executionOrder, setExecutionOrder] = useState(member?.execution_order || 0);
  const [isSaving, setIsSaving] = useState(false);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    
    const data: AgentMemberCreate | AgentMemberUpdate = {
      name,
      role,
      system_prompt: systemPrompt,
      model: model || undefined,
      temperature,
      max_tokens: maxTokens,
      color,
      execution_order: executionOrder,
    };
    
    await onSave(data);
    setIsSaving(false);
  };
  
  const handleOpenChange = (open: boolean) => {
    if (!open) {
      // Reset form when closing
      setName(member?.name || '');
      setRole(member?.role || 'member');
      setSystemPrompt(member?.system_prompt || 'You are a helpful AI assistant.');
      setModel(member?.model || '');
      setTemperature(member?.temperature || 0.7);
      setMaxTokens(member?.max_tokens || 2048);
      setColor(member?.color || PRESET_COLORS[0]);
      setExecutionOrder(member?.execution_order || 0);
    }
    onOpenChange(open);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-[600px] max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {member ? 'Edit Member' : 'Add New Member'}
          </DialogTitle>
          <DialogDescription>
            Configure the agent that will join this collaboration team
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            {/* Name and Role */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="name">Name</Label>
                <Input
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g., Code Analyzer"
                  required
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="role">Role</Label>
                <Select value={role} onValueChange={(v) => setRole(v as MemberRole)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {(Object.keys(ROLE_DESCRIPTIONS) as MemberRole[]).map((r) => (
                      <SelectItem key={r} value={r}>
                        <div className="flex items-center gap-2">
                          <div 
                            className="w-3 h-3 rounded-full" 
                            style={{ backgroundColor: MEMBER_ROLE_COLORS[r] }}
                          />
                          <span className="capitalize">{r}</span>
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            <div className="text-sm text-muted-foreground -mt-2">
              {ROLE_DESCRIPTIONS[role]}
            </div>
            
            {/* System Prompt */}
            <div className="space-y-2">
              <Label htmlFor="systemPrompt">System Prompt</Label>
              <Textarea
                id="systemPrompt"
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                placeholder="Instructions for this agent..."
                rows={4}
                required
              />
            </div>
            
            {/* Model Settings */}
            <div className="grid grid-cols-3 gap-4">
              <div className="space-y-2">
                <Label htmlFor="model">Model (optional)</Label>
                <Input
                  id="model"
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  placeholder="llama2"
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="temperature">Temperature</Label>
                <Input
                  id="temperature"
                  type="number"
                  step="0.1"
                  min="0"
                  max="2"
                  value={temperature}
                  onChange={(e) => setTemperature(parseFloat(e.target.value))}
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="maxTokens">Max Tokens</Label>
                <Input
                  id="maxTokens"
                  type="number"
                  min="100"
                  max="32768"
                  value={maxTokens}
                  onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                />
              </div>
            </div>
            
            {/* Color and Order */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Color</Label>
                <div className="flex gap-2 flex-wrap">
                  {PRESET_COLORS.map((c) => (
                    <button
                      key={c}
                      type="button"
                      className={`w-8 h-8 rounded-full border-2 transition-all ${
                        color === c ? 'border-primary scale-110' : 'border-transparent'
                      }`}
                      style={{ backgroundColor: c }}
                      onClick={() => setColor(c)}
                    />
                  ))}
                </div>
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="executionOrder">Execution Order</Label>
                <Input
                  id="executionOrder"
                  type="number"
                  min="0"
                  value={executionOrder}
                  onChange={(e) => setExecutionOrder(parseInt(e.target.value))}
                />
                <p className="text-xs text-muted-foreground">
                  Order in sequential collaboration
                </p>
              </div>
            </div>
            
            {/* Preview */}
            <div className="space-y-2">
              <Label>Preview</Label>
              <div 
                className="p-4 rounded-lg border-2"
                style={{ 
                  borderColor: color,
                  backgroundColor: color + '10'
                }}
              >
                <div className="flex items-center gap-2 mb-2">
                  <div 
                    className="w-4 h-4 rounded-full" 
                    style={{ backgroundColor: color }}
                  />
                  <span className="font-medium">{name || 'Agent Name'}</span>
                  <span className="text-xs px-2 py-0.5 rounded bg-muted capitalize">{role}</span>
                </div>
                <p className="text-sm text-muted-foreground line-clamp-2">
                  {systemPrompt || 'Agent system prompt...'}
                </p>
              </div>
            </div>
          </div>
          
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => handleOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={!name || !systemPrompt || isSaving}>
              {isSaving ? 'Saving...' : member ? 'Save Changes' : 'Add Member'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
