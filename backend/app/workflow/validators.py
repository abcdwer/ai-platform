"""Workflow validators for checking workflow validity."""
from typing import List, Set, Tuple, Optional, Dict, Any


class WorkflowValidationError(Exception):
    """Exception raised for workflow validation errors."""
    pass


class WorkflowValidator:
    """Validator for workflow graphs."""
    
    @staticmethod
    def validate(graph_data: dict) -> List[str]:
        """Validate workflow graph and return list of errors.
        
        Checks:
        - Has at least one start and end node
        - All referenced nodes exist
        - No circular dependencies (except allowed loops)
        - Start node has no incoming edges
        - End node has no outgoing edges
        """
        errors = []
        
        nodes = graph_data.get('nodes', [])
        edges = graph_data.get('edges', [])
        
        if not nodes:
            errors.append("Workflow must have at least one node")
            return errors
        
        # Build node lookup
        node_map = {n['id']: n for n in nodes}
        node_ids = set(node_map.keys())
        
        # Check for start and end nodes
        node_types = [n.get('type') for n in nodes]
        if 'start' not in node_types:
            errors.append("Workflow must have a Start node")
        if 'end' not in node_types:
            errors.append("Workflow must have an End node")
        
        # Check all edges reference valid nodes
        for edge in edges:
            if edge.get('source') not in node_ids:
                errors.append(f"Edge '{edge.get('id')}' references non-existent source node '{edge.get('source')}'")
            if edge.get('target') not in node_ids:
                errors.append(f"Edge '{edge.get('id')}' references non-existent target node '{edge.get('target')}'")
        
        # Check start node has no incoming edges
        for node in nodes:
            if node.get('type') == 'start':
                incoming = [e for e in edges if e.get('target') == node['id']]
                if incoming:
                    errors.append(f"Start node '{node['id']}' should not have incoming edges")
        
        # Check end node has no outgoing edges
        for node in nodes:
            if node.get('type') == 'end':
                outgoing = [e for e in edges if e.get('source') == node['id']]
                if outgoing:
                    errors.append(f"End node '{node['id']}' should not have outgoing edges")
        
        # Check for cycles (excluding loop nodes)
        cycle_errors = WorkflowValidator._check_cycles(nodes, edges)
        errors.extend(cycle_errors)
        
        # Check connectivity from start to end
        if 'start' in node_types and 'end' in node_types:
            connected = WorkflowValidator._check_connectivity(nodes, edges)
            if not connected:
                errors.append("Workflow must have a path from Start to End")
        
        return errors
    
    @staticmethod
    def _check_cycles(nodes: List[dict], edges: List[dict]) -> List[str]:
        """Check for cycles in the graph using DFS."""
        errors = []
        
        # Build adjacency list
        adj: Dict[str, List[str]] = {n['id']: [] for n in nodes}
        for edge in edges:
            source = edge.get('source', '')
            target = edge.get('target', '')
            if source and target:
                adj[source].append(target)
        
        # Track visited and recursion stack
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        
        def dfs(node_id: str, path: List[str]) -> bool:
            """DFS to detect cycles. Returns True if cycle found."""
            if node_id not in visited:
                visited.add(node_id)
                rec_stack.add(node_id)
                path.append(node_id)
                
                for neighbor in adj.get(node_id, []):
                    if neighbor not in visited:
                        if dfs(neighbor, path[:]):
                            return True
                    elif neighbor in rec_stack:
                        # Found cycle
                        cycle_start = path.index(neighbor)
                        cycle = path[cycle_start:] + [neighbor]
                        # Special handling for intentional loops (loop nodes)
                        if WorkflowValidator._is_intentional_loop(cycle, nodes, edges):
                            continue
                        errors.append(f"Circular dependency detected: {' -> '.join(cycle)}")
                        return True
                
            rec_stack.remove(node_id)
            return False
        
        for node in nodes:
            if node['id'] not in visited:
                dfs(node['id'], [])
        
        return errors
    
    @staticmethod
    def _is_intentional_loop(cycle: List[str], nodes: List[dict], edges: List[dict]) -> bool:
        """Check if a cycle is an intentional loop (has a loop node)."""
        # Find the loop node in the cycle
        for node_id in cycle:
            for node in nodes:
                if node['id'] == node_id and node.get('type') == 'loop':
                    return True
        return False
    
    @staticmethod
    def _check_connectivity(nodes: List[dict], edges: List[dict]) -> bool:
        """Check if there's a path from start to end."""
        # Find start and end nodes
        start_id = None
        end_id = None
        for n in nodes:
            if n.get('type') == 'start':
                start_id = n['id']
            if n.get('type') == 'end':
                end_id = n['id']
        
        if not start_id or not end_id:
            return False
        
        # BFS from start
        visited = {start_id}
        queue = [start_id]
        
        while queue:
            current = queue.pop(0)
            if current == end_id:
                return True
            
            for edge in edges:
                if edge.get('source') == current:
                    target = edge.get('target')
                    if target and target not in visited:
                        visited.add(target)
                        queue.append(target)
        
        return False
    
    @staticmethod
    def get_execution_order(graph_data: dict) -> List[List[str]]:
        """Get nodes grouped by execution level (for parallel execution).
        
        Returns list of lists, where each inner list contains nodes
        that can be executed in parallel.
        """
        nodes = graph_data.get('nodes', [])
        edges = graph_data.get('edges', [])
        
        # Build adjacency and in-degree
        adj: Dict[str, List[str]] = {n['id']: [] for n in nodes}
        in_degree: Dict[str, int] = {n['id']: 0 for n in nodes}
        
        for edge in edges:
            source = edge.get('source')
            target = edge.get('target')
            if source and target:
                adj[source].append(target)
                in_degree[target] = in_degree.get(target, 0) + 1
        
        # Topological sort with level tracking
        levels: List[List[str]] = []
        current_level = [nid for nid, deg in in_degree.items() if deg == 0]
        processed: Set[str] = set()
        
        while current_level:
            levels.append(current_level[:])
            processed.update(current_level)
            
            next_level: List[str] = []
            for node_id in current_level:
                for neighbor in adj.get(node_id, []):
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0 and neighbor not in processed:
                        next_level.append(neighbor)
            
            current_level = next_level
        
        return levels
