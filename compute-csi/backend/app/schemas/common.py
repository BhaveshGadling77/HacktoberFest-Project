from __future__ import annotations

from typing import Generic, List, TypeVar, Optional
from pydantic import BaseModel
from enum import Enum

T = TypeVar("T")


class StatusEnum(str, Enum):
    OK = "ok"
    ERROR = "error"
    DEGRADED = "degraded"


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def build(cls, items: List[T], total: int, page: int, page_size: int) -> "PaginatedResponse[T]":
        total_pages = max(1, (total + page_size - 1) // page_size)
        return cls(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages)


class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
