# Interactive Chat Code Explanation

## Overview

`interactive-chat.py` is an interactive AI chatbot that allows users to ask natural language questions about pets. It uses the Strands Agent framework to process queries and automatically calls the appropriate tools via AgentCore Gateway.

---

## Code Structure

### 1. Imports and Configuration

```python
import json
from strands import Agent
from strands.tools import tool
import httpx
```

**Purpose:**
- `json` - Parse configuration and API responses
- `strands.Agent` - AI agent framework for natural language processing
- `strands.tools.tool` - Decorator to define agent tools
- `httpx` - HTTP client for MCP protocol communication

```python
# Load config
with open('deployment-config.json') as f:
    config = json.load(f)

with open('access-token.txt') as f:
    access_token = f.read().strip()
```

**Purpose:**
- Loads gateway URL, API IDs, and other configuration
- Reads Cognito ACCESS token for authentication

---

### 2. MCP Client Setup

```python
mcp_client = httpx.Client(
    base_url=config['gateway_url'],
    headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    },
    timeout=30.0
)
```

**Purpose:**
- Creates persistent HTTP client for AgentCore Gateway
- Sets base URL to gateway endpoint
- Adds JWT authentication header
- Sets 30-second timeout for requests

**Key Points:**
- Uses ACCESS token (not ID token)
- Bearer token authentication
- Reuses connection for efficiency

---

### 3. Tool Definitions

#### Tool 1: List Pets

```python
@tool
def list_pets() -> str:
    """List all available pets in the store"""
    response = mcp_client.post("", json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "PetStoreTarget___ListPets",
            "arguments": {}
        }
    })
    result = response.json()
    if 'result' in result:
        content = json.loads(result['result']['content'][0]['text'])
        return json.dumps(content, indent=2)
    return f"Error: {result}"
```

**How It Works:**

1. **@tool Decorator** - Registers function as an agent tool
2. **Docstring** - Describes tool purpose (AI uses this to decide when to call)
3. **MCP Request** - Sends JSON-RPC 2.0 request to gateway
   - `method: "tools/call"` - Invokes a tool
   - `name: "PetStoreTarget___ListPets"` - Tool name with prefix
   - `arguments: {}` - No parameters needed
4. **Response Parsing** - Extracts JSON data from MCP response
5. **Return** - Formatted JSON string for AI to process

**MCP Protocol Flow:**
```
Tool Function → MCP Request → Gateway → API Gateway → Lambda → DynamoDB → Response
```

**Data Source:**
- Lambda queries DynamoDB table "PetStore"
- Returns 15 pets stored persistently
- Data survives Lambda container recycling

#### Tool 2: Get Pet by ID

```python
@tool
def get_pet_by_id(pet_id: int) -> str:
    """Get details of a specific pet by ID"""
    response = mcp_client.post("", json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "PetStoreTarget___GetPetById",
            "arguments": {"petId": str(pet_id)}
        }
    })
    result = response.json()
    if 'result' in result:
        content = json.loads(result['result']['content'][0]['text'])
        return json.dumps(content, indent=2)
    return f"Error: {result}"
```

**Key Differences from list_pets:**
- Takes `pet_id` parameter
- Passes parameter to API: `"arguments": {"petId": str(pet_id)}`
- Converts int to string (API expects string)

**Parameter Flow:**
```
User: "Tell me about pet 2"
  ↓
AI extracts: pet_id = 2
  ↓
Tool called: get_pet_by_id(2)
  ↓
MCP request: {"petId": "2"}
  ↓
API Gateway: GET /pets/2
  ↓
Lambda queries DynamoDB
  ↓
Returns pet data
```

#### Tool 3: Add Pet

```python
@tool
def add_pet(name: str, pet_type: str, price: float) -> str:
    """Add a new pet to the store"""
    response = mcp_client.post("", json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "PetStoreTarget___AddPet",
            "arguments": {
                "name": name,
                "type": pet_type,
                "price": price
            }
        }
    })
    result = response.json()
    if 'result' in result:
        content = json.loads(result['result']['content'][0]['text'])
        return json.dumps(content, indent=2)
    return f"Error: {result}"
```

**Key Features:**
- Takes 3 parameters: name, pet_type, price
- Sends POST request to API
- Lambda auto-generates ID
- Stores in DynamoDB persistently

**Parameter Flow:**
```
User: "Add a parrot named Polly for $89.99"
  ↓
AI extracts: name="Polly", pet_type="parrot", price=89.99
  ↓
Tool called: add_pet("Polly", "parrot", 89.99)
  ↓
MCP request: {"name": "Polly", "type": "parrot", "price": 89.99}
  ↓
API Gateway: POST /pets
  ↓
Lambda writes to DynamoDB
  ↓
Returns new pet with ID
```

---

### 4. Agent Creation

```python
agent = Agent(
    name="PetStoreAssistant",
    system_prompt="""You are a helpful pet store assistant. You can help customers:
    - Browse available pets
    - Get details about specific pets
    - Add new pets to the store
    - Answer questions about pets
    
    Always be friendly and helpful!""",
    tools=[list_pets, get_pet_by_id, add_pet]
)
```

**Components:**

1. **name** - Agent identifier
2. **system_prompt** - Instructions for AI behavior
   - Defines agent personality
   - Lists capabilities
   - Sets tone (friendly, helpful)
3. **tools** - Available functions AI can call
   - `list_pets` - For general queries
   - `get_pet_by_id` - For specific pet queries
   - `add_pet` - For adding new pets

**How AI Decides Which Tool to Use:**
- Reads tool docstrings
- Analyzes user query
- Matches query intent to tool purpose
- Calls appropriate tool with extracted parameters

---

### 5. Interactive Loop

```python
print("=" * 70)
print("🤖 AI Pet Store Assistant")
print("=" * 70)
print("\nAsk me anything about pets! Type 'quit' to exit.\n")

while True:
    try:
        question = input("You: ").strip()
        
        if not question:
            continue
            
        if question.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Goodbye!")
            break
        
        print("\nAssistant: ", end="", flush=True)
        response = agent(question)
        print(response)
        print()
        
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        break
    except Exception as e:
        print(f"\n❌ Error: {e}\n")

mcp_client.close()
```

**Flow:**

1. **Display Welcome** - Shows banner and instructions
2. **Input Loop** - Continuously accepts user questions
3. **Empty Check** - Skips empty inputs
4. **Exit Check** - Breaks on quit/exit/q
5. **Agent Call** - `agent(question)` processes query
   - AI analyzes question
   - Decides which tool(s) to call
   - Calls tools via MCP
   - Generates natural language response
6. **Display Response** - Shows AI's answer
7. **Error Handling** - Catches Ctrl+C and exceptions
8. **Cleanup** - Closes HTTP client

---

## Example Execution Flow

### Example 1: "What pets do you have?"

```
User Input: "What pets do you have?"
    ↓
Agent analyzes query
    ↓
AI Decision: Need to list all pets
    ↓
Calls: list_pets()
    ↓
MCP Request:
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "PetStoreTarget___ListPets",
    "arguments": {}
  }
}
    ↓
Gateway → API Gateway → Lambda
    ↓
Lambda Response (from DynamoDB):
[
  {"id": 1, "name": "Buddy", "type": "dog", "price": 249.99},
  {"id": 2, "name": "Whiskers", "type": "cat", "price": 124.99},
  {"id": 3, "name": "Nemo", "type": "fish", "price": 0.99},
  ... (15 pets total)
]
    ↓
Tool returns JSON string
    ↓
AI generates response:
"We have 15 wonderful pets available including:
🐕 Buddy - Dog ($249.99)
🐱 Whiskers - Cat ($124.99)
🐠 Nemo - Fish ($0.99)
... and 12 more!"
    ↓
Display to user
```

### Example 2: "Tell me about pet 2"

```
User Input: "Tell me about pet 2"
    ↓
Agent analyzes query
    ↓
AI Decision: Need specific pet details
AI Extracts: pet_id = 2
    ↓
Calls: get_pet_by_id(2)
    ↓
MCP Request:
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "PetStoreTarget___GetPetById",
    "arguments": {"petId": "2"}
  }
}
    ↓
Gateway → API Gateway → Lambda
    ↓
Lambda queries DynamoDB
    ↓
Lambda Response:
{"id": 2, "name": "Whiskers", "type": "cat", "price": 124.99}
    ↓
Tool returns JSON string
    ↓
AI generates response:
"Here are the details about Whiskers:
🐱 Name: Whiskers
Type: Cat
Price: $124.99
Pet ID: 2"
    ↓
Display to user
```

---

## Key Concepts

### 1. Tool Decorator Pattern
```python
@tool
def function_name() -> str:
    """Description for AI"""
    # Implementation
```
- Makes function available to AI
- Docstring guides AI's decision-making
- Return type must be string

### 2. MCP Protocol
```python
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "ToolName",
    "arguments": {}
  }
}
```
- Standard JSON-RPC 2.0 format
- `method` specifies operation
- `params` contains tool name and arguments

### 3. Agent Intelligence
- Reads tool docstrings
- Analyzes user intent
- Extracts parameters from natural language
- Calls appropriate tools
- Generates human-friendly responses

### 4. Error Handling
- Try-except for runtime errors
- KeyboardInterrupt for Ctrl+C
- Graceful error messages
- Connection cleanup

---

## Advantages of This Approach

1. **Natural Language Interface** - Users don't need to know API syntax
2. **Automatic Tool Selection** - AI decides which tool to call
3. **Parameter Extraction** - AI extracts parameters from queries
4. **Conversational** - Friendly, human-like responses
5. **Extensible** - Easy to add more tools
6. **Standard Protocol** - Uses MCP for interoperability

---

## Customization Options

### Add More Tools
```python
@tool
def search_pets_by_type(pet_type: str) -> str:
    """Search for pets by type (dog, cat, fish)"""
    # Implementation
```

### Modify Agent Personality
```python
system_prompt="""You are an expert pet consultant with 20 years of experience.
Provide detailed advice about pet care, behavior, and selection."""
```

### Add Context Memory
```python
# Store conversation history
conversation_history = []

# Add to history after each exchange
conversation_history.append({"user": question, "assistant": response})
```

### Add Streaming Responses
```python
# For real-time response generation
for chunk in agent.stream(question):
    print(chunk, end="", flush=True)
```

---

## Common Issues and Solutions

### Issue 1: Token Expired
**Error:** `401 Invalid Bearer token`
**Solution:** Regenerate access token
```bash
aws cognito-idp initiate-auth ... > access-token.txt
```

### Issue 2: Tool Not Found
**Error:** `Unknown tool: ListPets`
**Solution:** Use correct name with prefix: `PetStoreTarget___ListPets`

### Issue 3: Connection Timeout
**Error:** `httpx.ReadTimeout`
**Solution:** Increase timeout or check network
```python
mcp_client = httpx.Client(timeout=60.0)
```

### Issue 4: JSON Parse Error
**Error:** `json.JSONDecodeError`
**Solution:** Check API response format and error handling

---

## Testing the Code

```bash
# Run interactive chat
python3 interactive-chat.py

# Example queries to try:
You: What pets do you have?
You: Tell me about the cat
You: What's the cheapest pet?
You: Show me pet number 1
You: Which pet costs $124.99?
You: Add a parrot named Rio for $79.99
You: quit
```

### Example 3: Adding a Pet

```
User: "Add a parrot named Rio for $79.99"
    ↓
Agent analyzes query
    ↓
AI Decision: Need to add new pet
AI Extracts: name="Rio", pet_type="parrot", price=79.99
    ↓
Calls: add_pet("Rio", "parrot", 79.99)
    ↓
MCP Request:
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "PetStoreTarget___AddPet",
    "arguments": {
      "name": "Rio",
      "type": "parrot",
      "price": 79.99
    }
  }
}
    ↓
Gateway → API Gateway → Lambda
    ↓
Lambda writes to DynamoDB (auto-generates ID 16)
    ↓
Lambda Response:
{"id": 16, "name": "Rio", "type": "parrot", "price": 79.99}
    ↓
Tool returns JSON string
    ↓
AI generates response:
"Great! I've added Rio the parrot to our store for $79.99. 
The pet has been assigned ID 16."
    ↓
Display to user
```

---

## Performance Considerations

- **Connection Reuse** - Single HTTP client for all requests
- **Timeout** - 30 seconds prevents hanging
- **Error Recovery** - Continues on errors
- **Resource Cleanup** - Closes client on exit

---

## Security Notes

- **Token Storage** - ACCESS token in file (not hardcoded)
- **Token Expiry** - Regenerate every hour
- **HTTPS** - All communication encrypted
- **No Credentials** - No passwords in code
