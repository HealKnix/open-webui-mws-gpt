from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


PolicyMode = Literal['fast', 'balanced', 'quality']
ArtifactType = Literal['text', 'image', 'audio', 'structured']
OperationKind = Literal['generate_text', 'analyze_image', 'transcribe_audio', 'retrieve_context', 'critique_text']


class Artifact(BaseModel):
    model_config = ConfigDict(extra='allow')

    id: str
    type: ArtifactType
    source: str = 'system'
    text: Optional[str] = None
    mime_type: Optional[str] = None
    file_id: Optional[str] = None
    url: Optional[str] = None
    path: Optional[str] = None
    data: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Operation(BaseModel):
    model_config = ConfigDict(extra='allow')

    id: str
    kind: OperationKind
    inputs: list[str] = Field(default_factory=list)
    output_id: str
    required_capabilities: list[str] = Field(default_factory=list)
    prompt: Optional[str] = None
    description: Optional[str] = None
    max_rounds: int = 1
    stop_on_no_change: int = 0
    options: dict[str, Any] = Field(default_factory=dict)


class ModelRoleAssignment(BaseModel):
    role: str
    primary: Optional[str] = None
    fallbacks: list[str] = Field(default_factory=list)
    selected: Optional[str] = None


class ExecutionTraceEvent(BaseModel):
    phase: str
    operation_id: Optional[str] = None
    status: str
    model_id: Optional[str] = None
    detail: Optional[str] = None
    step: Optional[int] = None
    total_steps: Optional[int] = None
    attempt: Optional[int] = None
    elapsed_ms: Optional[int] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExecutionTrace(BaseModel):
    events: list[ExecutionTraceEvent] = Field(default_factory=list)


class FinalOutput(BaseModel):
    text: Optional[str] = None
    artifacts: list[Artifact] = Field(default_factory=list)


class OrchestrationPlan(BaseModel):
    request_id: str
    intent_mode: str
    user_goal: str
    policy_mode: PolicyMode = 'balanced'
    input_artifacts: list[Artifact] = Field(default_factory=list)
    operations: list[Operation] = Field(default_factory=list)
    output_artifact_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class OrchestrationRequest(BaseModel):
    model: str = 'mts-router'
    messages: list[dict] = Field(default_factory=list)
    files: list[dict] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    policy_mode: PolicyMode = 'balanced'
    dry_run: bool = False


class ExecutionResult(BaseModel):
    plan: OrchestrationPlan
    output_artifacts: list[Artifact] = Field(default_factory=list)
    final_output: FinalOutput = Field(default_factory=FinalOutput)
    trace: ExecutionTrace = Field(default_factory=ExecutionTrace)
    selected_models: dict[str, ModelRoleAssignment] = Field(default_factory=dict)
    metrics: dict[str, Any] = Field(default_factory=dict)
