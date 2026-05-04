'use client';

import { useState } from 'react';
import { ChevronDown, ChevronUp, FileText, Quote } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { RAGSource } from '@/types';

interface CitationProps {
  sources: RAGSource[];
}

export function Citation({ sources }: CitationProps) {
  const [expanded, setExpanded] = useState(false);

  if (sources.length === 0) return null;

  return (
    <Card className="mt-4 bg-muted/50">
      <CardContent className="p-3">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center justify-between w-full text-sm font-medium"
        >
          <div className="flex items-center gap-2">
            <Quote className="h-4 w-4 text-muted-foreground" />
            <span>Sources ({sources.length})</span>
          </div>
          {expanded ? (
            <ChevronUp className="h-4 w-4 text-muted-foreground" />
          ) : (
            <ChevronDown className="h-4 w-4 text-muted-foreground" />
          )}
        </button>

        {expanded && (
          <div className="mt-3 space-y-3">
            {sources.map((source, index) => (
              <div
                key={`${source.document_id}-${index}`}
                className="p-3 rounded-lg bg-background border"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                    <span className="text-sm font-medium">{source.document_title}</span>
                  </div>
                  <Badge variant="outline" className="text-xs">
                    {source.score.toFixed(2)}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground line-clamp-3">
                  {source.content}
                </p>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
