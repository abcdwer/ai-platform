'use client';

import { useState, useEffect } from 'react';
import { useAuthStore } from '@/stores';
import { 
  Search, 
  Copy, 
  Check, 
  Download, 
  Book, 
  Code, 
  MessageSquare, 
  Workflow, 
  Database,
  Users,
  Settings,
  Cpu,
  FileText,
  ChevronDown,
  ChevronRight,
  ExternalLink
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/components/ui/use-toast';
import { cn } from '@/lib/utils';

// API endpoint categories with icons
const categoryIcons: Record<string, React.ReactNode> = {
  'Auth': <Users className="w-4 h-4" />,
  'Conversations': <MessageSquare className="w-4 h-4" />,
  'Workflows': <Workflow className="w-4 h-4" />,
  'Knowledge Base': <Database className="w-4 h-4" />,
  'Models': <Cpu className="w-4 h-4" />,
  'Multi-Agent': <Users className="w-4 h-4" />,
  'Fine-tuning': <Settings className="w-4 h-4" />,
  'MCP Servers': <Settings className="w-4 h-4" />,
  'Export & Import': <FileText className="w-4 h-4" />,
};

// API documentation data
const apiEndpoints = {
  'Auth': [
    {
      method: 'POST',
      path: '/api/auth/register',
      summary: 'Register new user',
      description: 'Create a new user account with email and password',
      requestBody: {
        email: 'user@example.com',
        password: 'password123',
        username: 'johndoe',
        full_name: 'John Doe'
      },
      response: { id: 'uuid', email: 'user@example.com' },
    },
    {
      method: 'POST',
      path: '/api/auth/login',
      summary: 'Login user',
      description: 'Authenticate with username/email and password, returns JWT token',
      requestBody: { username: 'johndoe', password: 'password123' },
      response: { access_token: 'eyJ...', token_type: 'bearer' },
    },
    {
      method: 'GET',
      path: '/api/auth/me',
      summary: 'Get current user',
      description: 'Get authenticated user profile',
      response: { id: 'uuid', email: 'user@example.com' },
    },
    {
      method: 'POST',
      path: '/api/auth/refresh',
      summary: 'Refresh token',
      description: 'Refresh expired access token',
      requestBody: { refresh_token: 'token' },
      response: { access_token: 'eyJ...', token_type: 'bearer' },
    },
  ],
  'Conversations': [
    {
      method: 'GET',
      path: '/api/conversations',
      summary: 'List conversations',
      description: 'Get paginated list of user conversations',
      queryParams: [
        { name: 'page', type: 'number', default: '1', description: 'Page number' },
        { name: 'page_size', type: 'number', default: '20', description: 'Items per page' },
        { name: 'search', type: 'string', description: 'Search by title' },
        { name: 'include_archived', type: 'boolean', default: 'false', description: 'Include archived' },
      ],
      response: { items: [], total: 100, page: 1, page_size: 20 },
    },
    {
      method: 'POST',
      path: '/api/conversations',
      summary: 'Create conversation',
      description: 'Create a new chat conversation',
      requestBody: {
        title: 'My Chat',
        model: 'llama2',
        model_provider: 'ollama',
      },
      response: { id: 'uuid', title: 'My Chat', messages: [] },
    },
    {
      method: 'GET',
      path: '/api/conversations/{id}',
      summary: 'Get conversation',
      description: 'Get conversation details with messages',
      response: { id: 'uuid', title: '...', messages: [] },
    },
    {
      method: 'PUT',
      path: '/api/conversations/{id}',
      summary: 'Update conversation',
      description: 'Update conversation title or status',
      requestBody: { title: 'New Title', is_pinned: true },
      response: { id: 'uuid', title: 'New Title' },
    },
    {
      method: 'DELETE',
      path: '/api/conversations/{id}',
      summary: 'Delete conversation',
      description: 'Permanently delete a conversation',
      response: { message: 'Conversation deleted successfully' },
    },
    {
      method: 'GET',
      path: '/api/conversations/{id}/export',
      summary: 'Export conversation',
      description: 'Export conversation to Markdown, JSON, PDF, or HTML',
      queryParams: [
        { name: 'format', type: 'string', default: 'markdown', description: 'Export format' },
      ],
      response: 'File download',
    },
  ],
  'Chat': [
    {
      method: 'POST',
      path: '/api/chat',
      summary: 'Send chat message',
      description: 'Send a message and get AI response',
      requestBody: {
        messages: [
          { role: 'user', content: 'Hello!' }
        ],
        model: 'llama2',
        stream: false,
      },
      response: { message: { role: 'assistant', content: 'Hello!' } },
    },
  ],
  'Knowledge Base': [
    {
      method: 'GET',
      path: '/api/knowledge',
      summary: 'List knowledge bases',
      description: 'Get paginated list of knowledge bases',
      response: { items: [], total: 10, page: 1 },
    },
    {
      method: 'POST',
      path: '/api/knowledge',
      summary: 'Create knowledge base',
      description: 'Create a new knowledge base',
      requestBody: {
        name: 'My Knowledge Base',
        description: 'Description',
        tags: ['tag1', 'tag2'],
      },
      response: { id: 'uuid', name: 'My Knowledge Base' },
    },
    {
      method: 'GET',
      path: '/api/knowledge/{id}',
      summary: 'Get knowledge base',
      description: 'Get knowledge base details',
      response: { id: 'uuid', name: '...', document_count: 10 },
    },
    {
      method: 'POST',
      path: '/api/knowledge/{id}/documents',
      summary: 'Upload document',
      description: 'Upload a document to knowledge base',
      requestBody: 'multipart/form-data with file',
      response: { id: 'uuid', status: 'processing' },
    },
    {
      method: 'POST',
      path: '/api/knowledge/{id}/search',
      summary: 'Search knowledge base',
      description: 'Semantic search across documents',
      requestBody: { query: 'search query', top_k: 5 },
      response: { results: [], query: 'search query', total: 5 },
    },
    {
      method: 'POST',
      path: '/api/knowledge/{id}/chat',
      summary: 'RAG chat',
      description: 'Chat with knowledge base using RAG',
      requestBody: { query: 'question?', top_k: 5 },
      response: { answer: '...', sources: [], retrieved_chunks: 5 },
    },
    {
      method: 'GET',
      path: '/api/knowledge/{id}/export',
      summary: 'Export knowledge base',
      description: 'Export knowledge base to Markdown, JSON, or HTML',
      queryParams: [
        { name: 'format', type: 'string', default: 'json', description: 'Export format' },
      ],
      response: 'File download',
    },
    {
      method: 'POST',
      path: '/api/knowledge/{id}/import',
      summary: 'Import documents',
      description: 'Batch import documents into knowledge base',
      requestBody: {
        documents: [
          { title: 'Doc 1', content: '...', source: 'url' }
        ]
      },
      response: { message: 'Imported 5 documents', imported_count: 5 },
    },
  ],
  'Workflows': [
    {
      method: 'GET',
      path: '/api/workflows',
      summary: 'List workflows',
      description: 'Get paginated list of workflows',
      response: { items: [], total: 10, page: 1 },
    },
    {
      method: 'POST',
      path: '/api/workflows',
      summary: 'Create workflow',
      description: 'Create a new workflow',
      requestBody: {
        name: 'My Workflow',
        description: 'Description',
        graph_data: { nodes: [], edges: [] },
      },
      response: { id: 'uuid', name: 'My Workflow', status: 'draft' },
    },
    {
      method: 'GET',
      path: '/api/workflows/{id}',
      summary: 'Get workflow',
      description: 'Get workflow with graph configuration',
      response: { id: 'uuid', name: '...', graph_data: { nodes: [], edges: [] } },
    },
    {
      method: 'PUT',
      path: '/api/workflows/{id}',
      summary: 'Update workflow',
      description: 'Update workflow configuration',
      requestBody: { name: 'New Name', graph_data: { nodes: [], edges: [] } },
      response: { id: 'uuid' },
    },
    {
      method: 'POST',
      path: '/api/workflows/{id}/publish',
      summary: 'Publish workflow',
      description: 'Publish workflow to make it executable',
      response: { id: 'uuid', version: 2, status: 'published' },
    },
    {
      method: 'POST',
      path: '/api/workflows/{id}/execute',
      summary: 'Execute workflow',
      description: 'Start workflow execution',
      requestBody: { inputs: {} },
      response: { execution_id: 'uuid', status: 'pending' },
    },
    {
      method: 'GET',
      path: '/api/workflows/{id}/share',
      summary: 'Share workflow',
      description: 'Generate shareable link and export config',
      response: { share_token: 'uuid', share_url: '...', workflow: {} },
    },
    {
      method: 'GET',
      path: '/api/workflows/{id}/export',
      summary: 'Export workflow',
      description: 'Export workflow as JSON configuration',
      response: 'File download (JSON)',
    },
    {
      method: 'POST',
      path: '/api/workflows/import',
      summary: 'Import workflow',
      description: 'Import workflow from JSON configuration',
      requestBody: { name: '...', description: '...', graph_data: {} },
      response: { id: 'uuid', name: '...', status: 'draft' },
    },
  ],
  'Models': [
    {
      method: 'GET',
      path: '/api/models',
      summary: 'List models',
      description: 'Get all available models by provider',
      response: { ollama: [{ name: 'llama2' }], openai: [] },
    },
    {
      method: 'GET',
      path: '/api/models/{id}',
      summary: 'Get model config',
      description: 'Get specific model configuration',
      response: { id: 'uuid', name: 'llama2', provider: 'ollama' },
    },
  ],
  'Multi-Agent': [
    {
      method: 'GET',
      path: '/api/multi-agent/sessions',
      summary: 'List sessions',
      description: 'Get all multi-agent sessions',
      response: { items: [], total: 5 },
    },
    {
      method: 'POST',
      path: '/api/multi-agent/sessions',
      summary: 'Create session',
      description: 'Create a new multi-agent session',
      requestBody: { name: 'My Session', mode: 'sequential', agent_ids: [] },
      response: { id: 'uuid', name: 'My Session', ... },
    },
    {
      method: 'POST',
      path: '/api/multi-agent/run',
      summary: 'Run multi-agent',
      description: 'Execute task with multiple agents',
      requestBody: { session_id: 'uuid', task: 'task description' },
      response: { results: [], task_id: 'uuid' },
    },
  ],
  'Fine-tuning': [
    {
      method: 'GET',
      path: '/api/finetune/datasets',
      summary: 'List datasets',
      description: 'Get all fine-tuning datasets',
      response: { items: [], total: 3 },
    },
    {
      method: 'POST',
      path: '/api/finetune/datasets',
      summary: 'Create dataset',
      description: 'Create a new training dataset',
      requestBody: { name: 'My Dataset', description: '...' },
      response: { id: 'uuid', name: 'My Dataset' },
    },
    {
      method: 'GET',
      path: '/api/finetune/jobs',
      summary: 'List jobs',
      description: 'Get all fine-tuning jobs',
      response: { items: [], total: 2 },
    },
    {
      method: 'POST',
      path: '/api/finetune/jobs',
      summary: 'Create training job',
      description: 'Start a new fine-tuning job',
      requestBody: { name: 'Job 1', base_model: 'llama2', dataset_id: 'uuid' },
      response: { id: 'uuid', status: 'pending' },
    },
  ],
  'MCP Servers': [
    {
      method: 'GET',
      path: '/api/mcp/servers',
      summary: 'List servers',
      description: 'Get all MCP server configurations',
      response: { items: [], total: 2 },
    },
    {
      method: 'POST',
      path: '/api/mcp/servers',
      summary: 'Create server',
      description: 'Create a new MCP server',
      requestBody: { name: 'My Server', command: 'npx', args: ['-y', '@example/server'] },
      response: { id: 'uuid', name: 'My Server', status: 'stopped' },
    },
  ],
  'System': [
    {
      method: 'GET',
      path: '/health',
      summary: 'Health check',
      description: 'Check API health status',
      response: { status: 'healthy', timestamp: '...' },
    },
    {
      method: 'GET',
      path: '/api/status',
      summary: 'System status',
      description: 'Get detailed system status',
      response: { status: 'online', providers: {} },
    },
    {
      method: 'GET',
      path: '/api/docs/postman-collection',
      summary: 'Download Postman collection',
      description: 'Download Postman collection for all endpoints',
      response: 'File download (JSON)',
    },
  ],
};

const methodColors: Record<string, string> = {
  GET: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
  POST: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
  PUT: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300',
  PATCH: 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300',
  DELETE: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
};

export default function APIDocsPage() {
  const { token } = useAuthStore();
  const { toast } = useToast();
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedCategories, setExpandedCategories] = useState<string[]>(Object.keys(apiEndpoints));
  const [expandedEndpoint, setExpandedEndpoint] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const toggleCategory = (category: string) => {
    setExpandedCategories(prev =>
      prev.includes(category)
        ? prev.filter(c => c !== category)
        : [...prev, category]
    );
  };

  const copyToClipboard = async (text: string, id: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
      toast({ title: 'Copied to clipboard' });
    } catch {
      toast({ title: 'Failed to copy', variant: 'destructive' });
    }
  };

  const downloadPostmanCollection = async () => {
    try {
      const response = await fetch('/api/docs/postman-collection');
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'ai-platform-api.postman_collection.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
        toast({ title: 'Postman collection downloaded' });
      }
    } catch {
      toast({ title: 'Failed to download', variant: 'destructive' });
    }
  };

  const filteredEndpoints = Object.entries(apiEndpoints).reduce((acc, [category, endpoints]) => {
    const filtered = endpoints.filter(endpoint =>
      endpoint.path.toLowerCase().includes(searchQuery.toLowerCase()) ||
      endpoint.summary.toLowerCase().includes(searchQuery.toLowerCase()) ||
      endpoint.description.toLowerCase().includes(searchQuery.toLowerCase())
    );
    if (filtered.length > 0) {
      acc[category] = filtered;
    }
    return acc;
  }, {} as Record<string, typeof apiEndpoints['Auth']>);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b bg-card">
        <div className="container py-8">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-primary/10 rounded-lg">
                <Book className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h1 className="text-2xl font-bold">API Documentation</h1>
                <p className="text-muted-foreground">AI Platform REST API Reference</p>
              </div>
            </div>
            <Button onClick={downloadPostmanCollection} variant="outline">
              <Download className="w-4 h-4 mr-2" />
              Download Postman Collection
            </Button>
          </div>

          {/* Search */}
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search endpoints..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="container py-8">
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">Categories</CardTitle>
              </CardHeader>
              <CardContent className="space-y-1">
                {Object.keys(filteredEndpoints).map(category => (
                  <button
                    key={category}
                    onClick={() => toggleCategory(category)}
                    className={cn(
                      "w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors",
                      expandedCategories.includes(category)
                        ? "bg-primary/10 text-primary"
                        : "hover:bg-muted"
                    )}
                  >
                    {categoryIcons[category]}
                    <span className="flex-1 text-left">{category}</span>
                    <Badge variant="secondary" className="text-xs">
                      {filteredEndpoints[category].length}
                    </Badge>
                  </button>
                ))}
              </CardContent>
            </Card>

            {/* Quick Links */}
            <Card className="mt-4">
              <CardHeader className="pb-3">
                <CardTitle className="text-sm">Quick Links</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                <a
                  href="/docs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 text-sm text-muted-foreground hover:text-primary"
                >
                  <ExternalLink className="w-4 h-4" />
                  Swagger UI
                </a>
                <a
                  href="/redoc"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 text-sm text-muted-foreground hover:text-primary"
                >
                  <ExternalLink className="w-4 h-4" />
                  ReDoc
                </a>
              </CardContent>
            </Card>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3 space-y-6">
            {Object.entries(filteredEndpoints).map(([category, endpoints]) => (
              <Card key={category}>
                <CardHeader
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => toggleCategory(category)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {categoryIcons[category]}
                      <CardTitle>{category}</CardTitle>
                    </div>
                    {expandedCategories.includes(category) ? (
                      <ChevronDown className="w-4 h-4" />
                    ) : (
                      <ChevronRight className="w-4 h-4" />
                    )}
                  </div>
                  <CardDescription>
                    {endpoints.length} endpoint{endpoints.length !== 1 ? 's' : ''}
                  </CardDescription>
                </CardHeader>

                {expandedCategories.includes(category) && (
                  <CardContent className="space-y-4">
                    {endpoints.map((endpoint, index) => (
                      <div
                        key={index}
                        className="border rounded-lg overflow-hidden"
                      >
                        <button
                          onClick={() => setExpandedEndpoint(
                            expandedEndpoint === `${category}-${index}` 
                              ? null 
                              : `${category}-${index}`
                          )}
                          className="w-full flex items-center gap-3 p-4 hover:bg-muted/50 transition-colors"
                        >
                          <Badge
                            className={cn('font-medium', methodColors[endpoint.method])}
                          >
                            {endpoint.method}
                          </Badge>
                          <code className="flex-1 text-left font-mono text-sm">
                            {endpoint.path}
                          </code>
                          <span className="text-sm text-muted-foreground">
                            {endpoint.summary}
                          </span>
                          {expandedEndpoint === `${category}-${index}` ? (
                            <ChevronDown className="w-4 h-4" />
                          ) : (
                            <ChevronRight className="w-4 h-4" />
                          )}
                        </button>

                        {expandedEndpoint === `${category}-${index}` && (
                          <div className="border-t p-4 space-y-4 bg-muted/30">
                            <p className="text-sm text-muted-foreground">
                              {endpoint.description}
                            </p>

                            {/* Query Parameters */}
                            {endpoint.queryParams && (
                              <div>
                                <h4 className="text-sm font-semibold mb-2">Query Parameters</h4>
                                <div className="bg-muted rounded-lg p-3 space-y-2">
                                  {endpoint.queryParams.map((param, i) => (
                                    <div key={i} className="flex items-center gap-2 text-sm">
                                      <code className="bg-background px-2 py-0.5 rounded">
                                        {param.name}
                                      </code>
                                      <Badge variant="outline" className="text-xs">
                                        {param.type}
                                      </Badge>
                                      {param.default && (
                                        <span className="text-muted-foreground">
                                          = {param.default}
                                        </span>
                                      )}
                                      <span className="text-muted-foreground">
                                        {param.description}
                                      </span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}

                            {/* Request Body */}
                            {endpoint.requestBody && (
                              <div>
                                <div className="flex items-center justify-between mb-2">
                                  <h4 className="text-sm font-semibold">Request Body</h4>
                                  <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      copyToClipboard(
                                        JSON.stringify(endpoint.requestBody, null, 2),
                                        'request'
                                      );
                                    }}
                                  >
                                    {copiedId === 'request' ? (
                                      <Check className="w-4 h-4" />
                                    ) : (
                                      <Copy className="w-4 h-4" />
                                    )}
                                  </Button>
                                </div>
                                <pre className="bg-muted rounded-lg p-3 overflow-x-auto text-sm">
                                  <code>
                                    {typeof endpoint.requestBody === 'string'
                                      ? endpoint.requestBody
                                      : JSON.stringify(endpoint.requestBody, null, 2)
                                    }
                                  </code>
                                </pre>
                              </div>
                            )}

                            {/* Response */}
                            <div>
                              <div className="flex items-center justify-between mb-2">
                                <h4 className="text-sm font-semibold">Response Example</h4>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    copyToClipboard(
                                      JSON.stringify(endpoint.response, null, 2),
                                      'response'
                                    );
                                  }}
                                >
                                  {copiedId === 'response' ? (
                                    <Check className="w-4 h-4" />
                                  ) : (
                                    <Copy className="w-4 h-4" />
                                  )}
                                </Button>
                              </div>
                              <pre className="bg-muted rounded-lg p-3 overflow-x-auto text-sm">
                                <code>
                                  {typeof endpoint.response === 'string'
                                    ? endpoint.response
                                    : JSON.stringify(endpoint.response, null, 2)
                                  }
                                </code>
                              </pre>
                            </div>

                            {/* cURL Example */}
                            <div>
                              <div className="flex items-center justify-between mb-2">
                                <h4 className="text-sm font-semibold">cURL Example</h4>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    let curl = `curl -X ${endpoint.method} 'http://localhost:8000${endpoint.path}'`;
                                    if (token) {
                                      curl += ` \\\n  -H 'Authorization: Bearer ${token.substring(0, 20)}...'`;
                                    }
                                    if (endpoint.requestBody && typeof endpoint.requestBody === 'object') {
                                      curl += ` \\\n  -H 'Content-Type: application/json'`;
                                      curl += ` \\\n  -d '${JSON.stringify(endpoint.requestBody)}'`;
                                    }
                                    copyToClipboard(curl, 'curl');
                                  }}
                                >
                                  {copiedId === 'curl' ? (
                                    <Check className="w-4 h-4" />
                                  ) : (
                                    <Copy className="w-4 h-4" />
                                  )}
                                </Button>
                              </div>
                              <pre className="bg-muted rounded-lg p-3 overflow-x-auto text-sm">
                                <code className="text-muted-foreground">
                                  {`# ${endpoint.summary}\ncurl -X ${endpoint.method} 'http://localhost:8000${endpoint.path}'`}
                                  {token && `\n  -H 'Authorization: Bearer <your-token>'`}
                                  {endpoint.requestBody && typeof endpoint.requestBody === 'object' && (
                                    `\n  -H 'Content-Type: application/json' \\\n  -d '${JSON.stringify(endpoint.requestBody)}'`
                                  )}
                                </code>
                              </pre>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </CardContent>
                )}
              </CardHeader>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}
