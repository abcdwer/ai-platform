'use client';

import { useEffect, useState, useRef } from 'react';
import { Sidebar } from '@/components/sidebar';
import { MessageList } from '@/components/chat/message-list';
import { ChatInput } from '@/components/chat/chat-input';
import { ModelSelector } from '@/components/chat/model-selector';
import { AgentSelector } from '@/components/chat/agent-selector';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Plus,
  PanelLeft,
  Search,
  MoreHorizontal,
  Pin,
  Trash2,
  Edit3,
  Check,
  X,
  Copy,
  RefreshCw,
  Loader2,
  Sparkles,
  Download,
} from 'lucide-react';
import { useChatStore, useModelStore, useAgentStore } from '@/stores';
import { cn } from '@/lib/utils';
import { useToast } from '@/components/ui/use-toast';
import { ExportConversationDialog } from '@/components/export-dialog';
import type { Conversation, Message } from '@/types';

export default function ChatPage() {
  const [showSidebar, setShowSidebar] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const [showExportDialog, setShowExportDialog] = useState(false);
  
  const { toast } = useToast();
  
  const {
    messages,
    isStreaming,
    streamingContent,
    selectedModel,
    selectedProvider,
    availableModels,
    currentConversation,
    conversations,
    selectedAgent,
    setSelectedModel,
    setSelectedProvider,
    setAvailableModels,
    setSelectedAgent,
    sendMessage,
    loadConversations,
    loadConversation,
    createNewConversation,
    regenerateMessage,
    updateConversationTitle,
    deleteConversation,
    togglePinConversation,
  } = useChatStore();

  const { loadModels } = useModelStore();
  const { agents, loadAgents } = useAgentStore();

  useEffect(() => {
    loadModels();
    loadConversations();
    loadAgents();
  }, [loadModels, loadConversations, loadAgents]);

  const handleSendMessage = async (content: string) => {
    await sendMessage(content);
  };

  const handleSelectConversation = async (id: string) => {
    await loadConversation(id);
  };

  const handleCreateNewConversation = () => {
    createNewConversation();
  };

  const handleDeleteConversation = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    try {
      await deleteConversation(id);
      toast({
        title: 'Conversation deleted',
        description: 'The conversation has been successfully deleted.',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete the conversation.',
        variant: 'destructive',
      });
    }
  };

  const handleTogglePin = async (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    try {
      await togglePinConversation(id);
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to pin/unpin the conversation.',
        variant: 'destructive',
      });
    }
  };

  const handleStartEdit = (e: React.MouseEvent, conversation: Conversation) => {
    e.stopPropagation();
    setEditingId(conversation.id);
    setEditTitle(conversation.title);
  };

  const handleSaveEdit = async (id: string) => {
    if (editTitle.trim()) {
      await updateConversationTitle(id, editTitle.trim());
    }
    setEditingId(null);
    setEditTitle('');
  };

  const handleCancelEdit = () => {
    setEditingId(null);
    setEditTitle('');
  };

  const handleCopyMessage = async (content: string, messageId: string) => {
    try {
      await navigator.clipboard.writeText(content);
      setCopiedMessageId(messageId);
      setTimeout(() => setCopiedMessageId(null), 2000);
      toast({
        title: 'Copied',
        description: 'Message copied to clipboard.',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to copy message.',
        variant: 'destructive',
      });
    }
  };

  const handleRegenerate = async () => {
    if (messages.length > 0) {
      await regenerateMessage();
    }
  };

  const handleExportConversation = async (format: string) => {
    if (!currentConversation) return;
    
    const response = await fetch(
      `/api/conversations/${currentConversation.id}/export?format=${format}`
    );
    
    if (!response.ok) {
      throw new Error('Export failed');
    }
    
    const blob = await response.blob();
    const contentDisposition = response.headers.get('Content-Disposition');
    let filename = `conversation_${currentConversation.title}.${format}`;
    if (contentDisposition) {
      const match = contentDisposition.match(/filename=(.+)/);
      if (match) {
        filename = match[1].replace(/"/g, '');
      }
    }
    
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  // Filter conversations by search
  const filteredConversations = conversations.filter((c) =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Separate pinned and regular conversations
  const pinnedConversations = filteredConversations.filter((c) => c.is_pinned);
  const regularConversations = filteredConversations.filter((c) => !c.is_pinned);

  return (
    <div className="flex h-screen">
      {/* Sidebar */}
      {showSidebar && (
        <div className="w-80 border-r bg-card flex flex-col">
          {/* New Chat Button */}
          <div className="p-4 border-b space-y-3">
            <Button
              variant="outline"
              className="w-full justify-start gap-2"
              onClick={handleCreateNewConversation}
            >
              <Plus className="h-4 w-4" />
              New Chat
            </Button>
            
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search conversations..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9 h-9"
              />
            </div>
          </div>

          {/* Conversation List */}
          <ScrollArea className="flex-1">
            <div className="p-2 space-y-4">
              {/* Pinned Conversations */}
              {pinnedConversations.length > 0 && (
                <div className="space-y-1">
                  <div className="px-2 py-1 text-xs font-semibold text-muted-foreground uppercase flex items-center gap-1">
                    <Pin className="h-3 w-3" />
                    Pinned
                  </div>
                  {pinnedConversations.map((conversation) => (
                    <ConversationItem
                      key={conversation.id}
                      conversation={conversation}
                      isActive={currentConversation?.id === conversation.id}
                      isEditing={editingId === conversation.id}
                      editTitle={editTitle}
                      onSelect={handleSelectConversation}
                      onDelete={handleDeleteConversation}
                      onTogglePin={handleTogglePin}
                      onStartEdit={handleStartEdit}
                      onSaveEdit={handleSaveEdit}
                      onCancelEdit={handleCancelEdit}
                      onEditTitleChange={setEditTitle}
                    />
                  ))}
                </div>
              )}

              {/* Regular Conversations */}
              <div className="space-y-1">
                {pinnedConversations.length > 0 && (
                  <div className="px-2 py-1 text-xs font-semibold text-muted-foreground uppercase">
                    Recent
                  </div>
                )}
                {regularConversations.length === 0 && pinnedConversations.length === 0 ? (
                  <div className="p-4 text-center text-sm text-muted-foreground">
                    {searchQuery ? 'No conversations found' : 'No conversations yet'}
                  </div>
                ) : (
                  regularConversations.map((conversation) => (
                    <ConversationItem
                      key={conversation.id}
                      conversation={conversation}
                      isActive={currentConversation?.id === conversation.id}
                      isEditing={editingId === conversation.id}
                      editTitle={editTitle}
                      onSelect={handleSelectConversation}
                      onDelete={handleDeleteConversation}
                      onTogglePin={handleTogglePin}
                      onStartEdit={handleStartEdit}
                      onSaveEdit={handleSaveEdit}
                      onCancelEdit={handleCancelEdit}
                      onEditTitleChange={setEditTitle}
                    />
                  ))
                )}
              </div>
            </div>
          </ScrollArea>
        </div>
      )}

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="h-14 border-b bg-card flex items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setShowSidebar(!showSidebar)}
              className="md:hidden"
            >
              <PanelLeft className="h-5 w-5" />
            </Button>
            
            {editingId === currentConversation?.id ? (
              <div className="flex items-center gap-2">
                <Input
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  className="h-8 w-64"
                  autoFocus
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleSaveEdit(currentConversation!.id);
                    if (e.key === 'Escape') handleCancelEdit();
                  }}
                />
                <Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => handleSaveEdit(currentConversation!.id)}>
                  <Check className="h-4 w-4" />
                </Button>
                <Button size="icon" variant="ghost" className="h-8 w-8" onClick={handleCancelEdit}>
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <h1 className="font-semibold text-lg">
                  {currentConversation?.title || 'New Chat'}
                </h1>
                {currentConversation && (
                  <Button
                    size="icon"
                    variant="ghost"
                    className="h-8 w-8 opacity-0 group-hover:opacity-100 hover:opacity-100"
                    onClick={(e) => handleStartEdit(e, currentConversation)}
                  >
                    <Edit3 className="h-4 w-4" />
                  </Button>
                )}
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            {/* Agent Selector */}
            <AgentSelector
              agents={agents}
              selectedAgent={selectedAgent}
              onAgentChange={setSelectedAgent}
            />
            
            {/* Model Selector */}
            <ModelSelector
              models={availableModels}
              selectedModel={selectedModel}
              selectedProvider={selectedProvider}
              onModelChange={setSelectedModel}
              onProviderChange={setSelectedProvider}
            />

            {/* Export Button */}
            {currentConversation && (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setShowExportDialog(true)}
                title="Export conversation"
              >
                <Download className="h-4 w-4" />
              </Button>
            )}
          </div>
        </header>

        {/* Messages */}
        <MessageList
          messages={messages}
          streamingContent={streamingContent}
          isStreaming={isStreaming}
          onCopy={handleCopyMessage}
          onRegenerate={handleRegenerate}
          copiedMessageId={copiedMessageId}
        />

        {/* Input */}
        <div className="border-t bg-card">
          <ChatInput
            onSend={handleSendMessage}
            isLoading={isStreaming}
            disabled={!selectedModel}
          />
          
          {/* Message Actions */}
          {messages.length > 0 && !isStreaming && (
            <div className="px-4 pb-3 flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                className="h-8 text-muted-foreground"
                onClick={handleRegenerate}
              >
                <RefreshCw className="h-4 w-4 mr-1" />
                Regenerate
              </Button>
              <Button
                variant="ghost"
                size="sm"
                className="h-8 text-muted-foreground"
                onClick={() => handleCopyMessage(messages[messages.length - 1]?.content || '', messages[messages.length - 1]?.id || '')}
              >
                <Copy className="h-4 w-4 mr-1" />
                Copy
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Export Dialog */}
      <ExportConversationDialog
        open={showExportDialog}
        onOpenChange={setShowExportDialog}
        conversationId={currentConversation?.id || ''}
        conversationTitle={currentConversation?.title || 'Conversation'}
        onExport={handleExportConversation}
      />
    </div>
  );
}

// Conversation Item Component
interface ConversationItemProps {
  conversation: Conversation;
  isActive: boolean;
  isEditing: boolean;
  editTitle: string;
  onSelect: (id: string) => void;
  onDelete: (e: React.MouseEvent, id: string) => void;
  onTogglePin: (e: React.MouseEvent, id: string) => void;
  onStartEdit: (e: React.MouseEvent, conversation: Conversation) => void;
  onSaveEdit: (id: string) => void;
  onCancelEdit: () => void;
  onEditTitleChange: (title: string) => void;
}

function ConversationItem({
  conversation,
  isActive,
  isEditing,
  editTitle,
  onSelect,
  onDelete,
  onTogglePin,
  onStartEdit,
  onSaveEdit,
  onCancelEdit,
  onEditTitleChange,
}: ConversationItemProps) {
  return (
    <div
      className={cn(
        'group flex items-center gap-2 p-2 rounded-md cursor-pointer transition-colors',
        isActive ? 'bg-accent' : 'hover:bg-muted'
      )}
      onClick={() => !isEditing && onSelect(conversation.id)}
    >
      {isEditing ? (
        <>
          <Input
            value={editTitle}
            onChange={(e) => onEditTitleChange(e.target.value)}
            className="h-7 flex-1"
            autoFocus
            onKeyDown={(e) => {
              if (e.key === 'Enter') onSaveEdit(conversation.id);
              if (e.key === 'Escape') onCancelEdit();
            }}
            onClick={(e) => e.stopPropagation()}
          />
          <Button
            size="icon"
            variant="ghost"
            className="h-7 w-7"
            onClick={(e) => {
              e.stopPropagation();
              onSaveEdit(conversation.id);
            }}
          >
            <Check className="h-3 w-3" />
          </Button>
          <Button
            size="icon"
            variant="ghost"
            className="h-7 w-7"
            onClick={(e) => {
              e.stopPropagation();
              onCancelEdit();
            }}
          >
            <X className="h-3 w-3" />
          </Button>
        </>
      ) : (
        <>
          <div className="flex-shrink-0">
            {conversation.is_pinned ? (
              <Pin className="h-4 w-4 text-muted-foreground" />
            ) : (
              <div className="w-4 h-4" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-sm truncate">{conversation.title || 'New conversation'}</div>
            <div className="text-xs text-muted-foreground truncate">
              {new Date(conversation.updated_at).toLocaleDateString()} · {conversation.model}
            </div>
          </div>
          <div className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
            <Button
              size="icon"
              variant="ghost"
              className="h-7 w-7"
              onClick={(e) => {
                e.stopPropagation();
                onTogglePin(e, conversation.id);
              }}
            >
              {conversation.is_pinned ? (
                <Pin className="h-3 w-3 fill-current" />
              ) : (
                <Pin className="h-3 w-3" />
              )}
            </Button>
            <Button
              size="icon"
              variant="ghost"
              className="h-7 w-7"
              onClick={(e) => {
                e.stopPropagation();
                onStartEdit(e, conversation);
              }}
            >
              <Edit3 className="h-3 w-3" />
            </Button>
            <Button
              size="icon"
              variant="ghost"
              className="h-7 w-7 text-destructive hover:text-destructive"
              onClick={(e) => onDelete(e, conversation.id)}
            >
              <Trash2 className="h-3 w-3" />
            </Button>
          </div>
        </>
      )}
    </div>
  );
}
