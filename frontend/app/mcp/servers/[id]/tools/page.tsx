'use client';

import { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useMCPStore, MCPTool } from '@/stores/mcpStore';

export default function ToolsPage() {
  const params = useParams();
  const router = useRouter();
  const serverId = params.id as string;
  
  const { tools, loadServerTools, getTool, callTool, currentTool } = useMCPStore();
  
  const [selectedTool, setSelectedTool] = useState<MCPTool | null>(null);
  const [parameters, setParameters] = useState<Record<string, string>>({});
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [calling, setCalling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadTools = async () => {
      try {
        await loadServerTools(serverId);
      } catch (err) {
        console.error('Failed to load tools:', err);
      }
      setLoading(false);
    };
    loadTools();
  }, [serverId, loadServerTools]);

  const handleSelectTool = async (tool: MCPTool) => {
    setSelectedTool(tool);
    setResult(null);
    setError(null);
    
    // Initialize parameters from schema
    const initialParams: Record<string, string> = {};
    if (tool.input_schema?.properties) {
      Object.entries(tool.input_schema.properties).forEach(([key, prop]: [string, any]) => {
        initialParams[key] = '';
      });
    }
    setParameters(initialParams);
  };

  const handleCallTool = async () => {
    if (!selectedTool) return;
    
    setCalling(true);
    setError(null);
    setResult(null);
    
    try {
      // Parse parameters
      const parsedParams: Record<string, any> = {};
      Object.entries(parameters).forEach(([key, value]) => {
        if (value) {
          // Try to parse as JSON, otherwise use as string
          try {
            parsedParams[key] = JSON.parse(value);
          } catch {
            parsedParams[key] = value;
          }
        }
      });
      
      const response = await callTool(selectedTool.id, parsedParams);
      setResult(response);
    } catch (err: any) {
      setError(err.message || 'Failed to call tool');
    }
    setCalling(false);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="mb-6">
        <button
          onClick={() => router.push('/mcp/servers')}
          className="text-sm text-blue-600 hover:text-blue-800 mb-2"
        >
          ← Back to Servers
        </button>
        <h1 className="text-2xl font-bold text-gray-900">MCP Tools</h1>
        <p className="text-gray-600 mt-1">Test and manage MCP tools</p>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* Tool List */}
        <div className="bg-white rounded-lg shadow p-4">
          <h2 className="text-lg font-medium text-gray-900 mb-4">Available Tools</h2>
          
          {tools.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No tools available. Connect to the server to discover tools.
            </div>
          ) : (
            <div className="space-y-2">
              {tools.map((tool) => (
                <button
                  key={tool.id}
                  onClick={() => handleSelectTool(tool)}
                  className={`w-full text-left p-3 rounded-lg transition-colors ${
                    selectedTool?.id === tool.id
                      ? 'bg-blue-50 border border-blue-200'
                      : 'hover:bg-gray-50 border border-transparent'
                  }`}
                >
                  <div className="font-medium text-gray-900">{tool.name}</div>
                  {tool.description && (
                    <div className="text-sm text-gray-500 mt-1">{tool.description}</div>
                  )}
                  {tool.category && (
                    <span className="inline-block mt-2 px-2 py-0.5 text-xs bg-gray-100 text-gray-600 rounded">
                      {tool.category}
                    </span>
                  )}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Tool Details & Test */}
        <div className="col-span-2 bg-white rounded-lg shadow p-6">
          {selectedTool ? (
            <>
              <div className="mb-6">
                <h2 className="text-lg font-medium text-gray-900">{selectedTool.name}</h2>
                {selectedTool.description && (
                  <p className="text-gray-600 mt-1">{selectedTool.description}</p>
                )}
              </div>

              {/* Parameters */}
              <div className="mb-6">
                <h3 className="text-sm font-medium text-gray-700 mb-3">Parameters</h3>
                
                {Object.keys(parameters).length === 0 ? (
                  <p className="text-gray-500 text-sm">This tool has no parameters.</p>
                ) : (
                  <div className="space-y-4">
                    {Object.entries(parameters).map(([key, value]) => (
                      <div key={key}>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          {key}
                        </label>
                        <input
                          type="text"
                          value={value}
                          onChange={(e) => setParameters({ ...parameters, [key]: e.target.value })}
                          placeholder="Enter value (or JSON)"
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                        />
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Execute */}
              <div className="flex items-center space-x-4">
                <button
                  onClick={handleCallTool}
                  disabled={calling}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
                >
                  {calling ? 'Calling...' : 'Execute Tool'}
                </button>
              </div>

              {/* Result */}
              {(result || error) && (
                <div className="mt-6">
                  <h3 className="text-sm font-medium text-gray-700 mb-2">Result</h3>
                  <div className={`p-4 rounded-lg ${error ? 'bg-red-50' : 'bg-green-50'}`}>
                    {error ? (
                      <div className="text-red-700 font-mono text-sm">{error}</div>
                    ) : (
                      <pre className="text-sm font-mono overflow-x-auto">
                        {JSON.stringify(result, null, 2)}
                      </pre>
                    )}
                  </div>
                </div>
              )}

              {/* Stats */}
              <div className="mt-6 pt-6 border-t">
                <h3 className="text-sm font-medium text-gray-700 mb-3">Statistics</h3>
                <div className="grid grid-cols-4 gap-4 text-sm">
                  <div>
                    <div className="text-gray-500">Total Calls</div>
                    <div className="font-medium">{selectedTool.total_calls}</div>
                  </div>
                  <div>
                    <div className="text-gray-500">Success Rate</div>
                    <div className="font-medium">{selectedTool.success_rate.toFixed(1)}%</div>
                  </div>
                  <div>
                    <div className="text-gray-500">Avg Time</div>
                    <div className="font-medium">{selectedTool.avg_execution_time_ms}ms</div>
                  </div>
                  <div>
                    <div className="text-gray-500">Status</div>
                    <div className="font-medium">
                      <span className="text-green-600">{selectedTool.success_count}</span>
                      {' / '}
                      <span className="text-red-600">{selectedTool.failure_count}</span>
                    </div>
                  </div>
                </div>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-64 text-gray-400">
              Select a tool from the list to test it
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
