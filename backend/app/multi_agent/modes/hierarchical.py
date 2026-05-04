"""Hierarchical collaboration mode - leader coordinates subordinates."""
from typing import Optional, List
from ..orchestrator import (
    CollaborationModeHandler, ExecutionContext, ExecutionMessage, MemberContext
)


class HierarchicalModeHandler(CollaborationModeHandler):
    """Handler for hierarchical collaboration mode.
    
    A leader/manager agent coordinates subordinate agents,
    delegating tasks and synthesizing results.
    """
    
    @property
    def mode_name(self) -> str:
        return "hierarchical"
    
    async def initialize(self, context: ExecutionContext) -> ExecutionContext:
        """Initialize for hierarchical execution."""
        config = context.mode_config or {}
        
        # Set default max depth
        if "max_depth" not in config:
            config["max_depth"] = 3
        
        context.context["max_depth"] = config.get("max_depth", 3)
        context.context["delegate_threshold"] = config.get("delegate_threshold", 0.5)
        context.context["current_depth"] = 0
        context.context["delegation_chain"] = []
        
        # Identify leader
        leader = self._get_member_by_role(context, "leader")
        if not leader and context.members:
            leader = context.members[0]
        
        context.context["leader"] = leader
        
        # Identify subordinates
        subordinates = [m for m in context.members if m.member_id != leader.member_id] if leader else context.members
        context.context["subordinates"] = subordinates
        
        return context
    
    async def execute_iteration(self, context: ExecutionContext) -> ExecutionContext:
        """Execute one iteration: leader delegates and synthesizes."""
        current_depth = context.context.get("current_depth", 0)
        max_depth = context.context.get("max_depth", 3)
        
        if current_depth >= max_depth:
            context.is_complete = True
            return context
        
        leader = context.context.get("leader")
        subordinates = context.context.get("subordinates", [])
        
        if not leader:
            # No leader, fall back to sequential
            return await self._execute_sequential_fallback(context)
        
        # Leader analyzes the task and decides whether to delegate
        should_delegate, delegation_instruction = await self._leader_delegate(
            context, leader, subordinates
        )
        
        if not should_delegate or not subordinates:
            # Leader handles it directly
            await self._leader_direct_task(context, leader)
        else:
            # Leader delegates to subordinates
            subordinate_results = await self._delegate_to_subordinates(
                context, leader, subordinates, delegation_instruction
            )
            
            # Leader synthesizes results
            await self._leader_synthesize(context, leader, subordinate_results)
        
        context.context["current_depth"] = current_depth + 1
        context.current_turn += 1
        
        return context
    
    async def _leader_delegate(
        self,
        context: ExecutionContext,
        leader: MemberContext,
        subordinates: List[MemberContext]
    ) -> tuple[bool, str]:
        """Leader decides whether to delegate and what to delegate."""
        subordinate_info = "\n".join([
            f"- {s.name}: {s.system_prompt[:100]}..." 
            for s in subordinates
        ])
        
        prompt = f"""You are the leader coordinating a team to solve a task.

Available subordinates:
{subordinate_info}

Task: {context.initial_input}

Analyze the task and decide:
1. Should you delegate parts to subordinates, or handle it yourself?
2. If delegating, what specific instruction should each subordinate receive?

Respond in this format:
DELEGATE: [yes/no]
INSTRUCTIONS: [what to tell subordinates or explanation of your approach]"""
        
        result = await context.orchestrator.llm_call(
            system_prompt=leader.system_prompt,
            user_message=prompt,
            temperature=leader.temperature,
            max_tokens=leader.max_tokens,
            tools=[]
        )
        
        content = result.get("content", "")
        
        # Parse the response
        should_delegate = "DELEGATE: yes" in content.upper()
        instructions = content
        
        return should_delegate, instructions
    
    async def _leader_direct_task(
        self,
        context: ExecutionContext,
        leader: MemberContext
    ) -> None:
        """Leader handles the task directly."""
        await self._call_agent(
            context=context,
            member=leader,
            user_message=f"""Complete this task yourself:

{context.initial_input}

Provide your complete response.""",
            turn=context.current_turn,
            iteration=context.current_iteration
        )
    
    async def _delegate_to_subordinates(
        self,
        context: ExecutionContext,
        leader: MemberContext,
        subordinates: List[MemberContext],
        instructions: str
    ) -> List[ExecutionMessage]:
        """Delegate tasks to subordinates and collect results."""
        results = []
        
        for subordinate in subordinates:
            # Get subordinate's portion of the task
            sub_task = await self._get_subordinate_task(
                context, leader, subordinate, instructions
            )
            
            message = await self._call_agent(
                context=context,
                member=subordinate,
                user_message=sub_task,
                turn=context.current_turn,
                iteration=context.current_iteration
            )
            results.append(message)
        
        return results
    
    async def _get_subordinate_task(
        self,
        context: ExecutionContext,
        leader: MemberContext,
        subordinate: MemberContext,
        instructions: str
    ) -> str:
        """Determine what task to give a specific subordinate."""
        prompt = f"""You are the leader. Based on the overall task and instructions, 
determine the specific portion for {subordinate.name}.

Overall task: {context.initial_input}

Leader's instructions:
{instructions}

Provide the specific task for {subordinate.name}."""
        
        result = await context.orchestrator.llm_call(
            system_prompt="You are a task coordinator.",
            user_message=prompt,
            temperature=0.3,
            max_tokens=500,
            tools=[]
        )
        
        return f"""Your role: {subordinate.name}

{subordinate.system_prompt}

Task from your manager:
{result.get('content', instructions)}

Complete this task and report your findings."""
    
    async def _leader_synthesize(
        self,
        context: ExecutionContext,
        leader: MemberContext,
        subordinate_results: List[ExecutionMessage]
    ) -> None:
        """Leader synthesizes results from subordinates."""
        if not subordinate_results:
            return
        
        results_text = "\n\n".join([
            f"### {r.member_name}'s Results:\n{r.content}"
            for r in subordinate_results
        ])
        
        await self._call_agent(
            context=context,
            member=leader,
            user_message=f"""Your subordinates have completed their tasks. Synthesize their results into a cohesive response.

Subordinate Results:
{results_text}

Original Task: {context.initial_input}

Provide a synthesized response that incorporates the subordinate work.""",
            turn=context.current_turn,
            iteration=context.current_iteration
        )
    
    async def _execute_sequential_fallback(
        self, 
        context: ExecutionContext
    ) -> ExecutionContext:
        """Fallback to sequential execution if no leader."""
        for member in context.members:
            await self._call_agent(
                context=context,
                member=member,
                user_message=context.initial_input,
                turn=context.current_turn,
                iteration=context.current_iteration
            )
        return context
    
    async def should_terminate(self, context: ExecutionContext) -> bool:
        """Check termination conditions for hierarchical mode."""
        current_depth = context.context.get("current_depth", 0)
        max_depth = context.context.get("max_depth", 3)
        
        return current_depth >= max_depth
    
    async def finalize(self, context: ExecutionContext) -> ExecutionContext:
        """Finalize hierarchical execution."""
        leader = context.context.get("leader")
        
        if leader:
            # Use leader's last message as final output
            for msg in reversed(context.messages):
                if msg.member_id == leader.member_id:
                    context.final_output = msg.content
                    break
        
        if not context.final_output:
            # Fallback to last message
            for msg in reversed(context.messages):
                if msg.message_type == "agent_output":
                    context.final_output = msg.content
                    break
        
        return context
