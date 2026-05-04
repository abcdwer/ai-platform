"""Workflow nodes base class and implementations."""
from abc import ABC, abstractmethod
from typing import Any, Optional, List, Dict
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
import json
import re


@dataclass
class NodeResult:
    """Result from node execution."""
    success: bool = True
    data: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def outputs(self) -> dict:
        """Get outputs as a dictionary."""
        return {"result": self.data, **self.metadata}


class BaseNode(ABC):
    """Base class for all workflow nodes."""
    
    def __init__(self, node_id: str, config: dict):
        self.node_id = node_id
        self.config = config
        self.node_type = self.__class__.__name__.replace('Node', '').lower()
    
    @abstractmethod
    async def execute(self, context) -> NodeResult:
        """Execute the node.
        
        Args:
            context: ExecutionContext with workflow state
            
        Returns:
            NodeResult with execution outputs
        """
        pass
    
    def get_input(self, context, key: str = 'input', default: Any = None) -> Any:
        """Get input from context, resolving templates."""
        value = self.config.get(key, default)
        if isinstance(value, str) and '{{' in value:
            return context.resolve_template(value)
        return value if value is not None else default
    
    def set_output(self, context, data: Any):
        """Set output in context."""
        context.set_node_output(self.node_id, NodeResult(success=True, data=data))


class StartNode(BaseNode):
    """Start node - workflow entry point."""
    
    async def execute(self, context) -> NodeResult:
        trigger = self.config.get('trigger', 'manual')
        
        return NodeResult(
            success=True,
            data={"trigger": trigger, "started": True},
            metadata={"trigger_type": trigger}
        )


class EndNode(BaseNode):
    """End node - workflow exit point."""
    
    async def execute(self, context) -> NodeResult:
        output_var = self.config.get('output_variable', 'result')
        output_value = self.get_input(context, 'output_value', context.get_variable('input'))
        
        # Store final output
        context.set_variable(output_var, output_value)
        
        return NodeResult(
            success=True,
            data=output_value,
            metadata={"output_variable": output_var}
        )


class LLMNode(BaseNode):
    """LLM node for AI model calls."""
    
    async def execute(self, context) -> NodeResult:
        model = self.config.get('model', 'gpt-4')
        provider = self.config.get('provider', 'openai')
        prompt_template = self.config.get('prompt_template', '{{input}}')
        system_prompt = self.config.get('system_prompt')
        temperature = self.config.get('temperature', 0.7)
        max_tokens = self.config.get('max_tokens', 4096)
        
        # Resolve templates
        prompt = context.resolve_template(prompt_template)
        
        try:
            # Import model dispatcher
            from app.services.model_dispatcher import get_model_dispatcher
            
            dispatcher = get_model_dispatcher()
            
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": context.resolve_template(system_prompt)})
            messages.append({"role": "user", "content": prompt})
            
            response = await dispatcher.generate(
                model=model,
                provider=provider,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            self.set_output(context, response)
            
            return NodeResult(
                success=True,
                data=response,
                metadata={"model": model, "provider": provider}
            )
        except Exception as e:
            return NodeResult(success=False, error=str(e))


class CodeNode(BaseNode):
    """Code execution node."""
    
    async def execute(self, context) -> NodeResult:
        language = self.config.get('language', 'python')
        code = self.config.get('code', '')
        timeout = self.config.get('timeout', 30)
        
        # Get input
        input_data = context.get_variable('input')
        
        try:
            if language == 'python':
                result = await self._execute_python(code, input_data, context, timeout)
            elif language == 'javascript':
                result = await self._execute_javascript(code, input_data, context, timeout)
            else:
                return NodeResult(success=False, error=f"Unsupported language: {language}")
            
            self.set_output(context, result)
            return NodeResult(success=True, data=result)
        except Exception as e:
            return NodeResult(success=False, error=str(e))
    
    async def _execute_python(self, code: str, input_data: Any, context, timeout: int) -> Any:
        """Execute Python code in sandbox."""
        import sys
        from io import StringIO
        from app.agents.sandbox import create_sandbox
        
        # Create sandbox namespace
        sandbox = create_sandbox()
        sandbox['input'] = input_data
        sandbox['context'] = context
        sandbox['variables'] = context.variables
        
        try:
            exec(code, sandbox)
            result = sandbox.get('result', sandbox.get('output', input_data))
            return result
        except Exception as e:
            raise RuntimeError(f"Python execution error: {e}")
    
    async def _execute_javascript(self, code: str, input_data: Any, context, timeout: int) -> Any:
        """Execute JavaScript code."""
        # Simple JS execution (in production, use a proper sandbox)
        try:
            # Replace template variables
            resolved_code = code
            
            # Note: Full JS execution would require a proper sandbox like QuickJS or Node sandbox
            # For now, return a placeholder
            return {"status": "javascript_execution", "input": str(input_data)}
        except Exception as e:
            raise RuntimeError(f"JavaScript execution error: {e}")


class ConditionNode(BaseNode):
    """Condition node for branching."""
    
    async def execute(self, context) -> NodeResult:
        condition_type = self.config.get('condition_type', 'expression')
        
        if condition_type == 'expression':
            result = self._evaluate_expression(context)
        elif condition_type == 'threshold':
            result = self._evaluate_threshold(context)
        else:
            return NodeResult(success=False, error=f"Unknown condition type: {condition_type}")
        
        # Store condition result for edge routing
        context.set_variable(f"{self.node_id}_condition", result)
        context.set_variable(f"{self.node_id}_result", result)
        
        return NodeResult(
            success=True,
            data=result,
            metadata={"condition_type": condition_type, "result": result}
        )
    
    def _evaluate_expression(self, context) -> bool:
        """Evaluate a boolean expression."""
        expression = self.config.get('expression', 'True')
        resolved = context.resolve_template(expression)
        
        # Safe evaluation for simple expressions
        try:
            # Replace common operators
            safe_globals = {"true": True, "false": False, "null": None}
            result = eval(resolved, {"__builtins__": {}}, safe_globals)
            return bool(result)
        except:
            return resolved == True
    
    def _evaluate_threshold(self, context) -> bool:
        """Evaluate threshold comparison."""
        input_value = float(self.get_input(context, 'input', 0))
        threshold = float(self.config.get('threshold_value', 0))
        comparison = self.config.get('threshold_comparison', '>')
        
        comparisons = {
            '>': lambda a, b: a > b,
            '<': lambda a, b: a < b,
            '>=': lambda a, b: a >= b,
            '<=': lambda a, b: a <= b,
            '==': lambda a, b: a == b,
            '!=': lambda a, b: a != b,
        }
        
        comp_func = comparisons.get(comparison, lambda a, b: False)
        return comp_func(input_value, threshold)


class LoopNode(BaseNode):
    """Loop node for iteration."""
    
    async def execute(self, context) -> NodeResult:
        loop_type = self.config.get('loop_type', 'count')
        max_iterations = self.config.get('max_iterations', 100)
        
        iterations = []
        loop_var = f"{self.node_id}_iteration"
        
        if loop_type == 'count':
            count = int(self.config.get('iterations', 10))
            for i in range(min(count, max_iterations)):
                context.set_variable(loop_var, i)
                context.set_variable(f"{self.node_id}_current", i)
                iterations.append(i)
        elif loop_type == 'while':
            condition = self.config.get('while_condition', 'False')
            i = 0
            while context.resolve_template(condition) and i < max_iterations:
                context.set_variable(loop_var, i)
                context.set_variable(f"{self.node_id}_current", i)
                iterations.append(i)
                i += 1
        elif loop_type == 'for_each':
            items = self.get_input(context, 'items', [])
            if not isinstance(items, list):
                items = [items]
            for i, item in enumerate(items[:max_iterations]):
                context.set_variable(loop_var, item)
                context.set_variable(f"{self.node_id}_current", item)
                iterations.append(item)
        
        self.set_output(context, iterations)
        
        return NodeResult(
            success=True,
            data=iterations,
            metadata={"iterations": len(iterations), "loop_type": loop_type}
        )


class DelayNode(BaseNode):
    """Delay/wait node."""
    
    async def execute(self, context) -> NodeResult:
        delay_type = self.config.get('delay_type', 'seconds')
        delay_value = int(self.config.get('delay_value', 1))
        
        if delay_type == 'seconds':
            wait_time = delay_value
        elif delay_type == 'minutes':
            wait_time = delay_value * 60
        elif delay_type == 'hours':
            wait_time = delay_value * 3600
        else:
            wait_time = delay_value
        
        # Cap at 5 minutes
        wait_time = min(wait_time, 300)
        
        await asyncio.sleep(wait_time)
        
        return NodeResult(
            success=True,
            data={"delayed": True, "waited_seconds": wait_time}
        )


class HTTPRequestNode(BaseNode):
    """HTTP request node."""
    
    async def execute(self, context) -> NodeResult:
        import httpx
        
        method = self.config.get('method', 'GET').upper()
        url = context.resolve_template(self.config.get('url', ''))
        headers = self.config.get('headers', {})
        body = self.config.get('body')
        timeout = self.config.get('timeout', 30)
        
        # Resolve templates in headers
        resolved_headers = {}
        for k, v in headers.items():
            resolved_headers[k] = context.resolve_template(str(v))
        
        # Resolve templates in body
        if body:
            if isinstance(body, str):
                body = context.resolve_template(body)
            elif isinstance(body, dict):
                body = {k: context.resolve_template(str(v)) for k, v in body.items()}
        
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                if method == 'GET':
                    response = await client.get(url, headers=resolved_headers)
                elif method == 'POST':
                    response = await client.post(url, headers=resolved_headers, json=body)
                elif method == 'PUT':
                    response = await client.put(url, headers=resolved_headers, json=body)
                elif method == 'DELETE':
                    response = await client.delete(url, headers=resolved_headers)
                elif method == 'PATCH':
                    response = await client.patch(url, headers=resolved_headers, json=body)
                else:
                    return NodeResult(success=False, error=f"Unsupported HTTP method: {method}")
                
                # Try to parse JSON response
                try:
                    response_data = response.json()
                except:
                    response_data = response.text
                
                self.set_output(context, response_data)
                
                return NodeResult(
                    success=True,
                    data=response_data,
                    metadata={
                        "status_code": response.status_code,
                        "method": method,
                        "url": url
                    }
                )
        except Exception as e:
            return NodeResult(success=False, error=str(e))


class TransformNode(BaseNode):
    """Data transformation node."""
    
    async def execute(self, context) -> NodeResult:
        transform_type = self.config.get('transform_type', 'json_path')
        input_data = self.get_input(context, 'input')
        
        try:
            if transform_type == 'json_path':
                result = self._json_path_transform(input_data, context)
            elif transform_type == 'template':
                result = self._template_transform(input_data, context)
            elif transform_type == 'join':
                result = self._join_transform(input_data, context)
            elif transform_type == 'split':
                result = self._split_transform(input_data, context)
            else:
                return NodeResult(success=False, error=f"Unknown transform type: {transform_type}")
            
            self.set_output(context, result)
            return NodeResult(success=True, data=result)
        except Exception as e:
            return NodeResult(success=False, error=str(e))
    
    def _json_path_transform(self, data: Any, context) -> Any:
        """Extract data using JSON path-like syntax."""
        path = self.config.get('json_path', '')
        
        # Simple JSON path: $.key1.key2 or $[0].key
        if path.startswith('$'):
            path = path[1:]
        
        current = data
        parts = re.split(r'([.\[\]])', path)
        
        for part in parts:
            if part == '.' or part == '':
                continue
            elif part == '[':
                continue
            elif part == ']':
                continue
            elif part.isdigit():
                current = current[int(part)]
            else:
                current = current.get(part, {})
        
        return current
    
    def _template_transform(self, data: Any, context) -> str:
        """Transform using template."""
        template = self.config.get('template', '{{input}}')
        context.set_variable('_transform_input', data)
        return context.resolve_template(template)
    
    def _join_transform(self, data: Any, context) -> str:
        """Join array elements."""
        delimiter = self.config.get('delimiter', ', ')
        join_key = self.config.get('join_key')
        
        if join_key and isinstance(data, list):
            data = [d.get(join_key, d) for d in data]
        elif not isinstance(data, list):
            data = [data]
        
        return delimiter.join(str(item) for item in data)
    
    def _split_transform(self, data: Any, context) -> list:
        """Split string into array."""
        separator = self.config.get('separator', ',')
        data_str = str(data) if data else ''
        return data_str.split(separator)


class MergeNode(BaseNode):
    """Merge node for combining branches."""
    
    async def execute(self, context) -> NodeResult:
        merge_type = self.config.get('merge_type', 'first')
        
        # Get outputs from connected nodes
        # In a real implementation, this would gather from multiple edges
        result = None
        
        if merge_type == 'first':
            # Use first available output
            for key, value in context.node_outputs.items():
                if hasattr(value, 'data'):
                    result = value.data
                    break
        elif merge_type == 'last':
            # Use last available output
            for key, value in context.node_outputs.items():
                if hasattr(value, 'data'):
                    result = value.data
        elif merge_type == 'all':
            # Collect all outputs
            result = [v.data if hasattr(v, 'data') else v for v in context.node_outputs.values()]
        
        self.set_output(context, result)
        return NodeResult(success=True, data=result)


class KnowledgeBaseQueryNode(BaseNode):
    """Knowledge base query node."""
    
    async def execute(self, context) -> NodeResult:
        from app.services.rag_service import RAGService
        
        kb_id = self.config.get('knowledge_base_id')
        query_template = self.config.get('query_template', '{{input}}')
        top_k = self.config.get('top_k', 5)
        similarity_threshold = self.config.get('similarity_threshold', 0.7)
        
        query = context.resolve_template(query_template)
        
        try:
            rag_service = RAGService()
            results = await rag_service.query(
                knowledge_base_id=kb_id,
                query=query,
                top_k=top_k,
                similarity_threshold=similarity_threshold
            )
            
            self.set_output(context, results)
            return NodeResult(
                success=True,
                data=results,
                metadata={"kb_id": kb_id, "query": query, "results_count": len(results)}
            )
        except Exception as e:
            return NodeResult(success=False, error=str(e))


class AgentCallNode(BaseNode):
    """Agent call node."""
    
    async def execute(self, context) -> NodeResult:
        from app.services.agent_service import AgentService
        
        agent_id = self.config.get('agent_id')
        input_template = self.config.get('input_template', '{{input}}')
        
        input_text = context.resolve_template(input_template)
        
        try:
            agent_service = AgentService()
            result = await agent_service.run_agent(agent_id, input_text)
            
            self.set_output(context, result)
            return NodeResult(success=True, data=result)
        except Exception as e:
            return NodeResult(success=False, error=str(e))


class TextSplitterNode(BaseNode):
    """Text splitting node."""
    
    async def execute(self, context) -> NodeResult:
        from app.rag.chunker import TextChunker
        
        input_text = str(self.get_input(context, 'input', ''))
        split_type = self.config.get('split_type', 'character')
        chunk_size = int(self.config.get('chunk_size', 1000))
        chunk_overlap = int(self.config.get('chunk_overlap', 200))
        separator = self.config.get('separator', '\n')
        
        try:
            chunker = TextChunker(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                split_by=split_type,
                separator=separator
            )
            chunks = chunker.chunk(input_text)
            
            self.set_output(context, chunks)
            return NodeResult(
                success=True,
                data=chunks,
                metadata={"chunks_count": len(chunks)}
            )
        except Exception as e:
            return NodeResult(success=False, error=str(e))


class EmbeddingNode(BaseNode):
    """Text embedding node."""
    
    async def execute(self, context) -> NodeResult:
        from app.services.embedding_service import EmbeddingService
        
        input_text = str(self.get_input(context, 'input', ''))
        model = self.config.get('model', 'text-embedding-ada-002')
        provider = self.config.get('provider', 'openai')
        batch_size = int(self.config.get('batch_size', 100))
        
        try:
            embedding_service = EmbeddingService()
            
            # Split into batches if needed
            if isinstance(input_text, list):
                texts = input_text
            else:
                texts = [input_text]
            
            embeddings = []
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                batch_embeddings = await embedding_service.embed_batch(
                    texts=batch,
                    model=model,
                    provider=provider
                )
                embeddings.extend(batch_embeddings)
            
            self.set_output(context, embeddings)
            return NodeResult(
                success=True,
                data=embeddings,
                metadata={"count": len(embeddings), "model": model}
            )
        except Exception as e:
            return NodeResult(success=False, error=str(e))


class WebSearchNode(BaseNode):
    """Web search node."""
    
    async def execute(self, context) -> NodeResult:
        from app.services.web_search_service import WebSearchService
        
        query_template = self.config.get('query_template', '{{input}}')
        num_results = int(self.config.get('num_results', 10))
        search_engine = self.config.get('search_engine', 'google')
        
        query = context.resolve_template(query_template)
        
        try:
            search_service = WebSearchService()
            results = await search_service.search(
                query=query,
                num_results=num_results,
                engine=search_engine
            )
            
            self.set_output(context, results)
            return NodeResult(
                success=True,
                data=results,
                metadata={"query": query, "results_count": len(results)}
            )
        except Exception as e:
            return NodeResult(success=False, error=str(e))


class FileReadNode(BaseNode):
    """File read node."""
    
    async def execute(self, context) -> NodeResult:
        import aiofiles
        
        file_path = context.resolve_template(self.config.get('file_path', ''))
        encoding = self.config.get('encoding', 'utf-8')
        
        try:
            async with aiofiles.open(file_path, 'r', encoding=encoding) as f:
                content = await f.read()
            
            self.set_output(context, content)
            return NodeResult(
                success=True,
                data=content,
                metadata={"file_path": file_path}
            )
        except Exception as e:
            return NodeResult(success=False, error=str(e))


class FileWriteNode(BaseNode):
    """File write node."""
    
    async def execute(self, context) -> NodeResult:
        import aiofiles
        import os
        
        file_path = context.resolve_template(self.config.get('file_path', ''))
        content_template = self.config.get('content_template', '{{input}}')
        encoding = self.config.get('encoding', 'utf-8')
        append = self.config.get('append', False)
        
        content = context.resolve_template(content_template)
        
        try:
            # Create directory if needed
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            mode = 'a' if append else 'w'
            async with aiofiles.open(file_path, mode, encoding=encoding) as f:
                await f.write(str(content))
            
            return NodeResult(
                success=True,
                data={"file_path": file_path, "written": True},
                metadata={"file_path": file_path}
            )
        except Exception as e:
            return NodeResult(success=False, error=str(e))


class SendEmailNode(BaseNode):
    """Send email node."""
    
    async def execute(self, context) -> NodeResult:
        # In production, integrate with email service
        to = context.resolve_template(self.config.get('to', ''))
        subject = context.resolve_template(self.config.get('subject', 'Workflow Notification'))
        body_template = self.config.get('body_template', '{{input}}')
        
        body = context.resolve_template(body_template)
        
        # Placeholder - would integrate with actual email service
        result = {
            "to": to,
            "subject": subject,
            "sent": True,
            "note": "Email service not configured"
        }
        
        self.set_output(context, result)
        return NodeResult(success=True, data=result)


class NotificationNode(BaseNode):
    """Notification node."""
    
    async def execute(self, context) -> NodeResult:
        notification_type = self.config.get('notification_type', 'log')
        message_template = self.config.get('message_template', '{{input}}')
        
        message = context.resolve_template(message_template)
        
        if notification_type == 'log':
            import logging
            logging.info(f"Workflow notification: {message}")
            result = {"type": "log", "message": message}
        elif notification_type == 'webhook':
            webhook_url = self.config.get('webhook_url')
            if webhook_url:
                import httpx
                async with httpx.AsyncClient() as client:
                    response = await client.post(webhook_url, json={"message": message})
                result = {"type": "webhook", "status": response.status_code}
            else:
                result = {"type": "webhook", "error": "No webhook URL configured"}
        else:
            result = {"type": notification_type, "message": message}
        
        self.set_output(context, result)
        return NodeResult(success=True, data=result)


# Node registry
NODE_TYPES = {
    'start': StartNode,
    'end': EndNode,
    'llm': LLMNode,
    'code': CodeNode,
    'condition': ConditionNode,
    'loop': LoopNode,
    'delay': DelayNode,
    'http': HTTPRequestNode,
    'transform': TransformNode,
    'merge': MergeNode,
    'knowledge': KnowledgeBaseQueryNode,
    'agent': AgentCallNode,
    'text_splitter': TextSplitterNode,
    'embedding': EmbeddingNode,
    'web_search': WebSearchNode,
    'file_read': FileReadNode,
    'file_write': FileWriteNode,
    'send_email': SendEmailNode,
    'notification': NotificationNode,
}


def create_node(node_id: str, node_type: str, config: dict) -> BaseNode:
    """Create a node instance by type."""
    node_class = NODE_TYPES.get(node_type)
    if not node_class:
        raise ValueError(f"Unknown node type: {node_type}")
    return node_class(node_id, config)
