'use client';

import Link from 'next/link';
import { MessageSquare, Pin, Trash2, MoreHorizontal } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Conversation } from '@/types';
import { useChatStore } from '@/stores';
import { useState } from 'react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface ConversationListProps {
  conversations: Conversation[];
  currentConversationId?: string;
  onSelect?: (id: string) => void;
}

export function ConversationList({
  conversations,
  currentConversationId,
  onSelect,
}: ConversationListProps) {
  const { deleteConversation, updateConversation } = useChatStore();

  const handleDelete = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (confirm('Are you sure you want to delete this conversation?')) {
      await fetch(`/api/conversations/${id}`, { method: 'DELETE' });
      deleteConversation(id);
    }
  };

  const handlePin = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    // TODO: Implement pin toggle
  };

  return (
    <div className="space-y-1 p-2">
      {conversations.length === 0 ? (
        <div className="p-4 text-center text-sm text-muted-foreground">
          No conversations yet
        </div>
      ) : (
        conversations.map((conversation) => (
          <div
            key={conversation.id}
            className={cn(
              'group flex items-center gap-2 p-2 rounded-md cursor-pointer transition-colors',
              currentConversationId === conversation.id
                ? 'bg-accent'
                : 'hover:bg-muted'
            )}
            onClick={() => onSelect?.(conversation.id)}
          >
            <MessageSquare className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-1">
                {conversation.is_pinned && (
                  <Pin className="h-3 w-3 text-muted-foreground flex-shrink-0" />
                )}
                <span className="text-sm truncate">
                  {conversation.title || 'New conversation'}
                </span>
              </div>
              <div className="text-xs text-muted-foreground truncate">
                {new Date(conversation.updated_at).toLocaleDateString()}
              </div>
            </div>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 opacity-0 group-hover:opacity-100"
                >
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={(e) => handlePin(e, conversation.id)}>
                  <Pin className="h-4 w-4 mr-2" />
                  {conversation.is_pinned ? 'Unpin' : 'Pin'}
                </DropdownMenuItem>
                <DropdownMenuItem
                  onClick={(e) => handleDelete(e, conversation.id)}
                  className="text-destructive"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        ))
      )}
    </div>
  );
}
