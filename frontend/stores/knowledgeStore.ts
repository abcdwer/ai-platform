'use client';

import { create } from 'zustand';
import type { 
  KnowledgeBase, 
  Document, 
  SearchResult,
  RAGSource,
  KnowledgeBaseListResponse,
  DocumentListResponse
} from '@/types';

interface KnowledgeState {
  // Knowledge bases
  knowledgeBases: KnowledgeBase[];
  currentKnowledgeBase: KnowledgeBase | null;
  isLoadingKBs: boolean;
  kbError: string | null;
  
  // Documents
  documents: Document[];
  isLoadingDocs: boolean;
  docError: string | null;
  
  // Search
  searchResults: SearchResult[];
  isSearching: boolean;
  searchError: string | null;
  
  // RAG Chat
  chatMessages: { role: 'user' | 'assistant'; content: string; sources?: RAGSource[] }[];
  isChatting: boolean;
  chatError: string | null;
  streamingContent: string;
  
  // Actions - Knowledge Bases
  loadKnowledgeBases: () => Promise<void>;
  loadKnowledgeBase: (id: string) => Promise<void>;
  createKnowledgeBase: (data: Partial<KnowledgeBase>) => Promise<KnowledgeBase>;
  updateKnowledgeBase: (id: string, data: Partial<KnowledgeBase>) => Promise<void>;
  deleteKnowledgeBase: (id: string) => Promise<void>;
  setCurrentKnowledgeBase: (kb: KnowledgeBase | null) => void;
  
  // Actions - Documents
  loadDocuments: (kbId: string) => Promise<void>;
  uploadDocument: (kbId: string, file: File) => Promise<Document>;
  addDocumentFromURL: (kbId: string, url: string, title?: string) => Promise<Document>;
  deleteDocument: (kbId: string, docId: string) => Promise<void>;
  
  // Actions - Search
  search: (kbId: string, query: string, topK?: number, threshold?: number) => Promise<void>;
  clearSearchResults: () => void;
  
  // Actions - RAG Chat
  sendRAGMessage: (kbId: string, message: string, topK?: number, threshold?: number) => Promise<void>;
  clearChat: () => void;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const useKnowledgeStore = create<KnowledgeState>((set, get) => ({
  // Initial state
  knowledgeBases: [],
  currentKnowledgeBase: null,
  isLoadingKBs: false,
  kbError: null,
  
  documents: [],
  isLoadingDocs: false,
  docError: null,
  
  searchResults: [],
  isSearching: false,
  searchError: null,
  
  chatMessages: [],
  isChatting: false,
  chatError: null,
  streamingContent: '',
  
  // Knowledge Base Actions
  loadKnowledgeBases: async () => {
    set({ isLoadingKBs: true, kbError: null });
    try {
      const response = await fetch(`${API_BASE}/api/knowledge`);
      if (!response.ok) throw new Error('Failed to load knowledge bases');
      const data: KnowledgeBaseListResponse = await response.json();
      set({ knowledgeBases: data.items, isLoadingKBs: false });
    } catch (error) {
      set({ kbError: (error as Error).message, isLoadingKBs: false });
    }
  },
  
  loadKnowledgeBase: async (id: string) => {
    set({ isLoadingKBs: true, kbError: null });
    try {
      const response = await fetch(`${API_BASE}/api/knowledge/${id}`);
      if (!response.ok) throw new Error('Failed to load knowledge base');
      const kb: KnowledgeBase = await response.json();
      set({ currentKnowledgeBase: kb, isLoadingKBs: false });
    } catch (error) {
      set({ kbError: (error as Error).message, isLoadingKBs: false });
    }
  },
  
  createKnowledgeBase: async (data: Partial<KnowledgeBase>) => {
    const response = await fetch(`${API_BASE}/api/knowledge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: data.name,
        description: data.description,
        embedding_model: data.embedding_model || 'nomic-embed-text',
        embedding_provider: data.embedding_provider || 'ollama',
        chunk_size: data.chunk_size || 500,
        chunk_overlap: data.chunk_overlap || 50,
        chunking_strategy: data.chunking_strategy || 'paragraph',
        top_k: data.top_k || 5,
        similarity_threshold: data.similarity_threshold || 0.7,
        tags: data.tags || [],
      }),
    });
    if (!response.ok) throw new Error('Failed to create knowledge base');
    const kb: KnowledgeBase = await response.json();
    set((state) => ({ knowledgeBases: [kb, ...state.knowledgeBases] }));
    return kb;
  },
  
  updateKnowledgeBase: async (id: string, data: Partial<KnowledgeBase>) => {
    const response = await fetch(`${API_BASE}/api/knowledge/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update knowledge base');
    const updatedKB: KnowledgeBase = await response.json();
    set((state) => ({
      knowledgeBases: state.knowledgeBases.map((kb) =>
        kb.id === id ? updatedKB : kb
      ),
      currentKnowledgeBase: state.currentKnowledgeBase?.id === id
        ? updatedKB
        : state.currentKnowledgeBase,
    }));
  },
  
  deleteKnowledgeBase: async (id: string) => {
    const response = await fetch(`${API_BASE}/api/knowledge/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete knowledge base');
    set((state) => ({
      knowledgeBases: state.knowledgeBases.filter((kb) => kb.id !== id),
      currentKnowledgeBase: state.currentKnowledgeBase?.id === id
        ? null
        : state.currentKnowledgeBase,
    }));
  },
  
  setCurrentKnowledgeBase: (kb: KnowledgeBase | null) => {
    set({ currentKnowledgeBase: kb });
  },
  
  // Document Actions
  loadDocuments: async (kbId: string) => {
    set({ isLoadingDocs: true, docError: null });
    try {
      const response = await fetch(`${API_BASE}/api/knowledge/${kbId}/documents`);
      if (!response.ok) throw new Error('Failed to load documents');
      const data: DocumentListResponse = await response.json();
      set({ documents: data.items, isLoadingDocs: false });
    } catch (error) {
      set({ docError: (error as Error).message, isLoadingDocs: false });
    }
  },
  
  uploadDocument: async (kbId: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE}/api/knowledge/${kbId}/documents`, {
      method: 'POST',
      body: formData,
    });
    if (!response.ok) throw new Error('Failed to upload document');
    const doc: Document = await response.json();
    set((state) => ({ documents: [doc, ...state.documents] }));
    return doc;
  },
  
  addDocumentFromURL: async (kbId: string, url: string, title?: string) => {
    const response = await fetch(`${API_BASE}/api/knowledge/${kbId}/documents/url`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url, title }),
    });
    if (!response.ok) throw new Error('Failed to add document from URL');
    const doc: Document = await response.json();
    set((state) => ({ documents: [doc, ...state.documents] }));
    return doc;
  },
  
  deleteDocument: async (kbId: string, docId: string) => {
    const response = await fetch(`${API_BASE}/api/knowledge/${kbId}/documents/${docId}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete document');
    set((state) => ({
      documents: state.documents.filter((doc) => doc.id !== docId),
    }));
  },
  
  // Search Actions
  search: async (kbId: string, query: string, topK?: number, threshold?: number) => {
    set({ isSearching: true, searchError: null });
    try {
      const response = await fetch(`${API_BASE}/api/knowledge/${kbId}/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, top_k: topK, similarity_threshold: threshold }),
      });
      if (!response.ok) throw new Error('Failed to search');
      const data = await response.json();
      set({ searchResults: data.results, isSearching: false });
    } catch (error) {
      set({ searchError: (error as Error).message, isSearching: false });
    }
  },
  
  clearSearchResults: () => {
    set({ searchResults: [] });
  },
  
  // RAG Chat Actions
  sendRAGMessage: async (kbId: string, message: string, topK?: number, threshold?: number) => {
    // Add user message
    set((state) => ({
      chatMessages: [...state.chatMessages, { role: 'user', content: message }],
      isChatting: true,
      chatError: null,
      streamingContent: '',
    }));
    
    try {
      const response = await fetch(`${API_BASE}/api/knowledge/${kbId}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          top_k: topK,
          similarity_threshold: threshold,
          include_sources: true,
        }),
      });
      
      if (!response.ok) throw new Error('Failed to send message');
      
      const reader = response.body?.getReader();
      if (!reader) throw new Error('No response body');
      
      let fullContent = '';
      let sources: RAGSource[] = [];
      const decoder = new TextDecoder();
      
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');
        
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === 'sources') {
                sources = data.sources || [];
              } else if (data.type === 'message') {
                fullContent += data.content || '';
                set({ streamingContent: fullContent });
              } else if (data.type === 'done') {
                set((state) => ({
                  chatMessages: [
                    ...state.chatMessages,
                    { role: 'assistant', content: fullContent, sources },
                  ],
                  streamingContent: '',
                  isChatting: false,
                }));
              } else if (data.type === 'error') {
                throw new Error(data.error);
              }
            } catch (e) {
              // Ignore parse errors for incomplete JSON
            }
          }
        }
      }
    } catch (error) {
      set({ 
        chatError: (error as Error).message, 
        isChatting: false,
        streamingContent: '',
      });
    }
  },
  
  clearChat: () => {
    set({ chatMessages: [], streamingContent: '', chatError: null });
  },
}));
