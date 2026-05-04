'use client';

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { 
  ArrowLeft, 
  Database, 
  Upload, 
  Link as LinkIcon,
  Search,
  Settings,
  Loader2,
  RefreshCw,
  FileText,
  Trash2,
  Download,
  Upload as UploadIcon,
} from 'lucide-react';
import { Sidebar } from '@/components/sidebar';
import { 
  DocumentUpload, 
  DocumentList, 
  URLAddDialog,
  SearchResultView
} from '@/components/knowledge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { useKnowledgeStore } from '@/stores';
import { useToast } from '@/components/ui/use-toast';
import { cn } from '@/lib/utils';
import { ExportKnowledgeDialog, ImportKnowledgeDialog } from '@/components/export-dialog';

export default function KnowledgeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const kbId = params.id as string;
  
  const { toast } = useToast();
  const {
    currentKnowledgeBase,
    documents,
    isLoadingDocs,
    docError,
    searchResults,
    isSearching,
    loadKnowledgeBase,
    loadDocuments,
    uploadDocument,
    addDocumentFromURL,
    deleteDocument,
    search,
    clearSearchResults,
  } = useKnowledgeStore();

  const [showURLDialog, setShowURLDialog] = useState(false);
  const [activeTab, setActiveTab] = useState('documents');
  const [searchQuery, setSearchQuery] = useState('');
  const [showExportDialog, setShowExportDialog] = useState(false);
  const [showImportDialog, setShowImportDialog] = useState(false);

  useEffect(() => {
    if (kbId) {
      loadKnowledgeBase(kbId);
      loadDocuments(kbId);
    }
  }, [kbId, loadKnowledgeBase, loadDocuments]);

  const handleUpload = async (file: File) => {
    try {
      await uploadDocument(kbId, file);
      toast({
        title: 'Document uploaded',
        description: 'Your document is being processed.',
      });
    } catch (error) {
      toast({
        title: 'Upload failed',
        description: (error as Error).message,
        variant: 'destructive',
      });
    }
  };

  const handleAddURL = async (url: string, title?: string) => {
    try {
      await addDocumentFromURL(kbId, url, title);
      toast({
        title: 'URL added',
        description: 'Fetching and processing content...',
      });
    } catch (error) {
      toast({
        title: 'Failed to add URL',
        description: (error as Error).message,
        variant: 'destructive',
      });
    }
  };

  const handleDeleteDoc = async (docId: string) => {
    if (!confirm('Delete this document?')) return;
    try {
      await deleteDocument(kbId, docId);
      toast({
        title: 'Document deleted',
      });
    } catch (error) {
      toast({
        title: 'Failed to delete',
        variant: 'destructive',
      });
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    await search(kbId, searchQuery);
  };

  const handleExportKnowledge = async (format: string) => {
    const response = await fetch(`/api/knowledge/${kbId}/export?format=${format}`);
    if (!response.ok) throw new Error('Export failed');
    
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `knowledge_${currentKnowledgeBase?.name?.replace(/\s+/g, '_') || 'base'}.${format}`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
  };

  const handleImportDocuments = async (documents: any[]) => {
    const response = await fetch(`/api/knowledge/${kbId}/import`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ documents }),
    });
    
    if (!response.ok) throw new Error('Import failed');
    
    // Refresh documents list
    await loadDocuments(kbId);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
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

  const readyDocs = documents.filter((d) => d.status === 'ready').length;
  const processingDocs = documents.filter((d) => ['uploading', 'parsing', 'embedding'].includes(d.status)).length;

  return (
    <div className="flex h-screen">
      <Sidebar />
      
      <main className="flex-1 overflow-hidden flex flex-col">
        {/* Header */}
        <div className="border-b p-4">
          <div className="max-w-6xl mx-auto">
            <div className="flex items-center gap-4 mb-4">
              <Button variant="ghost" size="icon" asChild>
                <Link href="/knowledge">
                  <ArrowLeft className="h-5 w-5" />
                </Link>
              </Button>
              <div className="flex-1">
                <h1 className="text-2xl font-bold flex items-center gap-2">
                  <Database className="h-6 w-6" />
                  {currentKnowledgeBase.name}
                </h1>
                {currentKnowledgeBase.description && (
                  <p className="text-sm text-muted-foreground">
                    {currentKnowledgeBase.description}
                  </p>
                )}
              </div>
              <div className="flex items-center gap-2">
                <Badge variant="outline">
                  {readyDocs} ready
                </Badge>
                {processingDocs > 0 && (
                  <Badge variant="secondary">
                    {processingDocs} processing
                  </Badge>
                )}
                <Button variant="outline" onClick={() => setShowImportDialog(true)}>
                  <UploadIcon className="h-4 w-4 mr-2" />
                  Import
                </Button>
                <Button variant="outline" onClick={() => setShowExportDialog(true)}>
                  <Download className="h-4 w-4 mr-2" />
                  Export
                </Button>
              </div>
              <Link href={`/knowledge/${kbId}/chat`}>
                <Button>Start Chat</Button>
              </Link>
            </div>

            {/* Search Bar */}
            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search within this knowledge base..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyDown={handleKeyDown}
                  className="pl-10"
                />
              </div>
              <Button onClick={handleSearch} disabled={isSearching || !searchQuery.trim()}>
                {isSearching ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  'Search'
                )}
              </Button>
              <Button 
                variant="outline" 
                onClick={clearSearchResults}
                disabled={searchResults.length === 0}
              >
                Clear
              </Button>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          <div className="max-w-6xl mx-auto">
            {searchResults.length > 0 ? (
              <div>
                <h2 className="text-lg font-semibold mb-4">
                  Search Results ({searchResults.length})
                </h2>
                <SearchResultView results={searchResults} />
              </div>
            ) : (
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList>
                  <TabsTrigger value="documents" className="gap-2">
                    <FileText className="h-4 w-4" />
                    Documents
                  </TabsTrigger>
                  <TabsTrigger value="settings" className="gap-2">
                    <Settings className="h-4 w-4" />
                    Settings
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="documents" className="mt-6">
                  <div className="space-y-6">
                    {/* Upload Section */}
                    <div className="grid md:grid-cols-2 gap-6">
                      <div className="border rounded-lg p-4">
                        <h3 className="font-medium mb-4 flex items-center gap-2">
                          <Upload className="h-4 w-4" />
                          Upload Files
                        </h3>
                        <DocumentUpload onUpload={handleUpload} />
                      </div>

                      <div className="border rounded-lg p-4">
                        <h3 className="font-medium mb-4 flex items-center gap-2">
                          <LinkIcon className="h-4 w-4" />
                          Add from URL
                        </h3>
                        <p className="text-sm text-muted-foreground mb-4">
                          Paste a URL to fetch and add web content.
                        </p>
                        <Button onClick={() => setShowURLDialog(true)} className="w-full">
                          <LinkIcon className="h-4 w-4 mr-2" />
                          Add URL
                        </Button>
                      </div>
                    </div>

                    {/* Document List */}
                    <div>
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="font-medium">Documents ({documents.length})</h3>
                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={() => loadDocuments(kbId)}
                          className="gap-2"
                        >
                          <RefreshCw className="h-4 w-4" />
                          Refresh
                        </Button>
                      </div>
                      <DocumentList
                        documents={documents}
                        loading={isLoadingDocs}
                        onDelete={handleDeleteDoc}
                      />
                    </div>
                  </div>
                </TabsContent>

                <TabsContent value="settings" className="mt-6">
                  <div className="border rounded-lg p-6 max-w-2xl">
                    <h3 className="font-medium mb-4">Configuration</h3>
                    <div className="space-y-4">
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label className="text-muted-foreground">Embedding Model</Label>
                          <p className="font-medium">{currentKnowledgeBase.embedding_model}</p>
                        </div>
                        <div>
                          <Label className="text-muted-foreground">Embedding Provider</Label>
                          <p className="font-medium">{currentKnowledgeBase.embedding_provider}</p>
                        </div>
                        <div>
                          <Label className="text-muted-foreground">Chunking Strategy</Label>
                          <p className="font-medium">{currentKnowledgeBase.chunking_strategy}</p>
                        </div>
                        <div>
                          <Label className="text-muted-foreground">Chunk Size</Label>
                          <p className="font-medium">{currentKnowledgeBase.chunk_size}</p>
                        </div>
                        <div>
                          <Label className="text-muted-foreground">Chunk Overlap</Label>
                          <p className="font-medium">{currentKnowledgeBase.chunk_overlap}</p>
                        </div>
                        <div>
                          <Label className="text-muted-foreground">Top K</Label>
                          <p className="font-medium">{currentKnowledgeBase.top_k}</p>
                        </div>
                        <div>
                          <Label className="text-muted-foreground">Similarity Threshold</Label>
                          <p className="font-medium">{currentKnowledgeBase.similarity_threshold}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </TabsContent>
              </Tabs>
            )}
          </div>
        </div>
      </main>

      <URLAddDialog
        open={showURLDialog}
        onOpenChange={setShowURLDialog}
        onSubmit={handleAddURL}
      />

      {/* Export Dialog */}
      <ExportKnowledgeDialog
        open={showExportDialog}
        onOpenChange={setShowExportDialog}
        knowledgeBaseId={kbId}
        knowledgeBaseName={currentKnowledgeBase?.name || 'Knowledge Base'}
        onExport={handleExportKnowledge}
      />

      {/* Import Dialog */}
      <ImportKnowledgeDialog
        open={showImportDialog}
        onOpenChange={setShowImportDialog}
        onImport={handleImportDocuments}
      />
    </div>
  );
}
