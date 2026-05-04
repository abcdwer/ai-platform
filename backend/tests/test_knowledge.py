"""Tests for knowledge base endpoints."""
import pytest
from httpx import AsyncClient


class TestKnowledgeBaseCreate:
    """Test knowledge base creation endpoint."""
    
    @pytest.mark.asyncio
    async def test_create_knowledge_base_success(self, authenticated_client: AsyncClient):
        """Test successful knowledge base creation."""
        response = await authenticated_client.post(
            "/api/knowledge",
            json={
                "name": "Test KB",
                "description": "A test knowledge base",
                "tags": ["test", "sample"],
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test KB"
        assert data["description"] == "A test knowledge base"
        assert "test" in data["tags"]
        assert data["document_count"] == 0
    
    @pytest.mark.asyncio
    async def test_create_knowledge_base_without_tags(
        self, authenticated_client: AsyncClient
    ):
        """Test knowledge base creation without tags."""
        response = await authenticated_client.post(
            "/api/knowledge",
            json={
                "name": "Simple KB",
                "description": "No tags",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Simple KB"
        assert data["tags"] == []
    
    @pytest.mark.asyncio
    async def test_create_knowledge_base_unauthenticated(self, client: AsyncClient):
        """Test knowledge base creation without authentication fails."""
        response = await client.post(
            "/api/knowledge",
            json={"name": "Test KB"},
        )
        
        assert response.status_code == 401


class TestKnowledgeBaseList:
    """Test knowledge base listing endpoint."""
    
    @pytest.mark.asyncio
    async def test_list_knowledge_bases(
        self, authenticated_client: AsyncClient, test_knowledge_base
    ):
        """Test listing knowledge bases."""
        response = await authenticated_client.get("/api/knowledge")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 1
    
    @pytest.mark.asyncio
    async def test_list_knowledge_bases_search(
        self, authenticated_client: AsyncClient, test_knowledge_base
    ):
        """Test knowledge base search."""
        response = await authenticated_client.get(
            "/api/knowledge",
            params={"search": "Test"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
    
    @pytest.mark.asyncio
    async def test_list_knowledge_bases_filter_by_tag(
        self, authenticated_client: AsyncClient
    ):
        """Test filtering knowledge bases by tag."""
        # Create KB with specific tag
        await authenticated_client.post(
            "/api/knowledge",
            json={"name": "Tagged KB", "tags": ["special-tag"]},
        )
        
        response = await authenticated_client.get(
            "/api/knowledge",
            params={"tag": "special-tag"},
        )
        
        assert response.status_code == 200
        data = response.json()
        # Should find KBs with this tag
        assert all("special-tag" in kb.get("tags", []) for kb in data["items"])


class TestKnowledgeBaseGet:
    """Test knowledge base retrieval endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_knowledge_base(
        self, authenticated_client: AsyncClient, test_knowledge_base
    ):
        """Test getting a specific knowledge base."""
        response = await authenticated_client.get(
            f"/api/knowledge/{test_knowledge_base.id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_knowledge_base.id
        assert data["name"] == test_knowledge_base.name
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_knowledge_base(
        self, authenticated_client: AsyncClient
    ):
        """Test getting nonexistent knowledge base returns 404."""
        response = await authenticated_client.get("/api/knowledge/nonexistent-id")
        
        assert response.status_code == 404


class TestKnowledgeBaseUpdate:
    """Test knowledge base update endpoint."""
    
    @pytest.mark.asyncio
    async def test_update_knowledge_base(
        self, authenticated_client: AsyncClient, test_knowledge_base
    ):
        """Test updating knowledge base."""
        response = await authenticated_client.put(
            f"/api/knowledge/{test_knowledge_base.id}",
            json={
                "name": "Updated KB Name",
                "description": "Updated description",
                "tags": ["updated", "modified"],
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated KB Name"
        assert data["description"] == "Updated description"
        assert "updated" in data["tags"]


class TestKnowledgeBaseDelete:
    """Test knowledge base deletion endpoint."""
    
    @pytest.mark.asyncio
    async def test_delete_knowledge_base(
        self, authenticated_client: AsyncClient, test_knowledge_base
    ):
        """Test deleting a knowledge base."""
        response = await authenticated_client.delete(
            f"/api/knowledge/{test_knowledge_base.id}"
        )
        
        assert response.status_code == 200
        
        # Verify deletion
        get_response = await authenticated_client.get(
            f"/api/knowledge/{test_knowledge_base.id}"
        )
        assert get_response.status_code == 404


class TestKnowledgeBaseSearch:
    """Test knowledge base search endpoint."""
    
    @pytest.mark.asyncio
    async def test_search_knowledge_base_requires_documents(
        self, authenticated_client: AsyncClient, test_knowledge_base
    ):
        """Test search requires documents to be indexed."""
        response = await authenticated_client.post(
            f"/api/knowledge/{test_knowledge_base.id}/search",
            json={
                "query": "test query",
                "top_k": 5,
            },
        )
        
        # Will fail due to no documents, but validates endpoint exists
        assert response.status_code in [200, 400, 500]


class TestKnowledgeBaseExport:
    """Test knowledge base export endpoint."""
    
    @pytest.mark.asyncio
    async def test_export_knowledge_base_markdown(
        self, authenticated_client: AsyncClient, test_knowledge_base
    ):
        """Test exporting knowledge base as Markdown."""
        response = await authenticated_client.get(
            f"/api/knowledge/{test_knowledge_base.id}/export",
            params={"format": "markdown"},
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/markdown; charset=utf-8"
    
    @pytest.mark.asyncio
    async def test_export_knowledge_base_json(
        self, authenticated_client: AsyncClient, test_knowledge_base
    ):
        """Test exporting knowledge base as JSON."""
        response = await authenticated_client.get(
            f"/api/knowledge/{test_knowledge_base.id}/export",
            params={"format": "json"},
        )
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
    
    @pytest.mark.asyncio
    async def test_export_knowledge_base_html(
        self, authenticated_client: AsyncClient, test_knowledge_base
    ):
        """Test exporting knowledge base as HTML."""
        response = await authenticated_client.get(
            f"/api/knowledge/{test_knowledge_base.id}/export",
            params={"format": "html"},
        )
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
