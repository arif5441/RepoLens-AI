from app.core.database import check_database_connection
from app.llm.ollama_provider import OllamaProvider
from app.schemas.health import ComponentStatus, HealthResponse


def get_health(ollama_provider: OllamaProvider) -> HealthResponse:
    api_status = ComponentStatus(status="ok")

    db_ok, db_error = check_database_connection()
    database_status = ComponentStatus(status="ok" if db_ok else "error", detail=db_error)

    ollama_ok, ollama_error = ollama_provider.is_available()
    ollama_status = ComponentStatus(
        status="ok" if ollama_ok else "unavailable", detail=ollama_error
    )

    overall = "ok" if db_ok and ollama_ok else "degraded"

    return HealthResponse(
        status=overall,
        api=api_status,
        database=database_status,
        ollama=ollama_status,
    )
