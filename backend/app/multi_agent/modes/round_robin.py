"""Round Robin collaboration mode - agents take turns speaking."""
from typing import Optional
from ..orchestrator import (
    CollaborationModeHandler, ExecutionContext, ExecutionMessage, MemberContext
)


class RoundRobinModeHandler(CollaborationModeHandler):
    """Handler for round robin collaboration mode.
    
    Agents speak in a rotating turn order, building on each other's
    contributions until a conclusion is reached or max turns are reached.
    """
    
    @property
    def mode_name(self) -> str:
        return "round_robin"
    
    async def initialize(self, context: ExecutionContext) -> ExecutionContext:
        """Initialize for round robin execution."""
        config = context.mode_config or {}
        
        # Set default max turns
        if "max_turns" not in config:
            config["max_turns"] = 10
        
        context.context["max_turns"] = config.get("max_turns", 10)
        context.context["allow_skip"] = config.get("allow_skip", True)
        context.context["current_turn_index"] = 0
        context.context["total_turns_taken"] = 0
        context.context["consecutive_skips"] = 0
        
        return context
    
    async def execute_iteration(self, context: ExecutionContext) -> ExecutionContext:
        """Execute one iteration: one agent takes a turn."""
        members = context.members
        if not members:
            context.is_complete = True
            return context
        
        max_turns = context.context.get("max_turns", 10)
        total_turns = context.context.get("total_turns_taken", 0)
        
        if total_turns >= max_turns:
            context.is_complete = True
            return context
        
        # Get current speaker based on round robin order
        current_index = context.context.get("current_turn_index", 0)
        current_member = members[current_index % len(members)]
        
        # Determine if this member should speak or skip
        should_speak = await self._should_member_speak(context, current_member)
        
        if should_speak:
            await self._member_speaks(context, current_member)
            context.context["consecutive_skips"] = 0
        elif context.context.get("allow_skip"):
            # Member chooses to skip this turn
            await self._member_skips(context, current_member)
            context.context["consecutive_skips"] = context.context.get("consecutive_skips", 0) + 1
        else:
            # Skip not allowed, move to next
            current_index = (current_index + 1) % len(members)
            context.context["current_turn_index"] = current_index
            return context
        
        # Move to next speaker
        context.context["current_turn_index"] = (current_index + 1) % len(members)
        context.context["total_turns_taken"] = total_turns + 1
        context.current_turn += 1
        
        return context
    
    async def _should_member_speak(
        self, 
        context: ExecutionContext, 
        member: MemberContext
    ) -> bool:
        """Determine if a member should take their turn or skip."""
        # Check if this is a new round (first member speaking)
        if context.current_turn == 0:
            return True
        
        # Check recent messages for consensus signals
        recent_messages = context.messages[-len(context.members):] if context.messages else []
        recent_content = " ".join([m.content.lower() for m in recent_messages])
        
        # Signals that might indicate the discussion is complete
        completion_signals = [
            "conclusion", "final", "summarize", "in conclusion",
            "to summarize", "in summary", "to conclude", 
            "agreed", "consensus", "decision made"
        ]
        
        if any(signal in recent_content for signal in completion_signals):
            # Check if current member is likely to add value
            return False
        
        return True
    
    async def _member_speaks(
        self,
        context: ExecutionContext,
        member: MemberContext
    ) -> ExecutionMessage:
        """Current member takes their turn."""
        # Build context for the member
        conversation_history = self._build_conversation_summary(context)
        
        prompt = f"""{member.system_prompt}

You are taking your turn in a round-robin discussion.

Topic: {context.initial_input}

Previous discussion:
{conversation_history}

Take your turn. You can:
- Build on previous points
- Add new perspectives
- Challenge others respectfully
- Suggest next steps
- Indicate if you believe the discussion is complete

Be concise but substantive."""
        
        return await self._call_agent(
            context=context,
            member=member,
            user_message=prompt,
            turn=context.current_turn,
            iteration=context.current_iteration
        )
    
    async def _member_skips(
        self,
        context: ExecutionContext,
        member: MemberContext
    ) -> None:
        """Member skips their turn with an explanation."""
        # Add a system message indicating skip
        skip_message = ExecutionMessage(
            id=f"msg-{context.current_turn}-{member.member_id}",
            member_id=member.member_id,
            member_name=member.name,
            member_color=member.color,
            message_type="system",
            content=f"{member.name} passes their turn.",
            turn=context.current_turn,
            iteration=context.current_iteration
        )
        context.messages.append(skip_message)
    
    def _build_conversation_summary(self, context: ExecutionContext) -> str:
        """Build a summary of the conversation so far."""
        if not context.messages:
            return "No previous discussion."
        
        # Get last few messages
        recent = context.messages[-min(5, len(context.messages)):]
        
        summary_parts = []
        for msg in recent:
            if msg.message_type == "user_input":
                summary_parts.append(f"User: {msg.content[:200]}")
            elif msg.message_type == "agent_output":
                summary_parts.append(f"{msg.member_name}: {msg.content[:200]}")
            elif msg.message_type == "system":
                summary_parts.append(f"[System]: {msg.content}")
        
        return "\n".join(summary_parts)
    
    async def should_terminate(self, context: ExecutionContext) -> bool:
        """Check termination conditions for round robin mode."""
        max_turns = context.context.get("max_turns", 10)
        total_turns = context.context.get("total_turns_taken", 0)
        
        # Terminate if max turns reached
        if total_turns >= max_turns:
            return True
        
        # Terminate if too many consecutive skips (everyone passing)
        consecutive_skips = context.context.get("consecutive_skips", 0)
        if consecutive_skips >= len(context.members):
            return True
        
        # Check for explicit conclusion signals
        if context.messages:
            last_message = context.messages[-1]
            conclusion_keywords = ["conclusion", "final decision", "agreed upon", "consensus reached"]
            if any(kw in last_message.content.lower() for kw in conclusion_keywords):
                return True
        
        return False
    
    async def finalize(self, context: ExecutionContext) -> ExecutionContext:
        """Finalize round robin execution."""
        # Look for a message that summarizes or concludes
        for msg in reversed(context.messages):
            if msg.message_type == "agent_output":
                # Check if this looks like a summary
                content_lower = msg.content.lower()
                if any(kw in content_lower for kw in ["summary", "conclusion", "final", "agreed"]):
                    context.final_output = msg.content
                    break
        
        if not context.final_output:
            # Use the last agent message
            for msg in reversed(context.messages):
                if msg.message_type == "agent_output":
                    context.final_output = msg.content
                    break
        
        return context
