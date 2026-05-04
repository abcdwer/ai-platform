'use client';

import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, X, Loader2, CheckCircle2, AlertCircle, File } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';

interface DocumentUploadProps {
  onUpload: (file: File) => Promise<void>;
  accept?: Record<string, string[]>;
  maxSize?: number;
  disabled?: boolean;
}

interface UploadedFile {
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'success' | 'error';
  error?: string;
}

export function DocumentUpload({ 
  onUpload, 
  accept = {
    'application/pdf': ['.pdf'],
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
    'text/plain': ['.txt'],
    'text/markdown': ['.md'],
    'text/csv': ['.csv'],
    'text/html': ['.html', '.htm'],
  },
  maxSize = 50 * 1024 * 1024, // 50MB
  disabled = false,
}: DocumentUploadProps) {
  const [uploadedFiles, setUploadedFiles] = React.useState<UploadedFile[]>([]);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    for (const file of acceptedFiles) {
      const uploadedFile: UploadedFile = {
        file,
        progress: 0,
        status: 'uploading',
      };
      
      setUploadedFiles((prev) => [...prev, uploadedFile]);
      
      try {
        await onUpload(file);
        setUploadedFiles((prev) =>
          prev.map((f) =>
            f.file === file ? { ...f, progress: 100, status: 'success' } : f
          )
        );
      } catch (error) {
        setUploadedFiles((prev) =>
          prev.map((f) =>
            f.file === file
              ? { ...f, status: 'error', error: (error as Error).message }
              : f
          )
        );
      }
    }
  }, [onUpload]);

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept,
    maxSize,
    disabled,
  });

  const removeFile = (file: File) => {
    setUploadedFiles((prev) => prev.filter((f) => f.file !== file));
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  const getFileIcon = (file: File) => {
    const ext = file.name.split('.').pop()?.toLowerCase();
    switch (ext) {
      case 'pdf':
        return <FileText className="h-5 w-5 text-red-500" />;
      case 'docx':
      case 'doc':
        return <FileText className="h-5 w-5 text-blue-500" />;
      case 'csv':
        return <FileText className="h-5 w-5 text-green-500" />;
      case 'md':
        return <FileText className="h-5 w-5 text-gray-500" />;
      default:
        return <File className="h-5 w-5 text-muted-foreground" />;
    }
  };

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={cn(
          'border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors',
          isDragActive && 'border-primary bg-primary/5',
          isDragReject && 'border-destructive bg-destructive/5',
          !isDragActive && 'hover:border-primary/50',
          disabled && 'opacity-50 cursor-not-allowed'
        )}
      >
        <input {...getInputProps()} />
        
        <div className="flex flex-col items-center gap-3">
          <div className={cn(
            'w-12 h-12 rounded-full flex items-center justify-center',
            isDragActive ? 'bg-primary/10' : 'bg-muted'
          )}>
            <Upload className={cn(
              'h-6 w-6',
              isDragActive ? 'text-primary' : 'text-muted-foreground'
            )} />
          </div>
          
          <div>
            <p className="text-sm font-medium">
              {isDragActive
                ? 'Drop files here...'
                : isDragReject
                ? 'Invalid file type'
                : 'Drag & drop files here, or click to select'}
            </p>
            <p className="text-xs text-muted-foreground mt-1">
              Supports PDF, Word, TXT, Markdown, CSV, HTML (max {formatSize(maxSize)})
            </p>
          </div>
        </div>
      </div>

      {uploadedFiles.length > 0 && (
        <div className="space-y-2">
          {uploadedFiles.map((uploaded, index) => (
            <div
              key={index}
              className="flex items-center gap-3 p-3 rounded-lg border bg-card"
            >
              {getFileIcon(uploaded.file)}
              
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">
                  {uploaded.file.name}
                </p>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span>{formatSize(uploaded.file.size)}</span>
                  {uploaded.status === 'uploading' && (
                    <span className="flex items-center gap-1">
                      <Loader2 className="h-3 w-3 animate-spin" />
                      Uploading...
                    </span>
                  )}
                  {uploaded.status === 'success' && (
                    <span className="flex items-center gap-1 text-green-600">
                      <CheckCircle2 className="h-3 w-3" />
                      Uploaded
                    </span>
                  )}
                  {uploaded.status === 'error' && (
                    <span className="flex items-center gap-1 text-destructive">
                      <AlertCircle className="h-3 w-3" />
                      {uploaded.error || 'Upload failed'}
                    </span>
                  )}
                </div>
              </div>
              
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8"
                onClick={() => removeFile(uploaded.file)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Need to import React for useState
import React from 'react';
