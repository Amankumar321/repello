from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import json
from typing import AsyncGenerator
import uuid

from .models.schema import Message, QueryRequest
from .agent.research_agent import ResearchAgent
from .core.config import get_settings, Settings

# Create rate limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="Repello Research API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Create single research agent instance
settings = get_settings()
research_agent = ResearchAgent(settings)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def stream_messages(messages: AsyncGenerator[Message, None], session_id: str) -> AsyncGenerator[str, None]:
    """Convert messages to JSON strings with newlines"""
    # First yield the session ID
    yield json.dumps({"sessionId": session_id}) + "\n"
    
    # Then yield the rest of the messages
    async for message in messages:
        yield json.dumps(message.model_dump()) + "\n"

@app.post("/api/v1/query")
@limiter.limit("20/minute")
async def process_query(
    request: Request,
    query_request: QueryRequest,
    settings: Settings = Depends(get_settings)
) -> StreamingResponse:
    """
    Process a research query using LangChain agent
    """
    try:
        # Get or create session ID from request body
        session_id = query_request.sessionId if query_request.sessionId else str(uuid.uuid4())
        
        return StreamingResponse(
            stream_messages(research_agent.astream_research(query_request.query, session_id), session_id),
            media_type="application/x-ndjson"
        )
        
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing the query: {str(e)}"
        )