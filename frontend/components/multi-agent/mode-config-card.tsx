'use client';

import { useState } from 'react';
import { CollaborationMode, MODE_DESCRIPTIONS, ModeConfig } from '@/types/multi-agent';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

interface ModeConfigCardProps {
  mode: CollaborationMode;
  config: ModeConfig;
  onChange: (config: ModeConfig) => void;
}

export function ModeConfigCard({ mode, config, onChange }: ModeConfigCardProps) {
  const updateConfig = (updates: Partial<ModeConfig>) => {
    onChange({ ...config, ...updates });
  };

  const renderSequentialConfig = () => (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Sequential Mode Settings</CardTitle>
        <CardDescription>
          Agents execute one after another in order
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <Label htmlFor="stopOnFirstSuccess">Stop on First Success</Label>
            <p className="text-sm text-muted-foreground">
              End collaboration when a member completes the task
            </p>
          </div>
          <Switch
            id="stopOnFirstSuccess"
            checked={config.stop_on_first_success || false}
            onCheckedChange={(checked) => updateConfig({ stop_on_first_success: checked })}
          />
        </div>
      </CardContent>
    </Card>
  );

  const renderParallelConfig = () => (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Parallel Mode Settings</CardTitle>
        <CardDescription>
          Multiple agents work simultaneously
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="maxParallel">Max Parallel Agents</Label>
          <Input
            id="maxParallel"
            type="number"
            min={1}
            max={10}
            value={config.max_parallel || 3}
            onChange={(e) => updateConfig({ max_parallel: parseInt(e.target.value) })}
            className="w-32"
          />
          <p className="text-sm text-muted-foreground">
            Maximum number of agents to run in parallel
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="aggregationMethod">Aggregation Method</Label>
          <Select 
            value={config.aggregation_method || 'merge'} 
            onValueChange={(v) => updateConfig({ aggregation_method: v as 'merge' | 'vote' | 'first' })}
          >
            <SelectTrigger className="w-48">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="merge">Merge (Synthesize all)</SelectItem>
              <SelectItem value="vote">Vote (Select best)</SelectItem>
              <SelectItem value="first">First (Use first response)</SelectItem>
            </SelectContent>
          </Select>
          <p className="text-sm text-muted-foreground">
            How to combine results from parallel agents
          </p>
        </div>
      </CardContent>
    </Card>
  );

  const renderDebateConfig = () => (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Debate Mode Settings</CardTitle>
        <CardDescription>
          Pro/con debate with optional judge
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="rounds">Number of Rounds</Label>
          <Input
            id="rounds"
            type="number"
            min={1}
            max={10}
            value={config.rounds || 3}
            onChange={(e) => updateConfig({ rounds: parseInt(e.target.value) })}
            className="w-32"
          />
          <p className="text-sm text-muted-foreground">
            How many debate rounds before judgment
          </p>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <Label htmlFor="allowRebuttal">Allow Rebuttal</Label>
            <p className="text-sm text-muted-foreground">
              Agents can respond to opponent arguments
            </p>
          </div>
          <Switch
            id="allowRebuttal"
            checked={config.allow_rebuttal !== false}
            onCheckedChange={(checked) => updateConfig({ allow_rebuttal: checked })}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="judgeModel">Judge Model (optional)</Label>
          <Input
            id="judgeModel"
            value={config.judge_model || ''}
            onChange={(e) => updateConfig({ judge_model: e.target.value || undefined })}
            placeholder="Use default model"
          />
          <p className="text-sm text-muted-foreground">
            Specific model for the judge agent
          </p>
        </div>
      </CardContent>
    </Card>
  );

  const renderHierarchicalConfig = () => (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Hierarchical Mode Settings</CardTitle>
        <CardDescription>
          Leader coordinates subordinates through delegation
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="maxDepth">Max Delegation Depth</Label>
          <Input
            id="maxDepth"
            type="number"
            min={1}
            max={5}
            value={config.max_depth || 3}
            onChange={(e) => updateConfig({ max_depth: parseInt(e.target.value) })}
            className="w-32"
          />
          <p className="text-sm text-muted-foreground">
            Maximum delegation chain depth
          </p>
        </div>

        <div className="space-y-2">
          <Label htmlFor="delegateThreshold">Delegation Threshold</Label>
          <div className="flex items-center gap-4">
            <Input
              id="delegateThreshold"
              type="number"
              step="0.1"
              min="0"
              max="1"
              value={config.delegate_threshold || 0.5}
              onChange={(e) => updateConfig({ delegate_threshold: parseFloat(e.target.value) })}
              className="w-32"
            />
            <span className="text-sm text-muted-foreground">
              Confidence level to trigger delegation
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  const renderRoundRobinConfig = () => (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Round Robin Mode Settings</CardTitle>
        <CardDescription>
          Agents take turns speaking in rotation
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="maxTurns">Maximum Turns</Label>
          <Input
            id="maxTurns"
            type="number"
            min={1}
            max={50}
            value={config.max_turns || 10}
            onChange={(e) => updateConfig({ max_turns: parseInt(e.target.value) })}
            className="w-32"
          />
          <p className="text-sm text-muted-foreground">
            Maximum number of turns before ending
          </p>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <Label htmlFor="allowSkip">Allow Skipping Turns</Label>
            <p className="text-sm text-muted-foreground">
              Agents can pass their turn if they have nothing to add
            </p>
          </div>
          <Switch
            id="allowSkip"
            checked={config.allow_skip !== false}
            onCheckedChange={(checked) => updateConfig({ allow_skip: checked })}
          />
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6">
      {mode === 'sequential' && renderSequentialConfig()}
      {mode === 'parallel' && renderParallelConfig()}
      {mode === 'debate' && renderDebateConfig()}
      {mode === 'hierarchical' && renderHierarchicalConfig()}
      {mode === 'round_robin' && renderRoundRobinConfig()}
    </div>
  );
}
