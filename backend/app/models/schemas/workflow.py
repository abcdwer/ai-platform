"""Workflow Pydantic schemas."""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, Field


# ============ Workflow Schemas ============

class WorkflowNodeData(BaseModel):
    """Schema for a node in the workflow graph."""
    label: str = "Node"
    config: dict = Field(default_factory=dict)


class WorkflowNode(BaseModel):
    """Schema for a workflow node."""
    id: str
    type: str
    position: dict = Field(default_factory=dict)
    data: WorkflowNodeData = Field(default_factory=WorkflowNodeData)
    handles: Optional[dict] = None


class WorkflowEdge(BaseModel):
    """Schema for an edge between nodes."""
    id: str
    source: str
    target: str
    sourceHandle: Optional[str] = None
    targetHandle: Optional[str] = None
    label: Optional[str] = None


class GraphData(BaseModel):
    """Schema for the complete graph data."""
    nodes: list[WorkflowNode] = Field(default_factory=list)
    edges: list[WorkflowEdge] = Field(default_factory=list)


class WorkflowBase(BaseModel):
    """Base schema for workflow."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None


class WorkflowCreate(WorkflowBase):
    """Schema for creating a workflow."""
    graph_data: Optional[dict] = Field(default_factory=dict)


class WorkflowUpdate(BaseModel):
    """Schema for updating a workflow."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    graph_data: Optional[dict] = None
    status: Optional[str] = None


class WorkflowResponse(WorkflowBase):
    """Schema for workflow response."""
    id: str
    user_id: str
    version: int
    status: str
    graph_data: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class WorkflowListResponse(BaseModel):
    """Schema for workflow list response."""
    items: list[WorkflowResponse]
    total: int
    page: int
    page_size: int


class WorkflowPublishResponse(BaseModel):
    """Schema for workflow publish response."""
    id: str
    version: int
    status: str
    message: str


# ============ Execution Schemas ============

class ExecutionBase(BaseModel):
    """Base schema for execution."""
    pass


class ExecutionCreate(ExecutionBase):
    """Schema for creating an execution."""
    inputs: Optional[dict] = Field(default_factory=dict)


class NodeExecutionResponse(BaseModel):
    """Schema for node execution response."""
    id: str
    execution_id: str
    node_id: str
    node_type: str
    node_name: Optional[str] = None
    status: str
    inputs: Optional[dict] = None
    outputs: Optional[dict] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    
    class Config:
        from_attributes = True


class ExecutionResponse(BaseModel):
    """Schema for execution response."""
    id: str
    workflow_id: str
    user_id: str
    status: str
    trigger_type: str
    inputs: Optional[dict] = None
    outputs: Optional[dict] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    node_executions: Optional[list[NodeExecutionResponse]] = None
    
    class Config:
        from_attributes = True


class ExecutionListResponse(BaseModel):
    """Schema for execution list response."""
    items: list[ExecutionResponse]
    total: int
    page: int
    page_size: int


class ExecutionStartResponse(BaseModel):
    """Schema for starting an execution."""
    execution_id: str
    status: str
    message: str


# ============ Node Config Schemas ============

class StartNodeConfig(BaseModel):
    """Configuration for Start node."""
    trigger: str = "manual"  # manual, api, schedule, event
    schedule_cron: Optional[str] = None
    event_type: Optional[str] = None


class EndNodeConfig(BaseModel):
    """Configuration for End node."""
    output_variable: Optional[str] = None
    output_value: Optional[Any] = None


class LLMNodeConfig(BaseModel):
    """Configuration for LLM node."""
    model: str = "gpt-4"
    provider: str = "openai"
    prompt_template: str = "{{input}}"
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: Optional[float] = 0.9


class CodeNodeConfig(BaseModel):
    """Configuration for Code node."""
    language: str = "python"  # python, javascript
    code: str = "# Process input\nresult = input\nprint(result)"
    timeout: int = 30


class ConditionNodeConfig(BaseModel):
    """Configuration for Condition node."""
    condition_type: str = "expression"  # expression, threshold
    expression: str = "{{input}} > 0"
    threshold_value: Optional[float] = None
    threshold_comparison: str = ">"  # >, <, >=, <=, ==, !=


class LoopNodeConfig(BaseModel):
    """Configuration for Loop node."""
    loop_type: str = "count"  # count, while, for_each
    iterations: int = 10
    while_condition: Optional[str] = None
    for_each_variable: Optional[str] = None
    max_iterations: int = 100


class DelayNodeConfig(BaseModel):
    """Configuration for Delay node."""
    delay_type: str = "seconds"  # seconds, minutes, hours
    delay_value: int = 1


class HTTPRequestNodeConfig(BaseModel):
    """Configuration for HTTP Request node."""
    method: str = "GET"  # GET, POST, PUT, DELETE, PATCH
    url: str = ""
    headers: Optional[dict] = None
    body: Optional[Any] = None
    timeout: int = 30


class TransformNodeConfig(BaseModel):
    """Configuration for Transform node."""
    transform_type: str = "json_path"  # json_path, template, join, split
    json_path: Optional[str] = None
    template: Optional[str] = None
    delimiter: Optional[str] = None
    join_key: Optional[str] = None


class KnowledgeBaseQueryConfig(BaseModel):
    """Configuration for Knowledge Base Query node."""
    knowledge_base_id: Optional[str] = None
    query_template: str = "{{input}}"
    top_k: int = 5
    similarity_threshold: float = 0.7


class AgentCallConfig(BaseModel):
    """Configuration for Agent Call node."""
    agent_id: Optional[str] = None
    input_template: str = "{{input}}"


class TextSplitterConfig(BaseModel):
    """Configuration for Text Splitter node."""
    split_type: str = "character"  # character, token, sentence, paragraph
    chunk_size: int = 1000
    chunk_overlap: int = 200
    separator: Optional[str] = None


class EmbeddingConfig(BaseModel):
    """Configuration for Embedding node."""
    model: str = "text-embedding-ada-002"
    provider: str = "openai"
    batch_size: int = 100


class WebSearchConfig(BaseModel):
    """Configuration for Web Search node."""
    search_engine: str = "google"
    query_template: str = "{{input}}"
    num_results: int = 10


class FileReadConfig(BaseModel):
    """Configuration for File Read node."""
    file_path: str = ""
    encoding: str = "utf-8"


class FileWriteConfig(BaseModel):
    """Configuration for File Write node."""
    file_path: str = ""
    content_template: str = "{{input}}"
    encoding: str = "utf-8"
    append: bool = False


class SendEmailConfig(BaseModel):
    """Configuration for Send Email node."""
    to: str = ""
    subject: str = "Workflow Notification"
    body_template: str = "{{input}}"
    from_name: Optional[str] = None


class NotificationConfig(BaseModel):
    """Configuration for Notification node."""
    notification_type: str = "log"  # log, webhook, sms
    message_template: str = "{{input}}"
    webhook_url: Optional[str] = None


class MergeNodeConfig(BaseModel):
    """Configuration for Merge node."""
    merge_type: str = "first"  # first, last, all, custom
    output_key: Optional[str] = None
