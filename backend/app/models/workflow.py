"""Workflow models."""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from enum import Enum
from sqlalchemy import String, DateTime, Text, JSON, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class WorkflowStatus(str, Enum):
    """Workflow status enum."""
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ExecutionStatus(str, Enum):
    """Workflow execution status enum."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class NodeExecutionStatus(str, Enum):
    """Node execution status enum."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class TriggerType(str, Enum):
    """Execution trigger type enum."""
    MANUAL = "manual"
    API = "api"
    SCHEDULE = "schedule"
    EVENT = "event"


class Workflow(Base):
    """Workflow model for visual workflow definitions."""
    
    __tablename__ = "workflows"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(20), default=WorkflowStatus.DRAFT.value)
    
    # Graph definition (nodes and edges)
    graph_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    
    # Metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="workflows")
    executions: Mapped[list["WorkflowExecution"]] = relationship(
        "WorkflowExecution", 
        back_populates="workflow",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Workflow(id={self.id}, name={self.name}, version={self.version})>"


class WorkflowExecution(Base):
    """Workflow execution model for tracking workflow runs."""
    
    __tablename__ = "workflow_executions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workflow_id: Mapped[str] = mapped_column(String(36), ForeignKey("workflows.id"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    
    status: Mapped[str] = mapped_column(String(20), default=ExecutionStatus.PENDING.value)
    trigger_type: Mapped[str] = mapped_column(String(20), default=TriggerType.MANUAL.value)
    
    # Execution inputs/outputs
    inputs: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    outputs: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    workflow: Mapped["Workflow"] = relationship("Workflow", back_populates="executions")
    node_executions: Mapped[list["NodeExecution"]] = relationship(
        "NodeExecution",
        back_populates="execution",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<WorkflowExecution(id={self.id}, workflow_id={self.workflow_id}, status={self.status})>"


class NodeExecution(Base):
    """Node execution model for tracking individual node execution."""
    
    __tablename__ = "node_executions"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    execution_id: Mapped[str] = mapped_column(String(36), ForeignKey("workflow_executions.id"), nullable=False, index=True)
    
    node_id: Mapped[str] = mapped_column(String(100), nullable=False)
    node_type: Mapped[str] = mapped_column(String(50), nullable=False)
    node_name: Mapped[str] = mapped_column(String(200), nullable=True)
    
    status: Mapped[str] = mapped_column(String(20), default=NodeExecutionStatus.PENDING.value)
    
    # Node inputs/outputs
    inputs: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    outputs: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Error tracking
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Computed
    @property
    def duration_ms(self) -> Optional[int]:
        """Calculate execution duration in milliseconds."""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds() * 1000)
        return None
    
    # Relationships
    execution: Mapped["WorkflowExecution"] = relationship(
        "WorkflowExecution", 
        back_populates="node_executions"
    )
    
    def __repr__(self) -> str:
        return f"<NodeExecution(id={self.id}, node_id={self.node_id}, status={self.status})>"
