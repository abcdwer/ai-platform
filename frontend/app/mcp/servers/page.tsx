'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useMCPStore, MCPServer } from '@/stores/mcpStore';

export default function ServersPage() {
  const { servers, serversLoading, loadServers, connectServer, disconnectServer, deleteServer } = useMCPStore();
  const [actionServer, setActionServer] = useState<string | null>(null);

  useEffect(() => {
    loadServers();
  }, [loadServers]);

  const handleConnect = async (id: string) => {
    setActionServer(id);
    try {
      await connectServer(id);
    } catch (error) {
      console.error('Failed to connect:', error);
    }
    setActionServer(null);
  };

  const handleDisconnect = async (id: string) => {
    setActionServer(id);
    try {
      await disconnectServer(id);
    } catch (error) {
      console.error('Failed to disconnect:', error);
    }
    setActionServer(null);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to delete this server?')) return;
    try {
      await deleteServer(id);
    } catch (error) {
      console.error('Failed to delete:', error);
    }
  };

  const getTransportIcon = (type: string) => {
    switch (type) {
      case 'sse':
        return (
          <svg className="h-5 w-5 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
          </svg>
        );
      case 'stdio':
        return (
          <svg className="h-5 w-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        );
      case 'http_stream':
        return (
          <svg className="h-5 w-5 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" />
          </svg>
        );
      default:
        return null;
    }
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">MCP Servers</h1>
          <p className="text-gray-600 mt-1">Manage Model Context Protocol servers</p>
        </div>
        <Link
          href="/mcp/servers/new"
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Add Server
        </Link>
      </div>

      {serversLoading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      ) : servers.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
          </svg>
          <h3 className="mt-4 text-lg font-medium text-gray-900">No servers yet</h3>
          <p className="mt-2 text-gray-500">Add your first MCP server to get started.</p>
          <Link
            href="/mcp/servers/new"
            className="mt-4 inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Add Server
          </Link>
        </div>
      ) : (
        <div className="grid gap-4">
          {servers.map((server) => (
            <div key={server.id} className="bg-white rounded-lg shadow p-6">
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-4">
                  <div className={`p-3 rounded-lg ${server.is_connected ? 'bg-green-100' : 'bg-gray-100'}`}>
                    {getTransportIcon(server.transport_type)}
                  </div>
                  <div>
                    <div className="flex items-center space-x-3">
                      <h3 className="text-lg font-medium text-gray-900">{server.name}</h3>
                      {server.is_connected ? (
                        <span className="px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                          Connected
                        </span>
                      ) : (
                        <span className="px-2 py-1 text-xs font-medium bg-gray-100 text-gray-600 rounded-full">
                          Disconnected
                        </span>
                      )}
                    </div>
                    {server.description && (
                      <p className="text-sm text-gray-500 mt-1">{server.description}</p>
                    )}
                    <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                      <span className="capitalize">{server.transport_type.replace('_', ' ')}</span>
                      {server.last_connected_at && (
                        <>
                          <span>•</span>
                          <span>Last connected: {new Date(server.last_connected_at).toLocaleString()}</span>
                        </>
                      )}
                    </div>
                    {server.connection_error && (
                      <p className="text-sm text-red-500 mt-2">{server.connection_error}</p>
                    )}
                  </div>
                </div>
                
                <div className="flex space-x-2">
                  <Link
                    href={`/mcp/servers/${server.id}`}
                    className="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Configure
                  </Link>
                  <Link
                    href={`/mcp/servers/${server.id}/tools`}
                    className="px-3 py-1 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Tools
                  </Link>
                  {server.is_connected ? (
                    <button
                      onClick={() => handleDisconnect(server.id)}
                      disabled={actionServer === server.id}
                      className="px-3 py-1 text-sm border border-red-300 text-red-600 rounded-lg hover:bg-red-50 disabled:opacity-50"
                    >
                      Disconnect
                    </button>
                  ) : (
                    <button
                      onClick={() => handleConnect(server.id)}
                      disabled={actionServer === server.id}
                      className="px-3 py-1 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
                    >
                      Connect
                    </button>
                  )}
                  <button
                    onClick={() => handleDelete(server.id)}
                    className="px-3 py-1 text-sm text-red-600 border border-red-300 rounded-lg hover:bg-red-50"
                  >
                    Delete
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
