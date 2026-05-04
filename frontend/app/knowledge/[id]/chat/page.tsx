'use client';

import { useState, useEffect, useRef } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { 
  ArrowLeft, 
  Database, 
  Send, 
  Loader2,
  Trash2,
  Settings,
  MessageSquare,
  Copy,
  Check
} from 'lucide-react';
import { Sidebar } from '@/components/sidebar';
import { Citation } from '@/components/knowledge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useKnowledgeStore } from '@/stores';
import { cn } from '@/lib/utils';

export default function KnowledgeChatPage() {
  const params = useParams();
  const kbId = params.id as string;
  
  const [input, setInput] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  
  const {
    currentKnowledgeBase,
    chatMessages,
    isChatting,
    streamingContent,
    chatError,
    loadKnowledgeBase,
    sendRAGMessage,
    clearChat,
  } = useKnowledgeStore();

  useEffect(() => {
    if (kbId) {
      loadKnowledgeBase(kbId);
    }
  }, [kbId, loadKnowledgeBase]);

  useEffect(() => {
    // Scroll to bottom on new messages
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [chatMessages, streamingContent]);

  const handleSend = async () => {
    if (!input.trim() || isChatting) return;
    
    const message = input.trim();
    setInput('');
    
    await sendRAGMessage(kbId, message);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleCopy = (content: string, id: string) => {
    navigator.clipboard.writeText(content);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  if (!currentKnowledgeBase) {
    return (
      <div className="flex h-screen">
        <Sidebar />
        <main className="flex-1 flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </main>
      </div>
    );
  }

  const readyDocs = currentKnowledgeBase.document_count;

  return (
    <div className="flex h-screen">
      <Sidebar />
      
      <main className="flex-1 flex flex-col">
        {/* Header */}
        <div className="border-b p-4">
          <div className="max-w-4xl mx-auto flex items-center gap-4">
            <Button variant="ghost" size="icon" asChild>
              <Link href={`/knowledge/${kbId}`}>
                <ArrowLeft className="h-5 w-5" />
              </Link>
            </Button>
            <div className="flex-1">
              <h1 className="text-xl font-bold flex items-center gap-2">
                <MessageSquare className="h-5 w-5" />
                Chat with {currentKnowledgeBase.name}
              </h1>
              <p className="text-sm text-muted-foreground">
                {readyDocs} documents indexed • {currentKnowledgeBase.vector_count} vectors
              </p>
            </div>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={clearChat}
              disabled={chatMessages.length === 0}
              className="gap-2"
            >
              <Trash2 className="h-4 w-4" />
              Clear
            </Button>
          </div>
        </div>

        {/* Chat Area */}
        <div className="flex-1 overflow-hidden">
          <div className="h-full max-w-4xl mx-auto flex flex-col">
            <ScrollArea className="flex-1 p-4" ref={scrollRef}>
              {chatMessages.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center">
                  <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mb-4">
                    <Database className="h-8 w-8 text-primary" />
                  </div>
                  <h2 className="text-xl font-semibold mb-2">
                    Ask questions about your documents
                  </h2>
                  <p className="text-muted-foreground max-w-md">
                    I&apos;ll search through your knowledge base and provide answers 
                    with citations to the source documents.
                  </p>
                </div>
              ) : (
                <div className="space-y-6">
                  {chatMessages.map((msg, index) => (
                    <div key={index} className="space-y-2">
                      <div className={cn(
                        'flex gap-3',
                        msg.role === 'user' ? 'justify-end' : 'justify-start'
                      )}>
                        <div className={cn(
                          'max-w-[80%] rounded-lg px-4 py-3',
                          msg.role === 'user' 
                            ? 'bg-primary text-primary-foreground' 
                            : 'bg-muted'
                        )}>
                          <p className="whitespace-pre-wrap">{msg.content}</p>
                          {msg.role === 'assistant' && (
                            <div className="flex items-center gap-1 mt-2">
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-7 text-xs gap-1"
                                onClick={() => handleCopy(msg.content, `msg-${index}`)}
                              >
                                {copiedId === `msg-${index}` ? (
                                  <Check className="h-3 w-3" />
                                ) : (
                                  <Copy className="h-3 w-3" />
                                )}
                                Copy
                              </Button>
                            </div>
                          )}
                        </div>
                      </div>
                      
                      {/* Sources for assistant messages */}
                      {msg.role === 'assistant' && msg.sources && (
                        <Citation sources={msg.sources} />
                      )}
                    </div>
                  ))}
                  
                  {/* Streaming content */}
                  {streamingContent && (
                    <div className="flex gap-3 justify-start">
                      <div className="max-w-[80%] rounded-lg px-4 py-3 bg-muted">
                        <p className="whitespace-pre-wrap">{streamingContent}</p>
                        <span className="inline-block w-2 h-4 bg-primary animate-pulse ml-1" />
                      </div>
                    </div>
                  )}
                  
                  {/* Error */}
                  {chatError && (
                    <div className="p-3 rounded-lg bg-destructive/10 text-destructive text-sm">
                      Error: {chatError}
                    </div>
                  )}
                </div>
              )}
            </ScrollArea>

            {/* Input Area */}
            <div className="border-t p-4">
              <div className="max-w-4xl mx-auto">
                <div className="flex gap-2">
                  <Input
                    placeholder={`Ask about ${currentKnowledgeBase.name}...`}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={isChatting}
                    className="flex-1"
                  />
                  <Button 
                    onClick={handleSend} 
                    disabled={!input.trim() || isChatting}
                    className="gap-2"
                  >
                    {isChatting ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Send className="h-4 w-4" />
                    )}
                    Send
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground mt-2 text-center">
                  Press Enter to send • Shift+Enter for new line
                </p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
