"""Workflow execution engine."""
import asyncio
from typing import Any, Dict, List, Optional, Set
from datetime import datetime

from app.workflow.context import ExecutionContext
from app.workflow.nodes import create_node, BaseNode, NodeResult
from app.workflow.validators import WorkflowValidator


class WorkflowEngine:
    """Engine for executing workflows."""
    
    def __init__(self, service):
        """Initialize engine with workflow service."""
        self.service = service
        self.validator = WorkflowValidator()
        self.max_retries = 3
    
    async def execute(self, graph_data: dict, inputs: dict = None) -> dict:
        """Execute a workflow.
        
        Args:
            graph_data: Workflow graph definition with nodes and edges
            inputs: Initial inputs to the workflow
            
        Returns:
            Final workflow outputs
        """
        # Validate workflow
        errors = self.validator.validate(graph_data)
        if errors:
            raise ValueError(f"Workflow validation failed: {', '.join(errors)}")
        
        # Initialize context
        context = ExecutionContext()
        if inputs:
            context.variables.update(inputs)
        
        # Get execution order
        execution_levels = self.validator.get_execution_order(graph_data)
        
        # Build node lookup and adjacency list
        nodes = {n['id']: n for n in graph_data.get('nodes', [])}
        edges = graph_data.get('edges', [])
        
        # Build edge lookup (source -> list of targets)
        edge_map = {}
        for edge in edges:
            source = edge.get('source')
            target = edge.get('target')
            handle = edge.get('sourceHandle', 'output')
            
            if source not in edge_map:
                edge_map[source] = []
            edge_map[source].append({
                'target': target,
                'handle': handle
            })
        
        # Execute nodes level by level
        for level_nodes in execution_levels:
            level_results = []
            
            for node_id in level_nodes:
                node_data = nodes[node_id]
                node_type = node_data.get('type')
                
                # Skip nodes without execution (like some UI-only nodes)
                if node_type not in ['start', 'end', 'llm', 'code', 'condition', 
                                     'loop', 'delay', 'http', 'transform', 'merge',
                                     'knowledge', 'agent', 'text_splitter', 'embedding',
                                     'web_search', 'file_read', 'file_write', 
                                     'send_email', 'notification']:
                    continue
                
                # Check if node should be skipped (condition not met)
                condition_result = context.get_variable(f"{node_id}_skip")
                if condition_result:
                    await self._skip_node(context, node_id, node_type)
                    continue
                
                # Execute node
                result = await self._execute_node(context, node_id, node_type, node_data)
                level_results.append((node_id, result))
                
                # Handle condition branching
                if node_type == 'condition':
                    self._process_condition_branching(context, node_id, result, edges)
            
            # Wait for parallel level to complete
            await asyncio.sleep(0)
        
        # Get final output
        final_output = context.get_variable('result', context.get_variable('output'))
        
        return {
            'success': True,
            'output': final_output,
            'variables': context.variables
        }
    
    async def _execute_node(
        self, 
        context: ExecutionContext, 
        node_id: str, 
        node_type: str, 
        node_data: dict
    ) -> NodeResult:
        """Execute a single node with retry logic."""
        config = node_data.get('data', {}).get('config', {})
        label = node_data.get('data', {}).get('label', node_id)
        
        for attempt in range(self.max_retries):
            try:
                # Create node instance
                node = create_node(node_id, node_type, config)
                
                # Execute
                result = await node.execute(context)
                
                if result.success:
                    return result
                else:
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                        continue
                    return result
                    
            except Exception as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1 * (attempt + 1))
                    continue
                return NodeResult(success=False, error=str(e))
        
        return NodeResult(success=False, error="Max retries exceeded")
    
    async def _skip_node(
        self, 
        context: ExecutionContext, 
        node_id: str, 
        node_type: str
    ):
        """Handle node skipping."""
        # Set skip flag in context
        context.set_node_output(node_id, NodeResult(
            success=True, 
            data=None,
            metadata={"skipped": True}
        ))
    
    def _process_condition_branching(
        self,
        context: ExecutionContext,
        node_id: str,
        result: NodeResult,
        edges: list
    ):
        """Process condition node branching.
        
        Sets flags on target nodes based on condition result.
        """
        condition_result = result.data
        
        # Find edges from this condition node
        for edge in edges:
            if edge.get('source') == node_id:
                target = edge.get('target')
                handle = edge.get('sourceHandle', 'output')
                
                # Determine if this branch should be taken
                if handle == 'output-true':
                    should_take = condition_result == True
                elif handle == 'output-false':
                    should_take = condition_result == False
                else:
                    should_take = True
                
                if not should_take:
                    context.set_variable(f"{target}_skip", True)
    
    def get_next_nodes(
        self, 
        node_id: str, 
        edges: list, 
        context: ExecutionContext
    ) -> List[str]:
        """Get next nodes to execute based on current node and context."""
        next_nodes = []
        
        for edge in edges:
            if edge.get('source') == node_id:
                target = edge.get('target')
                handle = edge.get('sourceHandle', 'output')
                
                # For condition nodes, check which branch
                if context.get_variable(f"{node_id}_skip"):
                    continue
                
                next_nodes.append(target)
        
        return next_nodes


class NodeExecutor:
    """Handles execution of individual nodes."""
    
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
    
    async def execute_with_timeout(
        self, 
        node: BaseNode, 
        context: ExecutionContext,
        timeout: int = 60
    ) -> NodeResult:
        """Execute node with timeout."""
        try:
            result = await asyncio.wait_for(
                node.execute(context),
                timeout=timeout
            )
            return result
        except asyncio.TimeoutError:
            return NodeResult(
                success=False,
                error=f"Node execution timed out after {timeout} seconds"
            )
    
    async def execute_with_retry(
        self,
        node: BaseNode,
        context: ExecutionContext,
        max_retries: int = None
    ) -> NodeResult:
        """Execute node with retry logic."""
        max_retries = max_retries or self.max_retries
        
        for attempt in range(max_retries):
            result = await node.execute(context)
            
            if result.success:
                return result
            
            if attempt < max_retries - 1:
                # Exponential backoff
                await asyncio.sleep(2 ** attempt)
        
        return result
