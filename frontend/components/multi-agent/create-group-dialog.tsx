'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useMultiAgentStore } from '@/stores/multiAgentStore';
import { CollaborationMode, MODE_DESCRIPTIONS, MODE_COLORS } from '@/types/multi-agent';
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

interface CreateGroupDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function CreateGroupDialog({ open, onOpenChange }: CreateGroupDialogProps) {
  const router = useRouter();
  const { createGroup, isLoadingGroups } = useMultiAgentStore();
  
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [mode, setMode] = useState<CollaborationMode>('sequential');
  const [maxIterations, setMaxIterations] = useState(10);
  
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const group = await createGroup({
      name,
      description,
      mode,
      max_iterations: maxIterations,
    });
    
    if (group) {
      onOpenChange(false);
      router.push(`/multi-agent/${group.id}/edit`);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Create Agent Group</DialogTitle>
          <DialogDescription>
            Create a team of AI agents that will collaborate together
          </DialogDescription>
        </DialogHeader>
        
        <form onSubmit={handleSubmit}>
          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">Group Name</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Code Review Team"
                required
              />
            </div>
            
            <div className="grid gap-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe the purpose of this agent team..."
                rows={3}
              />
            </div>
            
            <div className="grid gap-2">
              <Label htmlFor="mode">Collaboration Mode</Label>
              <Select value={mode} onValueChange={(v) => setMode(v as CollaborationMode)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {(Object.keys(MODE_DESCRIPTIONS) as CollaborationMode[]).map((m) => (
                    <SelectItem key={m} value={m}>
                      <div className="flex items-center gap-2">
                        <span>{MODE_DESCRIPTIONS[m].icon}</span>
                        <span>{MODE_DESCRIPTIONS[m].title}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-xs text-muted-foreground mt-1">
                {MODE_DESCRIPTIONS[mode]?.description}
              </p>
            </div>
            
            <div className="grid gap-2">
              <Label htmlFor="maxIterations">Max Iterations</Label>
              <Input
                id="maxIterations"
                type="number"
                value={maxIterations}
                onChange={(e) => setMaxIterations(parseInt(e.target.value) || 10)}
                min={1}
                max={100}
              />
              <p className="text-xs text-muted-foreground mt-1">
                Maximum number of collaboration rounds
              </p>
            </div>
          </div>
          
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={!name || isLoadingGroups}>
              Create Group
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
