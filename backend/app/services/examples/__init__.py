"""Service to initialize sample data for new users."""
import uuid
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.models.knowledge import KnowledgeBase
from app.models.document import Document, DocumentStatus
from app.models.workflow import Workflow, WorkflowStatus
from app.models.conversation import Conversation, Message
from app.services.examples.sample_data import (
    KNOWLEDGE_BASE_TEMPLATES,
    WORKFLOW_TEMPLATES,
    EXAMPLE_CONVERSATIONS,
)


class SampleDataService:
    """Service to populate sample data for users."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_knowledge_bases(self, user_id: str) -> List[KnowledgeBase]:
        """Create sample knowledge bases for a user."""
        created_kbs = []
        
        for template in KNOWLEDGE_BASE_TEMPLATES:
            kb = KnowledgeBase(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=template["name"],
                description=template["description"],
                tags=template.get("tags", []),
                document_count=len(template.get("documents", [])),
                vector_count=0,
            )
            self.db.add(kb)
            created_kbs.append(kb)
            
            # Create documents for this knowledge base
            for doc_template in template.get("documents", []):
                doc = Document(
                    id=str(uuid.uuid4()),
                    knowledge_base_id=kb.id,
                    title=doc_template["title"],
                    content_type="text",
                    content=doc_template["content"],
                    file_size=len(doc_template["content"]),
                    status=DocumentStatus.COMPLETED.value,
                    chunk_count=len(doc_template["content"]) // 500 + 1,
                )
                self.db.add(doc)
                kb.vector_count += doc.chunk_count
            
            kb.document_count = len(template.get("documents", []))
        
        await self.db.flush()
        logger.info(f"Created {len(created_kbs)} sample knowledge bases for user {user_id}")
        return created_kbs
    
    async def create_workflows(self, user_id: str) -> List[Workflow]:
        """Create sample workflows for a user."""
        created_workflows = []
        
        for template in WORKFLOW_TEMPLATES:
            workflow = Workflow(
                id=str(uuid.uuid4()),
                user_id=user_id,
                name=template["name"],
                description=template["description"],
                graph_data=template["graph_data"],
                status=WorkflowStatus.DRAFT.value,
            )
            self.db.add(workflow)
            created_workflows.append(workflow)
        
        await self.db.flush()
        logger.info(f"Created {len(created_workflows)} sample workflows for user {user_id}")
        return created_workflows
    
    async def create_example_conversations(self, user_id: str) -> List[Conversation]:
        """Create sample conversations for a user."""
        created_conversations = []
        
        for template in EXAMPLE_CONVERSATIONS:
            conversation = Conversation(
                id=str(uuid.uuid4()),
                user_id=user_id,
                title=template["title"],
                model=template.get("model", "llama2"),
                model_provider=template.get("model_provider", "ollama"),
            )
            self.db.add(conversation)
            created_conversations.append(conversation)
            
            # Create messages for this conversation
            for msg_template in template.get("messages", []):
                message = Message(
                    id=str(uuid.uuid4()),
                    conversation_id=conversation.id,
                    role=msg_template["role"],
                    content=msg_template["content"],
                )
                self.db.add(message)
        
        await self.db.flush()
        logger.info(f"Created {len(created_conversations)} sample conversations for user {user_id}")
        return created_conversations
    
    async def initialize_user_samples(self, user_id: str) -> Dict[str, Any]:
        """Initialize all sample data for a new user."""
        logger.info(f"Initializing sample data for user {user_id}")
        
        # Create all sample data
        knowledge_bases = await self.create_knowledge_bases(user_id)
        workflows = await self.create_workflows(user_id)
        conversations = await self.create_example_conversations(user_id)
        
        await self.db.commit()
        
        return {
            "knowledge_bases": len(knowledge_bases),
            "workflows": len(workflows),
            "conversations": len(conversations),
        }
