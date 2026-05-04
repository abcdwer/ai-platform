"""Multi-Agent collaboration orchestration."""
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
import json
import asyncio
from datetime import datetime

from app.models.multi_agent import (
    AgentGroup, AgentMember, CollaborationSession, AgentMessage,
    MessageType, SessionStatus
)


@dataclass
class MemberContext:
    """Context for an agent member execution."""
    member_id: str
    name: str
    role: str
    system_prompt: str
    model: str
    model_provider: str
    temperature: float
    max_tokens: int
    tools: List[dict]
    icon: Optional[str] = None
    color: Optional[str] = None


@dataclass
class ExecutionMessage:
    """Message in the collaboration execution."""
    id: str
    member_id: Optional[str]
    member_name: Optional[str]
    member_color: Optional[str]
    message_type: str
    content: str
    turn: int
    iteration: int
    referenced_message_id: Optional[str] = None
    tool_calls: Optional[List[dict]] = None
    tool_results: Optional[List[dict]] = None
    model_used: Optional[str] = None
    tokens_used: Optional[int] = None
    execution_time_ms: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ExecutionContext:
    """Context for the entire collaboration execution."""
    session_id: str
    group_id: str
    mode: str
    mode_config: Dict[str, Any]
    members: List[MemberContext]
    initial_input: str
    user_input: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    messages: List[ExecutionMessage] = field(default_factory=list)
    current_turn: int = 0
    current_iteration: int = 0
    enable_orchestrator: bool = True
    orchestrator_prompt: Optional[str] = None
    max_iterations: int = 10
    termination_prompt: Optional[str] = None
    is_complete: bool = False
    final_output: Optional[str] = None
    error: Optional[str] = None


# Type for LLM call function
LLMCallFunc = Callable[[str, str, float, int, List[dict]], Awaitable[Dict[str, Any]]]


class CollaborationOrchestrator:
    """Orchestrator for multi-agent collaboration.
    
    This is the main entry point for executing multi-agent collaboration sessions.
    It coordinates the different collaboration modes and manages the execution context.
    """
    
    def __init__(
        self,
        llm_call_func: LLMCallFunc,
        message_callback: Optional[Callable[[ExecutionMessage], Awaitable[None]]] = None
    ):
        """Initialize the orchestrator.
        
        Args:
            llm_call_func: Function to call the LLM with parameters:
                (system_prompt, user_message, temperature, max_tokens, tools) -> Dict
                Returns: {"content": str, "tool_calls": list, "tokens_used": int, ...}
            message_callback: Optional async callback for each new message
        """
        self.llm_call = llm_call_func
        self.message_callback = message_callback
    
    async def execute(
        self,
        context: ExecutionContext,
        mode_handler: "CollaborationModeHandler"
    ) -> ExecutionContext:
        """Execute a collaboration session.
        
        Args:
            context: The execution context
            mode_handler: The mode-specific handler
            
        Returns:
            Updated execution context with results
        """
        try:
            # Initialize session
            context = await mode_handler.initialize(context)
            
            # Main execution loop
            while not context.is_complete and context.current_iteration < context.max_iterations:
                # Execute one iteration
                context = await mode_handler.execute_iteration(context)
                
                # Check termination conditions
                if await self._check_termination(context, mode_handler):
                    context.is_complete = True
                    break
                
                context.current_iteration += 1
            
            # Finalize
            context = await mode_handler.finalize(context)
            
            # Set final output if not set
            if not context.final_output and context.messages:
                # Use the last agent message as final output
                for msg in reversed(context.messages):
                    if msg.message_type == MessageType.AGENT_OUTPUT.value:
                        context.final_output = msg.content
                        break
            
        except Exception as e:
            context.error = str(e)
            context.is_complete = True
        
        return context
    
    async def _check_termination(
        self,
        context: ExecutionContext,
        mode_handler: "CollaborationModeHandler"
    ) -> bool:
        """Check if the collaboration should terminate."""
        # Check if mode handler says to terminate
        if await mode_handler.should_terminate(context):
            return True
        
        # Check termination prompt if provided
        if context.termination_prompt and context.messages:
            # Build conversation history for LLM
            history = self._build_history(context)
            
            result = await self.llm_call(
                system_prompt=context.termination_prompt,
                user_message=f"Based on the conversation history, should the collaboration terminate?\n\n{history}",
                temperature=0.1,
                max_tokens=10,
                tools=[]
            )
            
            content = result.get("content", "").lower().strip()
            if "yes" in content or "terminate" in content or "complete" in content:
                return True
        
        return False
    
    def _build_history(self, context: ExecutionContext) -> str:
        """Build conversation history string."""
        history_parts = []
        for msg in context.messages:
            speaker = msg.member_name or "User"
            history_parts.append(f"[{speaker}]: {msg.content[:500]}...")
        return "\n".join(history_parts)
    
    async def _emit_message(self, message: ExecutionMessage) -> None:
        """Emit a message via callback if registered."""
        if self.message_callback:
            await self.message_callback(message)


class CollaborationModeHandler(ABC):
    """Abstract base class for collaboration mode handlers."""
    
    @property
    @abstractmethod
    def mode_name(self) -> str:
        """Return the mode name."""
        pass
    
    @abstractmethod
    async def initialize(self, context: ExecutionContext) -> ExecutionContext:
        """Initialize the execution context for this mode."""
        pass
    
    @abstractmethod
    async def execute_iteration(self, context: ExecutionContext) -> ExecutionContext:
        """Execute one iteration of the collaboration."""
        pass
    
    @abstractmethod
    async def should_terminate(self, context: ExecutionContext) -> bool:
        """Check if the collaboration should terminate."""
        pass
    
    @abstractmethod
    async def finalize(self, context: ExecutionContext) -> ExecutionContext:
        """Finalize the execution and prepare results."""
        pass
    
    async def _call_agent(
        self,
        context: ExecutionContext,
        member: MemberContext,
        user_message: str,
        turn: int,
        iteration: int,
        referenced_message_id: Optional[str] = None
    ) -> ExecutionMessage:
        """Call an agent and return the result."""
        # Build system prompt with context
        system_prompt = member.system_prompt
        
        # Add context about other agents if relevant
        if context.messages:
            context_summary = self._summarize_context(context)
            system_prompt = f"{system_prompt}\n\nContext from this collaboration:\n{context_summary}"
        
        start_time = datetime.utcnow()
        
        # Call LLM
        result = await context.orchestrator.llm_call(
            system_prompt=system_prompt,
            user_message=user_message,
            temperature=member.temperature,
            max_tokens=member.max_tokens,
            tools=member.tools
        )
        
        end_time = datetime.utcnow()
        execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        message = ExecutionMessage(
            id=f"msg-{datetime.utcnow().timestamp()}",
            member_id=member.member_id,
            member_name=member.name,
            member_color=member.color,
            message_type=MessageType.AGENT_OUTPUT.value,
            content=result.get("content", ""),
            turn=turn,
            iteration=iteration,
            referenced_message_id=referenced_message_id,
            tool_calls=result.get("tool_calls"),
            tool_results=result.get("tool_results"),
            model_used=member.model,
            tokens_used=result.get("tokens_used"),
            execution_time_ms=execution_time_ms,
        )
        
        context.messages.append(message)
        await context.orchestrator._emit_message(message)
        
        return message
    
    def _summarize_context(self, context: ExecutionContext) -> str:
        """Summarize the context from previous messages."""
        summaries = []
        # Get recent messages (last 5)
        recent = context.messages[-5:] if len(context.messages) > 5 else context.messages
        
        for msg in recent:
            if msg.message_type == MessageType.USER_INPUT.value:
                summaries.append(f"User: {msg.content[:200]}...")
            elif msg.message_type == MessageType.AGENT_OUTPUT.value:
                summaries.append(f"{msg.member_name}: {msg.content[:200]}...")
        
        return "\n".join(summaries) if summaries else "No previous context"
    
    def _get_member_by_id(self, context: ExecutionContext, member_id: str) -> Optional[MemberContext]:
        """Get a member by ID."""
        for member in context.members:
            if member.member_id == member_id:
                return member
        return None
    
    def _get_member_by_role(self, context: ExecutionContext, role: str) -> Optional[MemberContext]:
        """Get a member by role."""
        for member in context.members:
            if member.role.lower() == role.lower():
                return member
        return None
