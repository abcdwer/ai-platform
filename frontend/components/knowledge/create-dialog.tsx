'use client';

import { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import type { KnowledgeBase } from '@/types';

interface CreateDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: Partial<KnowledgeBase>) => Promise<void>;
  editData?: KnowledgeBase | null;
}

export function CreateDialog({ open, onOpenChange, onSubmit, editData }: CreateDialogProps) {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    embedding_model: 'nomic-embed-text',
    embedding_provider: 'ollama' as 'ollama' | 'openai',
    chunk_size: 500,
    chunk_overlap: 50,
    chunking_strategy: 'paragraph' as 'paragraph' | 'fixed' | 'semantic',
    top_k: 5,
    similarity_threshold: 0.7,
    tags: '',
  });

  useEffect(() => {
    if (editData) {
      setFormData({
        name: editData.name,
        description: editData.description || '',
        embedding_model: editData.embedding_model,
        embedding_provider: editData.embedding_provider,
        chunk_size: editData.chunk_size,
        chunk_overlap: editData.chunk_overlap,
        chunking_strategy: editData.chunking_strategy,
        top_k: editData.top_k,
        similarity_threshold: editData.similarity_threshold,
        tags: editData.tags?.join(', ') || '',
      });
    } else {
      setFormData({
        name: '',
        description: '',
        embedding_model: 'nomic-embed-text',
        embedding_provider: 'ollama',
        chunk_size: 500,
        chunk_overlap: 50,
        chunking_strategy: 'paragraph',
        top_k: 5,
        similarity_threshold: 0.7,
        tags: '',
      });
    }
  }, [editData, open]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await onSubmit({
        ...formData,
        tags: formData.tags ? formData.tags.split(',').map(t => t.trim()).filter(Boolean) : [],
      });
      onOpenChange(false);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>
              {editData ? 'Edit Knowledge Base' : 'Create Knowledge Base'}
            </DialogTitle>
            <DialogDescription>
              {editData 
                ? 'Update the knowledge base configuration.'
                : 'Create a new knowledge base for document storage and RAG.'}
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="grid gap-2">
              <Label htmlFor="name">Name</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="My Knowledge Base"
                required
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="description">Description</Label>
              <Textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Optional description..."
                rows={2}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="embedding_provider">Embedding Provider</Label>
                <Select
                  value={formData.embedding_provider}
                  onValueChange={(v) => setFormData({ ...formData, embedding_provider: v as 'ollama' | 'openai' })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="ollama">Ollama (Local)</SelectItem>
                    <SelectItem value="openai">OpenAI</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="embedding_model">Embedding Model</Label>
                <Input
                  id="embedding_model"
                  value={formData.embedding_model}
                  onChange={(e) => setFormData({ ...formData, embedding_model: e.target.value })}
                  placeholder="nomic-embed-text"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="chunking_strategy">Chunking Strategy</Label>
                <Select
                  value={formData.chunking_strategy}
                  onValueChange={(v) => setFormData({ ...formData, chunking_strategy: v as 'paragraph' | 'fixed' | 'semantic' })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="paragraph">Paragraph</SelectItem>
                    <SelectItem value="fixed">Fixed Size</SelectItem>
                    <SelectItem value="semantic">Semantic</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="grid gap-2">
                <Label htmlFor="chunk_size">Chunk Size</Label>
                <Input
                  id="chunk_size"
                  type="number"
                  value={formData.chunk_size}
                  onChange={(e) => setFormData({ ...formData, chunk_size: parseInt(e.target.value) || 500 })}
                  min={100}
                  max={2000}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="grid gap-2">
                <Label htmlFor="chunk_overlap">Chunk Overlap</Label>
                <Input
                  id="chunk_overlap"
                  type="number"
                  value={formData.chunk_overlap}
                  onChange={(e) => setFormData({ ...formData, chunk_overlap: parseInt(e.target.value) || 0 })}
                  min={0}
                  max={500}
                />
              </div>

              <div className="grid gap-2">
                <Label htmlFor="top_k">Top K (Retrieval)</Label>
                <Input
                  id="top_k"
                  type="number"
                  value={formData.top_k}
                  onChange={(e) => setFormData({ ...formData, top_k: parseInt(e.target.value) || 5 })}
                  min={1}
                  max={50}
                />
              </div>
            </div>

            <div className="grid gap-2">
              <Label htmlFor="similarity_threshold">Similarity Threshold</Label>
              <Input
                id="similarity_threshold"
                type="number"
                step={0.1}
                min={0}
                max={1}
                value={formData.similarity_threshold}
                onChange={(e) => setFormData({ ...formData, similarity_threshold: parseFloat(e.target.value) || 0.7 })}
              />
            </div>

            <div className="grid gap-2">
              <Label htmlFor="tags">Tags (comma-separated)</Label>
              <Input
                id="tags"
                value={formData.tags}
                onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
                placeholder="docs, research, faq"
              />
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Saving...' : editData ? 'Update' : 'Create'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
