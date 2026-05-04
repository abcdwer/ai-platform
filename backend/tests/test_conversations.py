"""Tests for conversation endpoints."""
import pytest
from httpx import AsyncClient


class TestConversationCreate:
    """Test conversation creation endpoint."""
    
    @pytest.mark.asyncio
    async def test_create_conversation_success(self, authenticated_client: AsyncClient):
        """Test successful conversation creation."""
        response = await authenticated_client.post(
            "/api/conversations",
            json={
                "title": "Test Chat",
                "model": "llama2",
                "model_provider": "ollama",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Chat"
        assert data["model"] == "llama2"
        assert data["model_provider"] == "ollama"
        assert "id" in data
        assert data["messages"] == []
    
    @pytest.mark.asyncio
    async def test_create_conversation_with_agent(
        self, authenticated_client: AsyncClient, test_workflow
    ):
        """Test conversation creation with agent."""
        response = await authenticated_client.post(
            "/api/conversations",
            json={
                "title": "Agent Chat",
                "model": "llama2",
                "model_provider": "ollama",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Agent Chat"
    
    @pytest.mark.asyncio
    async def test_create_conversation_unauthenticated(self, client: AsyncClient):
        """Test conversation creation without authentication fails."""
        response = await client.post(
            "/api/conversations",
            json={"title": "Test Chat"},
        )
        
        assert response.status_code == 401


class TestConversationList:
    """Test conversation listing endpoint."""
    
    @pytest.mark.asyncio
    async def test_list_conversations(
        self, authenticated_client: AsyncClient, test_conversation
    ):
        """Test listing conversations."""
        response = await authenticated_client.get("/api/conversations")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 1
    
    @pytest.mark.asyncio
    async def test_list_conversations_pagination(
        self, authenticated_client: AsyncClient, test_conversation
    ):
        """Test conversation listing with pagination."""
        response = await authenticated_client.get(
            "/api/conversations",
            params={"page": 1, "page_size": 10},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10
    
    @pytest.mark.asyncio
    async def test_list_conversations_search(
        self, authenticated_client: AsyncClient, test_conversation
    ):
        """Test conversation search."""
        response = await authenticated_client.get(
            "/api/conversations",
            params={"search": "Test"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert "Test" in data["items"][0]["title"]


class TestConversationGet:
    """Test conversation retrieval endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_conversation(
        self, authenticated_client: AsyncClient, test_conversation
    ):
        """Test getting a specific conversation."""
        response = await authenticated_client.get(
            f"/api/conversations/{test_conversation.id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_conversation.id
        assert data["title"] == test_conversation.title
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_conversation(self, authenticated_client: AsyncClient):
        """Test getting nonexistent conversation returns 404."""
        response = await authenticated_client.get("/api/conversations/nonexistent-id")
        
        assert response.status_code == 404


class TestConversationUpdate:
    """Test conversation update endpoint."""
    
    @pytest.mark.asyncio
    async def test_update_conversation_title(
        self, authenticated_client: AsyncClient, test_conversation
    ):
        """Test updating conversation title."""
        response = await authenticated_client.put(
            f"/api/conversations/{test_conversation.id}",
            json={"title": "Updated Title"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
    
    @pytest.mark.asyncio
    async def test_update_conversation_pin(
        self, authenticated_client: AsyncClient, test_conversation
    ):
        """Test pinning a conversation."""
        response = await authenticated_client.put(
            f"/api/conversations/{test_conversation.id}",
            json={"is_pinned": True},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_pinned"] == True


class TestConversationDelete:
    """Test conversation deletion endpoint."""
    
    @pytest.mark.asyncio
    async def test_delete_conversation(
        self, authenticated_client: AsyncClient, test_conversation
    ):
        """Test deleting a conversation."""
        response = await authenticated_client.delete(
            f"/api/conversations/{test_conversation.id}"
        )
        
        assert response.status_code == 200
        
        # Verify deletion
        get_response = await authenticated_client.get(
            f"/api/conversations/{test_conversation.id}"
        )
        assert get_response.status_code == 404


class TestConversationExport:
    """Test conversation export endpoint."""
    
    @pytest.mark.asyncio
    async def test_export_conversation_markdown(
        self, authenticated_client: AsyncClient, test_conversation
    ):
        """Test exporting conversation as Markdown."""
        response = await authenticated_client.get(
            f"/api/conversations/{test_conversation.id}/export",
            params={"format": "markdown"},
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/markdown; charset=utf-8"
    
    @pytest.mark.asyncio
    async def test_export_conversation_json(
        self, authenticated_client: AsyncClient, test_conversation
    ):
        """Test exporting conversation as JSON."""
        response = await authenticated_client.get(
            f"/api/conversations/{test_conversation.id}/export",
            params={"format": "json"},
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
    
    @pytest.mark.asyncio
    async def test_export_conversation_html(
        self, authenticated_client: AsyncClient, test_conversation
    ):
        """Test exporting conversation as HTML."""
        response = await authenticated_client.get(
            f"/api/conversations/{test_conversation.id}/export",
            params={"format": "html"},
        )
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
    
    @pytest.mark.asyncio
    async def test_export_conversation_invalid_format(
        self, authenticated_client: AsyncClient, test_conversation
    ):
        """Test exporting with invalid format fails."""
        response = await authenticated_client.get(
            f"/api/conversations/{test_conversation.id}/export",
            params={"format": "invalid"},
        )
        
        assert response.status_code == 400
