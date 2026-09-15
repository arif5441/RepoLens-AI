from pydantic import BaseModel


class ComponentStatus(BaseModel):
    status: str  # "ok" | "error" | "unavailable"
    detail: str | None = None


class HealthResponse(BaseModel):
    status: str  # overall: "ok" | "degraded"
    api: ComponentStatus
    database: ComponentStatus
    ollama: ComponentStatus
