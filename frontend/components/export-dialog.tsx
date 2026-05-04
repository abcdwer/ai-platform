'use client';

import { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { 
  FileText, 
  FileJson, 
  FileCode,
  File,
  Download,
  Loader2
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useToast } from '@/components/ui/use-toast';

interface ExportDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  conversationId: string;
  conversationTitle: string;
  onExport: (format: string) => Promise<void>;
}

const formatOptions = [
  { 
    value: 'markdown', 
    label: 'Markdown (.md)',
    description: 'Best for readability and documentation',
    icon: FileText,
  },
  { 
    value: 'json', 
    label: 'JSON (.json)',
    description: 'Best for data and programmatic use',
    icon: FileJson,
  },
  { 
    value: 'html', 
    label: 'HTML (.html)',
    description: 'Best for printing and sharing',
    icon: FileCode,
  },
  { 
    value: 'pdf', 
    label: 'Plain Text (.txt)',
    description: 'Best for simple text extraction',
    icon: File,
  },
];

export function ExportConversationDialog({
  open,
  onOpenChange,
  conversationId,
  conversationTitle,
  onExport,
}: ExportDialogProps) {
  const [selectedFormat, setSelectedFormat] = useState('markdown');
  const [isExporting, setIsExporting] = useState(false);
  const { toast } = useToast();

  const handleExport = async () => {
    setIsExporting(true);
    try {
      await onExport(selectedFormat);
      toast({
        title: 'Export successful',
        description: `Conversation exported as ${selectedFormat.toUpperCase()}`,
      });
      onOpenChange(false);
    } catch (error) {
      toast({
        title: 'Export failed',
        description: (error as Error).message,
        variant: 'destructive',
      });
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Export Conversation</DialogTitle>
          <DialogDescription>
            Export "{conversationTitle}" to a file for backup or sharing.
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          <Label className="text-sm font-medium mb-3 block">Select Format</Label>
          <RadioGroup value={selectedFormat} onValueChange={setSelectedFormat}>
            <div className="space-y-3">
              {formatOptions.map((format) => (
                <div
                  key={format.value}
                  className={cn(
                    'flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors',
                    selectedFormat === format.value
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/50'
                  )}
                  onClick={() => setSelectedFormat(format.value)}
                >
                  <RadioGroupItem value={format.value} id={format.value} className="mt-1" />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <format.icon className="w-4 h-4 text-muted-foreground" />
                      <Label htmlFor={format.value} className="font-medium cursor-pointer">
                        {format.label}
                      </Label>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">
                      {format.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </RadioGroup>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isExporting}>
            Cancel
          </Button>
          <Button onClick={handleExport} disabled={isExporting}>
            {isExporting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Exporting...
              </>
            ) : (
              <>
                <Download className="w-4 h-4 mr-2" />
                Export
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Workflow Export Dialog
interface WorkflowExportDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  workflowId: string;
  workflowName: string;
  onExport: () => Promise<void>;
  onShare: () => Promise<void>;
}

export function ExportWorkflowDialog({
  open,
  onOpenChange,
  workflowId,
  workflowName,
  onExport,
  onShare,
}: WorkflowExportDialogProps) {
  const [isExporting, setIsExporting] = useState(false);
  const [isSharing, setIsSharing] = useState(false);
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const { toast } = useToast();

  const handleExport = async () => {
    setIsExporting(true);
    try {
      await onExport();
      toast({
        title: 'Export successful',
        description: 'Workflow configuration downloaded',
      });
      onOpenChange(false);
    } catch (error) {
      toast({
        title: 'Export failed',
        description: (error as Error).message,
        variant: 'destructive',
      });
    } finally {
      setIsExporting(false);
    }
  };

  const handleShare = async () => {
    setIsSharing(true);
    try {
      const result = await onShare();
      setShareUrl(result.share_url);
      toast({
        title: 'Share link generated',
        description: 'Share link copied to clipboard',
      });
    } catch (error) {
      toast({
        title: 'Share failed',
        description: (error as Error).message,
        variant: 'destructive',
      });
    } finally {
      setIsSharing(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Share & Export Workflow</DialogTitle>
          <DialogDescription>
            Share "{workflowName}" with others or export as configuration.
          </DialogDescription>
        </DialogHeader>

        <div className="py-4 space-y-4">
          {/* Share Section */}
          <div className="space-y-3">
            <Label className="text-sm font-medium">Share</Label>
            {shareUrl ? (
              <div className="p-3 bg-muted rounded-lg">
                <p className="text-sm text-muted-foreground mb-2">Share URL:</p>
                <code className="text-xs break-all">{shareUrl}</code>
              </div>
            ) : (
              <Button variant="outline" className="w-full" onClick={handleShare} disabled={isSharing}>
                {isSharing ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Download className="w-4 h-4 mr-2" />
                )}
                Generate Share Link
              </Button>
            )}
          </div>

          <div className="border-t pt-4">
            {/* Export Section */}
            <div className="space-y-3">
              <Label className="text-sm font-medium">Export</Label>
              <Button variant="outline" className="w-full" onClick={handleExport} disabled={isExporting}>
                {isExporting ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <FileJson className="w-4 h-4 mr-2" />
                )}
                Export as JSON Configuration
              </Button>
              <p className="text-xs text-muted-foreground">
                Export the workflow as a JSON file that can be imported into another AI Platform instance.
              </p>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Workflow Import Dialog
interface ImportWorkflowDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onImport: (config: object) => Promise<void>;
}

export function ImportWorkflowDialog({
  open,
  onOpenChange,
  onImport,
}: ImportWorkflowDialogProps) {
  const [isImporting, setIsImporting] = useState(false);
  const [jsonContent, setJsonContent] = useState('');
  const { toast } = useToast();

  const handleImport = async () => {
    if (!jsonContent.trim()) {
      toast({
        title: 'Invalid input',
        description: 'Please paste workflow configuration JSON',
        variant: 'destructive',
      });
      return;
    }

    setIsImporting(true);
    try {
      const config = JSON.parse(jsonContent);
      await onImport(config);
      toast({
        title: 'Import successful',
        description: 'Workflow imported successfully',
      });
      setJsonContent('');
      onOpenChange(false);
    } catch (error) {
      toast({
        title: 'Import failed',
        description: error instanceof SyntaxError 
          ? 'Invalid JSON format' 
          : (error as Error).message,
        variant: 'destructive',
      });
    } finally {
      setIsImporting(false);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      setJsonContent(event.target?.result as string || '');
    };
    reader.readAsText(file);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Import Workflow</DialogTitle>
          <DialogDescription>
            Import a workflow from JSON configuration file or paste the configuration.
          </DialogDescription>
        </DialogHeader>

        <div className="py-4 space-y-4">
          <div className="space-y-2">
            <Label htmlFor="file-upload">Upload JSON File</Label>
            <input
              type="file"
              id="file-upload"
              accept=".json"
              onChange={handleFileUpload}
              className="w-full text-sm text-slate-500
                file:mr-4 file:py-2 file:px-4
                file:rounded-full file:border-0
                file:text-sm file:font-semibold
                file:bg-primary file:text-primary-foreground
                hover:file:bg-primary/90
                cursor-pointer"
            />
          </div>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-background px-2 text-muted-foreground">Or</span>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="json-content">Paste Configuration</Label>
            <textarea
              id="json-content"
              value={jsonContent}
              onChange={(e) => setJsonContent(e.target.value)}
              placeholder='{"name": "My Workflow", "graph_data": {...}}'
              className="w-full h-40 p-3 text-sm font-mono border rounded-lg resize-none"
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isImporting}>
            Cancel
          </Button>
          <Button onClick={handleImport} disabled={isImporting || !jsonContent.trim()}>
            {isImporting ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Download className="w-4 h-4 mr-2" />
            )}
            Import
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Knowledge Base Export Dialog
interface KnowledgeExportDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  knowledgeBaseId: string;
  knowledgeBaseName: string;
  onExport: (format: string) => Promise<void>;
}

const kbFormatOptions = [
  { 
    value: 'json', 
    label: 'JSON (.json)',
    description: 'Best for backup and data migration',
    icon: FileJson,
  },
  { 
    value: 'markdown', 
    label: 'Markdown (.md)',
    description: 'Best for documentation and readability',
    icon: FileText,
  },
  { 
    value: 'html', 
    label: 'HTML (.html)',
    description: 'Best for web viewing and printing',
    icon: FileCode,
  },
];

export function ExportKnowledgeDialog({
  open,
  onOpenChange,
  knowledgeBaseId,
  knowledgeBaseName,
  onExport,
}: KnowledgeExportDialogProps) {
  const [selectedFormat, setSelectedFormat] = useState('json');
  const [isExporting, setIsExporting] = useState(false);
  const { toast } = useToast();

  const handleExport = async () => {
    setIsExporting(true);
    try {
      await onExport(selectedFormat);
      toast({
        title: 'Export successful',
        description: `Knowledge base exported as ${selectedFormat.toUpperCase()}`,
      });
      onOpenChange(false);
    } catch (error) {
      toast({
        title: 'Export failed',
        description: (error as Error).message,
        variant: 'destructive',
      });
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Export Knowledge Base</DialogTitle>
          <DialogDescription>
            Export "{knowledgeBaseName}" to a file for backup or sharing.
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          <Label className="text-sm font-medium mb-3 block">Select Format</Label>
          <RadioGroup value={selectedFormat} onValueChange={setSelectedFormat}>
            <div className="space-y-3">
              {kbFormatOptions.map((format) => (
                <div
                  key={format.value}
                  className={cn(
                    'flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors',
                    selectedFormat === format.value
                      ? 'border-primary bg-primary/5'
                      : 'border-border hover:border-primary/50'
                  )}
                  onClick={() => setSelectedFormat(format.value)}
                >
                  <RadioGroupItem value={format.value} id={format.value} className="mt-1" />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <format.icon className="w-4 h-4 text-muted-foreground" />
                      <Label htmlFor={format.value} className="font-medium cursor-pointer">
                        {format.label}
                      </Label>
                    </div>
                    <p className="text-sm text-muted-foreground mt-1">
                      {format.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </RadioGroup>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isExporting}>
            Cancel
          </Button>
          <Button onClick={handleExport} disabled={isExporting}>
            {isExporting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Exporting...
              </>
            ) : (
              <>
                <Download className="w-4 h-4 mr-2" />
                Export
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

// Knowledge Base Import Dialog
interface KnowledgeImportDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onImport: (documents: object[]) => Promise<void>;
}

export function ImportKnowledgeDialog({
  open,
  onOpenChange,
  onImport,
}: KnowledgeImportDialogProps) {
  const [isImporting, setIsImporting] = useState(false);
  const [documents, setDocuments] = useState<Array<{
    title: string;
    content: string;
    source?: string;
  }>>([{ title: '', content: '', source: '' }]);
  const { toast } = useToast();

  const addDocument = () => {
    setDocuments([...documents, { title: '', content: '', source: '' }]);
  };

  const updateDocument = (index: number, field: string, value: string) => {
    const updated = [...documents];
    (updated[index] as any)[field] = value;
    setDocuments(updated);
  };

  const removeDocument = (index: number) => {
    if (documents.length > 1) {
      setDocuments(documents.filter((_, i) => i !== index));
    }
  };

  const handleImport = async () => {
    const validDocs = documents.filter(d => d.title.trim() && d.content.trim());
    if (validDocs.length === 0) {
      toast({
        title: 'Invalid input',
        description: 'Please add at least one document with title and content',
        variant: 'destructive',
      });
      return;
    }

    setIsImporting(true);
    try {
      await onImport(validDocs);
      toast({
        title: 'Import successful',
        description: `${validDocs.length} document(s) imported`,
      });
      setDocuments([{ title: '', content: '', source: '' }]);
      onOpenChange(false);
    } catch (error) {
      toast({
        title: 'Import failed',
        description: (error as Error).message,
        variant: 'destructive',
      });
    } finally {
      setIsImporting(false);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const content = event.target?.result as string;
        if (file.name.endsWith('.json')) {
          const parsed = JSON.parse(content);
          if (Array.isArray(parsed)) {
            setDocuments(parsed.map((d: any) => ({
              title: d.title || 'Untitled',
              content: d.content || '',
              source: d.source || '',
            })));
          }
        } else {
          setDocuments([{
            title: file.name,
            content: content,
            source: file.name,
          }]);
        }
      } catch {
        toast({
          title: 'Parse error',
          description: 'Could not parse the file',
          variant: 'destructive',
        });
      }
    };
    reader.readAsText(file);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>Import Documents</DialogTitle>
          <DialogDescription>
            Add documents to your knowledge base.
          </DialogDescription>
        </DialogHeader>

        <div className="py-4 space-y-4">
          <div className="space-y-2">
            <Label>Upload File</Label>
            <input
              type="file"
              accept=".json,.txt,.md"
              onChange={handleFileUpload}
              className="w-full text-sm text-slate-500
                file:mr-4 file:py-2 file:px-4
                file:rounded-full file:border-0
                file:text-sm file:font-semibold
                file:bg-primary file:text-primary-foreground
                hover:file:bg-primary/90
                cursor-pointer"
            />
          </div>

          <div className="relative">
            <div className="absolute inset-0 flex items-center">
              <span className="w-full border-t" />
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-background px-2 text-muted-foreground">Or add manually</span>
            </div>
          </div>

          <div className="space-y-3 max-h-60 overflow-y-auto">
            {documents.map((doc, index) => (
              <div key={index} className="p-3 border rounded-lg space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">Document {index + 1}</span>
                  {documents.length > 1 && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeDocument(index)}
                      className="h-6 px-2 text-destructive"
                    >
                      Remove
                    </Button>
                  )}
                </div>
                <Input
                  placeholder="Title"
                  value={doc.title}
                  onChange={(e) => updateDocument(index, 'title', e.target.value)}
                />
                <textarea
                  placeholder="Content..."
                  value={doc.content}
                  onChange={(e) => updateDocument(index, 'content', e.target.value)}
                  className="w-full h-20 p-2 text-sm border rounded resize-none"
                />
                <Input
                  placeholder="Source (optional)"
                  value={doc.source || ''}
                  onChange={(e) => updateDocument(index, 'source', e.target.value)}
                />
              </div>
            ))}
          </div>

          <Button variant="outline" size="sm" onClick={addDocument}>
            + Add Another Document
          </Button>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isImporting}>
            Cancel
          </Button>
          <Button onClick={handleImport} disabled={isImporting}>
            {isImporting ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Download className="w-4 h-4 mr-2" />
            )}
            Import {documents.filter(d => d.title && d.content).length} Document(s)
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
