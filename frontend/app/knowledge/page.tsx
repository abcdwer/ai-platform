'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Database, Plus, Search, Loader2 } from 'lucide-react';
import { Sidebar } from '@/components/sidebar';
import { KnowledgeCard, CreateDialog } from '@/components/knowledge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Pagination } from '@/components/ui/pagination';
import { useKnowledgeStore } from '@/stores';
import { useToast } from '@/components/ui/use-toast';
import type { KnowledgeBase } from '@/types';

export default function KnowledgePage() {
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [editData, setEditData] = useState<KnowledgeBase | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  
  // P1: Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(12);
  
  const { toast } = useToast();
  const {
    knowledgeBases,
    isLoadingKBs,
    kbError,
    loadKnowledgeBases,
    createKnowledgeBase,
    updateKnowledgeBase,
    deleteKnowledgeBase,
  } = useKnowledgeStore();

  useEffect(() => {
    loadKnowledgeBases();
  }, [loadKnowledgeBases]);

  const handleCreate = async (data: Partial<KnowledgeBase>) => {
    try {
      await createKnowledgeBase(data);
      toast({
        title: 'Knowledge base created',
        description: 'Your new knowledge base is ready.',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to create knowledge base.',
        variant: 'destructive',
      });
    }
  };

  const handleUpdate = async (data: Partial<KnowledgeBase>) => {
    if (!editData) return;
    try {
      await updateKnowledgeBase(editData.id, data);
      setEditData(null);
      toast({
        title: 'Knowledge base updated',
        description: 'Changes saved successfully.',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to update knowledge base.',
        variant: 'destructive',
      });
    }
  };

  const handleDelete = async (kb: KnowledgeBase) => {
    if (!confirm(`Delete "${kb.name}"? This cannot be undone.`)) return;
    try {
      await deleteKnowledgeBase(kb.id);
      toast({
        title: 'Knowledge base deleted',
        description: 'The knowledge base has been removed.',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to delete knowledge base.',
        variant: 'destructive',
      });
    }
  };

  const filteredKBs = knowledgeBases.filter((kb) =>
    kb.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    kb.description?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // P1: Calculate pagination
  const totalPages = Math.ceil(filteredKBs.length / pageSize);
  const paginatedKBs = filteredKBs.slice(
    (currentPage - 1) * pageSize,
    currentPage * pageSize
  );

  // Reset to page 1 when search changes
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery]);

  return (
    <div className="flex h-screen">
      <Sidebar />
      
      <main className="flex-1 overflow-auto">
        <div className="max-w-6xl mx-auto p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold flex items-center gap-3">
                <Database className="h-8 w-8" />
                Knowledge Bases
              </h1>
              <p className="text-muted-foreground mt-1">
                Manage your document collections for RAG-powered conversations
              </p>
            </div>
            <Button onClick={() => setShowCreateDialog(true)} className="gap-2">
              <Plus className="h-4 w-4" />
              Create Knowledge Base
            </Button>
          </div>

          {/* Search */}
          <div className="relative mb-6">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search knowledge bases..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 max-w-md"
            />
          </div>

          {/* Loading State */}
          {isLoadingKBs && (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
            </div>
          )}

          {/* Error State */}
          {kbError && (
            <div className="text-center py-12">
              <p className="text-destructive">{kbError}</p>
              <Button variant="outline" onClick={loadKnowledgeBases} className="mt-4">
                Try Again
              </Button>
            </div>
          )}

          {/* Empty State */}
          {!isLoadingKBs && !kbError && filteredKBs.length === 0 && (
            <div className="text-center py-16 border rounded-lg">
              <Database className="h-12 w-12 mx-auto text-muted-foreground/50" />
              <h3 className="mt-4 text-lg font-medium">No knowledge bases yet</h3>
              <p className="text-sm text-muted-foreground mt-1">
                Create your first knowledge base to start organizing documents.
              </p>
              <Button onClick={() => setShowCreateDialog(true)} className="mt-4 gap-2">
                <Plus className="h-4 w-4" />
                Create Knowledge Base
              </Button>
            </div>
          )}

          {/* Knowledge Base Grid */}
          {!isLoadingKBs && !kbError && filteredKBs.length > 0 && (
            <>
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                {paginatedKBs.map((kb) => (
                  <KnowledgeCard
                    key={kb.id}
                    knowledgeBase={kb}
                    onEdit={(kb) => {
                      setEditData(kb);
                      setShowCreateDialog(true);
                    }}
                    onDelete={handleDelete}
                  />
                ))}
              </div>
              
              {/* P1: Pagination */}
              {totalPages > 1 && (
                <div className="mt-8 flex justify-center">
                  <Pagination
                    currentPage={currentPage}
                    totalPages={totalPages}
                    pageSize={pageSize}
                    totalItems={filteredKBs.length}
                    onPageChange={setCurrentPage}
                    onPageSizeChange={(size) => {
                      setPageSize(size);
                      setCurrentPage(1);
                    }}
                    showPageSize
                  />
                </div>
              )}
            </>
          )}
        </div>
      </main>

      {/* Create/Edit Dialog */}
      <CreateDialog
        open={showCreateDialog}
        onOpenChange={(open) => {
          setShowCreateDialog(open);
          if (!open) setEditData(null);
        }}
        onSubmit={editData ? handleUpdate : handleCreate}
        editData={editData}
      />
    </div>
  );
}
