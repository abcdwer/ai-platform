'use client';

import { useEffect } from 'react';
import { Sidebar } from '@/components/sidebar';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useModelStore } from '@/stores';
import { Bot, Cloud, CheckCircle2, XCircle, Loader2, RefreshCw, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function ModelsPage() {
  const {
    models,
    modelStatus,
    isLoading,
    error,
    loadModels,
    checkHealth,
  } = useModelStore();

  useEffect(() => {
    loadModels();
  }, [loadModels]);

  const ollamaStatus = modelStatus.find(s => s.provider === 'ollama');
  const openaiStatus = modelStatus.find(s => s.provider === 'openai');

  return (
    <div className="flex h-screen">
      <Sidebar />
      
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="border-b bg-card/50 backdrop-blur-sm sticky top-0 z-10">
          <div className="container mx-auto px-6 py-4 flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">Models</h1>
              <p className="text-muted-foreground">
                Manage and monitor AI models from different providers
              </p>
            </div>
            <Button variant="outline" onClick={() => loadModels()} disabled={isLoading}>
              <RefreshCw className={cn('h-4 w-4 mr-2', isLoading && 'animate-spin')} />
              Refresh
            </Button>
          </div>
        </header>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Provider Status Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
            {/* Ollama */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center">
                    <Bot className="h-6 w-6 text-orange-600 dark:text-orange-400" />
                  </div>
                  <div>
                    <CardTitle>Ollama</CardTitle>
                    <CardDescription>Local Models</CardDescription>
                  </div>
                </div>
                <StatusBadge 
                  status={ollamaStatus?.status || 'unknown'}
                  error={ollamaStatus?.error}
                />
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Models Available</span>
                    <span className="font-medium">{ollamaStatus?.model_count || models?.ollama?.length || 0}</span>
                  </div>
                  {ollamaStatus?.error && (
                    <p className="text-xs text-destructive mt-2">{ollamaStatus.error}</p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* OpenAI */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-lg bg-green-100 dark:bg-green-900/30 flex items-center justify-center">
                    <Cloud className="h-6 w-6 text-green-600 dark:text-green-400" />
                  </div>
                  <div>
                    <CardTitle>OpenAI</CardTitle>
                    <CardDescription>Cloud API</CardDescription>
                  </div>
                </div>
                <StatusBadge 
                  status={openaiStatus?.status || 'unknown'}
                  error={openaiStatus?.error}
                />
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Models Available</span>
                    <span className="font-medium">{openaiStatus?.model_count || models?.openai?.length || 0}</span>
                  </div>
                  {openaiStatus?.error && (
                    <p className="text-xs text-destructive mt-2">{openaiStatus.error}</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Ollama Models */}
          <section className="mb-8">
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Bot className="h-5 w-5" />
              Ollama Models
            </h2>
            {isLoading ? (
              <div className="flex items-center justify-center h-32">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : models?.ollama && models.ollama.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {models.ollama.map((model) => (
                  <Card key={model.id} className="hover:border-primary/50 transition-colors">
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base">{model.name}</CardTitle>
                        {model.is_default && (
                          <Badge variant="secondary" className="text-xs">Default</Badge>
                        )}
                      </div>
                      <CardDescription className="text-xs">{model.id}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="flex flex-wrap gap-2">
                        <CapabilityBadge 
                          icon={<Zap className="h-3 w-3" />}
                          label="Streaming"
                          enabled={model.supports_streaming}
                        />
                        <CapabilityBadge 
                          icon={<Bot className="h-3 w-3" />}
                          label="Tools"
                          enabled={model.supports_function_calling}
                        />
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <Card>
                <CardContent className="flex flex-col items-center justify-center h-32 text-muted-foreground">
                  <Bot className="h-8 w-8 mb-2 opacity-50" />
                  <p>No Ollama models found</p>
                  <p className="text-sm">Make sure Ollama is running locally</p>
                </CardContent>
              </Card>
            )}
          </section>

          {/* OpenAI Models */}
          <section>
            <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Cloud className="h-5 w-5" />
              OpenAI Models
            </h2>
            {models?.openai && models.openai.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {models.openai.map((model) => (
                  <Card key={model.id} className="hover:border-primary/50 transition-colors">
                    <CardHeader className="pb-2">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base">{model.name}</CardTitle>
                        {model.is_default && (
                          <Badge variant="secondary" className="text-xs">Default</Badge>
                        )}
                      </div>
                      <CardDescription className="text-xs">{model.id}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="flex flex-wrap gap-2">
                        <CapabilityBadge 
                          icon={<Zap className="h-3 w-3" />}
                          label="Streaming"
                          enabled={model.supports_streaming}
                        />
                        <CapabilityBadge 
                          icon={<Bot className="h-3 w-3" />}
                          label="Tools"
                          enabled={model.supports_function_calling}
                        />
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <Card>
                <CardContent className="flex flex-col items-center justify-center h-32 text-muted-foreground">
                  <Cloud className="h-8 w-8 mb-2 opacity-50" />
                  <p>No OpenAI models configured</p>
                  <p className="text-sm">Add your API key in Settings to enable</p>
                </CardContent>
              </Card>
            )}
          </section>

          {error && (
            <div className="mt-6 p-4 text-sm text-destructive bg-destructive/10 rounded-lg">
              Error: {error}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Helper components
function StatusBadge({ status, error }: { status: string; error?: string }) {
  if (status === 'online' || status === 'healthy' || status === 'configured') {
    return (
      <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-sm bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
        <CheckCircle2 className="h-4 w-4" />
        <span>Online</span>
      </div>
    );
  }
  
  if (status === 'not_configured') {
    return (
      <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-sm bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400">
        <XCircle className="h-4 w-4" />
        <span>Not Configured</span>
      </div>
    );
  }
  
  return (
    <div className="flex items-center gap-1.5 px-3 py-1 rounded-full text-sm bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400">
      <XCircle className="h-4 w-4" />
      <span>Offline</span>
    </div>
  );
}

function CapabilityBadge({ icon, label, enabled }: { icon: React.ReactNode; label: string; enabled: boolean }) {
  return (
    <div className={cn(
      'flex items-center gap-1 px-2 py-1 rounded text-xs',
      enabled 
        ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' 
        : 'bg-muted text-muted-foreground'
    )}>
      {icon}
      {label}
    </div>
  );
}
