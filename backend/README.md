# Repello Research Backend

An AI-powered research assistant that uses LangGraph for orchestrating search, analysis, and synthesis of information.

## Features

- Web search using Bing Search API
- Content security checks using LLM-Guard and OpenAI Moderation
- LangGraph-based agent workflow for research and synthesis
- Streaming responses for real-time updates
- FastAPI backend with async support

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with required API keys:
```env
OPENAI_API_KEY=your_openai_key
BING_API_KEY=your_bing_key
ENVIRONMENT=development
DEBUG=true
```

## Running the Server

```bash
python run.py
```

The server will start at `http://localhost:8000`.

## API Endpoints

### POST /api/query
Process a research query and stream results.

Request body:
```json
{
    "query": "your research query",
    "max_results": 5  // optional
}
```

Response: Server-Sent Events stream with the following message types:
- `status`: Progress updates
- `content`: Research findings
- `error`: Error messages

## Architecture

The backend uses a LangGraph-based agent with the following components:

1. Security Check Node
   - Input validation
   - Content moderation
   - Prompt injection detection

2. Search Node
   - Web search using Bing API
   - Content extraction and cleaning

3. Research Node
   - Analysis of search results
   - Source credibility evaluation
   - Pattern identification

4. Synthesis Node
   - Information synthesis
   - Citation generation
   - Response formatting

## Development

The project uses:
- FastAPI for the web framework
- LangGraph for agent orchestration
- Pydantic for data validation
- LLM-Guard for security
- OpenAI for LLM capabilities 