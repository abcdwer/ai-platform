"""Workflow execution context for passing data between nodes."""
from typing import Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ExecutionContext:
    """Context passed through workflow execution."""
    
    # Global execution state
    variables: dict[str, Any] = field(default_factory=dict)
    
    # Node outputs storage
    node_outputs: dict[str, Any] = field(default_factory=dict)
    
    # Execution metadata
    execution_id: str = ""
    workflow_id: str = ""
    
    # Timing
    started_at: Optional[datetime] = None
    
    def set_variable(self, key: str, value: Any):
        """Set a variable in the context."""
        self.variables[key] = value
    
    def get_variable(self, key: str, default: Any = None) -> Any:
        """Get a variable from the context."""
        return self.variables.get(key, default)
    
    def set_node_output(self, node_id: str, output: Any):
        """Set output for a node."""
        self.node_outputs[node_id] = output
    
    def get_node_output(self, node_id: str, default: Any = None) -> Any:
        """Get output from a node."""
        return self.node_outputs.get(node_id, default)
    
    def get_input_for_node(self, node_id: str, source_node_id: str, default: Any = None) -> Any:
        """Get input for a node from a source node's output."""
        source_output = self.get_node_output(source_node_id)
        if source_output is not None:
            return source_output
        return default
    
    def resolve_template(self, template: str) -> Any:
        """Resolve template variables in a string.
        
        Templates use {{variable}} or {{node_id.output_key}} syntax.
        """
        import re
        from app.workflow.nodes import NodeResult
        
        # Find all template variables
        pattern = r'\{\{([^}]+)\}\}'
        
        def replace_var(match):
            var_path = match.group(1).strip()
            
            # Check for node output reference
            if '.' in var_path:
                node_id, output_key = var_path.split('.', 1)
                node_output = self.get_node_output(node_id)
                if isinstance(node_output, NodeResult):
                    return str(node_output.data.get(output_key, ''))
                elif isinstance(node_output, dict):
                    return str(node_output.get(output_key, ''))
                return str(node_output or '')
            
            # Check for variable
            value = self.get_variable(var_path)
            if value is not None:
                return str(value)
            
            # Check for context variables
            if var_path == 'input':
                return str(self.get_variable('input', ''))
            
            return match.group(0)  # Return original if not found
        
        resolved = re.sub(pattern, replace_var, template)
        
        # Try to parse as JSON if it looks like one
        if resolved.startswith('{') or resolved.startswith('['):
            try:
                import json
                return json.loads(resolved)
            except json.JSONDecodeError:
                pass
        
        return resolved
    
    def to_dict(self) -> dict:
        """Convert context to dictionary for storage."""
        return {
            'variables': self.variables,
            'node_outputs': {k: v.data if hasattr(v, 'data') else v 
                           for k, v in self.node_outputs.items()},
            'execution_id': self.execution_id,
            'workflow_id': self.workflow_id
        }
