'use client';

import { useState } from 'react';
import { Bot, ChevronDown, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { cn } from '@/lib/utils';
import type { Agent } from '@/types';

interface AgentSelectorProps {
  agents: Agent[];
  selectedAgent: Agent | null;
  onAgentChange: (agent: Agent | null) => void;
}

export function AgentSelector({
  agents,
  selectedAgent,
  onAgentChange,
}: AgentSelectorProps) {
  const activeAgents = agents.filter((a) => a.is_active);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" className="gap-2">
          <Bot className="h-4 w-4" />
          <span className="hidden sm:inline">
            {selectedAgent ? selectedAgent.name : 'No Agent'}
          </span>
          <ChevronDown className="h-4 w-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuItem
          onClick={() => onAgentChange(null)}
          className={cn(!selectedAgent && 'bg-accent')}
        >
          <div className="flex items-center gap-2 w-full">
            <Bot className="h-4 w-4 text-muted-foreground" />
            <span className="flex-1">No Agent</span>
            {!selectedAgent && <Check className="h-4 w-4" />}
          </div>
        </DropdownMenuItem>
        
        {activeAgents.length > 0 && (
          <>
            <div className="px-2 py-1.5 text-xs font-semibold text-muted-foreground">
              Agents
            </div>
            {activeAgents.map((agent) => (
              <DropdownMenuItem
                key={agent.id}
                onClick={() => onAgentChange(agent)}
                className={cn(selectedAgent?.id === agent.id && 'bg-accent')}
              >
                <div className="flex items-start gap-2 w-full">
                  <Bot className="h-4 w-4 mt-0.5 text-primary" />
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate">{agent.name}</div>
                    {agent.description && (
                      <div className="text-xs text-muted-foreground truncate">
                        {agent.description}
                      </div>
                    )}
                  </div>
                  {selectedAgent?.id === agent.id && (
                    <Check className="h-4 w-4 flex-shrink-0" />
                  )}
                </div>
              </DropdownMenuItem>
            ))}
          </>
        )}
        
        {activeAgents.length === 0 && (
          <div className="p-4 text-center text-sm text-muted-foreground">
            No agents available
          </div>
        )}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
