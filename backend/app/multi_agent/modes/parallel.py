"""Parallel collaboration mode - multiple agents work simultaneously."""
import asyncio
from typing import List, Optional
from ..orchestrator import (
    CollaborationModeHandler, ExecutionContext, ExecutionMessage, MemberContext
)


class ParallelModeHandler(CollaborationModeHandler):
    """Handler for parallel collaboration mode.
    
    Multiple agents work simultaneously on the same task,
    then results are aggregated based on the configured method.
    """
    
    @property
    def mode_name(self) -> str:
        return "parallel"
    
    async def initialize(self, context: ExecutionContext) -> ExecutionContext:
        """Initialize for parallel execution."""
        config = context.mode_config or {}
        
        # Set default aggregation method
        if "aggregation_method" not in config:
            config["aggregation_method"] = "merge"
        
        context.context["aggregation_method"] = config.get("aggregation_method", "merge")
        context.context["max_parallel"] = config.get("max_parallel", len(context.members))
        
        return context
    
    async def execute_iteration(self, context: ExecutionContext) -> ExecutionContext:
        """Execute one iteration: all agents work in parallel."""
        max_parallel = context.context.get("max_parallel", len(context.members))
        members_to_run = context.members[:max_parallel]
        
        # Prepare tasks for parallel execution
        tasks = []
        for member in members_to_run:
            user_message = self._build_parallel_message(context, member)
            tasks.append(
                self._call_agent(
                    context=context,
                    member=member,
                    user_message=user_message,
                    turn=context.current_turn,
                    iteration=context.current_iteration
                )
            )
        
        # Execute all agents in parallel
        await asyncio.gather(*tasks)
        
        # Aggregate results
        aggregated = await self._aggregate_results(context)
        
        # Store aggregated result
        context.context["aggregated_result"] = aggregated
        context.current_turn += 1
        
        return context
    
    def _build_parallel_message(
        self, 
        context: ExecutionContext, 
        member: MemberContext
    ) -> str:
        """Build the message for parallel execution."""
        return f"""You are working in parallel with other agents on the same task.

Your role: {member.name}
{member.system_prompt}

Task: {context.initial_input}

Provide your perspective/contribution on this task. Be concise but thorough."""
    
    async def _aggregate_results(self, context: ExecutionContext) -> str:
        """Aggregate results from parallel agents."""
        method = context.context.get("aggregation_method", "merge")
        agent_messages = [
            msg for msg in context.messages 
            if msg.message_type == "agent_output"
        ]
        
        if method == "merge":
            return await self._aggregate_merge(context, agent_messages)
        elif method == "vote":
            return await self._aggregate_vote(context, agent_messages)
        elif method == "first":
            return agent_messages[0].content if agent_messages else ""
        else:
            return await self._aggregate_merge(context, agent_messages)
    
    async def _aggregate_merge(
        self, 
        context: ExecutionContext, 
        messages: List[ExecutionMessage]
    ) -> str:
        """Merge all agent outputs into a cohesive response."""
        if not messages:
            return ""
        
        if len(messages) == 1:
            return messages[0].content
        
        # Build merge prompt
        contributions = []
        for msg in messages:
            contributions.append(f"### {msg.member_name}'s Contribution:\n{msg.content}")
        
        contributions_text = "\n\n".join(contributions)
        
        merge_prompt = f"""You need to synthesize the following contributions from multiple agents into a cohesive response.

{contributions_text}

Create a unified, coherent response that incorporates the key insights from all contributors. Remove contradictions where possible and highlight consensus points."""
        
        # Use orchestrator to generate merged response
        result = await context.orchestrator.llm_call(
            system_prompt="You are an expert at synthesizing multiple perspectives into a coherent response.",
            user_message=merge_prompt,
            temperature=0.5,
            max_tokens=context.members[0].max_tokens if context.members else 4096,
            tools=[]
        )
        
        return result.get("content", contributions_text)
    
    async def _aggregate_vote(
        self, 
        context: ExecutionContext, 
        messages: List[ExecutionMessage]
    ) -> str:
        """Select the best response through an evaluation."""
        if not messages:
            return ""
        
        if len(messages) == 1:
            return messages[0].content
        
        # Build voting prompt
        options = []
        for i, msg in enumerate(messages):
            options.append(f"Option {i+1} ({msg.member_name}):\n{msg.content}")
        
        options_text = "\n\n".join(options)
        
        vote_prompt = f"""Given the following responses from different agents, select the best one.
Consider: accuracy, completeness, clarity, and relevance to the task.

Task: {context.initial_input}

{options_text}

Select the best option and explain why it's superior."""
        
        result = await context.orchestrator.llm_call(
            system_prompt="You are an expert evaluator selecting the best response.",
            user_message=vote_prompt,
            temperature=0.1,
            max_tokens=1000,
            tools=[]
        )
        
        return result.get("content", messages[0].content)
    
    async def should_terminate(self, context: ExecutionContext) -> bool:
        """Check termination conditions for parallel mode."""
        # Typically runs for a fixed number of iterations
        config = context.mode_config or {}
        fixed_iterations = config.get("fixed_iterations", 1)
        
        if context.current_iteration >= fixed_iterations - 1:
            return True
        
        return False
    
    async def finalize(self, context: ExecutionContext) -> ExecutionContext:
        """Finalize parallel execution."""
        context.final_output = context.context.get("aggregated_result", "")
        
        if not context.final_output:
            # Fallback to first agent's message
            for msg in reversed(context.messages):
                if msg.message_type == "agent_output":
                    context.final_output = msg.content
                    break
        
        return context
