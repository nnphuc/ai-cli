"""Chat models for AI CLI."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class Message(BaseModel):
    """Chat message model."""
    role: str = Field(..., description="Message role (system, user, assistant)")
    content: str = Field(..., description="Message content")


class ChatResponse(BaseModel):
    """Chat response model."""
    content: str = Field(..., description="Response content")
    model: str = Field(..., description="Model used for the response")
    usage: Optional[Dict[str, Any]] = Field(None, description="Token usage information")


class ChatSession(BaseModel):
    """Chat session model."""
    messages: list[Message] = Field(default_factory=list, description="Chat messages")
    model: str = Field(..., description="Model being used")
    provider: str = Field(..., description="AI provider being used")
    temperature: float = Field(..., description="Temperature setting")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens")
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the session."""
        self.messages.append(Message(role=role, content=content))
    
    def clear_messages(self) -> None:
        """Clear all messages from the session."""
        self.messages.clear()
    
    def get_messages(self) -> list[Message]:
        """Get all messages in the session."""
        return self.messages.copy() 