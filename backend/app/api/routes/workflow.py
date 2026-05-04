"""Workflow API routes with JWT authentication and comprehensive API documentation."""
import uuid
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.workflow import (
    Workflow, WorkflowExecution, WorkflowStatus, 
    ExecutionStatus, NodeExecution, NodeExecutionStatus
)
from app.models.schemas.workflow import (
    WorkflowCreate, WorkflowUpdate, WorkflowResponse, WorkflowListResponse,
    WorkflowPublishResponse, ExecutionCreate, ExecutionResponse, 
    ExecutionListResponse, ExecutionStartResponse, NodeExecutionResponse
)
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(
    prefix="/api/workflows", 
    tags=["Workflows"],
    summary="Workflow Management",
    description="""
    Visual workflow automation with drag-and-drop node editor.
    
    Features:
    - Create workflows with customizable nodes (Start, LLM, Condition, Code, etc.)
    - Execute workflows with real-time status tracking
    - Share workflows with others via exportable configuration
    - Import workflows from JSON configuration files
    
    Workflows support:
    - Sequential execution
    - Conditional branching
    - Loops and iterations
    - Error handling
    - Variable passing between nodes
    """
)


# ============ Workflow CRUD ============

@router.post(
    "",
    response_model=WorkflowResponse,
    summary="Create Workflow",
    description="Create a new empty workflow",
    responses={
        201: {"description": "Workflow created successfully"},
        401: {"description": "Authentication required"},
    }
)
async def create_workflow(
    workflow_data: WorkflowCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new workflow with optional initial configuration.
    
    - **name**: Workflow name (required)
    - **description**: Optional workflow description
    - **graph_data**: Initial graph data with nodes and edges (optional)
    
    Returns the created workflow in draft status.
    """
    workflow = Workflow(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        name=workflow_data.name,
        description=workflow_data.description,
        graph_data=workflow_data.graph_data or {"nodes": [], "edges": []},
        status=WorkflowStatus.DRAFT.value
    )
    db.add(workflow)
    await db.commit()
    await db.refresh(workflow)
    return workflow


@router.get(
    "",
    response_model=WorkflowListResponse,
    summary="List Workflows",
    description="Get paginated list of workflows with optional filtering",
    responses={
        200: {"description": "List of workflows"},
        401: {"description": "Authentication required"},
    }
)
async def list_workflows(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by workflow name"),
    status: Optional[str] = Query(None, description="Filter by status (draft/published)"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all workflows for the current user with pagination.
    
    - **page**: Page number for pagination
    - **page_size**: Number of items per page
    - **search**: Filter by workflow name
    - **status**: Filter by workflow status (draft/published)
    
    Returns paginated list sorted by update time.
    """
    query = select(Workflow).where(Workflow.user_id == current_user.id)
    
    if search:
        query = query.where(Workflow.name.ilike(f"%{search}%"))
    if status:
        query = query.where(Workflow.status == status)
    
    query = query.order_by(Workflow.updated_at.desc())
    
    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Get paginated results
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    workflows = result.scalars().all()
    
    return WorkflowListResponse(
        items=[WorkflowResponse.model_validate(w) for w in workflows],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get(
    "/{workflow_id}",
    response_model=WorkflowResponse,
    summary="Get Workflow",
    description="Retrieve a workflow by ID with its graph configuration",
    responses={
        200: {"description": "Workflow details"},
        401: {"description": "Authentication required"},
        404: {"description": "Workflow not found"},
    }
)
async def get_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a workflow by ID including its graph configuration.
    
    - **workflow_id**: Unique identifier of the workflow
    
    Returns the workflow with full graph data (nodes and edges).
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
    
    return workflow


@router.put(
    "/{workflow_id}",
    response_model=WorkflowResponse,
    summary="Update Workflow",
    description="Update workflow metadata and graph configuration",
    responses={
        200: {"description": "Workflow updated"},
        401: {"description": "Authentication required"},
        404: {"description": "Workflow not found"},
    }
)
async def update_workflow(
    workflow_id: str,
    workflow_data: WorkflowUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update workflow properties and graph configuration.
    
    - **workflow_id**: Unique identifier of the workflow
    - **name**: New workflow name (optional)
    - **description**: New description (optional)
    - **graph_data**: New graph data with nodes and edges (optional)
    
    Only provided fields will be updated.
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
    
    update_data = workflow_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(workflow, field, value)
    
    await db.commit()
    await db.refresh(workflow)
    return workflow


@router.delete(
    "/{workflow_id}",
    summary="Delete Workflow",
    description="Permanently delete a workflow and all its executions",
    responses={
        200: {"description": "Workflow deleted"},
        401: {"description": "Authentication required"},
        404: {"description": "Workflow not found"},
    }
)
async def delete_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a workflow permanently.
    
    - **workflow_id**: Unique identifier of the workflow
    
    This will also delete all execution history for this workflow.
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
    
    await db.delete(workflow)
    await db.commit()
    
    return {"message": "Workflow deleted successfully"}


@router.post(
    "/{workflow_id}/publish",
    response_model=WorkflowPublishResponse,
    summary="Publish Workflow",
    description="Publish a workflow to make it executable",
    responses={
        200: {"description": "Workflow published"},
        400: {"description": "Invalid workflow (missing required nodes)"},
        401: {"description": "Authentication required"},
        404: {"description": "Workflow not found"},
    }
)
async def publish_workflow(
    workflow_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Publish a workflow for execution.
    
    - **workflow_id**: Unique identifier of the workflow
    
    Requirements:
    - Workflow must have at least one Start node
    - Workflow must have at least one End node
    - Graph cannot be empty
    
    Increments the workflow version on successful publish.
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
    
    # Validate workflow before publishing
    if not workflow.graph_data or not workflow.graph_data.get("nodes"):
        raise HTTPException(status_code=400, detail="Cannot publish empty workflow")
    
    # Check for start and end nodes
    node_types = [n.get("type") for n in workflow.graph_data.get("nodes", [])]
    if "start" not in node_types:
        raise HTTPException(status_code=400, detail="Workflow must have a Start node")
    if "end" not in node_types:
        raise HTTPException(status_code=400, detail="Workflow must have an End node")
    
    workflow.status = WorkflowStatus.PUBLISHED.value
    workflow.version += 1
    await db.commit()
    
    return WorkflowPublishResponse(
        id=workflow.id,
        version=workflow.version,
        status=workflow.status,
        message=f"Workflow published as version {workflow.version}"
    )


# ============ Workflow Execution ============

@router.get(
    "/{workflow_id}/executions",
    response_model=ExecutionListResponse,
    summary="List Executions",
    description="Get execution history for a workflow",
    responses={
        200: {"description": "List of executions"},
        401: {"description": "Authentication required"},
        404: {"description": "Workflow not found"},
    }
)
async def list_executions(
    workflow_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get paginated list of workflow execution history."""
    # Verify workflow ownership
    wf_result = await db.execute(
        select(Workflow).where(
            Workflow.id == workflow_id,
            Workflow.user_id == current_user.id
        )
    )
    if not wf_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    query = (
        select(WorkflowExecution)
        .where(WorkflowExecution.workflow_id == workflow_id)
        .order_by(WorkflowExecution.started_at.desc())
    )
    
    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar() or 0
    
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    executions = result.scalars().all()
    
    return ExecutionListResponse(
        items=[ExecutionResponse.model_validate(e) for e in executions],
        total=total,
        page=page,
        page_size=page_size
    )


@router.post(
    "/{workflow_id}/execute",
    response_model=ExecutionStartResponse,
    summary="Execute Workflow",
    description="Start a new workflow execution",
    responses={
        200: {"description": "Execution started"},
        400: {"description": "Workflow not published or invalid"},
        401: {"description": "Authentication required"},
        404: {"description": "Workflow not found"},
    }
)
async def execute_workflow(
    workflow_id: str,
    execution_data: Optional[ExecutionCreate] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a new workflow execution with optional input parameters."""
    result = await db.execute(
        select(Workflow).where(
            Workflow.id == workflow_id,
            Workflow.user_id == current_user.id
        )
    )
    workflow = result.scalar_one_or_none()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    if workflow.status != WorkflowStatus.PUBLISHED.value:
        raise HTTPException(status_code=400, detail="Workflow must be published before execution")
    
    execution = WorkflowExecution(
        id=str(uuid.uuid4()),
        workflow_id=workflow_id,
        inputs=execution_data.inputs if execution_data else {},
        status=ExecutionStatus.PENDING.value
    )
    db.add(execution)
    await db.commit()
    await db.refresh(execution)
    
    return ExecutionStartResponse(
        execution_id=execution.id,
        status=execution.status,
        message="Workflow execution started"
    )


@router.get(
    "/{workflow_id}/executions/{execution_id}",
    response_model=ExecutionResponse,
    summary="Get Execution",
    description="Get execution details with node execution status",
    responses={
        200: {"description": "Execution details"},
        401: {"description": "Authentication required"},
        404: {"description": "Execution not found"},
    }
)
async def get_execution(
    workflow_id: str,
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed execution status including all node executions."""
    # Verify ownership
    wf_result = await db.execute(
        select(Workflow).where(
            Workflow.id == workflow_id,
            Workflow.user_id == current_user.id
        )
    )
    if not wf_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    result = await db.execute(
        select(WorkflowExecution).where(
            WorkflowExecution.id == execution_id,
            WorkflowExecution.workflow_id == workflow_id
        )
    )
    execution = result.scalar_one_or_none()
    
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    return execution


@router.get(
    "/{workflow_id}/executions/{execution_id}/nodes",
    summary="Get Node Executions",
    description="Get all node execution details for a workflow execution",
    responses={
        200: {"description": "Node execution details"},
        401: {"description": "Authentication required"},
        404: {"description": "Execution not found"},
    }
)
async def get_node_executions(
    workflow_id: str,
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed execution logs for each node in the workflow."""
    # Verify ownership
    wf_result = await db.execute(
        select(Workflow).where(
            Workflow.id == workflow_id,
            Workflow.user_id == current_user.id
        )
    )
    if not wf_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    result = await db.execute(
        select(NodeExecution)
        .where(NodeExecution.execution_id == execution_id)
        .order_by(NodeExecution.started_at.asc())
    )
    node_executions = result.scalars().all()
    
    return {"node_executions": node_executions}


@router.post(
    "/{workflow_id}/executions/{execution_id}/cancel",
    response_model=ExecutionResponse,
    summary="Cancel Execution",
    description="Cancel a running workflow execution",
    responses={
        200: {"description": "Execution cancelled"},
        400: {"description": "Execution not running"},
        401: {"description": "Authentication required"},
        404: {"description": "Execution not found"},
    }
)
async def cancel_execution(
    workflow_id: str,
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel a running workflow execution."""
    # Verify ownership
    wf_result = await db.execute(
        select(Workflow).where(
            Workflow.id == workflow_id,
            Workflow.user_id == current_user.id
        )
    )
    if not wf_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    result = await db.execute(
        select(WorkflowExecution).where(
            WorkflowExecution.id == execution_id,
            WorkflowExecution.workflow_id == workflow_id
        )
    )
    execution = result.scalar_one_or_none()
    
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    
    if execution.status not in [ExecutionStatus.PENDING.value, ExecutionStatus.RUNNING.value]:
        raise HTTPException(status_code=400, detail="Cannot cancel finished execution")
    
    execution.status = ExecutionStatus.CANCELLED.value
    execution.completed_at = datetime.utcnow()
    await db.commit()
    await db.refresh(execution)
    
    return execution
