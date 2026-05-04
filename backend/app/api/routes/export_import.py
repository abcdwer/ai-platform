"""Export and Import API routes for conversations, workflows, and knowledge bases."""
import uuid
import json
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.conversation import Conversation, Message
from app.models.workflow import Workflow
from app.models.knowledge import KnowledgeBase
from app.models.document import Document
from app.models.schemas.conversation import ConversationResponse
from app.models.schemas.workflow import WorkflowResponse
from app.models.schemas.knowledge import KnowledgeBaseResponse
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api", tags=["Export & Import"])


# ==================== Conversation Export ====================

class ConversationExporter:
    """Export conversation to various formats."""
    
    @staticmethod
    def to_markdown(conversation: dict, messages: list) -> str:
        """Export conversation to Markdown format."""
        lines = [
            f"# {conversation.get('title', 'Untitled Conversation')}",
            "",
            f"**Model:** {conversation.get('model', 'N/A')} ({conversation.get('model_provider', 'N/A')})",
            f"**Created:** {conversation.get('created_at', 'N/A')}",
            f"**Updated:** {conversation.get('updated_at', 'N/A')}",
            "",
            "---",
            ""
        ]
        
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            name = msg.get("name")
            created_at = msg.get("created_at", "")
            
            if role == "user":
                lines.append(f"## 👤 User")
            elif role == "assistant":
                lines.append(f"## 🤖 Assistant")
            elif role == "system":
                lines.append(f"## ⚙️ System")
            elif role == "tool":
                lines.append(f"## 🔧 Tool: {name or 'Result'}")
            else:
                lines.append(f"## {role}")
            
            lines.append(f"*{created_at}*" if created_at else "")
            lines.append("")
            lines.append(content)
            lines.append("")
            
            # Handle tool calls
            if msg.get("tool_calls"):
                lines.append("**Tool Calls:**")
                for tc in msg["tool_calls"]:
                    lines.append(f"```json\n{json.dumps(tc, indent=2, ensure_ascii=False)}\n```")
                lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def to_json(conversation: dict, messages: list) -> dict:
        """Export conversation to JSON format."""
        return {
            "export_version": "1.0",
            "exported_at": datetime.utcnow().isoformat(),
            "conversation": {
                "id": conversation.get("id"),
                "title": conversation.get("title"),
                "model": conversation.get("model"),
                "model_provider": conversation.get("model_provider"),
                "created_at": conversation.get("created_at"),
                "updated_at": conversation.get("updated_at"),
                "is_pinned": conversation.get("is_pinned", False),
                "is_archived": conversation.get("is_archived", False),
            },
            "messages": messages,
            "metadata": {
                "message_count": len(messages),
                "total_tokens": sum(m.get("tokens_used", 0) or 0 for m in messages),
            }
        }
    
    @staticmethod
    def to_pdf_text(conversation: dict, messages: list) -> str:
        """Export conversation to plain text for PDF conversion."""
        lines = [
            conversation.get('title', 'Untitled Conversation'),
            "=" * 50,
            "",
            f"Model: {conversation.get('model', 'N/A')}",
            f"Provider: {conversation.get('model_provider', 'N/A')}",
            f"Created: {conversation.get('created_at', 'N/A')}",
            "",
            "-" * 50,
            ""
        ]
        
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            role_label = {
                "user": "User",
                "assistant": "Assistant", 
                "system": "System",
                "tool": "Tool"
            }.get(role, role)
            
            lines.append(f"[{role_label}]")
            lines.append(content)
            lines.append("")
        
        return "\n".join(lines)


@router.get(
    "/conversations/{conversation_id}/export",
    summary="Export Conversation",
    description="Export a conversation to Markdown, JSON, or PDF format"
)
async def export_conversation(
    conversation_id: str,
    format: str = Query("markdown", enum=["markdown", "json", "pdf", "html"]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export a conversation in the specified format.
    
    - **conversation_id**: The ID of the conversation to export
    - **format**: Export format (markdown, json, pdf, html)
    
    Returns the exported file content with appropriate media type.
    """
    # Get conversation
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == current_user.id
        )
    )
    conversation = result.scalar_one_or_none()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get messages
    msg_result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    messages = msg_result.scalars().all()
    
    # Convert to dict
    conv_dict = {
        "id": conversation.id,
        "title": conversation.title,
        "model": conversation.model,
        "model_provider": conversation.model_provider,
        "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
        "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None,
        "is_pinned": conversation.is_pinned,
        "is_archived": conversation.is_archived,
    }
    
    msg_list = [{
        "id": m.id,
        "role": m.role,
        "content": m.content,
        "name": m.name,
        "tool_calls": m.tool_calls,
        "tool_call_id": m.tool_call_id,
        "tokens_used": m.tokens_used,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    } for m in messages]
    
    filename = f"conversation_{conversation.title[:20].replace(' ', '_')}_{conversation_id[:8]}"
    
    if format == "json":
        content = json.dumps(ConversationExporter.to_json(conv_dict, msg_list), indent=2, ensure_ascii=False)
        return StreamingResponse(
            iter([content]),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}.json"}
        )
    
    elif format == "markdown":
        content = ConversationExporter.to_markdown(conv_dict, msg_list)
        return StreamingResponse(
            iter([content]),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename={filename}.md"}
        )
    
    elif format == "pdf":
        content = ConversationExporter.to_pdf_text(conv_dict, msg_list)
        return StreamingResponse(
            iter([content]),
            media_type="text/plain",
            headers={"Content-Disposition": f"attachment; filename={filename}.txt"}
        )
    
    elif format == "html":
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{conversation.title}</title>
    <style>
        body {{ font-family: system-ui, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
        .header {{ border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }}
        .message {{ margin-bottom: 20px; padding: 15px; border-radius: 8px; }}
        .user {{ background: #e3f2fd; }}
        .assistant {{ background: #f5f5f5; }}
        .system {{ background: #fff3e0; }}
        .tool {{ background: #f3e5f5; }}
        .role {{ font-weight: bold; margin-bottom: 5px; color: #666; }}
        .content {{ white-space: pre-wrap; }}
        .meta {{ font-size: 12px; color: #999; margin-top: 5px; }}
        pre {{ background: #1e1e1e; color: #d4d4d4; padding: 10px; border-radius: 5px; overflow-x: auto; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{conversation.title}</h1>
        <p><strong>Model:</strong> {conversation.model} ({conversation.model_provider})</p>
        <p><strong>Created:</strong> {conversation.created_at}</p>
        <p><strong>Messages:</strong> {len(messages)}</p>
    </div>
"""
        for msg in msg_list:
            role_class = msg["role"]
            role_label = {"user": "👤 User", "assistant": "🤖 Assistant", "system": "⚙️ System", "tool": "🔧 Tool"}.get(msg["role"], msg["role"])
            content = msg["content"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            
            if msg.get("tool_calls"):
                content += "<pre>" + json.dumps(msg["tool_calls"], indent=2, ensure_ascii=False) + "</pre>"
            
            html_content += f"""
    <div class="message {role_class}">
        <div class="role">{role_label}</div>
        <div class="content">{content}</div>
        <div class="meta">{msg.get('created_at', '')}</div>
    </div>
"""
        html_content += """
</body>
</html>"""
        return StreamingResponse(
            iter([html_content]),
            media_type="text/html",
            headers={"Content-Disposition": f"attachment; filename={filename}.html"}
        )
    
    raise HTTPException(status_code=400, detail="Invalid format")


# ==================== Workflow Share & Export ====================

class WorkflowExporter:
    """Export workflow to shareable formats."""
    
    @staticmethod
    def to_shareable_config(workflow: dict) -> dict:
        """Convert workflow to shareable configuration."""
        return {
            "version": "1.0",
            "type": "ai-platform-workflow",
            "exported_at": datetime.utcnow().isoformat(),
            "workflow": {
                "name": workflow.get("name"),
                "description": workflow.get("description"),
                "graph_data": workflow.get("graph_data"),
            }
        }


@router.get(
    "/workflows/{workflow_id}/share",
    summary="Share Workflow",
    description="Generate a shareable link and export configuration for a workflow"
)
async def share_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Share a workflow by generating a shareable link and export configuration.
    
    - **workflow_id**: The ID of the workflow to share
    
    Returns a share link token and the workflow configuration JSON.
    """
    # Get workflow
    result = await db.execute(
        select(Workflow).where(
            Workflow.id == workflow_id,
            Workflow.user_id == current_user.id
        )
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Generate share token
    share_token = str(uuid.uuid4())
    
    # Build response
    workflow_dict = {
        "id": workflow.id,
        "name": workflow.name,
        "description": workflow.description,
        "status": workflow.status,
        "version": workflow.version,
        "graph_data": workflow.graph_data,
        "created_at": workflow.created_at.isoformat() if workflow.created_at else None,
        "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None,
    }
    
    return {
        "share_token": share_token,
        "share_url": f"/workflows/import?token={share_token}",
        "workflow": WorkflowExporter.to_shareable_config(workflow_dict),
        "export_config": WorkflowExporter.to_shareable_config(workflow_dict),
    }


@router.get(
    "/workflows/{workflow_id}/export",
    summary="Export Workflow",
    description="Export workflow as JSON configuration file"
)
async def export_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export a workflow as a JSON configuration file.
    
    - **workflow_id**: The ID of the workflow to export
    
    Returns the workflow configuration as a downloadable JSON file.
    """
    result = await db.execute(
        select(Workflow).where(
            Workflow.id == workflow_id,
            Workflow.user_id == current_user.id
        )
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    export_data = WorkflowExporter.to_shareable_config({
        "name": workflow.name,
        "description": workflow.description,
        "graph_data": workflow.graph_data,
    })
    
    filename = f"workflow_{workflow.name[:30].replace(' ', '_')}_{workflow_id[:8]}"
    
    return StreamingResponse(
        iter([json.dumps(export_data, indent=2, ensure_ascii=False)]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}.json"}
    )


class WorkflowImportRequest(BaseModel):
    """Request schema for importing a workflow."""
    name: str = Field(..., description="Name of the workflow")
    description: Optional[str] = Field(None, description="Description")
    graph_data: dict = Field(..., description="Workflow graph data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "My Workflow",
                "description": "A sample workflow",
                "graph_data": {
                    "nodes": [{"id": "1", "type": "start"}],
                    "edges": []
                }
            }
        }


from pydantic import BaseModel, Field

@router.post(
    "/workflows/import",
    response_model=WorkflowResponse,
    summary="Import Workflow",
    description="Import a workflow from JSON configuration",
    responses={
        200: {"description": "Workflow imported successfully"},
        400: {"description": "Invalid configuration format"},
    }
)
async def import_workflow(
    config: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Import a workflow from JSON configuration.
    
    - **config**: The workflow configuration object containing name, description, and graph_data
    
    Creates a new workflow with the imported configuration.
    """
    try:
        # Validate config structure
        if "workflow" in config:
            workflow_data = config["workflow"]
        else:
            workflow_data = config
        
        if not workflow_data.get("name"):
            raise HTTPException(status_code=400, detail="Workflow name is required")
        
        if not workflow_data.get("graph_data"):
            raise HTTPException(status_code=400, detail="Workflow graph_data is required")
        
        # Create new workflow
        workflow = Workflow(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            name=workflow_data["name"],
            description=workflow_data.get("description", ""),
            graph_data=workflow_data["graph_data"],
            status="draft"
        )
        
        db.add(workflow)
        await db.commit()
        await db.refresh(workflow)
        
        return workflow
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid workflow configuration: {str(e)}")


# ==================== Knowledge Base Export & Import ====================

class KnowledgeExporter:
    """Export knowledge base to various formats."""
    
    @staticmethod
    def to_markdown(kb: dict, documents: list) -> str:
        """Export knowledge base to Markdown format."""
        lines = [
            f"# {kb.get('name', 'Knowledge Base')}",
            "",
            kb.get('description', ''),
            "",
            f"**Tags:** {', '.join(kb.get('tags', []) or [])}",
            f"**Documents:** {len(documents)}",
            "",
            "---",
            ""
        ]
        
        for i, doc in enumerate(documents, 1):
            lines.append(f"## {i}. {doc.get('title', 'Untitled')}")
            lines.append("")
            lines.append(doc.get('content', ''))
            lines.append("")
            lines.append(f"*Source: {doc.get('source', 'N/A')}*")
            lines.append("")
            lines.append("---")
            lines.append("")
        
        return "\n".join(lines)
    
    @staticmethod
    def to_json(kb: dict, documents: list) -> dict:
        """Export knowledge base to JSON format."""
        return {
            "version": "1.0",
            "type": "ai-platform-knowledge-base",
            "exported_at": datetime.utcnow().isoformat(),
            "knowledge_base": {
                "name": kb.get("name"),
                "description": kb.get("description"),
                "tags": kb.get("tags", []),
            },
            "documents": [
                {
                    "title": doc.get("title"),
                    "content": doc.get("content"),
                    "source": doc.get("source"),
                    "metadata": doc.get("metadata", {}),
                }
                for doc in documents
            ],
            "metadata": {
                "document_count": len(documents),
                "total_chunks": sum(doc.get("chunk_count", 0) for doc in documents),
            }
        }
    
    @staticmethod
    def to_html(kb: dict, documents: list) -> str:
        """Export knowledge base to HTML format."""
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{kb.get('name', 'Knowledge Base')}</title>
    <style>
        body {{ font-family: system-ui, sans-serif; max-width: 900px; margin: 0 auto; padding: 20px; }}
        .header {{ border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px; }}
        .doc {{ margin-bottom: 40px; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }}
        .doc-title {{ font-size: 1.3em; margin-bottom: 10px; color: #333; }}
        .doc-content {{ line-height: 1.8; }}
        .doc-source {{ font-size: 12px; color: #666; margin-top: 10px; }}
        .tags {{ margin: 10px 0; }}
        .tag {{ background: #e0e0e0; padding: 2px 8px; border-radius: 4px; font-size: 12px; margin-right: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{kb.get('name', 'Knowledge Base')}</h1>
        <p>{kb.get('description', '')}</p>
        <div class="tags">
"""
        for tag in (kb.get('tags') or []):
            html += f'            <span class="tag">{tag}</span>\n'
        
        html += f"""        </div>
        <p><strong>Documents:</strong> {len(documents)}</p>
    </div>
"""
        for doc in documents:
            html += f"""
    <div class="doc">
        <div class="doc-title">{doc.get('title', 'Untitled')}</div>
        <div class="doc-content">{doc.get('content', '')}</div>
        <div class="doc-source">Source: {doc.get('source', 'N/A')}</div>
    </div>
"""
        
        html += """
</body>
</html>"""
        return html


@router.get(
    "/knowledge/{kb_id}/export",
    summary="Export Knowledge Base",
    description="Export a knowledge base to Markdown, JSON, or HTML format"
)
async def export_knowledge_base(
    kb_id: str,
    format: str = Query("json", enum=["markdown", "json", "html"]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export a knowledge base in the specified format.
    
    - **kb_id**: The ID of the knowledge base to export
    - **format**: Export format (markdown, json, html)
    
    Returns the exported file content with appropriate media type.
    """
    # Get knowledge base
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == current_user.id
        )
    )
    kb = result.scalar_one_or_none()
    
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    # Get documents
    doc_result = await db.execute(
        select(Document).where(Document.knowledge_base_id == kb_id)
    )
    documents = doc_result.scalars().all()
    
    kb_dict = {
        "id": kb.id,
        "name": kb.name,
        "description": kb.description,
        "tags": kb.tags or [],
    }
    
    doc_list = [{
        "id": d.id,
        "title": d.title,
        "content": d.content or "",
        "source": d.source or "",
        "metadata": d.metadata or {},
        "chunk_count": d.chunk_count or 0,
    } for d in documents]
    
    filename = f"knowledge_{kb.name[:30].replace(' ', '_')}_{kb_id[:8]}"
    
    if format == "json":
        content = json.dumps(KnowledgeExporter.to_json(kb_dict, doc_list), indent=2, ensure_ascii=False)
        return StreamingResponse(
            iter([content]),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}.json"}
        )
    
    elif format == "markdown":
        content = KnowledgeExporter.to_markdown(kb_dict, doc_list)
        return StreamingResponse(
            iter([content]),
            media_type="text/markdown",
            headers={"Content-Disposition": f"attachment; filename={filename}.md"}
        )
    
    elif format == "html":
        content = KnowledgeExporter.to_html(kb_dict, doc_list)
        return StreamingResponse(
            iter([content]),
            media_type="text/html",
            headers={"Content-Disposition": f"attachment; filename={filename}.html"}
        )
    
    raise HTTPException(status_code=400, detail="Invalid format")


class DocumentImportRequest(BaseModel):
    """Request schema for importing a document."""
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Document content")
    source: Optional[str] = Field(None, description="Source URL or path")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "My Document",
                "content": "Document content here...",
                "source": "https://example.com",
                "metadata": {"author": "John Doe"}
            }
        }


class KnowledgeImportRequest(BaseModel):
    """Request schema for batch importing documents."""
    documents: list[DocumentImportRequest] = Field(..., description="List of documents to import")
    
    class Config:
        json_schema_extra = {
            "example": {
                "documents": [
                    {
                        "title": "Document 1",
                        "content": "Content of document 1",
                        "source": "https://example.com/1"
                    },
                    {
                        "title": "Document 2", 
                        "content": "Content of document 2",
                        "source": "file://local/doc2.txt"
                    }
                ]
            }
        }


@router.post(
    "/knowledge/{kb_id}/import",
    response_model=dict,
    summary="Import Documents",
    description="Batch import documents into a knowledge base",
    responses={
        200: {"description": "Documents imported successfully"},
        404: {"description": "Knowledge base not found"},
    }
)
async def import_documents(
    kb_id: str,
    import_data: KnowledgeImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Batch import documents into a knowledge base.
    
    - **kb_id**: The ID of the target knowledge base
    - **documents**: List of documents to import (title, content, source, metadata)
    
    Returns the count of successfully imported documents.
    """
    # Verify knowledge base exists and user owns it
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.user_id == current_user.id
        )
    )
    kb = result.scalar_one_or_none()
    
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    # Import documents
    imported_count = 0
    imported_docs = []
    
    for doc_data in import_data.documents:
        document = Document(
            id=str(uuid.uuid4()),
            knowledge_base_id=kb_id,
            title=doc_data.title,
            content=doc_data.content,
            source=doc_data.source,
            content_type="text",
            metadata=doc_data.metadata,
            status="ready",
            chunk_count=0,
        )
        db.add(document)
        imported_docs.append(document)
        imported_count += 1
    
    await db.commit()
    
    return {
        "message": f"Successfully imported {imported_count} documents",
        "imported_count": imported_count,
        "documents": [{"id": d.id, "title": d.title} for d in imported_docs],
    }


# ==================== Postman Collection Generator ====================

@router.get(
    "/docs/postman-collection",
    summary="Download Postman Collection",
    description="Generate and download a Postman collection for all API endpoints"
)
async def get_postman_collection():
    """
    Generate a Postman Collection JSON file for all API endpoints.
    
    This includes all routes with their methods, paths, parameters,
    and example requests/responses for easy API testing.
    """
    collection = {
        "info": {
            "name": "AI Platform API",
            "description": "AI Platform - Unified interface for local and cloud AI models",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            "version": "1.0.0"
        },
        "variable": [
            {"key": "baseUrl", "value": "http://localhost:8000"}
        ],
        "auth": {
            "type": "bearer",
            "bearer": [{"key": "token", "value": "{{token}}", "type": "string"}]
        },
        "item": [
            {
                "name": "Authentication",
                "item": [
                    {
                        "name": "Register",
                        "request": {
                            "method": "POST",
                            "url": "{{baseUrl}}/api/auth/register",
                            "header": [{"key": "Content-Type", "value": "application/json"}],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "email": "user@example.com",
                                    "password": "password123",
                                    "full_name": "John Doe"
                                }, indent=2)
                            }
                        }
                    },
                    {
                        "name": "Login",
                        "request": {
                            "method": "POST",
                            "url": "{{baseUrl}}/api/auth/login",
                            "header": [{"key": "Content-Type", "value": "application/json"}],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "email": "user@example.com",
                                    "password": "password123"
                                }, indent=2)
                            }
                        }
                    },
                    {
                        "name": "Get Current User",
                        "request": {
                            "method": "GET",
                            "url": "{{baseUrl}}/api/auth/me",
                            "header": [{"key": "Authorization", "value": "Bearer {{token}}"}]
                        }
                    },
                    {
                        "name": "Refresh Token",
                        "request": {
                            "method": "POST",
                            "url": "{{baseUrl}}/api/auth/refresh",
                            "header": [
                                {"key": "Content-Type", "value": "application/json"}
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "refresh_token": "{{refresh_token}}"
                                }, indent=2)
                            }
                        }
                    }
                ]
            },
            {
                "name": "Conversations",
                "item": [
                    {
                        "name": "List Conversations",
                        "request": {
                            "method": "GET",
                            "url": {
                                "raw": "{{baseUrl}}/api/conversations?page=1&page_size=20",
                                "query": [
                                    {"key": "page", "value": "1"},
                                    {"key": "page_size", "value": "20"},
                                    {"key": "search", "value": "", "disabled": True},
                                    {"key": "include_archived", "value": "false"}
                                ]
                            },
                            "header": [{"key": "Authorization", "value": "Bearer {{token}}"}]
                        }
                    },
                    {
                        "name": "Create Conversation",
                        "request": {
                            "method": "POST",
                            "url": "{{baseUrl}}/api/conversations",
                            "header": [
                                {"key": "Content-Type", "value": "application/json"},
                                {"key": "Authorization", "value": "Bearer {{token}}"}
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "title": "New Chat",
                                    "model": "llama2",
                                    "model_provider": "ollama"
                                }, indent=2)
                            }
                        }
                    },
                    {
                        "name": "Get Conversation",
                        "request": {
                            "method": "GET",
                            "url": "{{baseUrl}}/api/conversations/{conversation_id}",
                            "header": [{"key": "Authorization", "value": "Bearer {{token}}"}]
                        }
                    },
                    {
                        "name": "Update Conversation",
                        "request": {
                            "method": "PUT",
                            "url": "{{baseUrl}}/api/conversations/{conversation_id}",
                            "header": [
                                {"key": "Content-Type", "value": "application/json"},
                                {"key": "Authorization", "value": "Bearer {{token}}"}
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "title": "Updated Title"
                                }, indent=2)
                            }
                        }
                    },
                    {
                        "name": "Delete Conversation",
                        "request": {
                            "method": "DELETE",
                            "url": "{{baseUrl}}/api/conversations/{conversation_id}",
                            "header": [{"key": "Authorization", "value": "Bearer {{token}}"}]
                        }
                    },
                    {
                        "name": "Export Conversation",
                        "request": {
                            "method": "GET",
                            "url": {
                                "raw": "{{baseUrl}}/api/conversations/{conversation_id}/export?format=markdown",
                                "query": [
                                    {"key": "format", "value": "markdown", "description": "Export format: markdown, json, pdf, html"}
                                ]
                            },
                            "header": [{"key": "Authorization", "value": "Bearer {{token}}"}]
                        }
                    }
                ]
            },
            {
                "name": "Chat",
                "item": [
                    {
                        "name": "Send Chat Message",
                        "request": {
                            "method": "POST",
                            "url": "{{baseUrl}}/api/chat",
                            "header": [
                                {"key": "Content-Type", "value": "application/json"},
                                {"key": "Authorization", "value": "Bearer {{token}}"}
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "messages": [
                                        {"role": "user", "content": "Hello, how are you?"}
                                    ],
                                    "model": "llama2",
                                    "stream": False
                                }, indent=2)
                            }
                        }
                    }
                ]
            },
            {
                "name": "Knowledge Base",
                "item": [
                    {
                        "name": "List Knowledge Bases",
                        "request": {
                            "method": "GET",
                            "url": {
                                "raw": "{{baseUrl}}/api/knowledge?page=1&page_size=20",
                                "query": [
                                    {"key": "page", "value": "1"},
                                    {"key": "page_size", "value": "20"}
                                ]
                            },
                            "header": [{"key": "Authorization", "value": "Bearer {{token}}"}]
                        }
                    },
                    {
                        "name": "Create Knowledge Base",
                        "request": {
                            "method": "POST",
                            "url": "{{baseUrl}}/api/knowledge",
                            "header": [
                                {"key": "Content-Type", "value": "application/json"},
                                {"key": "Authorization", "value": "Bearer {{token}}"}
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "name": "My Knowledge Base",
                                    "description": "Description here",
                                    "tags": ["tag1", "tag2"]
                                }, indent=2)
                            }
                        }
                    },
                    {
                        "name": "Get Knowledge Base",
                        "request": {
                            "method": "GET",
                            "url": "{{baseUrl}}/api/knowledge/{kb_id}",
                            "header": [{"key": "Authorization", "value": "Bearer {{token}}"}]
                        }
                    },
                    {
                        "name": "Search Knowledge Base",
                        "request": {
                            "method": "POST",
                            "url": "{{baseUrl}}/api/knowledge/{kb_id}/search",
                            "header": [
                                {"key": "Content-Type", "value": "application/json"},
                                {"key": "Authorization", "value": "Bearer {{token}}"}
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "query": "search query",
                                    "top_k": 5
                                }, indent=2)
                            }
                        }
                    },
                    {
                        "name": "Export Knowledge Base",
                        "request": {
                            "method": "GET",
                            "url": {
                                "raw": "{{baseUrl}}/api/knowledge/{kb_id}/export?format=json",
                                "query": [
                                    {"key": "format", "value": "json", "description": "Export format: markdown, json, html"}
                                ]
                            },
                            "header": [{"key": "Authorization", "value": "Bearer {{token}}"}]
                        }
                    },
                    {
                        "name": "Import Documents",
                        "request": {
                            "method": "POST",
                            "url": "{{baseUrl}}/api/knowledge/{kb_id}/import",
                            "header": [
                                {"key": "Content-Type", "value": "application/json"},
                                {"key": "Authorization", "value": "Bearer {{token}}"}
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "documents": [
                                        {
                                            "title": "Document Title",
                                            "content": "Document content...",
                                            "source": "https://example.com"
                                        }
                                    ]
                                }, indent=2)
                            }
                        }
                    }
                ]
            },
            {
                "name": "Workflows",
                "item": [
                    {
                        "name": "List Workflows",
                        "request": {
                            "method": "GET",
                            "url": "{{baseUrl}}/api/workflows",
                            "header": [{"key": "Authorization", "value": "Bearer {{token}}"}]
                        }
                    },
                    {
                        "name": "Create Workflow",
                        "request": {
                            "method": "POST",
                            "url": "{{baseUrl}}/api/workflows",
                            "header": [
                                {"key": "Content-Type", "value": "application/json"},
                                {"key": "Authorization", "value": "Bearer {{token}}"}
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "name": "My Workflow",
                                    "description": "Workflow description",
                                    "graph_data": {
                                        "nodes": [],
                                        "edges": []
                                    }
                                }, indent=2)
                            }
                        }
                    },
                    {
                        "name": "Get Workflow",
                        "request": {
                            "method": "GET",
                            "url": "{{baseUrl}}/api/workflows/{workflow_id}",
                            "header": [{"key": "Authorization", "value": "Bearer {{token}}"}]
                        }
                    },
                    {
                        "name": "Publish Workflow",
                        "request": {
                            "method": "POST",
                            "url": "{{baseUrl}}/api/workflows/{workflow_id}/publish",
                            "header": [{"key": "Authorization", "value": "Bearer {{token}}"}]
                        }
                    },
                    {
                        "name": "Execute Workflow",
                        "request": {
                            "method": "POST",
                            "url": "{{baseUrl}}/api/workflows/{workflow_id}/execute",
                            "header": [
                                {"key": "Content-Type", "value": "application/json"},
                                {"key": "Authorization", "value": "Bearer {{token}}"}
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "inputs": {}
                                }, indent=2)
                            }
                        }
                    },
                    {
                        "name": "Share Workflow",
                        "request": {
                            "method": "GET",
                            "url": "{{baseUrl}}/api/workflows/{workflow_id}/share",
                            "header": [{"key": "Authorization", "value": "Bearer {{token}}"}]
                        }
                    },
                    {
                        "name": "Export Workflow",
                        "request": {
                            "method": "GET",
                            "url": "{{baseUrl}}/api/workflows/{workflow_id}/export",
                            "header": [{"key": "Authorization", "value": "Bearer {{token}}"}]
                        }
                    },
                    {
                        "name": "Import Workflow",
                        "request": {
                            "method": "POST",
                            "url": "{{baseUrl}}/api/workflows/import",
                            "header": [
                                {"key": "Content-Type", "value": "application/json"},
                                {"key": "Authorization", "value": "Bearer {{token}}"}
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "name": "Imported Workflow",
                                    "description": "From import",
                                    "graph_data": {
                                        "nodes": [],
                                        "edges": []
                                    }
                                }, indent=2)
                            }
                        }
                    }
                ]
            },
            {
                "name": "Models",
                "item": [
                    {
                        "name": "List Models",
                        "request": {
                            "method": "GET",
                            "url": "{{baseUrl}}/api/models",
                            "header": [{"key": "Authorization", "value": "Bearer {{token}}"}]
                        }
                    },
                    {
                        "name": "Get Model Config",
                        "request": {
                            "method": "GET",
                            "url": "{{baseUrl}}/api/models/{model_id}",
                            "header": [{"key": "Authorization", "value": "Bearer {{token}}"}]
                        }
                    }
                ]
            },
            {
                "name": "Multi-Agent",
                "item": [
                    {
                        "name": "List Multi-Agent Sessions",
                        "request": {
                            "method": "GET",
                            "url": "{{baseUrl}}/api/multi-agent/sessions",
                            "header": [{"key": "Authorization", "value": "Bearer {{token}}"}]
                        }
                    },
                    {
                        "name": "Create Session",
                        "request": {
                            "method": "POST",
                            "url": "{{baseUrl}}/api/multi-agent/sessions",
                            "header": [
                                {"key": "Content-Type", "value": "application/json"},
                                {"key": "Authorization", "value": "Bearer {{token}}"}
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "name": "My Session",
                                    "mode": "sequential",
                                    "agent_ids": []
                                }, indent=2)
                            }
                        }
                    },
                    {
                        "name": "Run Multi-Agent",
                        "request": {
                            "method": "POST",
                            "url": "{{baseUrl}}/api/multi-agent/run",
                            "header": [
                                {"key": "Content-Type", "value": "application/json"},
                                {"key": "Authorization", "value": "Bearer {{token}}"}
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "session_id": "session_id",
                                    "task": "Your task here"
                                }, indent=2)
                            }
                        }
                    }
                ]
            },
            {
                "name": "Fine-tuning",
                "item": [
                    {
                        "name": "List Datasets",
                        "request": {
                            "method": "GET",
                            "url": "{{baseUrl}}/api/finetune/datasets",
                            "header": [{"key": "Authorization", "value": "Bearer {{token}}"}]
                        }
                    },
                    {
                        "name": "Create Dataset",
                        "request": {
                            "method": "POST",
                            "url": "{{baseUrl}}/api/finetune/datasets",
                            "header": [
                                {"key": "Content-Type", "value": "application/json"},
                                {"key": "Authorization", "value": "Bearer {{token}}"}
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "name": "My Dataset",
                                    "description": "Training data"
                                }, indent=2)
                            }
                        }
                    },
                    {
                        "name": "List Jobs",
                        "request": {
                            "method": "GET",
                            "url": "{{baseUrl}}/api/finetune/jobs",
                            "header": [{"key": "Authorization", "value": "Bearer {{token}}"}]
                        }
                    },
                    {
                        "name": "Create Training Job",
                        "request": {
                            "method": "POST",
                            "url": "{{baseUrl}}/api/finetune/jobs",
                            "header": [
                                {"key": "Content-Type", "value": "application/json"},
                                {"key": "Authorization", "value": "Bearer {{token}}"}
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "name": "Training Job",
                                    "base_model": "llama2",
                                    "dataset_id": "dataset_id"
                                }, indent=2)
                            }
                        }
                    }
                ]
            },
            {
                "name": "MCP Servers",
                "item": [
                    {
                        "name": "List MCP Servers",
                        "request": {
                            "method": "GET",
                            "url": "{{baseUrl}}/api/mcp/servers",
                            "header": [{"key": "Authorization", "value": "Bearer {{token}}"}]
                        }
                    },
                    {
                        "name": "Create MCP Server",
                        "request": {
                            "method": "POST",
                            "url": "{{baseUrl}}/api/mcp/servers",
                            "header": [
                                {"key": "Content-Type", "value": "application/json"},
                                {"key": "Authorization", "value": "Bearer {{token}}"}
                            ],
                            "body": {
                                "mode": "raw",
                                "raw": json.dumps({
                                    "name": "My MCP Server",
                                    "command": "npx",
                                    "args": ["-y", "@example/mcp-server"]
                                }, indent=2)
                            }
                        }
                    }
                ]
            },
            {
                "name": "System",
                "item": [
                    {
                        "name": "Health Check",
                        "request": {
                            "method": "GET",
                            "url": "{{baseUrl}}/health"
                        }
                    },
                    {
                        "name": "System Status",
                        "request": {
                            "method": "GET",
                            "url": "{{baseUrl}}/api/status"
                        }
                    }
                ]
            }
        ]
    }
    
    return StreamingResponse(
        iter([json.dumps(collection, indent=2, ensure_ascii=False)]),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=ai-platform-api.postman_collection.json"}
    )
