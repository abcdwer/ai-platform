"""Workflow service for business logic."""
from datetime import datetime
from typing import Optional, Any
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.workflow import (
    Workflow, WorkflowExecution, WorkflowStatus,
    ExecutionStatus, NodeExecution, NodeExecutionStatus
)


class WorkflowService:
    """Service for workflow operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get workflow by ID."""
        result = await self.db.execute(
            select(Workflow).where(Workflow.id == workflow_id)
        )
        return result.scalar_one_or_none()
    
    async def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Get execution by ID."""
        result = await self.db.execute(
            select(WorkflowExecution)
            .options(selectinload(WorkflowExecution.node_executions))
            .where(WorkflowExecution.id == execution_id)
        )
        return result.scalar_one_or_none()
    
    async def update_execution_status(
        self,
        execution_id: str,
        status: str,
        outputs: Optional[dict] = None,
        error_message: Optional[str] = None
    ):
        """Update execution status."""
        execution = await self.get_execution(execution_id)
        if execution:
            execution.status = status
            if outputs is not None:
                execution.outputs = outputs
            if error_message:
                execution.error_message = error_message
            if status in [ExecutionStatus.COMPLETED.value, ExecutionStatus.FAILED.value, ExecutionStatus.CANCELLED.value]:
                execution.completed_at = datetime.utcnow()
            await self.db.commit()
    
    async def create_node_execution(
        self,
        execution_id: str,
        node_id: str,
        node_type: str,
        node_name: Optional[str] = None
    ) -> NodeExecution:
        """Create a node execution record."""
        node_exec = NodeExecution(
            id=str(uuid.uuid4()),
            execution_id=execution_id,
            node_id=node_id,
            node_type=node_type,
            node_name=node_name,
            status=NodeExecutionStatus.PENDING.value
        )
        self.db.add(node_exec)
        await self.db.commit()
        return node_exec
    
    async def update_node_execution(
        self,
        node_exec_id: str,
        status: str,
        inputs: Optional[dict] = None,
        outputs: Optional[dict] = None,
        error_message: Optional[str] = None
    ):
        """Update node execution."""
        result = await self.db.execute(
            select(NodeExecution).where(NodeExecution.id == node_exec_id)
        )
        node_exec = result.scalar_one_or_none()
        if node_exec:
            node_exec.status = status
            if inputs is not None:
                node_exec.inputs = inputs
            if outputs is not None:
                node_exec.outputs = outputs
            if error_message:
                node_exec.error_message = error_message
            if status == NodeExecutionStatus.RUNNING.value:
                node_exec.started_at = datetime.utcnow()
            elif status in [NodeExecutionStatus.COMPLETED.value, NodeExecutionStatus.FAILED.value, NodeExecutionStatus.SKIPPED.value]:
                node_exec.completed_at = datetime.utcnow()
            await self.db.commit()


async def execute_workflow_async(execution_id: str, db: AsyncSession):
    """Execute workflow in background."""
    from app.workflow.engine import WorkflowEngine
    
    service = WorkflowService(db)
    execution = await service.get_execution(execution_id)
    
    if not execution:
        return
    
    workflow = await service.get_workflow(execution.workflow_id)
    if not workflow:
        await service.update_execution_status(
            execution_id,
            ExecutionStatus.FAILED.value,
            error_message="Workflow not found"
        )
        return
    
    engine = WorkflowEngine(service)
    
    try:
        execution.started_at = datetime.utcnow()
        await db.commit()
        
        result = await engine.execute(workflow.graph_data, execution.inputs)
        
        await service.update_execution_status(
            execution_id,
            ExecutionStatus.COMPLETED.value,
            outputs=result
        )
    except Exception as e:
        await service.update_execution_status(
            execution_id,
            ExecutionStatus.FAILED.value,
            error_message=str(e)
        )
