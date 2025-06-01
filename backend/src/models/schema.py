from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class MessageType(str, Enum):
    STATUS = "status"
    CONTENT = "content"
    ERROR = "error"

class Message(BaseModel):
    """Message model for streaming responses"""
    type: MessageType
    content: str

class QueryRequest(BaseModel):
    """Query request model"""
    query: str
    sessionId: Optional[str] = Field(default=None)
    max_results: Optional[int] = Field(default=None)

class SearchResult(BaseModel):
    """Search result model"""
    title: str
    url: str
    snippet: str
    source: str
    timestamp: datetime
    relevance_score: float

class ResearchResponse(BaseModel):
    query: str
    search_results: List[SearchResult]
    synthesis: str
    sources_used: int
    processing_time: float 