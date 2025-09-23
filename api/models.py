"""Pydantic models for the chat API."""
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""

    conversation_id: str | None = None
    message: str = Field(..., max_length=4096)  # 4KB limit

    @field_validator("message")
    @classmethod
    def validate_message_size(cls, v):
        if len(v.encode("utf-8")) > 4096:
            raise ValueError("Message exceeds 4KB limit")
        return v


class Turn(BaseModel):
    """A single turn in the conversation."""

    role: str = Field(..., pattern=r"^(user|bot)$")
    message: str
    sequence: int | None = Field(
        default=None, description="Monotonic sequence number within conversation"
    )


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""

    conversation_id: str
    message: list[Turn] = Field(..., max_length=10)


class ErrorDetail(BaseModel):
    """Error details for the unified error schema."""

    field: str | None = None


class ErrorEnvelope(BaseModel):
    """Unified error response envelope."""

    error: "ErrorInfo"


class ErrorInfo(BaseModel):
    """Error information."""

    code: str = Field(..., pattern=r"^(validation_error|not_found|internal_error|timeout)$")
    message: str
    details: dict[str, Any] | None = None
    trace_id: str


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    deps: dict[str, str] | None = None


# Update forward references
ErrorEnvelope.model_rebuild()
