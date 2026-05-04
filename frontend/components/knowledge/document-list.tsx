'use client';

import { FileText, ExternalLink, Trash2, MoreVertical, Loader2, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import type { Document } from '@/types';

interface DocumentListProps {
  documents: Document[];
  loading: boolean;
  onDelete: (docId: string) => void;
}

const statusConfig = {
  uploading: { label: 'Uploading', icon: Loader2, color: 'text-blue-500', bg: 'bg-blue-500/10' },
  parsing: { label: 'Parsing', icon: Loader2, color: 'text-yellow-500', bg: 'bg-yellow-500/10' },
  embedding: { label: 'Embedding', icon: Loader2, color: 'text-purple-500', bg: 'bg-purple-500/10' },
  ready: { label: 'Ready', icon: CheckCircle, color: 'text-green-500', bg: 'bg-green-500/10' },
  error: { label: 'Error', icon: XCircle, color: 'text-red-500', bg: 'bg-red-500/10' },
};

const contentTypeLabels: Record<string, string> = {
  pdf: 'PDF',
  docx: 'Word',
  txt: 'Text',
  md: 'Markdown',
  csv: 'CSV',
  html: 'HTML',
  url: 'URL',
};

export function DocumentList({ documents, loading, onDelete }: DocumentListProps) {
  const formatSize = (bytes?: number) => {
    if (!bytes) return '-';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (documents.length === 0) {
    return (
      <div className="text-center py-12 border rounded-lg">
        <FileText className="h-12 w-12 mx-auto text-muted-foreground/50" />
        <h3 className="mt-4 text-lg font-medium">No documents yet</h3>
        <p className="text-sm text-muted-foreground mt-1">
          Upload documents or add URLs to get started.
        </p>
      </div>
    );
  }

  return (
    <ScrollArea className="h-[500px]">
      <div className="space-y-2">
        {documents.map((doc) => {
          const status = statusConfig[doc.status] || statusConfig.uploading;
          const StatusIcon = status.icon;
          const isProcessing = ['uploading', 'parsing', 'embedding'].includes(doc.status);

          return (
            <div
              key={doc.id}
              className="flex items-center gap-4 p-4 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
            >
              <div className="w-10 h-10 rounded-lg bg-muted flex items-center justify-center flex-shrink-0">
                <FileText className="h-5 w-5 text-muted-foreground" />
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="font-medium truncate">{doc.title}</p>
                  <Badge variant="outline" className="text-xs">
                    {contentTypeLabels[doc.content_type] || doc.content_type}
                  </Badge>
                </div>
                <div className="flex items-center gap-3 text-xs text-muted-foreground mt-1">
                  <span>{formatSize(doc.file_size)}</span>
                  <span>•</span>
                  <span>{doc.chunk_count} chunks</span>
                  <span>•</span>
                  <span>{formatDate(doc.created_at)}</span>
                </div>
                {doc.status === 'error' && doc.error_message && (
                  <p className="text-xs text-destructive mt-1 flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
                    {doc.error_message}
                  </p>
                )}
              </div>

              <div className="flex items-center gap-2">
                <div className={`flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium ${status.bg} ${status.color}`}>
                  <StatusIcon className={`h-3.5 w-3.5 ${isProcessing ? 'animate-spin' : ''}`} />
                  {status.label}
                </div>

                {doc.status === 'ready' && (
                  <Button variant="ghost" size="icon" className="h-8 w-8" asChild>
                    <a href={doc.url || doc.file_path || '#'} target="_blank" rel="noopener noreferrer">
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  </Button>
                )}

                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon" className="h-8 w-8">
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem
                      className="text-destructive focus:text-destructive"
                      onClick={() => onDelete(doc.id)}
                    >
                      <Trash2 className="mr-2 h-4 w-4" />
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
          );
        })}
      </div>
    </ScrollArea>
  );
}
