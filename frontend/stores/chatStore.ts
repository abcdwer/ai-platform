'use client';

import { create } from 'zustand';
import type { Message, Conversation, ModelInfo, Agent, ChatStreamChunk } from '@/types';

interface ChatState {
  // Current conversation
  currentConversation: Conversation | null;
  conversations: Conversation[];
  
  // Messages
  messages: Message[];
  isLoading: boolean;
  error: string | null;
  
  // Streaming
  streamingContent: string;
  isStreaming: boolean;
  
  // Model selection
  selectedModel: string;
  selectedProvider: string;
  availableModels: ModelInfo[];
  
  // Agent selection
  selectedAgent: Agent | null;
  agents: Agent[];
  
  // Actions
  setCurrentConversation: (conversation: Conversation | null) => void;
  setConversations: (conversations: Conversation[]) => void;
  addConversation: (conversation: Conversation) => void;
  updateConversation: (id: string, updates: Partial<Conversation>) => void;
  deleteConversation: (id: string) => Promise<void>;
  togglePinConversation: (id: string) => Promise<void>;
  updateConversationTitle: (id: string, title: string) => Promise<void>;
  
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;
  updateStreamingContent: (content: string) => void;
  clearStreamingContent: () => void;
  
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  setIsStreaming: (streaming: boolean) => void;
  
  setSelectedModel: (model: string) => void;
  setSelectedProvider: (provider: string) => void;
  setAvailableModels: (models: ModelInfo[]) => void;
  
  setSelectedAgent: (agent: Agent | null) => void;
  setAgents: (agents: Agent[]) => void;
  
  sendMessage: (content: string) => Promise<void>;
  loadConversations: () => Promise<void>;
  loadConversation: (id: string) => Promise<void>;
  createNewConversation: () => void;
  regenerateMessage: () => Promise<void>;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const useChatStore = create<ChatState>((set, get) => ({
  // Initial state
  currentConversation: null,
  conversations: [],
  messages: [],
  isLoading: false,
  error: null,
  streamingContent: '',
  isStreaming: false,
  selectedModel: 'llama2',
  selectedProvider: 'ollama',
  availableModels: [],
  selectedAgent: null,
  agents: [],
  
  // Actions
  setCurrentConversation: (conversation) => {
    set({ 
      currentConversation: conversation,
      messages: conversation?.messages || []
    });
  },
  
  setConversations: (conversations) => set({ conversations }),
  
  addConversation: (conversation) => set((state) => ({
    conversations: [conversation, ...state.conversations]
  })),
  
  updateConversation: (id, updates) => set((state) => ({
    conversations: state.conversations.map((c) =>
      c.id === id ? { ...c, ...updates } : c
    ),
    currentConversation: state.currentConversation?.id === id
      ? { ...state.currentConversation, ...updates }
      : state.currentConversation
  })),
  
  deleteConversation: async (id) => {
    try {
      const response = await fetch(`${API_BASE}/api/conversations/${id}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error('Failed to delete conversation');
      
      set((state) => ({
        conversations: state.conversations.filter((c) => c.id !== id),
        currentConversation: state.currentConversation?.id === id
          ? null
          : state.currentConversation,
        messages: state.currentConversation?.id === id
          ? []
          : state.messages
      }));
    } catch (error) {
      set({ error: (error as Error).message });
      throw error;
    }
  },
  
  togglePinConversation: async (id) => {
    try {
      const response = await fetch(`${API_BASE}/api/conversations/${id}/pin`, {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Failed to toggle pin');
      
      const updated = await response.json();
      set((state) => ({
        conversations: state.conversations.map((c) =>
          c.id === id ? { ...c, is_pinned: updated.is_pinned } : c
        ),
        currentConversation: state.currentConversation?.id === id
          ? { ...state.currentConversation, is_pinned: updated.is_pinned }
          : state.currentConversation
      }));
    } catch (error) {
      set({ error: (error as Error).message });
      throw error;
    }
  },
  
  updateConversationTitle: async (id, title) => {
    try {
      const response = await fetch(`${API_BASE}/api/conversations/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title }),
      });
      if (!response.ok) throw new Error('Failed to update title');
      
      const updated = await response.json();
      set((state) => ({
        conversations: state.conversations.map((c) =>
          c.id === id ? { ...c, title: updated.title } : c
        ),
        currentConversation: state.currentConversation?.id === id
          ? { ...state.currentConversation, title: updated.title }
          : state.currentConversation
      }));
    } catch (error) {
      set({ error: (error as Error).message });
      throw error;
    }
  },
  
  setMessages: (messages) => set({ messages }),
  
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, message]
  })),
  
  updateStreamingContent: (content) => set({ streamingContent: content }),
  
  clearStreamingContent: () => set({ streamingContent: '' }),
  
  setLoading: (loading) => set({ isLoading: loading }),
  
  setError: (error) => set({ error }),
  
  setIsStreaming: (streaming) => set({ isStreaming: streaming }),
  
  setSelectedModel: (model) => set({ selectedModel: model }),
  
  setSelectedProvider: (provider) => set({ selectedProvider: provider }),
  
  setAvailableModels: (models) => set({ availableModels: models }),
  
  setSelectedAgent: (agent) => set({ selectedAgent: agent }),
  
  setAgents: (agents) => set({ agents }),
  
  createNewConversation: () => {
    set({
      currentConversation: null,
      messages: [],
      streamingContent: '',
      error: null,
      selectedAgent: null
    });
  },
  
  loadConversations: async () => {
    try {
      set({ isLoading: true, error: null });
      const response = await fetch(`${API_BASE}/api/conversations`);
      if (!response.ok) throw new Error('Failed to load conversations');
      const data = await response.json();
      set({ conversations: data.items || [] });
    } catch (error) {
      set({ error: (error as Error).message });
      // Provide mock data for demo
      set({ 
        conversations: [
          {
            id: 'demo-1',
            user_id: 'user-1',
            title: 'Welcome to AI Platform',
            model: 'llama2',
            model_provider: 'ollama',
            is_pinned: true,
            is_archived: false,
            messages: [],
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString()
          }
        ] 
      });
    } finally {
      set({ isLoading: false });
    }
  },
  
  loadConversation: async (id) => {
    try {
      set({ isLoading: true, error: null });
      const response = await fetch(`${API_BASE}/api/conversations/${id}`);
      if (!response.ok) throw new Error('Failed to load conversation');
      const conversation = await response.json();
      set({ 
        currentConversation: conversation,
        messages: conversation.messages || []
      });
    } catch (error) {
      set({ error: (error as Error).message });
      // Try to find in local state
      const local = get().conversations.find(c => c.id === id);
      if (local) {
        set({
          currentConversation: local,
          messages: local.messages || []
        });
      }
    } finally {
      set({ isLoading: false });
    }
  },
  
  regenerateMessage: async () => {
    const { messages, selectedModel, selectedProvider, currentConversation, selectedAgent } = get();
    
    // Remove the last assistant message if exists
    const messagesWithoutLastAssistant = messages.filter(
      (m, i) => !(i === messages.length - 1 && m.role === 'assistant')
    );
    
    if (messagesWithoutLastAssistant.length === 0) return;
    
    // Find the last user message
    const lastUserMessage = [...messagesWithoutLastAssistant].reverse().find(m => m.role === 'user');
    if (!lastUserMessage) return;
    
    set({
      messages: messagesWithoutLastAssistant,
      streamingContent: '',
      isStreaming: true,
      error: null
    });
    
    try {
      const response = await fetch(`${API_BASE}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: currentConversation?.id,
          messages: messagesWithoutLastAssistant,
          model: selectedModel,
          model_provider: selectedProvider,
          agent_id: selectedAgent?.id,
          stream: true
        })
      });
      
      if (!response.ok) throw new Error('Failed to regenerate');
      
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let conversationId = currentConversation?.id;
      let fullContent = '';
      
      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);
              if (data === '[DONE]') continue;
              
              try {
                const parsed: ChatStreamChunk = JSON.parse(data);
                
                if (parsed.type === 'conversation_id' && parsed.conversation_id) {
                  conversationId = parsed.conversation_id;
                  // Update current conversation if it's new
                  if (!get().currentConversation) {
                    set((state) => ({
                      currentConversation: {
                        id: parsed.conversation_id!,
                        user_id: 'user-1',
                        title: 'New Chat',
                        model: state.selectedModel,
                        model_provider: state.selectedProvider,
                        is_pinned: false,
                        is_archived: false,
                        messages: [],
                        created_at: new Date().toISOString(),
                        updated_at: new Date().toISOString()
                      }
                    }));
                  }
                } else if (parsed.type === 'message' && parsed.content) {
                  fullContent += parsed.content;
                  set({ streamingContent: fullContent });
                } else if (parsed.type === 'done') {
                  // Add the complete message
                  const assistantMessage: Message = {
                    id: `msg-${Date.now()}`,
                    conversation_id: conversationId || '',
                    role: 'assistant',
                    content: fullContent,
                    created_at: new Date().toISOString()
                  };
                  set((state) => ({
                    messages: [...state.messages, assistantMessage],
                    isStreaming: false,
                    streamingContent: ''
                  }));
                } else if (parsed.type === 'error') {
                  set({ error: parsed.error || 'Unknown error', isStreaming: false });
                }
              } catch (e) {
                // Ignore parse errors for incomplete JSON
              }
            }
          }
        }
      }
    } catch (error) {
      set({ error: (error as Error).message, isStreaming: false });
    }
  },
  
  sendMessage: async (content) => {
    const { messages, selectedModel, selectedProvider, currentConversation, selectedAgent } = get();
    
    const userMessage: Message = {
      id: `temp-${Date.now()}`,
      conversation_id: currentConversation?.id || '',
      role: 'user',
      content,
      created_at: new Date().toISOString()
    };
    
    set((state) => ({
      messages: [...state.messages, userMessage],
      streamingContent: '',
      isStreaming: true,
      error: null
    }));
    
    try {
      const response = await fetch(`${API_BASE}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          conversation_id: currentConversation?.id,
          messages: [...messages, userMessage],
          model: selectedModel,
          model_provider: selectedProvider,
          agent_id: selectedAgent?.id,
          stream: true
        })
      });
      
      if (!response.ok) throw new Error('Failed to send message');
      
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let conversationId = currentConversation?.id;
      let fullContent = '';
      let newTitle = '';
      
      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value);
          const lines = chunk.split('\n');
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const data = line.slice(6);
              if (data === '[DONE]') continue;
              
              try {
                const parsed: ChatStreamChunk = JSON.parse(data);
                
                if (parsed.type === 'conversation_id' && parsed.conversation_id) {
                  conversationId = parsed.conversation_id;
                  // Update current conversation if it's new
                  if (!get().currentConversation) {
                    set((state) => ({
                      currentConversation: {
                        id: parsed.conversation_id!,
                        user_id: 'user-1',
                        title: 'New Chat',
                        model: state.selectedModel,
                        model_provider: state.selectedProvider,
                        is_pinned: false,
                        is_archived: false,
                        messages: [],
                        created_at: new Date().toISOString(),
                        updated_at: new Date().toISOString()
                      }
                    }));
                  }
                } else if (parsed.type === 'title' && parsed.title) {
                  newTitle = parsed.title;
                } else if (parsed.type === 'message' && parsed.content) {
                  fullContent += parsed.content;
                  set({ streamingContent: fullContent });
                } else if (parsed.type === 'done') {
                  // Add the complete message
                  const assistantMessage: Message = {
                    id: `msg-${Date.now()}`,
                    conversation_id: conversationId || '',
                    role: 'assistant',
                    content: fullContent,
                    created_at: new Date().toISOString()
                  };
                  
                  set((state) => {
                    const updatedMessages = [...state.messages];
                    // Replace the temp user message with the final one
                    const finalMessages = updatedMessages.map(m => 
                      m.id.startsWith('temp-') ? { ...userMessage, id: `msg-${Date.now() - 1}` } : m
                    );
                    
                    // Update conversation title if new title was generated
                    let updatedConversation = state.currentConversation;
                    if (newTitle && conversationId && !currentConversation) {
                      updatedConversation = {
                        ...state.currentConversation!,
                        id: conversationId,
                        title: newTitle,
                      };
                    }
                    
                    return {
                      messages: [...finalMessages, assistantMessage],
                      isStreaming: false,
                      streamingContent: '',
                      currentConversation: updatedConversation
                    };
                  });
                  
                  // Update conversations list
                  if (conversationId) {
                    get().loadConversations();
                  }
                } else if (parsed.type === 'error') {
                  set({ error: parsed.error || 'Unknown error', isStreaming: false });
                }
              } catch (e) {
                // Ignore parse errors for incomplete JSON
              }
            }
          }
        }
      }
    } catch (error) {
      set({ error: (error as Error).message, isStreaming: false });
      
      // Demo mode: simulate a response
      set({ isStreaming: true });
      const demoResponse = `Hello! I'm your AI assistant. You said: "${content}"

I can help you with various tasks including:

- **Writing** - Articles, emails, stories, code comments
- **Coding** - Debugging, explanations, code snippets
- **Analysis** - Data interpretation, problem solving
- **Brainstorming** - Ideas, solutions, creative thinking

What would you like help with today?`;
      
      let i = 0;
      const simulateStream = () => {
        if (i < demoResponse.length) {
          set((state) => ({
            streamingContent: state.streamingContent + demoResponse[i]
          }));
          i++;
          setTimeout(simulateStream, 10);
        } else {
          const assistantMessage: Message = {
            id: `msg-${Date.now()}`,
            conversation_id: currentConversation?.id || 'demo',
            role: 'assistant',
            content: demoResponse,
            created_at: new Date().toISOString()
          };
          set((state) => ({
            messages: [...state.messages, assistantMessage],
            isStreaming: false,
            streamingContent: ''
          }));
        }
      };
      simulateStream();
    }
  },
}));
