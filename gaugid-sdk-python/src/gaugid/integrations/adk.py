"""
GaugidMemoryService - Google ADK MemoryService implementation using Gaugid SDK

This module provides a MemoryService implementation for Google ADK that uses
Gaugid profiles as the long-term memory store. This allows ADK agents to:
- Store session information in Gaugid profiles
- Search Gaugid memories for relevant context
- Integrate with existing Gaugid user profiles
- Use all three memory types (episodic, semantic, procedural)

The service implements the BaseMemoryService interface from Google ADK, making it
a drop-in replacement for InMemoryMemoryService or VertexAiMemoryBankService.

Based on: https://google.github.io/adk-docs/sessions/memory/

Example:
    ```python
    from google.adk import Agent, Runner
    from google.adk.tools.preload_memory_tool import PreloadMemoryTool
    from gaugid.integrations.adk import GaugidMemoryService
    
    # Create memory service
    memory_service = GaugidMemoryService(
        connection_token="gaugid_conn_xxx",
        app_name="my-adk-app"
    )
    
    # Create agent with memory
    agent = Agent(
        model="gemini-2.0-flash-exp",
        tools=[PreloadMemoryTool()],
    )
    
    # Use with runner
    runner = Runner(agent=agent, memory_service=memory_service)
    ```
"""

from typing import Optional, List, Dict, Any

try:
    from google.adk.memory import BaseMemoryService, SearchMemoryResponse, MemoryResult
    from google.adk.sessions import Session
    from google.genai import types
    GOOGLE_ADK_AVAILABLE = True
except ImportError:
    GOOGLE_ADK_AVAILABLE = False
    # Create minimal stubs for type checking when ADK not available
    class BaseMemoryService:
        async def add_session_to_memory(self, session, app_name=None, user_id=None):
            pass
        async def search_memory(self, query, app_name=None, user_id=None, limit=10):
            pass
    class SearchMemoryResponse:
        def __init__(self, memories=None):
            self.memories = memories or []
    class MemoryResult:
        def __init__(self, content=None, metadata=None):
            self.content = content
            self.metadata = metadata or {}
    class Session:
        pass
    class types:
        class Content:
            def __init__(self, parts=None):
                self.parts = parts or []
        class Part:
            def __init__(self, text=None):
                self.text = text

from gaugid.client import GaugidClient


class GaugidMemoryService(BaseMemoryService):
    """
    Google ADK MemoryService implementation using Gaugid SDK.
    
    This service allows Google ADK agents to use Gaugid profiles as their
    long-term memory store. It implements the BaseMemoryService interface
    and integrates seamlessly with ADK's memory tools.
    
    Example:
        ```python
        from google.adk import Runner
        from gaugid.integrations.adk import GaugidMemoryService
        
        memory_service = GaugidMemoryService(
            connection_token="gaugid_conn_xxx",
            app_name="my-adk-app"
        )
        
        runner = Runner(
            agent=my_agent,
            memory_service=memory_service
        )
        ```
    
    Based on: https://google.github.io/adk-docs/sessions/memory/
    """
    
    def __init__(
        self,
        connection_token: str,
        app_name: str = "adk-agent",
        api_url: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        """
        Initialize GaugidMemoryService.
        
        Args:
            connection_token: Gaugid connection token for authentication
            app_name: Application name (used as namespace for memories)
            api_url: Optional Gaugid API URL (defaults to production)
            user_id: Optional user ID (if not provided, uses token context)
        """
        if not GOOGLE_ADK_AVAILABLE:
            raise ImportError(
                "Google ADK is not installed. Install with: pip install gaugid[adk]"
                "\nNote: This requires google-adk>=1.22.0 and python-genai>=0.8.0"
            )
        
        self.client = GaugidClient(connection_token=connection_token, api_url=api_url)
        self.app_name = app_name
        self.user_id = user_id
        self._client_initialized = False
    
    async def _ensure_client_ready(self) -> None:
        """Ensure the client is ready (lazy initialization)."""
        if not self._client_initialized:
            # Client is already initialized in __init__, just mark as ready
            self._client_initialized = True
    
    async def add_session_to_memory(
        self,
        session: Session,
        app_name: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> None:
        """
        Add session information to Gaugid memory.
        
        This method extracts meaningful information from an ADK session and
        stores it in the user's Gaugid profile as memories. It follows the
        same pattern as Vertex AI Memory Bank, extracting structured information
        from conversation events.
        
        Based on: https://google.github.io/adk-docs/sessions/memory/
        
        Args:
            session: ADK Session object containing conversation events
            app_name: Optional app name override
            user_id: Optional user ID override
        """
        await self._ensure_client_ready()
        
        app_name = app_name or self.app_name
        user_id = user_id or self.user_id
        
        # Extract conversation summary from session events
        # ADK sessions have events that contain user messages and agent responses
        events = getattr(session, 'events', [])
        
        if not events:
            return  # No events to process
        
        # Build conversation summary
        conversation_parts = []
        user_messages = []
        agent_responses = []
        
        for event in events:
            # Extract user messages
            if hasattr(event, 'user_message'):
                text = self._extract_text(event.user_message)
                if text:
                    user_messages.append(text)
                    conversation_parts.append(f"User: {text}")
            
            # Extract agent responses
            if hasattr(event, 'agent_response'):
                text = self._extract_text(event.agent_response)
                if text:
                    agent_responses.append(text)
                    conversation_parts.append(f"Agent: {text}")
            
            # Also check for LLMResponse events
            if hasattr(event, 'LLMResponse'):
                text = self._extract_text(event.LLMResponse)
                if text:
                    agent_responses.append(text)
                    conversation_parts.append(f"Agent: {text}")
        
        if not conversation_parts:
            return  # No meaningful content to store
        
        conversation_summary = "\n".join(conversation_parts)
        
        # Store conversation as episodic memory (specific event)
        # This captures "what happened when" - the actual conversation
        await self.client.propose_memory(
            content=f"Conversation in {app_name}: {conversation_summary[:1000]}",
            category=f"a2p:context.{app_name}",
            memory_type="episodic",
            confidence=0.8,
            context=f"ADK session from {app_name}",
        )
        
        # Extract semantic knowledge from the conversation
        # This captures "what the user knows" - abstracted information
        if user_messages or agent_responses:
            # Extract key topics discussed
            topics = self._extract_topics(user_messages + agent_responses)
            for topic in topics:
                await self.client.propose_memory(
                    content=topic,
                    category=f"a2p:context.{app_name}",
                    memory_type="semantic",
                    confidence=0.7,
                    context=f"Extracted from ADK session in {app_name}",
                )
        
        # Extract procedural knowledge from session state
        # This captures "how the user does things" - behavioral patterns
        if hasattr(session, 'state') and session.state:
            state_summary = self._extract_state_summary(session.state)
            if state_summary:
                await self.client.propose_memory(
                    content=f"User behavior pattern in {app_name}: {state_summary}",
                    category=f"a2p:context.{app_name}",
                    memory_type="procedural",
                    confidence=0.6,
                    context=f"ADK session state from {app_name}",
                )
    
    async def search_memory(
        self,
        query: str,
        app_name: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 10,
    ) -> SearchMemoryResponse:
        """
        Search Gaugid memories for relevant information.
        
        This method searches the user's Gaugid profile for memories
        relevant to the query and returns them in ADK's expected format.
        
        Args:
            query: Search query string
            app_name: Optional app name to filter memories
            user_id: Optional user ID override
            limit: Maximum number of results to return
            
        Returns:
            SearchMemoryResponse with relevant memories
        """
        await self._ensure_client_ready()
        
        app_name = app_name or self.app_name
        
        # Get user profile with relevant scopes
        profile = await self.client.get_profile(
            scopes=["a2p:context", "a2p:interests", "a2p:professional"]
        )
        
        # Extract all memories
        memories = profile.get("memories", {})
        all_memories = []
        
        # Collect episodic memories
        for memory in memories.get("episodic", []):
            if self._is_relevant(memory, query, app_name):
                all_memories.append(memory)
        
        # Collect semantic memories
        for memory in memories.get("semantic", []):
            if self._is_relevant(memory, query, app_name):
                all_memories.append(memory)
        
        # Collect procedural memories
        for memory in memories.get("procedural", []):
            if self._is_relevant(memory, query, app_name):
                all_memories.append(memory)
        
        # Sort by relevance (simple keyword matching for now)
        # In production, you might use semantic search or embeddings
        all_memories.sort(
            key=lambda m: self._relevance_score(m, query),
            reverse=True
        )
        
        # Limit results
        all_memories = all_memories[:limit]
        
        # Convert to ADK MemoryResult format
        memory_results = []
        for memory in all_memories:
            # Create Content object with text part
            memory_content = memory.get("content", "")
            content = types.Content(
                parts=[types.Part(text=memory_content)]
            )
            
            # Create MemoryResult with content and metadata
            # ADK MemoryResult expects content and optional metadata
            try:
                memory_result = MemoryResult(
                    content=content,
                    metadata={
                        "category": memory.get("category", ""),
                        "memory_type": memory.get("memory_type", "episodic"),
                        "confidence": memory.get("confidence", 0.7),
                        "created_at": memory.get("created_at", ""),
                        "source": "gaugid",
                        "app_name": app_name,
                    }
                )
            except TypeError:
                # Fallback if MemoryResult doesn't accept metadata
                memory_result = MemoryResult(content=content)
                if hasattr(memory_result, 'metadata'):
                    memory_result.metadata = {
                        "category": memory.get("category", ""),
                        "memory_type": memory.get("memory_type", "episodic"),
                        "confidence": memory.get("confidence", 0.7),
                    }
            
            memory_results.append(memory_result)
        
        return SearchMemoryResponse(memories=memory_results)
    
    def _extract_text(self, content: Any) -> str:
        """Extract text from ADK content object."""
        if isinstance(content, str):
            return content
        
        if hasattr(content, 'parts'):
            text_parts = []
            for part in content.parts:
                if hasattr(part, 'text') and part.text:
                    text_parts.append(part.text)
            return " ".join(text_parts)
        
        if hasattr(content, 'text'):
            return content.text
        
        return str(content)
    
    def _extract_topics(self, messages: List[str]) -> List[str]:
        """Extract key topics from conversation messages."""
        # Simple keyword extraction - in production, use LLM or NLP
        topics = []
        all_text = " ".join(messages).lower()
        
        # Common topic keywords
        topic_keywords = {
            "python": "Python programming",
            "javascript": "JavaScript programming",
            "ai": "Artificial Intelligence",
            "machine learning": "Machine Learning",
            "async": "Asynchronous programming",
            "api": "API development",
        }
        
        for keyword, topic in topic_keywords.items():
            if keyword in all_text and topic not in topics:
                topics.append(topic)
        
        return topics[:5]  # Limit to 5 topics
    
    def _extract_state_summary(self, state: Dict[str, Any]) -> Optional[str]:
        """Extract a summary from session state."""
        if not state:
            return None
        
        # Extract key information from state
        summary_parts = []
        for key, value in state.items():
            if isinstance(value, (str, int, float, bool)):
                summary_parts.append(f"{key}: {value}")
            elif isinstance(value, dict):
                # Recursively extract from nested dicts
                nested = self._extract_state_summary(value)
                if nested:
                    summary_parts.append(f"{key}: {nested}")
        
        return "; ".join(summary_parts) if summary_parts else None
    
    def _is_relevant(self, memory: Dict[str, Any], query: str, app_name: str) -> bool:
        """Check if a memory is relevant to the query."""
        query_lower = query.lower()
        content = memory.get("content", "").lower()
        category = memory.get("category", "").lower()
        
        # Check if query terms appear in content or category
        query_terms = query_lower.split()
        matches = sum(1 for term in query_terms if term in content or term in category)
        
        # Also check if memory is from the same app
        category_matches_app = app_name.lower() in category
        
        return matches > 0 or category_matches_app
    
    def _relevance_score(self, memory: Dict[str, Any], query: str) -> float:
        """Calculate relevance score for a memory."""
        query_lower = query.lower()
        content = memory.get("content", "").lower()
        category = memory.get("category", "").lower()
        
        score = 0.0
        
        # Exact phrase match
        if query_lower in content:
            score += 10.0
        
        # Word matches
        query_terms = query_lower.split()
        for term in query_terms:
            if term in content:
                score += 2.0
            if term in category:
                score += 1.0
        
        # Boost by confidence
        confidence = memory.get("confidence", 0.5)
        score *= (0.5 + confidence)
        
        return score
    
    async def close(self) -> None:
        """Close the Gaugid client and cleanup resources."""
        if self._client_initialized:
            await self.client.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_client_ready()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
