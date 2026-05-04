"""Sequential collaboration mode - agents execute in fixed order."""
from typing import Optional
from ..orchestrator import (
    CollaborationModeHandler, ExecutionContext, ExecutionMessage, MemberContext
)


class SequentialModeHandler(CollaborationModeHandler):
    """Handler for sequential collaboration mode.
    
    Agents execute in a fixed order (determined by execution_order).
    Each agent sees the output of previous agents.
    """
    
    @property
    def mode_name(self) -> str:
        return "sequential"
    
    async def initialize(self, context: ExecutionContext) -> ExecutionContext:
        """Initialize for sequential execution."""
        # Sort members by execution order
        context.members = sorted(context.members, key=lambda m: m.execution_order)
        
        # Store the original input
        context.context["original_input"] = context.initial_input
        context.context["current_input"] = context.initial_input
        
        return context
    
    async def execute_iteration(self, context: ExecutionContext) -> ExecutionContext:
        """Execute one iteration: each agent processes in order."""
        current_input = context.context.get("current_input", context.initial_input)
        last_message_id = None
        
        for member in context.members:
            if not self._is_member_active(context, member):
                continue
            
            # Build user message
            user_message = self._build_agent_message(context, member, current_input)
            
            # Call the agent
            message = await self._call_agent(
                context=context,
                member=member,
                user_message=user_message,
                turn=context.current_turn,
                iteration=context.current_iteration,
                referenced_message_id=last_message_id
            )
            
            last_message_id = message.id
            current_input = message.content
        
        # Update context with final output
        context.context["current_input"] = current_input
        context.current_turn += 1
        
        return context
    
    def _is_member_active(self, context: ExecutionContext, member: MemberContext) -> bool:
        """Check if a member should participate in this iteration."""
        # Check mode config for selective participation
        config = context.mode_config or {}
        
        # If specific members are configured, only they participate
        if "active_members" in config:
            return member.member_id in config["active_members"]
        
        return True
    
    def _build_agent_message(
        self, 
        context: ExecutionContext, 
        member: MemberContext,
        current_input: str
    ) -> str:
        """Build the message for an agent based on context."""
        # Include previous outputs in context
        previous_outputs = []
        for msg in context.messages[-len(context.members):]:
            if msg.member_id and msg.member_id != member.member_id:
                previous_outputs.append(f"[{msg.member_name}]: {msg.content[:300]}...")
        
        if previous_outputs:
            context_info = "\n".join(previous_outputs)
            return f"""Previous agent outputs:
{context_info}

Now continue the task with your expertise:

Task: {current_input}"""
        else:
            return current_input
    
    async def should_terminate(self, context: ExecutionContext) -> bool:
        """Check termination conditions for sequential mode."""
        config = context.mode_config or {}
        
        # Check stop_on_first_success if configured
        if config.get("stop_on_first_success"):
            # Check if the last message contains completion keywords
            if context.messages:
                last_msg = context.messages[-1]
                completion_keywords = ["completed", "finished", "done", "conclusion"]
                if any(kw in last_msg.content.lower() for kw in completion_keywords):
                    return True
        
        # Check if all members have spoken in this iteration
        active_members = [m for m in context.members if self._is_member_active(context, m)]
        if len(active_members) == 0:
            return True
        
        return False
    
    async def finalize(self, context: ExecutionContext) -> ExecutionContext:
        """Finalize sequential execution."""
        # Use the last agent's output as final output
        for msg in reversed(context.messages):
            if msg.message_type == "agent_output":
                context.final_output = msg.content
                break
        
        return context
