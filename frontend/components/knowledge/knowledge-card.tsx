'use client';

import { useState } from 'react';
import { 
  Database, 
  FileText, 
  Tags, 
  MoreVertical,
  Edit3,
  Trash2,
  MessageSquare,
  ExternalLink,
  Plus,
  Settings
} from 'lucide-react';
import Link from 'next/link';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import type { KnowledgeBase } from '@/types';

interface KnowledgeCardProps {
  knowledgeBase: KnowledgeBase;
  onEdit: (kb: KnowledgeBase) => void;
  onDelete: (kb: KnowledgeBase) => void;
}

export function KnowledgeCard({ knowledgeBase, onEdit, onDelete }: KnowledgeCardProps) {
  const {
    id,
    name,
    description,
    document_count,
    vector_count,
    tags,
    embedding_model,
    chunking_strategy,
    created_at,
  } = knowledgeBase;

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return (
    <div className="rounded-lg border bg-card text-card-foreground shadow-sm hover:shadow-md transition-shadow">
      <div className="p-6">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <Database className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h3 className="font-semibold text-lg">{name}</h3>
              <p className="text-sm text-muted-foreground">
                {formatDate(created_at)}
              </p>
            </div>
          </div>
          
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-8 w-8">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onEdit(knowledgeBase)}>
                <Edit3 className="mr-2 h-4 w-4" />
                Edit
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link href={`/knowledge/${id}/chat`}>
                  <MessageSquare className="mr-2 h-4 w-4" />
                  Chat
                </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem 
                className="text-destructive focus:text-destructive"
                onClick={() => onDelete(knowledgeBase)}
              >
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {description && (
          <p className="mt-3 text-sm text-muted-foreground line-clamp-2">
            {description}
          </p>
        )}

        {tags && tags.length > 0 && (
          <div className="mt-3 flex flex-wrap gap-1">
            {tags.slice(0, 3).map((tag) => (
              <Badge key={tag} variant="secondary" className="text-xs">
                <Tags className="mr-1 h-3 w-3" />
                {tag}
              </Badge>
            ))}
            {tags.length > 3 && (
              <Badge variant="secondary" className="text-xs">
                +{tags.length - 3}
              </Badge>
            )}
          </div>
        )}

        <div className="mt-4 grid grid-cols-2 gap-4">
          <div className="flex items-center gap-2 text-sm">
            <FileText className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">Documents:</span>
            <span className="font-medium">{document_count}</span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <Database className="h-4 w-4 text-muted-foreground" />
            <span className="text-muted-foreground">Vectors:</span>
            <span className="font-medium">{vector_count}</span>
          </div>
        </div>

        <div className="mt-4 flex items-center gap-2 text-xs text-muted-foreground">
          <Badge variant="outline" className="text-xs">
            {embedding_model}
          </Badge>
          <Badge variant="outline" className="text-xs">
            {chunking_strategy}
          </Badge>
        </div>
      </div>

      <div className="border-t px-6 py-3 flex items-center justify-between">
        <Link href={`/knowledge/${id}`}>
          <Button variant="ghost" size="sm" className="gap-2">
            <ExternalLink className="h-4 w-4" />
            View Documents
          </Button>
        </Link>
        <Link href={`/knowledge/${id}/chat`}>
          <Button variant="default" size="sm" className="gap-2">
            <MessageSquare className="h-4 w-4" />
            Chat
          </Button>
        </Link>
      </div>
    </div>
  );
}
