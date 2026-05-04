"""Debate collaboration mode - agents debate with pro/con positions."""
from typing import Optional
from ..orchestrator import (
    CollaborationModeHandler, ExecutionContext, ExecutionMessage, MemberContext
)


class DebateModeHandler(CollaborationModeHandler):
    """Handler for debate collaboration mode.
    
    Agents take pro/con positions and debate, with an optional judge
    evaluating the arguments.
    """
    
    @property
    def mode_name(self) -> str:
        return "debate"
    
    async def initialize(self, context: ExecutionContext) -> ExecutionContext:
        """Initialize for debate execution."""
        config = context.mode_config or {}
        
        # Set default rounds
        if "rounds" not in config:
            config["rounds"] = 3
        
        context.context["debate_rounds"] = config.get("rounds", 3)
        context.context["allow_rebuttal"] = config.get("allow_rebuttal", True)
        context.context["current_debate_round"] = 0
        context.context["current_position"] = "pro"  # or "con"
        
        # Identify debate roles
        pro_member = self._get_member_by_role(context, "supporter")
        con_member = self._get_member_by_role(context, "opponent")
        judge_member = self._get_member_by_role(context, "judge")
        
        # Store debate participants
        context.context["pro_member"] = pro_member
        context.context["con_member"] = con_member
        context.context["judge_member"] = judge_member
        
        # Fallback: use first two members as pro/con if not explicitly defined
        if not pro_member and len(context.members) >= 1:
            context.context["pro_member"] = context.members[0]
        if not con_member and len(context.members) >= 2:
            context.context["con_member"] = context.members[1]
        if not judge_member and len(context.members) >= 3:
            context.context["judge_member"] = context.members[2]
        
        return context
    
    async def execute_iteration(self, context: ExecutionContext) -> ExecutionContext:
        """Execute one iteration of the debate."""
        current_round = context.context.get("current_debate_round", 0)
        max_rounds = context.context.get("debate_rounds", 3)
        
        if current_round >= max_rounds:
            # Debate concluded, judge makes final decision
            return await self._execute_judgment(context)
        
        pro_member = context.context.get("pro_member")
        con_member = context.context.get("con_member")
        
        if current_round == 0:
            # Round 0: Opening statements
            await self._pro_argument(context, pro_member)
            await self._con_argument(context, con_member)
        else:
            # Subsequent rounds: arguments and rebuttals
            if context.context.get("allow_rebuttal"):
                await self._pro_rebuttal(context, pro_member, con_member)
                await self._con_rebuttal(context, con_member, pro_member)
            else:
                await self._pro_argument(context, pro_member)
                await self._con_argument(context, con_member)
        
        context.context["current_debate_round"] = current_round + 1
        context.current_turn += 1
        
        return context
    
    async def _pro_argument(
        self, 
        context: ExecutionContext, 
        member: Optional[MemberContext]
    ) -> None:
        """Pro side makes an argument."""
        if not member:
            return
        
        message = await self._call_agent(
            context=context,
            member=member,
            user_message=f"""You are arguing FOR the following proposition:

Topic: {context.initial_input}

Present your strongest arguments in favor. Be logical, evidence-based, and persuasive.""",
            turn=context.current_turn,
            iteration=context.current_iteration
        )
        context.context["last_pro_argument"] = message.content
    
    async def _con_argument(
        self, 
        context: ExecutionContext, 
        member: Optional[MemberContext]
    ) -> None:
        """Con side makes an argument."""
        if not member:
            return
        
        message = await self._call_agent(
            context=context,
            member=member,
            user_message=f"""You are arguing AGAINST the following proposition:

Topic: {context.initial_input}

Present your strongest counter-arguments. Be logical, evidence-based, and persuasive.""",
            turn=context.current_turn,
            iteration=context.current_iteration
        )
        context.context["last_con_argument"] = message.content
    
    async def _pro_rebuttal(
        self, 
        context: ExecutionContext, 
        member: Optional[MemberContext],
        opponent: Optional[MemberContext]
    ) -> None:
        """Pro side responds to con's arguments."""
        if not member:
            return
        
        last_con = context.context.get("last_con_argument", "")
        
        message = await self._call_agent(
            context=context,
            member=member,
            user_message=f"""You are arguing FOR the proposition and responding to counter-arguments.

Topic: {context.initial_input}

Opponent's arguments:
{last_con}

Present your rebuttal, addressing their points while strengthening your own position.""",
            turn=context.current_turn,
            iteration=context.current_iteration
        )
        context.context["last_pro_argument"] = message.content
    
    async def _con_rebuttal(
        self, 
        context: ExecutionContext, 
        member: Optional[MemberContext],
        opponent: Optional[MemberContext]
    ) -> None:
        """Con side responds to pro's arguments."""
        if not member:
            return
        
        last_pro = context.context.get("last_pro_argument", "")
        
        message = await self._call_agent(
            context=context,
            member=member,
            user_message=f"""You are arguing AGAINST the proposition and responding to counter-arguments.

Topic: {context.initial_input}

Opponent's arguments:
{last_pro}

Present your rebuttal, addressing their points while strengthening your own position.""",
            turn=context.current_turn,
            iteration=context.current_iteration
        )
        context.context["last_con_argument"] = message.content
    
    async def _execute_judgment(self, context: ExecutionContext) -> ExecutionContext:
        """Judge evaluates the debate and makes a decision."""
        judge_member = context.context.get("judge_member")
        
        if not judge_member:
            # No judge, use the last pro argument as the synthesis
            context.final_output = context.context.get("last_pro_argument", "")
            return context
        
        # Collect all debate content
        pro_args = []
        con_args = []
        for msg in context.messages:
            if msg.message_type == "agent_output":
                if msg.member_id == context.context.get("pro_member", {}).get("member_id"):
                    pro_args.append(msg.content)
                elif msg.member_id == context.context.get("con_member", {}).get("member_id"):
                    con_args.append(msg.content)
        
        judgment_prompt = f"""You are the judge in a debate. Evaluate the arguments and make a decision.

Topic: {context.initial_input}

Arguments FOR:
{chr(10).join(pro_args)}

Arguments AGAINST:
{chr(10).join(con_args)}

Provide your evaluation and conclusion. Who made the stronger case? What are the key insights from both sides?"""
        
        message = await self._call_agent(
            context=context,
            member=judge_member,
            user_message=judgment_prompt,
            turn=context.current_turn,
            iteration=context.current_iteration
        )
        
        context.final_output = message.content
        return context
    
    async def should_terminate(self, context: ExecutionContext) -> bool:
        """Check termination conditions for debate mode."""
        current_round = context.context.get("current_debate_round", 0)
        max_rounds = context.context.get("debate_rounds", 3)
        
        # End debate after all rounds + judgment
        return current_round >= max_rounds + 1
    
    async def finalize(self, context: ExecutionContext) -> ExecutionContext:
        """Finalize debate execution."""
        if not context.final_output:
            # Use judge decision or last argument
            judge = context.context.get("judge_member")
            if judge:
                for msg in reversed(context.messages):
                    if msg.member_id == judge.get("member_id"):
                        context.final_output = msg.content
                        break
            
            if not context.final_output:
                context.final_output = context.context.get("last_pro_argument", "")
        
        return context
