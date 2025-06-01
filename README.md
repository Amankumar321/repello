# Repello AI Research Assistant
https://drive.google.com/file/d/1V32ROu88u263qlLtN8PTBdk6xI2HD953/view?usp=sharing

## Overview
This project implements Option 1: AI Research Assistant with Web Browsing. The system is a sophisticated AI agent that performs web research to answer user queries, combining web search capabilities with advanced language understanding to provide accurate, well-cited responses.

The agent breaks down complex queries into specific searches, gathers information from multiple sources, and synthesizes coherent answers while maintaining security and content safety. It demonstrates multi-step reasoning by performing targeted searches and combining information from various sources.

## Technical Approach

### Core Components
1. **Frontend (React/Next.js)**
   - Modern, responsive UI for query input and result display
   - Real-time streaming of agent's process and findings
   - Markdown rendering for formatted responses with citations

2. **Backend (FastAPI)**
   - RESTful API endpoints for query processing
   - Real-time response streaming
   - Session management and rate limiting
   - Prompt injection avoidance and input validation

3. **Research Agent**
   - LangChain-based implementation with custom tools
   - Multi-step pipeline
   - Web search integration
   - Content safety checks

### Reasoning Pipeline
1. Query Analysis
   - Input validation and safety check
   - Query breakdown into sub-questions
   
2. Information Gathering
   - Targeted web searches for each sub-question
   - Content extraction and filtering

3. Response Synthesis
   - Information aggregation from multiple sources
   - Citation generation
   - Content safety verification
   - Formatted response generation

### Key Libraries & Services
- LangChain for agent orchestration
- OpenAI GPT-4 for language understanding
- Web search API for information gathering
- FastAPI for backend services
- React/Next.js for frontend
- SlowAPI for rate limiting

## Security Measures

1. **Prompt Injection Protection**
   - LLM-Guard's PromptInjection scanner with HuggingFace model integration
   - Risk score-based detection with customizable thresholds
   - Sentence-level analysis for injection patterns
   - Automatic sanitization of potentially malicious inputs
   - User-friendly warning messages based on risk severity

2. **Content Safety & Moderation**
   - LLM-Guard's BanTopics scanner for detecting harmful content
   - Pre-defined banned topics: hate, violence, nsfw, self-harm
   - OpenAI's moderation API (model: omni-moderation-latest) for comprehensive content screening
   - Concurrent safety checks for both input and output content
   - Detailed category-based content scoring and flagging

3. **Rate Limiting & Session Management**
   - 20 requests per minute per client using SlowAPI
   - Session-based history tracking with automatic cleanup
   - 24-hour session expiration
   - Maximum 1000 concurrent sessions
   - Automatic old session pruning

4. **API Security**
   - Environment variable management for all sensitive credentials
   - Request validation using Pydantic models
   - Comprehensive error handling with safe error messages
   - Sanitized response formatting

## Setup & Running Instructions

### Prerequisites
- Python 3.9+
- Node.js 18+
- OpenAI API key
- Google Custom Search API key and Engine ID https://developers.google.com/custom-search/v1/introduction
- HuggingFace API key with permision - Make calls to Inference Providers

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create .env file with required environment variables:
   ```
   OPENAI_API_KEY=
   GOOGLE_API_KEY=
   GOOGLE_SEARCH_ENGINE_ID=
   HUGGINGFACE_TOKEN=
   ```

5. Start the backend server:
   ````bash
   python run.py
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create .env file:
   ```
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
   ```

4. Start the development server:
   ```bash
   npm run dev
   ```

The application will be available at http://localhost:3000

## Usage Guide

1. Open the web interface in your browser
2. Enter your research query in the input field
3. The agent will:
   - Show progress
   - Present the final answer with citations

## Example Scenarios

### Example 1: Technology Research
**Query**: "Compare the latest electric vehicle models and their safety features"

**Response**:
```markdown
Here's a comparison of the latest EV models and their safety features:

1. Tesla Model Y (2024)
- Standard Safety Features:
  - Autopilot with emergency braking
  - 360-degree cameras
  - NHTSA 5-star safety rating
[Source: Tesla.com/safety]

2. Ford Mustang Mach-E (2024)
...
```

### Example 2: Current Events
**Query**: "What are the latest developments in quantum computing?"

**Response**:
```markdown
Recent quantum computing breakthroughs include:

1. IBM's Latest Achievement
- New 1000+ qubit processor
- Improved error correction
[Source: IBM Research Blog, Feb 2024]
...
```

Key challenges included:
- Implementing robust content safety measures
- Optimizing the search process for accuracy
- Managing real-time streaming of responses
