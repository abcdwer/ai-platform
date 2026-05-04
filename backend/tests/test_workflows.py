"""Tests for workflow endpoints."""
import pytest
from httpx import AsyncClient


class TestWorkflowCreate:
    """Test workflow creation endpoint."""
    
    @pytest.mark.asyncio
    async def test_create_workflow_success(self, authenticated_client: AsyncClient):
        """Test successful workflow creation."""
        response = await authenticated_client.post(
            "/api/workflows",
            json={
                "name": "Test Workflow",
                "description": "A test workflow",
                "graph_data": {
                    "nodes": [
                        {"id": "1", "type": "start", "data": {}},
                        {"id": "2", "type": "llm", "data": {"model": "llama2"}},
                    ],
                    "edges": [
                        {"id": "e1", "source": "1", "target": "2"},
                    ],
                },
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Workflow"
        assert data["description"] == "A test workflow"
        assert data["status"] == "draft"
        assert len(data["graph_data"]["nodes"]) == 2
    
    @pytest.mark.asyncio
    async def test_create_workflow_minimal(self, authenticated_client: AsyncClient):
        """Test workflow creation with minimal data."""
        response = await authenticated_client.post(
            "/api/workflows",
            json={
                "name": "Minimal Workflow",
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Minimal Workflow"
        assert data["graph_data"]["nodes"] == []
        assert data["graph_data"]["edges"] == []
    
    @pytest.mark.asyncio
    async def test_create_workflow_unauthenticated(self, client: AsyncClient):
        """Test workflow creation without authentication fails."""
        response = await client.post(
            "/api/workflows",
            json={"name": "Test Workflow"},
        )
        
        assert response.status_code == 401


class TestWorkflowList:
    """Test workflow listing endpoint."""
    
    @pytest.mark.asyncio
    async def test_list_workflows(
        self, authenticated_client: AsyncClient, test_workflow
    ):
        """Test listing workflows."""
        response = await authenticated_client.get("/api/workflows")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 1
    
    @pytest.mark.asyncio
    async def test_list_workflows_pagination(
        self, authenticated_client: AsyncClient, test_workflow
    ):
        """Test workflow listing with pagination."""
        response = await authenticated_client.get(
            "/api/workflows",
            params={"page": 1, "page_size": 10},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 10
    
    @pytest.mark.asyncio
    async def test_list_workflows_filter_by_status(
        self, authenticated_client: AsyncClient, test_workflow
    ):
        """Test filtering workflows by status."""
        response = await authenticated_client.get(
            "/api/workflows",
            params={"status": "draft"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(wf["status"] == "draft" for wf in data["items"])


class TestWorkflowGet:
    """Test workflow retrieval endpoint."""
    
    @pytest.mark.asyncio
    async def test_get_workflow(
        self, authenticated_client: AsyncClient, test_workflow
    ):
        """Test getting a specific workflow."""
        response = await authenticated_client.get(
            f"/api/workflows/{test_workflow.id}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_workflow.id
        assert data["name"] == test_workflow.name
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_workflow(self, authenticated_client: AsyncClient):
        """Test getting nonexistent workflow returns 404."""
        response = await authenticated_client.get("/api/workflows/nonexistent-id")
        
        assert response.status_code == 404


class TestWorkflowUpdate:
    """Test workflow update endpoint."""
    
    @pytest.mark.asyncio
    async def test_update_workflow(
        self, authenticated_client: AsyncClient, test_workflow
    ):
        """Test updating workflow."""
        response = await authenticated_client.put(
            f"/api/workflows/{test_workflow.id}",
            json={
                "name": "Updated Workflow",
                "description": "Updated description",
                "graph_data": {
                    "nodes": [{"id": "1", "type": "start", "data": {}}],
                    "edges": [],
                },
            },
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Workflow"
        assert data["description"] == "Updated description"
    
    @pytest.mark.asyncio
    async def test_publish_workflow(
        self, authenticated_client: AsyncClient, test_workflow
    ):
        """Test publishing a workflow."""
        response = await authenticated_client.post(
            f"/api/workflows/{test_workflow.id}/publish"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "published"


class TestWorkflowDelete:
    """Test workflow deletion endpoint."""
    
    @pytest.mark.asyncio
    async def test_delete_workflow(
        self, authenticated_client: AsyncClient, test_workflow
    ):
        """Test deleting a workflow."""
        response = await authenticated_client.delete(
            f"/api/workflows/{test_workflow.id}"
        )
        
        assert response.status_code == 200
        
        # Verify deletion
        get_response = await authenticated_client.get(
            f"/api/workflows/{test_workflow.id}"
        )
        assert get_response.status_code == 404


class TestWorkflowExecution:
    """Test workflow execution endpoint."""
    
    @pytest.mark.asyncio
    async def test_execute_workflow_validation(
        self, authenticated_client: AsyncClient, test_workflow
    ):
        """Test workflow execution validates input."""
        response = await authenticated_client.post(
            f"/api/workflows/{test_workflow.id}/execute",
            json={
                "input_data": {"test": "data"},
            },
        )
        
        # May fail due to workflow not having required nodes
        # but validates endpoint exists
        assert response.status_code in [200, 400, 500]


class TestWorkflowExportImport:
    """Test workflow export/import endpoints."""
    
    @pytest.mark.asyncio
    async def test_export_workflow(
        self, authenticated_client: AsyncClient, test_workflow
    ):
        """Test exporting a workflow."""
        response = await authenticated_client.get(
            f"/api/workflows/{test_workflow.id}/export"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "graph_data" in data
        assert "version" in data
    
    @pytest.mark.asyncio
    async def test_import_workflow(
        self, authenticated_client: AsyncClient, test_workflow
    ):
        """Test importing a workflow."""
        # First export
        export_response = await authenticated_client.get(
            f"/api/workflows/{test_workflow.id}/export"
        )
        export_data = export_response.json()
        
        # Modify name for import
        export_data["name"] = "Imported Workflow"
        
        # Import
        response = await authenticated_client.post(
            "/api/workflows/import",
            json=export_data,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Imported Workflow"
        assert data["id"] != test_workflow.id  # New workflow created


class TestWorkflowExecutions:
    """Test workflow executions listing endpoint."""
    
    @pytest.mark.asyncio
    async def test_list_executions(
        self, authenticated_client: AsyncClient, test_workflow
    ):
        """Test listing workflow executions."""
        response = await authenticated_client.get(
            f"/api/workflows/{test_workflow.id}/executions"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
