'use client';

import { FileText, ExternalLink, Quote } from 'lucide-react';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { SearchResult } from '@/types';

interface SearchResultViewProps {
  results: SearchResult[];
  loading?: boolean;
}

export function SearchResultView({ results, loading }: SearchResultViewProps) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin h-6 w-6 border-2 border-primary border-t-transparent rounded-full" />
      </div>
    );
  }

  if (results.length === 0) {
    return (
      <div className="text-center py-8">
        <FileText className="h-10 w-10 mx-auto text-muted-foreground/50" />
        <p className="text-sm text-muted-foreground mt-2">No results found</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {results.map((result, index) => (
        <div
          key={`${result.document_id}-${result.chunk_index}`}
          className="border rounded-lg p-4 bg-card"
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <FileText className="h-4 w-4 text-muted-foreground" />
              <span className="font-medium text-sm">{result.document_title}</span>
            </div>
            <Badge variant="secondary" className="text-xs">
              Score: {result.score.toFixed(3)}
            </Badge>
          </div>
          
          <p className="text-sm text-muted-foreground line-clamp-4">
            {result.content}
          </p>
          
          <div className="mt-3 flex items-center gap-2">
            <Button variant="ghost" size="sm" className="h-7 text-xs gap-1">
              <Quote className="h-3 w-3" />
              Chunk {result.chunk_index + 1}
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
}
