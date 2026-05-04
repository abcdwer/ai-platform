'use client';

import React, { useCallback, useRef, useMemo } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  Connection,
  Edge,
  Node,
  useNodesState,
  useEdgesState,
  OnConnect,
  OnNodesChange,
  OnEdgesChange,
  applyNodeChanges,
  applyEdgeChanges,
  NodeChange,
  EdgeChange,
  BackgroundVariant,
  Panel,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { useWorkflowStore, WorkflowNode, WorkflowEdge, NODE_TYPES_CONFIG } from '@/stores/workflowStore';
import { nodeTypes } from './nodes';
import { NodePanel } from './node-panel';
import { NodeConfig } from './node-config';
import ELK from 'elkjs/lib/elk.bundled.js';

const elk = new ELK();

async function getLayoutedElements(nodes: Node[], edges: Edge[]) {
  const graph = {
    id: 'root',
    layoutOptions: {
      'elk.algorithm': 'layered',
      'elk.direction': 'RIGHT',
      'elk.spacing.nodeNode': '80',
      'elk.layered.spacing.nodeNodeBetweenLayers': '100',
      'elk.padding': '[top=50,left=50,bottom=50,right=50]',
    },
    children: nodes.map((node) => ({
      id: node.id,
      width: 200,
      height: 80,
    })),
    edges: edges.map((edge) => ({
      id: edge.id,
      sources: [edge.source],
      targets: [edge.target],
    })),
  };

  const layoutedGraph = await elk.layout(graph);

  return {
    nodes: nodes.map((node) => {
      const layoutedNode = layoutedGraph.children?.find((n) => n.id === node.id);
      return {
        ...node,
        position: {
          x: layoutedNode?.x ?? node.position.x,
          y: layoutedNode?.y ?? node.position.y,
        },
      };
    }),
    edges,
  };
}

export function WorkflowEditor() {
  const {
    nodes: storeNodes,
    edges: storeEdges,
    setNodes: setStoreNodes,
    setEdges: setStoreEdges,
    addNode,
    setSelectedNode,
    currentWorkflow,
  } = useWorkflowStore();

  // Convert store nodes to React Flow format
  const rfNodes = useMemo(() => {
    return storeNodes.map((n) => ({
      id: n.id,
      type: n.type,
      position: n.position,
      data: n.data,
      selected: false,
    }));
  }, [storeNodes]);

  const rfEdges = useMemo(() => {
    return storeEdges.map((e) => ({
      id: e.id,
      source: e.source,
      target: e.target,
      sourceHandle: e.sourceHandle,
      targetHandle: e.targetHandle,
      label: e.label,
      type: 'smoothstep',
      animated: false,
    }));
  }, [storeEdges]);

  const [nodes, setNodes] = useNodesState(rfNodes);
  const [edges, setEdges] = useEdgesState(rfEdges);
  const reactFlowWrapper = useRef<HTMLDivElement>(null);

  // Sync with store when external changes happen
  React.useEffect(() => {
    setNodes(rfNodes);
    setEdges(rfEdges);
  }, [rfNodes, rfEdges, setNodes, setEdges]);

  const onNodesChange: OnNodesChange = useCallback(
    (changes: NodeChange[]) => {
      setNodes((nds) => applyNodeChanges(changes, nds));
      
      // Update store on position changes
      changes.forEach((change) => {
        if (change.type === 'position' && change.position) {
          const storeNodes = useWorkflowStore.getState().nodes;
          const nodeIndex = storeNodes.findIndex((n) => n.id === change.id);
          if (nodeIndex !== -1) {
            const newNodes = [...storeNodes];
            newNodes[nodeIndex] = {
              ...newNodes[nodeIndex],
              position: change.position,
            };
            useWorkflowStore.setState({ nodes: newNodes });
          }
        }
      });
    },
    [setNodes]
  );

  const onEdgesChange: OnEdgesChange = useCallback(
    (changes: EdgeChange[]) => {
      setEdges((eds) => applyEdgeChanges(changes, eds));
    },
    [setEdges]
  );

  const onConnect: OnConnect = useCallback(
    (connection: Connection) => {
      setEdges((eds) =>
        addEdge(
          {
            ...connection,
            id: `edge-${Date.now()}`,
            type: 'smoothstep',
          },
          eds
        )
      );

      // Update store
      const newEdge: WorkflowEdge = {
        id: `edge-${Date.now()}`,
        source: connection.source!,
        target: connection.target!,
        sourceHandle: connection.sourceHandle || undefined,
        targetHandle: connection.targetHandle || undefined,
      };
      
      const storeEdges = useWorkflowStore.getState().edges;
      const exists = storeEdges.some(
        (e) =>
          e.source === newEdge.source &&
          e.target === newEdge.target &&
          e.sourceHandle === newEdge.sourceHandle
      );
      
      if (!exists) {
        useWorkflowStore.setState({ edges: [...storeEdges, newEdge] });
      }
    },
    [setEdges]
  );

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      const storeNode = storeNodes.find((n) => n.id === node.id);
      if (storeNode) {
        setSelectedNode(storeNode);
      }
    },
    [storeNodes, setSelectedNode]
  );

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, [setSelectedNode]);

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const type = event.dataTransfer.getData('application/reactflow');
      if (!type) return;

      const reactFlowBounds = reactFlowWrapper.current?.getBoundingClientRect();
      if (!reactFlowBounds) return;

      const position = {
        x: event.clientX - reactFlowBounds.left - 90,
        y: event.clientY - reactFlowBounds.top - 40,
      };

      const config = NODE_TYPES_CONFIG[type];
      const newNode: WorkflowNode = {
        id: `${type}-${Date.now()}`,
        type,
        position,
        data: {
          label: config?.label || type,
          config: getDefaultConfig(type),
        },
      };

      addNode(newNode);
    },
    [addNode]
  );

  const handleAutoLayout = useCallback(async () => {
    const { nodes: currentNodes, edges: currentEdges } = useWorkflowStore.getState();
    
    if (currentNodes.length === 0) return;

    const { nodes: layoutedNodes, edges: layoutedEdges } = await getLayoutedElements(
      currentNodes.map((n) => ({
        id: n.id,
        type: n.type,
        position: n.position,
        data: n.data,
        selected: false,
      })),
      currentEdges.map((e) => ({
        id: e.id,
        source: e.source,
        target: e.target,
        sourceHandle: e.sourceHandle,
        targetHandle: e.targetHandle,
        label: e.label,
        type: 'smoothstep',
        animated: false,
      }))
    );

    setNodes(layoutedNodes);
    setEdges(layoutedEdges);

    // Update store
    useWorkflowStore.setState({
      nodes: layoutedNodes.map((n) => ({
        id: n.id,
        type: n.type,
        position: n.position,
        data: n.data,
      })),
      edges: currentEdges,
    });
  }, [setNodes, setEdges]);

  return (
    <div ref={reactFlowWrapper} className="w-full h-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        onDragOver={onDragOver}
        onDrop={onDrop}
        nodeTypes={nodeTypes}
        fitView
        snapToGrid
        snapGrid={[15, 15]}
        defaultEdgeOptions={{
          type: 'smoothstep',
          animated: false,
        }}
      >
        <Background variant={BackgroundVariant.Dots} gap={20} size={1} />
        <Controls />
        <MiniMap
          nodeStrokeWidth={3}
          zoomable
          pannable
          style={{ backgroundColor: 'var(--background)' }}
        />
        
        {/* Node Panel */}
        <NodePanel />
        
        {/* Node Config Panel */}
        <NodeConfig />
        
        {/* Top-right controls */}
        <Panel position="top-right">
          <div className="flex gap-2">
            <button
              onClick={handleAutoLayout}
              className="px-3 py-2 bg-card border rounded-md text-sm hover:bg-accent transition-colors"
            >
              Auto Layout
            </button>
          </div>
        </Panel>
      </ReactFlow>
    </div>
  );
}

function getDefaultConfig(nodeType: string): Record<string, any> {
  switch (nodeType) {
    case 'start':
      return { trigger: 'manual' };
    case 'llm':
      return { model: 'gpt-4', provider: 'openai', prompt_template: '{{input}}', temperature: 0.7 };
    case 'code':
      return { language: 'python', code: '# Process input\nresult = input\nreturn result' };
    case 'condition':
      return { condition_type: 'expression', expression: '{{input}} == true' };
    case 'loop':
      return { loop_type: 'count', iterations: 10 };
    case 'delay':
      return { delay_type: 'seconds', delay_value: 1 };
    case 'http':
      return { method: 'GET', url: 'https://api.example.com' };
    case 'transform':
      return { transform_type: 'json_path', json_path: '$.data' };
    case 'knowledge':
      return { top_k: 5, similarity_threshold: 0.7 };
    case 'text_splitter':
      return { chunk_size: 1000, chunk_overlap: 200 };
    case 'embedding':
      return { model: 'text-embedding-ada-002' };
    case 'web_search':
      return { num_results: 10 };
    case 'file_read':
      return { file_path: '' };
    case 'file_write':
      return { file_path: '', content_template: '{{input}}' };
    case 'send_email':
      return { to: '', subject: 'Workflow Notification', body_template: '{{input}}' };
    case 'notification':
      return { notification_type: 'log', message_template: '{{input}}' };
    default:
      return {};
  }
}
