'use client';

import * as React from 'react';
import { useRouter } from 'next/navigation';
import { Dialog, DialogContent } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Search,
  MessageSquare,
  Database,
  Workflow,
  Bot,
  Users,
  Loader2,
  ArrowRight,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface SearchResult {
  id: string;
  type: 'conversation' | 'knowledge' | 'workflow' | 'agent' | 'multi_agent';
  title: string;
  description?: string;
  icon: React.ReactNode;
  href: string;
}

const typeIcons: Record<string, React.ReactNode> = {
  conversation: <MessageSquare className="h-4 w-4" />,
  knowledge: <Database className="h-4 w-4" />,
  workflow: <Workflow className="h-4 w-4" />,
  agent: <Bot className="h-4 w-4" />,
  multi_agent: <Users className="h-4 w-4" />,
};

const typeLabels: Record<string, string> = {
  conversation: 'Conversation',
  knowledge: 'Knowledge Base',
  workflow: 'Workflow',
  agent: 'Agent',
  multi_agent: 'Multi-Agent',
};

export function GlobalSearch() {
  const router = useRouter();
  const [isOpen, setIsOpen] = React.useState(false);
  const [query, setQuery] = React.useState('');
  const [results, setResults] = React.useState<SearchResult[]>([]);
  const [isLoading, setIsLoading] = React.useState(false);
  const [selectedIndex, setSelectedIndex] = React.useState(0);
  const inputRef = React.useRef<HTMLInputElement>(null);

  // Handle keyboard shortcut (Cmd/Ctrl + K)
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setIsOpen(true);
      }
      if (e.key === 'Escape') {
        setIsOpen(false);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Focus input when dialog opens
  React.useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 0);
    } else {
      setQuery('');
      setResults([]);
      setSelectedIndex(0);
    }
  }, [isOpen]);

  // Search as user types
  React.useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }

    const searchTimer = setTimeout(async () => {
      setIsLoading(true);
      try {
        // Search across all resources
        const [conversations, knowledge, workflows, agents] = await Promise.all([
          fetch(`/api/conversations?search=${encodeURIComponent(query)}`).then(r => r.ok ? r.json() : []).catch(() => []),
          fetch(`/api/knowledge?search=${encodeURIComponent(query)}`).then(r => r.ok ? r.json() : []).catch(() => []),
          fetch(`/api/workflows?search=${encodeURIComponent(query)}`).then(r => r.ok ? r.json() : []).catch(() => []),
          fetch(`/api/agents?search=${encodeURIComponent(query)}`).then(r => r.ok ? r.json() : []).catch(() => []),
        ]);

        const searchResults: SearchResult[] = [];

        // Format conversations
        if (Array.isArray(conversations)) {
          conversations.forEach((c: any) => {
            searchResults.push({
              id: c.id,
              type: 'conversation',
              title: c.title || 'Untitled',
              description: `Chat • ${new Date(c.updated_at).toLocaleDateString()}`,
              icon: typeIcons.conversation,
              href: `/chat?conversation=${c.id}`,
            });
          });
        }

        // Format knowledge bases
        if (Array.isArray(knowledge)) {
          knowledge.forEach((k: any) => {
            searchResults.push({
              id: k.id,
              type: 'knowledge',
              title: k.name,
              description: k.description || typeLabels.knowledge,
              icon: typeIcons.knowledge,
              href: `/knowledge/${k.id}`,
            });
          });
        }

        // Format workflows
        if (Array.isArray(workflows)) {
          workflows.forEach((w: any) => {
            searchResults.push({
              id: w.id,
              type: 'workflow',
              title: w.name,
              description: w.description || typeLabels.workflow,
              icon: typeIcons.workflow,
              href: `/workflows/${w.id}/edit`,
            });
          });
        }

        // Format agents
        if (Array.isArray(agents)) {
          agents.forEach((a: any) => {
            searchResults.push({
              id: a.id,
              type: 'agent',
              title: a.name,
              description: a.description || typeLabels.agent,
              icon: typeIcons.agent,
              href: `/agents`,
            });
          });
        }

        setResults(searchResults.slice(0, 10));
        setSelectedIndex(0);
      } catch (error) {
        console.error('Search failed:', error);
      } finally {
        setIsLoading(false);
      }
    }, 300);

    return () => clearTimeout(searchTimer);
  }, [query]);

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => Math.min(prev + 1, results.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => Math.max(prev - 1, 0));
    } else if (e.key === 'Enter' && results[selectedIndex]) {
      e.preventDefault();
      handleSelect(results[selectedIndex]);
    }
  };

  const handleSelect = (result: SearchResult) => {
    router.push(result.href);
    setIsOpen(false);
  };

  return (
    <>
      {/* Search trigger button */}
      <Button
        variant="outline"
        className="relative h-9 w-full justify-start text-sm text-muted-foreground sm:pr-12"
        onClick={() => setIsOpen(true)}
      >
        <Search className="mr-2 h-4 w-4" />
        <span className="hidden sm:inline-flex">Search...</span>
        <kbd className="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 hidden h-5 select-none items-center gap-1 rounded border bg-muted px-1.5 font-mono text-[10px] font-medium sm:flex">
          <span className="text-xs">⌘</span>K
        </kbd>
      </Button>

      {/* Search dialog */}
      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="p-0 gap-0 sm:max-w-[600px]">
          <div className="flex items-center border-b px-3">
            <Search className="mr-2 h-4 w-4 shrink-0 text-muted-foreground" />
            <Input
              ref={inputRef}
              placeholder="Search conversations, knowledge bases, workflows..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              className="border-0 h-12 focus-visible:ring-0 focus-visible:ring-offset-0"
            />
            {isLoading && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
          </div>

          {/* Results */}
          <div className="max-h-[400px] overflow-y-auto p-2">
            {query && results.length === 0 && !isLoading && (
              <div className="p-4 text-center text-sm text-muted-foreground">
                No results found for &quot;{query}&quot;
              </div>
            )}

            {!query && (
              <div className="p-4 text-center text-sm text-muted-foreground">
                <p>Start typing to search...</p>
                <p className="mt-2 text-xs">
                  Search across conversations, knowledge bases, workflows, and agents
                </p>
              </div>
            )}

            {results.length > 0 && (
              <div className="space-y-1">
                {results.map((result, index) => (
                  <button
                    key={`${result.type}-${result.id}`}
                    onClick={() => handleSelect(result)}
                    onMouseEnter={() => setSelectedIndex(index)}
                    className={cn(
                      'flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left transition-colors',
                      selectedIndex === index
                        ? 'bg-accent text-accent-foreground'
                        : 'hover:bg-accent/50'
                    )}
                  >
                    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-muted">
                      {result.icon}
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{result.title}</p>
                      <p className="text-xs text-muted-foreground truncate">{result.description}</p>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {typeLabels[result.type]}
                    </span>
                    {selectedIndex === index && (
                      <ArrowRight className="h-4 w-4 text-muted-foreground" />
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between border-t px-3 py-2 text-xs text-muted-foreground">
            <div className="flex items-center gap-2">
              <kbd className="rounded border bg-muted px-1.5 font-mono">↑↓</kbd>
              <span>Navigate</span>
              <kbd className="rounded border bg-muted px-1.5 font-mono">↵</kbd>
              <span>Select</span>
              <kbd className="rounded border bg-muted px-1.5 font-mono">esc</kbd>
              <span>Close</span>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
