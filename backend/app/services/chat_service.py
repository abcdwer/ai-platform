"""Chat service for handling conversations."""
import json
import uuid
import re
from typing import AsyncIterator, Optional, Any
from datetime import datetime

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation, Message
from app.models.agent import Agent
from app.models.schemas.conversation import ChatRequest, ChatMessage, MessageResponse, ConversationCreate
from app.services.model_dispatcher import ModelDispatcher, ChatMessage as DispatcherChatMessage, StreamChunk, ChatCompletion


class ChatService:
    """Service for handling chat operations."""
    
    def __init__(self, db: AsyncSession, dispatcher: ModelDispatcher):
        self.db = db
        self.dispatcher = dispatcher
    
    async def create_conversation(
        self,
        user_id: str,
        title: str = "New Chat",
        agent_id: Optional[str] = None,
        model: str = "llama2",
        model_provider: str = "ollama"
    ) -> Conversation:
        """Create a new conversation."""
        conversation = Conversation(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            agent_id=agent_id,
            model=model,
            model_provider=model_provider,
        )
        self.db.add(conversation)
        await self.db.flush()
        await self.db.refresh(conversation)
        return conversation
    
    async def get_conversation(self, conversation_id: str, user_id: str) -> Optional[Conversation]:
        """Get a conversation by ID."""
        result = await self.db.execute(
            select(Conversation)
            .options(selectinload(Conversation.messages))
            .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def get_conversations(
        self,
        user_id: str,
        page: int = 1,
        page_size: int = 20,
        include_archived: bool = False
    ) -> tuple[list[Conversation], int]:
        """Get paginated conversations for a user."""
        query = select(Conversation).where(Conversation.user_id == user_id)
        
        if not include_archived:
            query = query.where(Conversation.is_archived == False)
        
        # Get total count
        count_result = await self.db.execute(
            select(Conversation.id).where(Conversation.user_id == user_id)
        )
        total = len(count_result.scalars().all())
        
        # Get paginated results
        query = query.order_by(Conversation.updated_at.desc())
        query = query.offset((page - 1) * page_size).limit(page_size)
        
        result = await self.db.execute(query)
        conversations = result.scalars().all()
        
        return conversations, total
    
    async def update_conversation(
        self,
        conversation_id: str,
        user_id: str,
        **kwargs
    ) -> Optional[Conversation]:
        """Update a conversation."""
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            return None
        
        for key, value in kwargs.items():
            if hasattr(conversation, key) and value is not None:
                setattr(conversation, key, value)
        
        conversation.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(conversation)
        return conversation
    
    async def delete_conversation(self, conversation_id: str, user_id: str) -> bool:
        """Delete a conversation."""
        conversation = await self.get_conversation(conversation_id, user_id)
        if not conversation:
            return False
        
        await self.db.delete(conversation)
        await self.db.flush()
        return True
    
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        name: Optional[str] = None,
        tool_call_id: Optional[str] = None,
        tool_calls: Optional[dict] = None,
        tokens_used: Optional[int] = None
    ) -> Message:
        """Add a message to a conversation."""
        message = Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=role,
            content=content,
            name=name,
            tool_call_id=tool_call_id,
            tool_calls=tool_calls,
            tokens_used=tokens_used,
        )
        self.db.add(message)
        
        # Update conversation timestamp
        conversation = await self.db.get(Conversation, conversation_id)
        if conversation:
            conversation.updated_at = datetime.utcnow()
        
        await self.db.flush()
        await self.db.refresh(message)
        return message
    
    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Get an agent by ID."""
        result = await self.db.execute(
            select(Agent).where(Agent.id == agent_id, Agent.is_active == True)
        )
        return result.scalar_one_or_none()
    
    def _generate_title(self, first_message: str) -> str:
        """Generate a title from the first message."""
        content = first_message.strip()
        
        # Clean up the content
        # Remove markdown formatting
        content = re.sub(r'```[\s\S]*?```', '[code]', content)
        content = re.sub(r'`[^`]+`', '[code]', content)
        content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)
        content = re.sub(r'[#*_~>]+', '', content)
        
        # Take first 50 characters
        title = content[:50].strip()
        
        # If the title is too long, cut at word boundary
        if len(first_message) > 50:
            # Try to find a good cutoff point
            words = title.rsplit(' ', 1)
            if len(words) > 1:
                title = words[0]
            title = title + "..."
        
        return title or "New Chat"
    
    async def chat(
        self,
        request: ChatRequest,
        user_id: str
    ) -> tuple[Conversation, Message]:
        """Process a non-streaming chat request."""
        # Get or create conversation
        is_new_conversation = False
        if request.conversation_id:
            conversation = await self.get_conversation(request.conversation_id, user_id)
            if not conversation:
                raise ValueError("Conversation not found")
        else:
            # Create new conversation with temporary title
            conversation = await self.create_conversation(
                user_id=user_id,
                title="New Chat",
                agent_id=request.agent_id,
                model=request.model or "llama2",
                model_provider=request.model_provider or "ollama"
            )
            is_new_conversation = True
        
        # Get agent if specified
        agent = None
        if request.agent_id:
            agent = await self.get_agent(request.agent_id)
        
        # Build messages for the model
        model_messages = []
        
        # Add system prompt from agent if available
        if agent and agent.system_prompt:
            model_messages.append(DispatcherChatMessage(
                role="system",
                content=agent.system_prompt
            ))
        
        # Add conversation history
        for msg in conversation.messages:
            model_messages.append(DispatcherChatMessage(
                role=msg.role,
                content=msg.content,
                name=msg.name,
                tool_call_id=msg.tool_call_id
            ))
        
        # Add current messages
        for msg in request.messages:
            model_messages.append(DispatcherChatMessage(
                role=msg.role,
                content=msg.content,
                name=msg.name,
                tool_calls=msg.tool_calls,
                tool_call_id=msg.tool_call_id
            ))
        
        # Determine model and provider
        model = request.model or conversation.model or (agent.model if agent else "llama2")
        provider = request.model_provider or conversation.model_provider or (agent.model_provider if agent else "ollama")
        
        # Get tools
        tools = request.tools or (agent.get_available_tools() if agent else None)
        
        # Call the model
        response = await self.dispatcher.chat(
            messages=model_messages,
            model=model,
            provider=provider,
            temperature=request.temperature or (agent.temperature if agent else 0.7),
            max_tokens=request.max_tokens or (agent.max_tokens if agent else 4096),
            tools=tools
        )
        
        # Save assistant message
        assistant_message = await self.add_message(
            conversation_id=conversation.id,
            role="assistant",
            content=response.content,
            tool_calls=response.tool_calls
        )
        
        # Update conversation title if it's a new conversation
        if is_new_conversation and request.messages:
            first_message = request.messages[0].content
            conversation.title = self._generate_title(first_message)
        
        await self.db.commit()
        return conversation, assistant_message
    
    async def chat_stream(
        self,
        request: ChatRequest,
        user_id: str
    ) -> AsyncIterator[dict]:
        """Process a streaming chat request."""
        # Get or create conversation
        is_new_conversation = False
        if request.conversation_id:
            conversation = await self.get_conversation(request.conversation_id, user_id)
            if not conversation:
                raise ValueError("Conversation not found")
        else:
            # Create new conversation with temporary title
            conversation = await self.create_conversation(
                user_id=user_id,
                title="New Chat",
                agent_id=request.agent_id,
                model=request.model or "llama2",
                model_provider=request.model_provider or "ollama"
            )
            is_new_conversation = True
            await self.db.commit()
        
        # Get agent if specified
        agent = None
        if request.agent_id:
            agent = await self.get_agent(request.agent_id)
        
        # Save user messages
        for msg in request.messages:
            await self.add_message(
                conversation_id=conversation.id,
                role=msg.role,
                content=msg.content,
                name=msg.name,
                tool_call_id=msg.tool_call_id
            )
        await self.db.commit()
        
        # Build messages for the model
        model_messages = []
        
        if agent and agent.system_prompt:
            model_messages.append(DispatcherChatMessage(
                role="system",
                content=agent.system_prompt
            ))
        
        for msg in conversation.messages:
            model_messages.append(DispatcherChatMessage(
                role=msg.role,
                content=msg.content,
                name=msg.name,
                tool_call_id=msg.tool_call_id
            ))
        
        # Determine model and provider
        model = request.model or conversation.model or (agent.model if agent else "llama2")
        provider = request.model_provider or conversation.model_provider or (agent.model_provider if agent else "ollama")
        
        # Get tools
        tools = request.tools or (agent.get_available_tools() if agent else None)
        
        # Send conversation ID first
        yield {
            "type": "conversation_id",
            "conversation_id": conversation.id
        }
        
        # Send auto-generated title if new conversation
        if is_new_conversation and request.messages:
            title = self._generate_title(request.messages[0].content)
            yield {
                "type": "title",
                "title": title
            }
        
        # Stream the response
        full_content = ""
        tool_calls = None
        
        try:
            async for chunk in self.dispatcher.stream(
                messages=model_messages,
                model=model,
                provider=provider,
                temperature=request.temperature or (agent.temperature if agent else 0.7),
                max_tokens=request.max_tokens or (agent.max_tokens if agent else 4096),
                tools=tools
            ):
                if chunk.delta:
                    full_content += chunk.delta
                    yield {
                        "type": "message",
                        "content": chunk.delta
                    }
                
                if chunk.tool_call:
                    tool_calls = chunk.tool_call
                    yield {
                        "type": "tool_call",
                        "tool_call": chunk.tool_call
                    }
                
                if chunk.finish_reason:
                    yield {
                        "type": "done",
                        "finish_reason": chunk.finish_reason
                    }
                    
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield {
                "type": "error",
                "error": str(e)
            }
            return
        
        # Save assistant message
        if full_content or tool_calls:
            await self.add_message(
                conversation_id=conversation.id,
                role="assistant",
                content=full_content,
                tool_calls=[tool_calls] if tool_calls else None
            )
        
        # Update conversation title if new conversation
        if is_new_conversation and request.messages:
            title = self._generate_title(request.messages[0].content)
            conversation.title = title
            await self.db.commit()
