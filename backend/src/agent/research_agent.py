from typing import AsyncGenerator, List, Dict, Union
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool
from langchain.schema.messages import AIMessage, HumanMessage
from langchain.schema.runnable import RunnableConfig
from langchain_openai import ChatOpenAI
from datetime import datetime, timedelta

from ..services.search import SearchService
from ..services.security import SecurityService
from ..core.config import Settings
from ..models.schema import Message, MessageType

# Constants for history management
MAX_HISTORY_LENGTH = 10  # Maximum number of messages in history
MAX_SESSION_AGE_HOURS = 24  # Sessions older than this will be cleaned up
MAX_SESSIONS = 1000  # Maximum number of concurrent sessions

class ResearchAgent:
    """LangChain-based research agent with streaming capabilities"""
    
    # Singleton instance
    _instance = None
    
    def __new__(cls, settings: Settings = None):
        if cls._instance is None:
            cls._instance = super(ResearchAgent, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, settings: Settings = None):
        # Only initialize once
        if self._initialized:
            return
            
        if settings is None:
            raise ValueError("Settings required for first initialization")
            
        self.settings = settings
        self.search_service = SearchService(settings)
        self.security_service = SecurityService(settings)
        self.llm = ChatOpenAI(
            api_key=settings.OPENAI_API_KEY,
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            streaming=True
        )
        
        # Initialize tools
        self.tools = self._create_tools()
        
        # Create agent with tools
        self.agent = self._create_agent()
        
        # Create agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            handle_parsing_errors=True,
            max_iterations=settings.MAX_SEARCH_DEPTH
        )
        
        # Initialize sessions storage
        self._sessions: Dict[str, self.SessionData] = {}
        self._initialized = True

    class SessionData:
        def __init__(self):
            self.history: List[Union[AIMessage, HumanMessage]] = []
            self.last_access: datetime = datetime.now()
    
    def _cleanup_old_sessions(self):
        """Remove old sessions to prevent memory leaks"""
        now = datetime.now()
        cutoff = now - timedelta(hours=MAX_SESSION_AGE_HOURS)
        
        # Remove old sessions
        self._sessions = {
            sid: data 
            for sid, data in self._sessions.items() 
            if data.last_access > cutoff
        }
        
        # If still too many sessions, remove oldest ones
        if len(self._sessions) > MAX_SESSIONS:
            sorted_sessions = sorted(
                self._sessions.items(), 
                key=lambda x: x[1].last_access
            )
            self._sessions = dict(sorted_sessions[-MAX_SESSIONS:])
    
    def _get_session_history(self, session_id: str) -> List[Union[AIMessage, HumanMessage]]:
        """Get or create session history with limits"""
        # Clean up old sessions periodically
        self._cleanup_old_sessions()
        
        # Get or create session data
        if session_id not in self._sessions:
            self._sessions[session_id] = self.SessionData()
        
        session_data = self._sessions[session_id]
        session_data.last_access = datetime.now()
        
        # Trim history if too long
        if len(session_data.history) > MAX_HISTORY_LENGTH:
            session_data.history = session_data.history[-MAX_HISTORY_LENGTH:]
        
        return session_data.history
        
    def _create_tools(self) -> List[Tool]:
        """Create LangChain tools for the agent"""
        return [
            Tool(
                name="web_search",
                description="""
                Search the web for information. Use this tool when you need to find specific information.
                Don't search for the entire query at once - break it down into specific searches for key information.
                """,
                func=self.search_service.search,
                coroutine=self.search_service.search
            )
        ]
        
    def _create_agent(self):
        """Create LangChain agent with custom prompt"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a research assistant that helps find accurate information by searching the web.
            
            Important Instructions:
            1. Break down complex queries into specific searches for key information
            2. Verify information from multiple sources when possible
            3. Be skeptical of unreliable sources
            4. If you need more information, use the search tool again
            5. Stream your findings as you discover them
            6. Use bullets, sections, and other formatting to make your responses more readable
            
            Format your responses in markdown with proper citations."""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            ("system", "Always mention website links in response"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        return create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
    async def astream_research(self, query: str, session_id: str) -> AsyncGenerator[Message, None]:
        """Stream research results as they are generated"""
        # First yield a message that we're starting safety checks
        yield Message(
            type=MessageType.CONTENT,
            content="Running safety checks on your query..."
        )
        
        # First check security
        safety_result = await self.security_service.analyze_safety(query)
        if not safety_result["is_safe"]:
            # Get the specific error message from the safety result
            error_message = safety_result.get("message") or "I apologize, but I cannot process this query due to safety concerns."
            
            yield Message(
                type=MessageType.ERROR,
                content=error_message
            )
            return
            
        # Get chat history with limits
        chat_history = self._get_session_history(session_id)
        
        # Add user's query to history
        chat_history.append(HumanMessage(content=query))
        
        try:
            # Stream agent execution
            async for chunk in self.agent_executor.astream(
                {
                    "input": query,
                    "chat_history": chat_history
                },
                config=RunnableConfig(callbacks=None)
            ):
                content = None
                
                if isinstance(chunk, dict):
                    if "actions" in chunk and chunk["actions"]:
                        for action in chunk["actions"]:
                            if action.tool == "web_search":
                                content = f"🔍 Searching: {action.tool_input}"
                    elif "output" in chunk:
                        content = chunk["output"]
                        if content:
                            # Check output safety
                            safety_result = await self.security_service.analyze_safety(content)
                            if not safety_result["is_safe"]:
                                content = "⚠️ This part of the response was flagged as potentially unsafe and has been filtered."
                            else:
                                chat_history.append(AIMessage(content=content))
                elif isinstance(chunk, AIMessage):
                    content = chunk.content
                    if content:
                        # Check output safety
                        safety_result = await self.security_service.analyze_safety(content)
                        if not safety_result["is_safe"]:
                            content = "⚠️ This part of the response was flagged as potentially unsafe and has been filtered."
                        else:
                            chat_history.append(chunk)
                elif isinstance(chunk, str):
                    content = chunk
                    if content:
                        # Check output safety
                        safety_result = await self.security_service.analyze_safety(content)
                        if not safety_result["is_safe"]:
                            content = "⚠️ This part of the response was flagged as potentially unsafe and has been filtered."
                        else:
                            chat_history.append(AIMessage(content=content))
                
                if content:
                    yield Message(
                        type=MessageType.CONTENT,
                        content=content
                    )
            
            # Update the stored chat history
            self._sessions[session_id].history = chat_history
                    
        except Exception as e:
            yield Message(
                type=MessageType.ERROR,
                content=f"An error occurred during research: {str(e)}"
            ) 