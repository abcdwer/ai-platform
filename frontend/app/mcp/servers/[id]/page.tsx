'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useMCPStore, MCPServer } from '@/stores/mcpStore';

export default function ServerDetailPage() {
  const params = useParams();
  const router = useRouter();
  const serverId = params.id as string;
  
  const {
    currentServer,
    getServer,
    updateServer,
    connectServer,
    disconnectServer,
    testConnection,
  } = useMCPStore();
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  
  // Form state
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [transportType, setTransportType] = useState('sse');
  const [sseUrl, setSseUrl] = useState('');
  const [sseEndpoint, setSseEndpoint] = useState('/sse');
  const [stdioCommand, setStdioCommand] = useState('');
  const [httpUrl, setHttpUrl] = useState('');
  const [authType, setAuthType] = useState('');

  useEffect(() => {
    const loadServer = async () => {
      try {
        const server = await getServer(serverId);
        if (server) {
          setName(server.name);
          setDescription(server.description || '');
          setTransportType(server.transport_type);
          setSseUrl(server.sse_url || '');
          setSseEndpoint(server.sse_endpoint || '/sse');
          setStdioCommand(server.stdio_command || '');
          setHttpUrl(server.http_url || '');
          setAuthType(server.auth_type || '');
        }
      } catch (error) {
        console.error('Failed to load server:', error);
      }
      setLoading(false);
    };
    loadServer();
  }, [serverId, getServer]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await updateServer(serverId, {
        name,
        description,
        transport_type: transportType as any,
        sse_url: sseUrl || undefined,
        sse_endpoint: sseEndpoint || undefined,
        stdio_command: stdioCommand || undefined,
        http_url: httpUrl || undefined,
        auth_type: authType || undefined,
      });
    } catch (error) {
      console.error('Failed to save:', error);
    }
    setSaving(false);
  };

  const handleConnect = async () => {
    try {
      await connectServer(serverId);
    } catch (error) {
      console.error('Failed to connect:', error);
    }
  };

  const handleDisconnect = async () => {
    try {
      await disconnectServer(serverId);
    } catch (error) {
      console.error('Failed to disconnect:', error);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const result = await testConnection(serverId);
      setTestResult(result);
    } catch (error) {
      setTestResult({ success: false, message: 'Test failed' });
    }
    setTesting(false);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!currentServer) {
    return <div>Server not found</div>;
  }

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="mb-6">
        <button
          onClick={() => router.push('/mcp/servers')}
          className="text-sm text-blue-600 hover:text-blue-800 mb-2"
        >
          ← Back to Servers
        </button>
        <h1 className="text-2xl font-bold text-gray-900">{currentServer.name}</h1>
        <p className="text-gray-600 mt-1">Configure MCP server settings</p>
      </div>

      {testResult && (
        <div className={`mb-6 p-4 rounded-lg ${testResult.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
          <div className="flex items-center">
            {testResult.success ? (
              <svg className="h-5 w-5 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            ) : (
              <svg className="h-5 w-5 text-red-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            )}
            <span className={testResult.success ? 'text-green-700' : 'text-red-700'}>
              {testResult.message}
            </span>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow p-6 space-y-6">
        {/* Basic Info */}
        <div>
          <h2 className="text-lg font-medium text-gray-900 mb-4">Basic Information</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Description</label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={2}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>
        </div>

        {/* Transport Type */}
        <div>
          <h2 className="text-lg font-medium text-gray-900 mb-4">Transport Configuration</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Transport Type</label>
              <select
                value={transportType}
                onChange={(e) => setTransportType(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="sse">SSE (Server-Sent Events)</option>
                <option value="stdio">Stdio (Standard I/O)</option>
                <option value="http_stream">HTTP Stream</option>
              </select>
            </div>

            {transportType === 'sse' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">SSE URL</label>
                  <input
                    type="text"
                    value={sseUrl}
                    onChange={(e) => setSseUrl(e.target.value)}
                    placeholder="https://api.example.com"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">SSE Endpoint</label>
                  <input
                    type="text"
                    value={sseEndpoint}
                    onChange={(e) => setSseEndpoint(e.target.value)}
                    placeholder="/sse"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  />
                </div>
              </>
            )}

            {transportType === 'stdio' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Command</label>
                <input
                  type="text"
                  value={stdioCommand}
                  onChange={(e) => setStdioCommand(e.target.value)}
                  placeholder="npx"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            )}

            {transportType === 'http_stream' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">HTTP URL</label>
                <input
                  type="text"
                  value={httpUrl}
                  onChange={(e) => setHttpUrl(e.target.value)}
                  placeholder="https://api.example.com/mcp"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>
            )}
          </div>
        </div>

        {/* Authentication */}
        <div>
          <h2 className="text-lg font-medium text-gray-900 mb-4">Authentication</h2>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Auth Type</label>
            <select
              value={authType}
              onChange={(e) => setAuthType(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">None</option>
              <option value="bearer">Bearer Token</option>
              <option value="api_key">API Key</option>
            </select>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-between pt-4 border-t">
          <div className="flex space-x-2">
            <button
              onClick={handleTest}
              disabled={testing}
              className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50"
            >
              {testing ? 'Testing...' : 'Test Connection'}
            </button>
            {currentServer.is_connected ? (
              <button
                onClick={handleDisconnect}
                className="px-4 py-2 border border-red-300 text-red-600 rounded-lg hover:bg-red-50"
              >
                Disconnect
              </button>
            ) : (
              <button
                onClick={handleConnect}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                Connect
              </button>
            )}
          </div>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </div>
    </div>
  );
}
