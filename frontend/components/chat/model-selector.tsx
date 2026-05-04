'use client';

import { Bot, Loader2, CheckCircle2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { ModelInfo } from '@/types';

interface ModelSelectorProps {
  models: ModelInfo[];
  selectedModel: string;
  selectedProvider: string;
  onModelChange: (model: string) => void;
  onProviderChange: (provider: string) => void;
  isLoading?: boolean;
}

export function ModelSelector({
  models,
  selectedModel,
  selectedProvider,
  onModelChange,
  onProviderChange,
  isLoading,
}: ModelSelectorProps) {
  const ollamaModels = models.filter((m) => m.provider === 'ollama');
  const openaiModels = models.filter((m) => m.provider === 'openai');

  return (
    <div className="flex items-center gap-2">
      <Select value={selectedProvider} onValueChange={onProviderChange}>
        <SelectTrigger className="w-[140px]">
          <SelectValue placeholder="Provider" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="ollama">
            <div className="flex items-center gap-2">
              <span>🤖 Ollama</span>
            </div>
          </SelectItem>
          <SelectItem value="openai">
            <div className="flex items-center gap-2">
              <span>☁️ OpenAI</span>
            </div>
          </SelectItem>
        </SelectContent>
      </Select>

      <Select value={selectedModel} onValueChange={onModelChange}>
        <SelectTrigger className="w-[200px]">
          <SelectValue placeholder="Select model" />
        </SelectTrigger>
        <SelectContent>
          {selectedProvider === 'ollama' && (
            <>
              {ollamaModels.length > 0 ? (
                ollamaModels.map((model) => (
                  <SelectItem key={model.id} value={model.id}>
                    <div className="flex items-center gap-2">
                      <Bot className="h-4 w-4" />
                      <span>{model.name}</span>
                      {model.is_default && (
                        <CheckCircle2 className="h-3 w-3 text-green-500" />
                      )}
                    </div>
                  </SelectItem>
                ))
              ) : (
                <div className="p-2 text-sm text-muted-foreground">
                  {isLoading ? (
                    <div className="flex items-center gap-2">
                      <Loader2 className="h-4 w-4 animate-spin" />
                      Loading...
                    </div>
                  ) : (
                    'No models available'
                  )}
                </div>
              )}
            </>
          )}
          {selectedProvider === 'openai' && (
            <>
              {openaiModels.length > 0 ? (
                openaiModels.map((model) => (
                  <SelectItem key={model.id} value={model.id}>
                    <div className="flex items-center gap-2">
                      <span>{model.name}</span>
                      {model.supports_function_calling && (
                        <span className="text-xs text-muted-foreground">
                          (FC)
                        </span>
                      )}
                    </div>
                  </SelectItem>
                ))
              ) : (
                <div className="p-2 text-sm text-muted-foreground">
                  No models available
                </div>
              )}
            </>
          )}
        </SelectContent>
      </Select>
    </div>
  );
}
