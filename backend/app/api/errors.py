"""Turn LLM failures into HTTP errors with a clear message, the same way on every route."""

import logging
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import HTTPException, status

from app.llm.base import LLMError, LLMOutputError

logger = logging.getLogger(__name__)


@contextmanager
def llm_errors_as_http(action: str) -> Iterator[None]:
    """502 if the model answered in the wrong shape; 503 if it could not be reached."""
    try:
        yield
    except LLMOutputError as exc:
        logger.error("%s failed, bad model output: %s", action, exc)
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except LLMError as exc:
        logger.error("%s failed, LLM unavailable: %s", action, exc)
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
