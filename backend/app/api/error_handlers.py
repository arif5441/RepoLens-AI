import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.embeddings.exceptions import (
    EmbeddingInputError,
    EmbeddingModelUnavailableError,
    EmbeddingProviderError,
    EmbeddingRequestError,
)
from app.ingestion.exceptions import (
    GitHubRateLimitedError,
    GitHubRequestError,
    IngestionError,
    InvalidRepositoryUrlError,
    RepositoryNotFoundError,
)
from app.llm.exceptions import (
    LLMModelNotFoundError,
    LLMProviderError,
    LLMRequestError,
    LLMTimeoutError,
    LLMUnavailableError,
)
from app.repositories.exceptions import RepositoryError
from app.schemas.error import ErrorDetail, ErrorResponse
from app.services.exceptions import FileNotIndexedError, RepositoryNotIndexedError

logger = logging.getLogger(__name__)

_LLM_STATUS_BY_ERROR: dict[type[LLMProviderError], int] = {
    LLMUnavailableError: 503,
    LLMModelNotFoundError: 503,
    LLMTimeoutError: 504,
    LLMRequestError: 502,
}

_EMBEDDING_STATUS_BY_ERROR: dict[type[EmbeddingProviderError], int] = {
    EmbeddingModelUnavailableError: 503,
    EmbeddingInputError: 400,
    EmbeddingRequestError: 502,
}

_INGESTION_STATUS_BY_ERROR: dict[type[IngestionError], int] = {
    InvalidRepositoryUrlError: 400,
    RepositoryNotFoundError: 404,
    GitHubRateLimitedError: 429,
    GitHubRequestError: 502,
}


def _status_for(exc: Exception, status_by_type: dict[type, int], default: int) -> int:
    for error_type, status_code in status_by_type.items():
        if isinstance(exc, error_type):
            return status_code
    return default


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(LLMProviderError)
    async def handle_llm_provider_error(request: Request, exc: LLMProviderError) -> JSONResponse:
        status_code = _status_for(exc, _LLM_STATUS_BY_ERROR, default=502)
        logger.warning("LLM provider error on %s: %s", request.url.path, exc)
        body = ErrorResponse(error=ErrorDetail(code=type(exc).__name__, message=str(exc)))
        return JSONResponse(status_code=status_code, content=body.model_dump())

    @app.exception_handler(EmbeddingProviderError)
    async def handle_embedding_provider_error(
        request: Request, exc: EmbeddingProviderError
    ) -> JSONResponse:
        status_code = _status_for(exc, _EMBEDDING_STATUS_BY_ERROR, default=502)
        logger.warning("Embedding provider error on %s: %s", request.url.path, exc)
        body = ErrorResponse(error=ErrorDetail(code=type(exc).__name__, message=str(exc)))
        return JSONResponse(status_code=status_code, content=body.model_dump())

    @app.exception_handler(IngestionError)
    async def handle_ingestion_error(request: Request, exc: IngestionError) -> JSONResponse:
        status_code = _status_for(exc, _INGESTION_STATUS_BY_ERROR, default=502)
        logger.warning("Ingestion error on %s: %s", request.url.path, exc)
        body = ErrorResponse(error=ErrorDetail(code=type(exc).__name__, message=str(exc)))
        return JSONResponse(status_code=status_code, content=body.model_dump())

    @app.exception_handler(RepositoryError)
    async def handle_repository_error(request: Request, exc: RepositoryError) -> JSONResponse:
        # Full exception detail (may include table/column names) goes to the server log only —
        # never to the client, per the rule against exposing database internals.
        logger.error("Repository error on %s: %s", request.url.path, exc)
        body = ErrorResponse(error=ErrorDetail(code="DatabaseError", message="database unavailable"))
        return JSONResponse(status_code=503, content=body.model_dump())

    @app.exception_handler(RepositoryNotIndexedError)
    async def handle_repository_not_indexed_error(
        request: Request, exc: RepositoryNotIndexedError
    ) -> JSONResponse:
        logger.info("Search/ask against unindexed repository on %s: %s", request.url.path, exc)
        body = ErrorResponse(error=ErrorDetail(code="RepositoryNotIndexedError", message=str(exc)))
        return JSONResponse(status_code=404, content=body.model_dump())

    @app.exception_handler(FileNotIndexedError)
    async def handle_file_not_indexed_error(request: Request, exc: FileNotIndexedError) -> JSONResponse:
        logger.info("Explain requested for unindexed file on %s: %s", request.url.path, exc)
        body = ErrorResponse(error=ErrorDetail(code="FileNotIndexedError", message=str(exc)))
        return JSONResponse(status_code=404, content=body.model_dump())
