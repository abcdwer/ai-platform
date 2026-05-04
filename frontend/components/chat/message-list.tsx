'use client';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark, oneLight } from 'react-syntax-highlighter/dist/cjs/styles/prism';
import { useTheme } from 'next-themes';
import { cn } from '@/lib/utils';
import { Bot, User, Copy, Check, RefreshCw, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useState, useEffect } from 'react';
import type { Message } from '@/types';

interface MessageListProps {
  messages: Message[];
  streamingContent?: string;
  isStreaming?: boolean;
  onCopy?: (content: string, messageId: string) => void;
  onRegenerate?: () => void;
  copiedMessageId?: string | null;
}

export function MessageList({
  messages,
  streamingContent,
  isStreaming,
  onCopy,
  onRegenerate,
  copiedMessageId,
}: MessageListProps) {
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === 'dark';

  return (
    <ScrollArea className="flex-1">
      <div className="max-w-4xl mx-auto p-4 space-y-6">
        {messages.map((message, index) => (
          <MessageItem
            key={message.id}
            message={message}
            isFirst={index === 0}
            isLast={index === messages.length - 1}
            isStreaming={isStreaming && index === messages.length - 1}
            onCopy={onCopy}
            copiedMessageId={copiedMessageId}
          />
        ))}
        
        {/* Streaming indicator */}
        {isStreaming && streamingContent && (
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-9 h-9 rounded-full bg-primary flex items-center justify-center">
              <Bot className="w-5 h-5 text-primary-foreground" />
            </div>
            <div className="flex-1 space-y-2">
              <div className="rounded-lg px-4 py-3 bg-muted">
                <StreamingContent content={streamingContent} isDark={isDark} />
                <span className="inline-block w-2 h-4 bg-primary animate-pulse ml-1" />
              </div>
            </div>
          </div>
        )}
        
        {/* Empty state */}
        {!isStreaming && messages.length === 0 && !streamingContent && (
          <EmptyState />
        )}
      </div>
    </ScrollArea>
  );
}

interface MessageItemProps {
  message: Message;
  isFirst?: boolean;
  isLast?: boolean;
  isStreaming?: boolean;
  onCopy?: (content: string, messageId: string) => void;
  copiedMessageId?: string | null;
}

function MessageItem({
  message,
  isFirst,
  isLast,
  isStreaming,
  onCopy,
  copiedMessageId,
}: MessageItemProps) {
  const isUser = message.role === 'user';
  const { resolvedTheme } = useTheme();
  const isDark = resolvedTheme === 'dark';
  
  const [isHovered, setIsHovered] = useState(false);

  return (
    <div
      className={cn('flex gap-3 group', isUser && 'flex-row-reverse')}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      {/* Avatar */}
      <div className={cn(
        'flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center',
        isUser ? 'bg-secondary' : 'bg-primary'
      )}>
        {isUser ? (
          <User className="w-5 h-5 text-secondary-foreground" />
        ) : (
          <Bot className="w-5 h-5 text-primary-foreground" />
        )}
      </div>

      {/* Content */}
      <div className={cn('flex-1 space-y-2 max-w-[85%]', isUser && 'text-right')}>
        <div className={cn(
          'rounded-2xl px-4 py-3 inline-block text-left',
          isUser 
            ? 'bg-primary text-primary-foreground rounded-tr-sm' 
            : 'bg-muted rounded-tl-sm'
        )}>
          {message.role === 'tool' ? (
            <div className="text-sm">
              <div className="font-medium mb-1 text-xs opacity-70">
                Tool: {message.name || 'Unknown'}
              </div>
              <pre className="whitespace-pre-wrap text-xs bg-black/20 rounded p-2 mt-1 overflow-x-auto">
                {message.content}
              </pre>
            </div>
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ node, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '');
                    const isInline = !match && !className;
                    
                    return !isInline && match ? (
                      <CodeBlock
                        code={String(children).replace(/\n$/, '')}
                        language={match[1]}
                        isDark={isDark}
                      />
                    ) : (
                      <code
                        className={cn(
                          'bg-black/10 dark:bg-white/10 px-1.5 py-0.5 rounded text-sm',
                          className
                        )}
                        {...props}
                      >
                        {children}
                      </code>
                    );
                  },
                  pre({ children }) {
                    return <>{children}</>;
                  },
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {/* Message actions */}
        {isLast && !isUser && (
          <div className={cn(
            'flex items-center gap-1 transition-opacity',
            isHovered ? 'opacity-100' : 'opacity-0'
          )}>
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7"
              onClick={() => onCopy?.(message.content, message.id)}
            >
              {copiedMessageId === message.id ? (
                <Check className="h-3.5 w-3.5 text-green-500" />
              ) : (
                <Copy className="h-3.5 w-3.5" />
              )}
            </Button>
          </div>
        )}

        {/* Timestamp */}
        <div className="text-xs text-muted-foreground px-1">
          {new Date(message.created_at).toLocaleTimeString([], { 
            hour: '2-digit', 
            minute: '2-digit' 
          })}
        </div>
      </div>
    </div>
  );
}

// Code block with copy button
interface CodeBlockProps {
  code: string;
  language: string;
  isDark: boolean;
}

function CodeBlock({ code, language, isDark }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative group/code my-3">
      <div className="absolute top-2 right-2 opacity-0 group-hover/code:opacity-100 transition-opacity z-10">
        <Button
          variant="secondary"
          size="sm"
          className="h-7 gap-1.5 bg-background/80 backdrop-blur-sm hover:bg-background"
          onClick={handleCopy}
        >
          {copied ? (
            <>
              <Check className="h-3.5 w-3.5" />
              Copied
            </>
          ) : (
            <>
              <Copy className="h-3.5 w-3.5" />
              Copy
            </>
          )}
        </Button>
      </div>
      <div className="absolute top-0 left-0 px-3 py-1 text-xs font-mono text-muted-foreground bg-background/80 rounded-tl-md rounded-br-md">
        {language}
      </div>
      <SyntaxHighlighter
        style={isDark ? oneDark : oneLight}
        language={language}
        PreTag="div"
        className="!rounded-md !mt-0 !bg-zinc-900 dark:!bg-zinc-950"
        showLineNumbers
        lineNumberStyle={{
          minWidth: '2.5em',
          paddingRight: '1em',
          color: isDark ? '#6b7280' : '#9ca3af',
          userSelect: 'none',
        }}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  );
}

// Streaming content component
function StreamingContent({ content, isDark }: { content: string; isDark: boolean }) {
  return (
    <div className="prose prose-sm dark:prose-invert max-w-none">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ node, className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '');
            const isInline = !match && !className;
            
            return !isInline && match ? (
              <CodeBlock
                code={String(children).replace(/\n$/, '')}
                language={match[1]}
                isDark={isDark}
              />
            ) : (
              <code
                className={cn(
                  'bg-black/10 dark:bg-white/10 px-1.5 py-0.5 rounded text-sm',
                  className
                )}
                {...props}
              >
                {children}
              </code>
            );
          },
          pre({ children }) {
            return <>{children}</>;
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

// Empty state component
function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
        <Bot className="w-8 h-8 text-primary" />
      </div>
      <h2 className="text-xl font-semibold mb-2">Start a conversation</h2>
      <p className="text-muted-foreground max-w-md mb-6">
        Send a message to begin chatting with the AI. Select a model from the dropdown 
        above or choose an agent for specialized assistance.
      </p>
      
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-md">
        <QuickAction
          title="Explain code"
          description="Help me understand this"
          icon="💻"
        />
        <QuickAction
          title="Write email"
          description="Professional templates"
          icon="📧"
        />
        <QuickAction
          title="Brainstorm ideas"
          description="Creative thinking"
          icon="💡"
        />
        <QuickAction
          title="Summarize text"
          description="Quick summary"
          icon="📝"
        />
      </div>
    </div>
  );
}

interface QuickActionProps {
  title: string;
  description: string;
  icon: string;
}

function QuickAction({ title, description, icon }: QuickActionProps) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-lg border bg-card hover:bg-accent cursor-pointer transition-colors">
      <span className="text-2xl">{icon}</span>
      <div>
        <div className="font-medium text-sm">{title}</div>
        <div className="text-xs text-muted-foreground">{description}</div>
      </div>
    </div>
  );
}
