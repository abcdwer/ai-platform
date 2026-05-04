"""Multi-Agent collaboration engine."""
from typing import Optional, Dict, Any, Callable, Awaitable, List
from datetime import datetime
import logging

from app.models.multi_agent import CollaborationMode, SessionStatus, MessageType
from app.models.schemas.multi_agent import AgentMessageResponse
from .orchestrator import (
    CollaborationOrchestrator, ExecutionContext, ExecutionMessage,
    MemberContext, CollaborationModeHandler
)
from .modes.sequential import SequentialModeHandler
from .modes.parallel import ParallelModeHandler
from .modes.debate import DebateModeHandler
from .modes.hierarchical import HierarchicalModeHandler
from .modes.round_robin import RoundRobinModeHandler

logger = logging.getLogger(__name__)


class CollaborationEngine:
    """Main engine for multi-agent collaboration.
    
    This class provides the interface for executing multi-agent collaboration
    sessions using various collaboration modes.
    """
    
    def __init__(
        self,
        llm_call_func: Callable[[str, str, float, int, List[dict]], Awaitable[Dict[str, Any]]],
        message_callback: Optional[Callable[[Dict], Awaitable[None]]] = None
    ):
        """Initialize the collaboration engine.
        
        Args:
            llm_call_func: Function to call the LLM.
                Signature: (system_prompt, user_message, temperature, max_tokens, tools)
                Returns: {"content": str, "tool_calls": list, "tokens_used": int, ...}
            message_callback: Optional async callback for new messages during execution.
        """
        self.llm_call = llm_call_func
        self.message_callback = message_callback
        
        # Mode handlers registry
        self._mode_handlers: Dict[str, CollaborationModeHandler] = {
            CollaborationMode.SEQUENTIAL.value: SequentialModeHandler(),
            CollaborationMode.PARALLEL.value: ParallelModeHandler(),
            CollaborationMode.DEBATE.value: DebateModeHandler(),
            CollaborationMode.HIERARCHICAL.value: HierarchicalModeHandler(),
            CollaborationMode.ROUND_ROBIN.value: RoundRobinModeHandler(),
        }
    
    def get_mode_handler(self, mode: str) -> CollaborationModeHandler:
        """Get the handler for a specific mode."""
        handler = self._mode_handlers.get(mode)
        if not handler:
            # Default to sequential
            logger.warning(f"Unknown mode '{mode}', defaulting to sequential")
            handler = self._mode_handlers[CollaborationMode.SEQUENTIAL.value]
        return handler
    
    async def execute_session(
        self,
        group_config: Dict[str, Any],
        initial_input: str,
        session_id: str,
        user_input: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute a collaboration session.
        
        Args:
            group_config: Group configuration including members and settings
            initial_input: The initial task/prompt
            session_id: The session ID for tracking
            user_input: Optional additional user input
            context: Optional existing context
            
        Returns:
            Execution result with messages and final output
        """
        mode = group_config.get("mode", CollaborationMode.SEQUENTIAL.value)
        mode_config = group_config.get("mode_config", {})
        members_config = group_config.get("members", [])
        
        # Build member contexts
        members = []
        for m in members_config:
            member = MemberContext(
                member_id=m.get("id", ""),
                name=m.get("name", "Agent"),
                role=m.get("role", "member"),
                system_prompt=m.get("system_prompt", "You are a helpful AI assistant."),
                model=m.get("model", group_config.get("default_model", "llama2")),
                model_provider=m.get("model_provider", group_config.get("default_provider", "ollama")),
                temperature=m.get("temperature", 0.7),
                max_tokens=m.get("max_tokens", 4096),
                tools=m.get("tools", []),
                icon=m.get("icon"),
                color=m.get("color"),
            )
            members.append(member)
        
        # Build execution context
        exec_context = ExecutionContext(
            session_id=session_id,
            group_id=group_config.get("id", ""),
            mode=mode,
            mode_config=mode_config,
            members=members,
            initial_input=initial_input,
            user_input=user_input,
            context=context or {},
            enable_orchestrator=group_config.get("enable_orchestrator", True),
            orchestrator_prompt=group_config.get("orchestrator_prompt"),
            max_iterations=group_config.get("max_iterations", 10),
            termination_prompt=group_config.get("termination_prompt"),
        )
        
        # Attach orchestrator reference to context
        exec_context.orchestrator = CollaborationOrchestrator(
            llm_call_func=self.llm_call,
            message_callback=self._create_message_callback(session_id)
        )
        
        # Get mode handler
        mode_handler = self.get_mode_handler(mode)
        
        # Execute
        result = await exec_context.orchestrator.execute(exec_context, mode_handler)
        
        # Convert messages to response format
        messages = [
            AgentMessageResponse(
                id=msg.id,
                session_id=session_id,
                member_id=msg.member_id,
                member_name=msg.member_name,
                member_color=msg.member_color,
                message_type=msg.message_type,
                content=msg.content,
                turn=msg.turn,
                iteration=msg.iteration,
                referenced_message_id=msg.referenced_message_id,
                tool_calls=msg.tool_calls,
                tool_results=msg.tool_results,
                model_used=msg.model_used,
                tokens_used=msg.tokens_used,
                execution_time_ms=msg.execution_time_ms,
                created_at=msg.created_at,
            ).model_dump()
            for msg in result.messages
        ]
        
        return {
            "session_id": session_id,
            "status": "completed" if result.is_complete else "running",
            "current_turn": result.current_turn,
            "messages": messages,
            "final_output": result.final_output,
            "is_complete": result.is_complete,
            "error": result.error,
        }
    
    async def _create_message_callback(self, session_id: str):
        """Create a message callback for the orchestrator."""
        async def callback(message: ExecutionMessage):
            if self.message_callback:
                response = AgentMessageResponse(
                    id=message.id,
                    session_id=session_id,
                    member_id=message.member_id,
                    member_name=message.member_name,
                    member_color=message.member_color,
                    message_type=message.message_type,
                    content=message.content,
                    turn=message.turn,
                    iteration=message.iteration,
                    created_at=message.created_at,
                ).model_dump()
                await self.message_callback(response)
        return callback


# ============== LLM Integration ==============

async def default_llm_call(
    system_prompt: str,
    user_message: str,
    temperature: float,
    max_tokens: int,
    tools: List[dict]
) -> Dict[str, Any]:
    """Default LLM call function.
    
    This is a placeholder that should be replaced with actual LLM integration.
    In a real implementation, this would call Ollama, OpenAI, or another LLM provider.
    
    Args:
        system_prompt: System prompt for the model
        user_message: User message to process
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        tools: Available tools for function calling
        
    Returns:
        Dict with keys: content, tool_calls, tokens_used, etc.
    """
    # This is a placeholder implementation
    # In production, integrate with actual LLM providers
    return {
        "content": f"[Placeholder response] Processed: {user_message[:100]}...",
        "tool_calls": None,
        "tool_results": None,
        "tokens_used": len(user_message.split()) + 50,
        "model": "placeholder",
    }


class OllamaLLMCaller:
    """LLM caller for Ollama API.
    
    This class provides integration with Ollama for local model hosting.
    """
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        """Initialize Ollama caller.
        
        Args:
            base_url: Ollama API base URL
        """
        self.base_url = base_url.rstrip("/")
    
    async def __call__(
        self,
        system_prompt: str,
        user_message: str,
        temperature: float,
        max_tokens: int,
        tools: List[dict]
    ) -> Dict[str, Any]:
        """Call Ollama API.
        
        Args:
            system_prompt: System prompt
            user_message: User message
            temperature: Sampling temperature
            max_tokens: Max tokens
            tools: Available tools (simplified format)
            
        Returns:
            API response
        """
        import aiohttp
        import json
        
        # Build full prompt
        full_prompt = f"<<SYS>>\n{system_prompt}\n<</SYS>>\n\n[INST] {user_message} [/INST]"
        
        # Build request payload
        payload = {
            "model": "llama2",  # Default model, should be configurable
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status != 200:
                        return {
                            "content": f"Error: Ollama returned status {response.status}",
                            "tool_calls": None,
                            "tokens_used": 0,
                            "model": "ollama-error",
                        }
                    
                    result = await response.json()
                    
                    return {
                        "content": result.get("response", ""),
                        "tool_calls": None,
                        "tool_results": None,
                        "tokens_used": result.get("eval_count", 0),
                        "model": result.get("model", "llama2"),
                    }
        except Exception as e:
            return {
                "content": f"Error calling Ollama: {str(e)}",
                "tool_calls": None,
                "tokens_used": 0,
                "model": "ollama-error",
            }


# Export default instance
engine = CollaborationEngine(llm_call_func=default_llm_call)
