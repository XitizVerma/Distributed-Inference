from typing import Optional, List, Any

from pydantic import BaseModel


class RegisterRequest(BaseModel):
    hostname: str
    node_name: Optional[str] = None
    ip: Optional[str] = None
    gpu_info: Optional[str] = None
    cpu_info: Optional[str] = None
    total_memory_mb: Optional[int] = None
    available_memory_mb: Optional[int] = None
    worker_type: Optional[str] = None
    models_available: Optional[List[str]] = None


class RegisterResponse(BaseModel):
    worker_id: int
    is_new: bool = True


class HeartbeatRequest(BaseModel):
    worker_id: int
    status: Optional[str] = "online"
    available_memory_mb: Optional[int] = None
    cpu_percent: Optional[float] = None
    memory_percent: Optional[float] = None
    memory_used_mb: Optional[int] = None
    gpu_percent: Optional[float] = None  # null if the node can't report GPU load (e.g. Apple Silicon)
    gpu_memory_used_mb: Optional[int] = None


class PendingTask(BaseModel):
    task_id: int
    prompt: str
    model_name: str
    input_url: Optional[str] = None  # blob (image/pdf/etc.) the worker should download and use as input


class PendingCommand(BaseModel):
    command_id: int
    model_name: str
    backend: str  # selects the node-side adapter that runs this command
    action: str   # install | uninstall | start | stop
    params: Optional[Any] = None  # backend-specific hints from the model catalog


class HeartbeatResponse(BaseModel):
    ack: bool = True
    pending_task: Optional[PendingTask] = None
    pending_command: Optional[PendingCommand] = None


# /infer takes multipart form fields (prompt, model_name, optional input_file) rather
# than a JSON body, since it needs to accept an optional file upload — see routes/tasks.py.


class InferResponse(BaseModel):
    task_id: int
    status: str


class TaskAcceptRequest(BaseModel):
    worker_id: int


class TaskResultRequest(BaseModel):
    worker_id: int
    result: Optional[str] = None
    success: bool = True
    error: Optional[str] = None


class CreateModelRequest(BaseModel):
    name: str
    backend: str = "ollama"
    task_type: Optional[str] = None
    params: Optional[Any] = None


class CreateCommandRequest(BaseModel):
    worker_id: int
    action: str  # install | uninstall | start | stop


class CommandResultRequest(BaseModel):
    worker_id: int
    success: bool = True
    error: Optional[str] = None
    # Node's fresh installed-model list for the command's backend, so Master can
    # refresh workers.models_available after an install/uninstall.
    installed_models: Optional[List[str]] = None
