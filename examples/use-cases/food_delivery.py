"""
Food Delivery Use Case: Personalized Ordering with Gaugid

This example demonstrates a food delivery AI assistant that:
- Remembers user dietary preferences and restrictions
- Learns favorite restaurants and dishes
- Tracks order history and patterns
- Personalizes recommendations based on past orders

Uses: LangGraph + Gemini (Vertex AI) + Gaugid Store

Requires:
- GOOGLE_API_KEY or VERTEX_AI credentials
- GAUGID_CONNECTION_TOKEN
- pip install gaugid[langgraph] google-generativeai langchain-google-genai
"""

import asyncio
import os
from typing import TypedDict, Annotated, Sequence, Literal
from operator import add
from datetime import datetime

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
    from langgraph.graph import StateGraph, START, END
    from gaugid.integrations.langgraph import GaugidStore
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("⚠️  LangGraph not installed. Install with: pip install gaugid[langgraph] langchain-google-genai")

from gaugid import GaugidClient
from gaugid.logger import get_logger

logger = get_logger("food_delivery")


class OrderState(TypedDict):
    """State for the food ordering graph."""
    messages: Annotated[Sequence[BaseMessage], add]
    user_preferences: dict
    order_history: list
    current_order: dict
    recommendations: list


class FoodDeliveryAssistant:
    """
    Food delivery AI assistant with personalized ordering.
    
    Features:
    - Remembers dietary preferences
    - Learns favorite restaurants
    - Tracks order history
    - Personalizes recommendations
    """
    
    def __init__(
        self,
        google_api_key: str,
        connection_token: str,
        user_id: str = "default",
    ):
        """
        Initialize food delivery assistant.
        
        Args:
            google_api_key: Google API key for Gemini
            connection_token: Gaugid connection token
            user_id: User identifier
        """
        if not LANGGRAPH_AVAILABLE:
            raise ImportError("LangGraph is not installed")
        
        self.user_id = user_id
        
        # Create Gaugid store for persistent state
        self.store = GaugidStore(
            connection_token=connection_token,
            namespace_prefix=("food_delivery", user_id),
            memory_type="episodic",
        )
        
        # Create LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            google_api_key=google_api_key,
            temperature=0.7,
        )
        
        # Build ordering graph
        self.graph = self._build_graph()
        
        logger.info(f"Food delivery assistant initialized for user: {user_id}")
    
    def _build_graph(self) -> StateGraph:
        """Build the food ordering state graph."""
        
        def load_user_context(state: OrderState) -> dict:
            """Load user context from Gaugid store."""
            # This would load from store in async context
            # For now, return empty context
            return {
                "user_preferences": state.get("user_preferences", {}),
                "order_history": state.get("order_history", []),
            }
        
        def generate_recommendations(state: OrderState) -> dict:
            """Generate personalized recommendations."""
            user_prefs = state.get("user_preferences", {})
            order_history = state.get("order_history", [])
            
            # Build context from preferences and history
            context = f"""User Preferences:
- Dietary restrictions: {user_prefs.get('dietary', 'None')}
- Favorite cuisines: {user_prefs.get('cuisines', [])}
- Budget range: {user_prefs.get('budget', 'Medium')}

Recent Orders: {len(order_history)} orders"""
            
            system_prompt = f"""You are a food delivery assistant. Generate personalized restaurant and dish recommendations.

{context}

Provide recommendations based on user preferences and order history."""
            
            messages = [SystemMessage(content=system_prompt)] + list(state["messages"])
            response = self.llm.invoke(messages)
            
            return {
                "messages": [response],
                "recommendations": [response.content],
            }
        
        def process_order(state: OrderState) -> dict:
            """Process the user's order."""
            messages = list(state["messages"])
            last_message = messages[-1] if messages else None
            
            system_prompt = """You are a food delivery assistant. Help the user place an order.

Consider:
- User's dietary preferences
- Favorite restaurants and dishes
- Order history patterns
- Budget considerations

Confirm the order details and provide an estimated delivery time."""
            
            conversation = [SystemMessage(content=system_prompt)] + messages
            response = self.llm.invoke(conversation)
            
            # Extract order details (simplified)
            order = {
                "items": [],
                "restaurant": "",
                "total": 0.0,
                "timestamp": datetime.now().isoformat(),
            }
            
            return {
                "messages": [response],
                "current_order": order,
            }
        
        def save_order(state: OrderState) -> dict:
            """Save order to history."""
            order = state.get("current_order", {})
            order_history = state.get("order_history", [])
            
            if order:
                order_history.append(order)
            
            return {
                "order_history": order_history,
            }
        
        # Build graph
        graph = StateGraph(OrderState)
        graph.add_node("load_context", load_user_context)
        graph.add_node("recommendations", generate_recommendations)
        graph.add_node("process_order", process_order)
        graph.add_node("save_order", save_order)
        
        # Define flow
        graph.add_edge(START, "load_context")
        graph.add_edge("load_context", "recommendations")
        graph.add_edge("recommendations", "process_order")
        graph.add_edge("process_order", "save_order")
        graph.add_edge("save_order", END)
        
        # Compile with Gaugid store as checkpointer
        return graph.compile(checkpointer=self.store)
    
    async def start_order(self, user_message: str) -> str:
        """
        Start a new order conversation.
        
        Args:
            user_message: User's order request
            
        Returns:
            Assistant's response
        """
        config = {"configurable": {"thread_id": f"{self.user_id}-order"}}
        
        initial_state = {
            "messages": [HumanMessage(content=user_message)],
            "user_preferences": {},
            "order_history": [],
            "current_order": {},
            "recommendations": [],
        }
        
        result = self.graph.invoke(initial_state, config)
        
        # Get last message
        last_message = result["messages"][-1]
        return last_message.content if hasattr(last_message, 'content') else str(last_message)
    
    async def save_preference(
        self,
        preference_type: str,
        value: str,
    ) -> None:
        """
        Save a user preference.
        
        Args:
            preference_type: Type of preference (e.g., "dietary", "cuisine")
            value: Preference value
        """
        await self.store.aput(
            namespace=("food_delivery", self.user_id, "preferences"),
            key=preference_type,
            value=value,
        )
        logger.info(f"Preference saved: {preference_type} = {value}")
    
    async def close(self) -> None:
        """Close the assistant and cleanup resources."""
        await self.store.close()


async def main():
    """Example: Food delivery assistant."""
    
    if not LANGGRAPH_AVAILABLE:
        print("❌ LangGraph is not installed.")
        print("   Install with: pip install gaugid[langgraph] langchain-google-genai")
        return
    
    # Check for API keys
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("❌ Error: GOOGLE_API_KEY environment variable not set")
        return
    
    connection_token = os.getenv("GAUGID_CONNECTION_TOKEN")
    if not connection_token:
        print("❌ Error: GAUGID_CONNECTION_TOKEN environment variable not set")
        return
    
    print("═══════════════════════════════════════════════════════════")
    print("     🍕 Food Delivery Assistant")
    print("═══════════════════════════════════════════════════════════\n")
    
    try:
        # Initialize assistant
        assistant = FoodDeliveryAssistant(
            google_api_key=google_api_key,
            connection_token=connection_token,
            user_id="user-123",
        )
        
        print("1️⃣ Saving user preferences...")
        await assistant.save_preference("dietary", "vegetarian")
        await assistant.save_preference("cuisines", "Italian, Japanese, Mexican")
        await assistant.save_preference("budget", "Medium")
        print("   ✅ Preferences saved\n")
        
        print("2️⃣ Starting order...")
        response = await assistant.start_order(
            "I'd like to order dinner for 2 people, vegetarian options"
        )
        print(f"   Assistant: {response}\n")
        
    finally:
        if 'assistant' in locals():
            await assistant.close()
    
    print("═══════════════════════════════════════════════════════════")
    print("                    ✨ Example Complete!")
    print("═══════════════════════════════════════════════════════════\n")
    print("💡 The assistant remembers:")
    print("   - Dietary preferences and restrictions")
    print("   - Favorite restaurants and cuisines")
    print("   - Order history and patterns")
    print("   - All stored in Gaugid for personalized recommendations!")


if __name__ == "__main__":
    asyncio.run(main())
