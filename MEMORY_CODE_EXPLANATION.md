# Interactive Chat with Memory - Code Explanation

## Overview

`interactive-chat-with-memory.py` is a Python CLI chatbot that uses AgentCore Memory to persist conversations across sessions. This guide explains how the memory integration works.

---

## Architecture

```
User Input
    ↓
Load Previous Memory (on startup)
    ↓
Call AgentCore Gateway (get pet data)
    ↓
Save Conversation to Memory
    ↓
Display Response
```

---

## Code Breakdown

### 1. Imports and Setup

```python
import boto3
import json
import uuid
from datetime import datetime

# Load configuration
with open('deployment-config.json', 'r') as f:
    config = json.load(f)

# Initialize AWS clients
bedrock_runtime = boto3.client('bedrock-agent-runtime', region_name=config['region'])
```

**What it does:**
- Imports AWS SDK (boto3) for AgentCore Memory API
- Loads resource IDs from `deployment-config.json`
- Creates `bedrock-agent-runtime` client for memory operations

**Key client:** `bedrock-agent-runtime` handles both:
- `get_memory()` - Load previous conversations
- `put_memory()` - Save new conversations

---

### 2. Session ID Generation

```python
# Generate unique session ID
SESSION_ID = f"session-{int(datetime.now().timestamp())}"
MEMORY_ID = config['memory_id']

print(f"📝 Session ID: {SESSION_ID}")
```

**What it does:**
- Creates unique session ID using timestamp
- Each session has its own conversation history
- Same session ID = same conversation across devices

**Session ID format:** `session-1738135267606`

**Why it matters:**
- Multiple users can have separate conversations
- Same user can have multiple conversation threads
- Session ID in URL enables multi-device access

---

### 3. Load Memory Function

```python
def load_memory():
    """Load previous conversation from AgentCore Memory"""
    try:
        response = bedrock_runtime.get_memory(
            memoryId=MEMORY_ID,
            sessionId=SESSION_ID,
            maxResults=10
        )
        
        if 'memoryContents' in response and response['memoryContents']:
            print(f"\n💾 Loading previous conversation...")
            print("=" * 70)
            
            for item in response['memoryContents']:
                if 'userMessage' in item:
                    print(f"\nYou: {item['userMessage']}")
                if 'assistantMessage' in item:
                    print(f"Assistant: {item['assistantMessage']}")
            
            print("\n" + "=" * 70)
            return response['memoryContents']
        else:
            print("\n👋 Welcome! Starting a new conversation.")
            return []
            
    except Exception as e:
        print(f"\n⚠️  No previous memory found: {e}")
        return []
```

**What it does:**
1. Calls `get_memory()` API with session ID
2. Retrieves up to 10 previous message pairs
3. Displays conversation history on startup
4. Returns empty list if no previous memory

**API Parameters:**
- `memoryId` - Which memory store to use
- `sessionId` - Which conversation to load
- `maxResults` - How many messages to retrieve (max 100)

**Response structure:**
```json
{
  "memoryContents": [
    {
      "userMessage": "What pets do you have?",
      "assistantMessage": "We have 15 pets: Buddy, Whiskers..."
    },
    {
      "userMessage": "Tell me about Buddy",
      "assistantMessage": "Buddy is a Golden Retriever..."
    }
  ]
}
```

**Error handling:**
- If memory doesn't exist → Start new conversation
- If session ID not found → Start new conversation
- If API fails → Continue without memory

---

### 4. Save to Memory Function

```python
def save_to_memory(user_message, assistant_message):
    """Save conversation to AgentCore Memory"""
    try:
        bedrock_runtime.put_memory(
            memoryId=MEMORY_ID,
            sessionId=SESSION_ID,
            memoryContents=[{
                'userMessage': user_message,
                'assistantMessage': assistant_message
            }]
        )
        print("💾 Saved to memory")
    except Exception as e:
        print(f"⚠️  Failed to save to memory: {e}")
```

**What it does:**
1. Takes user message and AI response
2. Calls `put_memory()` API to save both
3. Appends to existing conversation history
4. Confirms save with visual indicator

**API Parameters:**
- `memoryId` - Which memory store to use
- `sessionId` - Which conversation to append to
- `memoryContents` - Array of message pairs to save

**Message pair structure:**
```python
{
    'userMessage': 'What pets do you have?',
    'assistantMessage': 'We have 15 pets: Buddy, Whiskers...'
}
```

**Why save both messages:**
- Maintains conversation context
- AI can reference previous exchanges
- User sees complete conversation history

**When it saves:**
- After every successful AI response
- Before program exits
- Automatically, no user action needed

---

### 5. Main Chat Loop

```python
# Load previous conversation on startup
conversation_history = load_memory()

print("\nAsk me anything about pets! Type 'quit' to exit.")

while True:
    user_input = input("\nYou: ").strip()
    
    if user_input.lower() == 'quit':
        print("\n👋 Goodbye! Your conversation has been saved.")
        break
    
    if not user_input:
        continue
    
    try:
        # Call AgentCore Gateway
        response = call_gateway_tool('ListPets', {})
        
        # Process and display response
        assistant_message = format_response(response)
        print(f"\nAssistant: {assistant_message}")
        
        # Save to memory
        save_to_memory(user_input, assistant_message)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
```

**Flow:**
1. **Startup:** Load previous conversation
2. **Input:** Get user message
3. **Process:** Call AgentCore Gateway for data
4. **Respond:** Format and display AI response
5. **Save:** Store message pair in memory
6. **Repeat:** Continue until user quits

---

## Memory Persistence Flow

### First Run (New Session)

```
User starts chatbot
    ↓
load_memory() → No previous memory
    ↓
User: "What pets do you have?"
    ↓
AI: "We have 15 pets..."
    ↓
save_to_memory() → Saves to AgentCore Memory
    ↓
User quits
```

### Second Run (Same Session ID)

```
User starts chatbot
    ↓
load_memory() → Finds previous conversation
    ↓
Displays: "You: What pets do you have?"
          "Assistant: We have 15 pets..."
    ↓
User: "Tell me about Buddy"
    ↓
AI: "Buddy is a Golden Retriever..." (has context!)
    ↓
save_to_memory() → Appends to existing memory
```

---

## Key Differences from Original Code

### Without Memory (interactive-chat.py)

```python
# No memory imports
# No session ID
# No load_memory()
# No save_to_memory()

while True:
    user_input = input("You: ")
    response = call_gateway()
    print(f"Assistant: {response}")
    # Conversation lost on exit
```

### With Memory (interactive-chat-with-memory.py)

```python
import boto3  # Added

SESSION_ID = generate_session_id()  # Added
conversation_history = load_memory()  # Added

while True:
    user_input = input("You: ")
    response = call_gateway()
    print(f"Assistant: {response}")
    save_to_memory(user_input, response)  # Added
    # Conversation persists!
```

---

## Memory Storage Structure

### In AgentCore Memory

```
Memory ID: PetStoreChatMemory-Zhm3u49PiK
├── Session: session-1738135267606
│   ├── Message 1: User + Assistant
│   ├── Message 2: User + Assistant
│   └── Message 3: User + Assistant
├── Session: session-1738135268000
│   ├── Message 1: User + Assistant
│   └── Message 2: User + Assistant
└── Session: session-1738135269000
    └── Message 1: User + Assistant
```

**Key points:**
- One memory ID per application
- Multiple sessions per memory
- Multiple message pairs per session
- Sessions are isolated from each other

---

## Configuration Requirements

### deployment-config.json

```json
{
  "memory_id": "PetStoreChatMemory-Zhm3u49PiK",
  "region": "us-east-1",
  "gateway_url": "https://...",
  "user_pool_id": "...",
  "client_id": "..."
}
```

**Required fields for memory:**
- `memory_id` - AgentCore Memory identifier
- `region` - AWS region (must match memory region)

**Optional but recommended:**
- `identity_pool_id` - For web interface
- All other fields for gateway access

---

## IAM Permissions Required

### For Python Script (Uses AWS Credentials)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock-agent-runtime:GetMemory",
        "bedrock-agent-runtime:PutMemory"
      ],
      "Resource": "arn:aws:bedrock-agentcore:us-east-1:ACCOUNT_ID:memory/MEMORY_ID"
    }
  ]
}
```

**What you need:**
- AWS credentials configured (`aws configure`)
- IAM user/role with above permissions
- Access to specific memory resource

---

## Testing Memory Persistence

### Test 1: Basic Persistence

```bash
# Run 1
python3 interactive-chat-with-memory.py
You: What pets do you have?
Assistant: We have 15 pets...
You: quit

# Run 2 (same session ID)
python3 interactive-chat-with-memory.py
💾 Loading previous conversation...
You: What pets do you have?
Assistant: We have 15 pets...

You: Tell me about the first one
Assistant: Buddy is a Golden Retriever... (remembers context!)
```

### Test 2: Multi-Device

```bash
# Device 1
python3 interactive-chat-with-memory.py
Session ID: session-1738135267606
You: What pets do you have?

# Device 2 (use same session ID)
SESSION_ID="session-1738135267606" python3 interactive-chat-with-memory.py
💾 Loading previous conversation...
You: What pets do you have?  # Shows previous conversation!
```

### Test 3: View Memory Contents

```bash
aws bedrock-agent-runtime get-memory \
  --memory-id PetStoreChatMemory-Zhm3u49PiK \
  --session-id session-1738135267606 \
  --region us-east-1
```

---

## Common Issues

### Issue: "Memory not found"

**Cause:** Memory ID doesn't exist or wrong region

**Fix:**
```bash
# Verify memory exists
aws bedrock-agentcore-control get-memory \
  --memory-id YOUR_MEMORY_ID \
  --region us-east-1

# Check status is ACTIVE
```

### Issue: "Access denied"

**Cause:** Missing IAM permissions

**Fix:**
```bash
# Check your AWS identity
aws sts get-caller-identity

# Verify permissions
aws iam get-user-policy \
  --user-name YOUR_USER \
  --policy-name MemoryAccess
```

### Issue: "Session not found"

**Cause:** Using different session ID

**Fix:**
- Session IDs are case-sensitive
- Copy exact session ID from first run
- Or use environment variable: `SESSION_ID="session-123"`

---

## Advanced Usage

### Custom Session IDs

```python
# Instead of timestamp
SESSION_ID = f"user-{username}-{date}"

# Or use UUID
import uuid
SESSION_ID = str(uuid.uuid4())
```

### Retrieve More History

```python
response = bedrock_runtime.get_memory(
    memoryId=MEMORY_ID,
    sessionId=SESSION_ID,
    maxResults=100  # Get up to 100 messages
)
```

### Clear Memory

```python
# Delete specific session (not directly supported)
# Workaround: Create new session ID

# Or wait for expiry (30 days default)
```

---

## Comparison: Python vs Web Interface

### Python Script
- Uses AWS credentials from `~/.aws/credentials`
- Requires `boto3` SDK
- CLI-based interaction
- Session ID in code

### Web Interface (HTML)
- Uses Cognito Identity Pool
- Uses AWS SDK for JavaScript
- Browser-based interaction
- Session ID in URL

**Both use the same:**
- AgentCore Memory API
- Same memory ID
- Same session ID format
- Same message structure

---

## Summary

**Key Functions:**
1. `load_memory()` - Retrieves conversation history on startup
2. `save_to_memory()` - Saves each message pair after response

**Key Concepts:**
- Session ID = Conversation identifier
- Memory ID = Storage location
- Message pairs = User + Assistant messages
- Persistence = Survives program restarts

**Benefits:**
- ✅ Conversations persist across sessions
- ✅ Multi-device access with same session ID
- ✅ Context-aware responses
- ✅ No database management needed
- ✅ Automatic scaling and backups

**Cost:** $2/month for 1000 conversations
