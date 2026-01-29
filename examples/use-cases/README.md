# Gaugid SDK Use Cases

Realistic examples demonstrating Gaugid SDK integration in various business scenarios.

## Use Cases

### 1. Travel Agency (`travel_agency.py`)

**Scenario**: Personalized travel planning assistant

**Features**:
- Remembers user travel preferences (window seats, hotel types, dietary restrictions)
- Learns from past trips (favorite destinations, travel patterns)
- Personalizes recommendations based on user profile
- Stores travel memories for future reference

**Technology Stack**:
- Google ADK + Gemini (Vertex AI)
- Gaugid Memory Service

**Installation**:
```bash
pip install gaugid[adk] google-generativeai
```

**Usage**:
```bash
export GOOGLE_API_KEY="your-key"
export GAUGID_CONNECTION_TOKEN="gaugid_conn_xxx"
python travel_agency.py
```

**Key Concepts**:
- Connection token mode (OAuth-based)
- Episodic memory for travel history
- Semantic memory for preferences
- Procedural memory for travel patterns

---

### 2. Food Delivery (`food_delivery.py`)

**Scenario**: Personalized food ordering assistant

**Features**:
- Remembers dietary preferences and restrictions
- Learns favorite restaurants and dishes
- Tracks order history and patterns
- Personalizes recommendations based on past orders

**Technology Stack**:
- LangGraph + Gemini (Vertex AI)
- Gaugid Store

**Installation**:
```bash
pip install gaugid[langgraph] langchain-google-genai
```

**Usage**:
```bash
export GOOGLE_API_KEY="your-key"
export GAUGID_CONNECTION_TOKEN="gaugid_conn_xxx"
python food_delivery.py
```

**Key Concepts**:
- State machine for order flow
- Persistent state with Gaugid Store
- Episodic memory for order history
- Semantic memory for preferences

---

### 3. Agent-to-Agent B2B (`agent_to_agent_b2b.py`)

**Scenario**: Business agent negotiation

**Features**:
- Company A's agent negotiates with Company B's agent
- Each agent has access to their company's profile and preferences
- Agents use A2P-Signature for protocol-compliant authentication
- Business preferences and constraints stored in Gaugid profiles

**Technology Stack**:
- Google ADK + Gemini (Vertex AI)
- A2P-Signature authentication

**Installation**:
```bash
pip install gaugid[adk] google-generativeai
```

**Usage**:
```bash
export GOOGLE_API_KEY="your-key"
export GAUGID_CONNECTION_TOKEN_COMPANY_A="gaugid_conn_xxx"
export GAUGID_CONNECTION_TOKEN_COMPANY_B="gaugid_conn_xxx"
python agent_to_agent_b2b.py
```

**Key Concepts**:
- A2P-Signature for agent authentication
- Protocol-compliant agent-to-agent communication
- Business profile access
- Negotiation outcome storage

---

### 4. Child Safety Agent (`child_safety_agent.py`)

**Scenario**: Child-safe AI assistant with content restrictions

**Features**:
- Enforces age-appropriate content restrictions
- Requires parent/guardian authorization
- Stores child preferences safely
- Limits access to specific scopes (no personal data exposure)
- Uses child-safe memory storage

**Technology Stack**:
- Google ADK + Gemini (Vertex AI)
- Gaugid Memory Service (restricted scopes)

**Installation**:
```bash
pip install gaugid[adk] google-generativeai
```

**Usage**:
```bash
export GOOGLE_API_KEY="your-key"
export GAUGID_CONNECTION_TOKEN="gaugid_conn_xxx"  # With child-safe scopes
python child_safety_agent.py
```

**Key Concepts**:
- Restricted scope access (child-safe)
- Parent/guardian authorization
- Content filtering and safety checks
- Safe memory storage (interests only, no personal data)

---

## Common Patterns

### Connection Token Mode (OAuth-based)

Used in: Travel Agency, Food Delivery, Child Safety

```python
from gaugid import GaugidClient

client = GaugidClient(connection_token="gaugid_conn_xxx")
profile = await client.get_profile(scopes=["a2p:preferences"])
```

**Benefits**:
- User-friendly OAuth flow
- No need to know user DIDs
- Easy to revoke access
- Better privacy

### A2P-Signature Mode (Protocol-native)

Used in: Agent-to-Agent B2B

```python
from gaugid import generate_a2p_signature_header

signature = generate_a2p_signature_header(
    did=agent_did,
    private_key=private_key,
    method="GET",
    path="/a2p/v1/profile/...",
)
```

**Benefits**:
- Fully decentralized
- Protocol-compliant
- Works across providers
- No token management

### Memory Types

- **Episodic**: Specific events and experiences
  - Travel history, order history, negotiation outcomes
- **Semantic**: Facts and knowledge
  - Preferences, favorite restaurants, business constraints
- **Procedural**: Behavioral patterns
  - Travel patterns, ordering habits, negotiation styles

### Scope Restrictions

- **Full Access**: `a2p:*` (all scopes)
- **Standard**: `a2p:preferences`, `a2p:interests`, `a2p:professional`
- **Restricted**: `a2p:interests` only (child-safe)

---

## Environment Variables

### Required

- `GOOGLE_API_KEY`: Google API key for Gemini
- `GAUGID_CONNECTION_TOKEN`: Gaugid connection token (OAuth-based)

### Optional

- `VERTEX_AI_PROJECT`: Vertex AI project ID (if using Vertex AI)
- `VERTEX_AI_LOCATION`: Vertex AI location (if using Vertex AI)
- `GAUGID_API_URL`: Custom Gaugid API URL (defaults to production)

### B2B Specific

- `GAUGID_CONNECTION_TOKEN_COMPANY_A`: Company A's connection token
- `GAUGID_CONNECTION_TOKEN_COMPANY_B`: Company B's connection token

---

## Best Practices

1. **Scope Management**: Request only necessary scopes
2. **Memory Types**: Use appropriate memory types for different data
3. **Error Handling**: Always handle authentication and API errors
4. **Privacy**: Respect user privacy and data protection
5. **Safety**: Implement content filtering for sensitive use cases
6. **Logging**: Use proper logging instead of print statements

---

## Next Steps

1. Review each use case example
2. Adapt to your specific business needs
3. Implement proper error handling
4. Add authentication flows (OAuth for connection tokens)
5. Deploy with proper security measures

---

**Note**: These examples are simplified for demonstration. In production, implement:
- Proper authentication flows
- Error handling and retries
- Rate limiting
- Security best practices
- Compliance with data protection regulations
