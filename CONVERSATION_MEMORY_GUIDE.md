# Conversation Memory Implementation Guide

**How to maintain conversation history across interactions**

---

## Current State: No Memory ❌

The basic web chatbot sends each message independently to AgentCore Gateway. The agent doesn't remember previous interactions.

**Problem:**
```
User: "What pets do you have?"
Agent: "We have 15 pets..."

User: "Tell me about the first one"
Agent: ❌ "Which pet?" (doesn't remember the list)
```

---

## Solution Options

### Option 1: Client-Side Memory (Simplest) ✅

Store conversation history in the browser and send it with each request.

**Cost:** $0 (no additional infrastructure)
**Complexity:** Low
**Best for:** Simple use cases, single-user sessions

### Option 2: DynamoDB Sessions

Store conversation history in DynamoDB.

**Cost:** ~$0.50/month
**Complexity:** Medium
**Best for:** Multi-device access, persistent history

### Option 3: AgentCore Memory

Use AWS AgentCore Memory service.

**Cost:** ~$2/month
**Complexity:** Medium
**Best for:** Advanced semantic search, managed service

---

## Option 1: Client-Side Memory (Recommended) ✅

### Updated HTML with Memory

Add this to your `chat.html`:

```javascript
// Add after CONFIG section
let conversationHistory = [];

// Update sendMessage function
async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    addMessage('user', message);
    input.value = '';
    
    // Add to conversation history
    conversationHistory.push({
        role: 'user',
        content: message
    });
    
    const typingId = addMessage('agent', 'Thinking...', true);
    
    try {
        // Build context from history
        const context = buildContext(conversationHistory);
        
        // Determine tool with context
        const { toolName, toolArgs } = determineToolWithContext(message, context);
        
        // Call AgentCore Gateway
        const response = await fetch(CONFIG.gatewayUrl, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${accessToken}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                jsonrpc: '2.0',
                id: Date.now(),
                method: 'tools/call',
                params: {
                    name: toolName,
                    arguments: toolArgs
                }
            })
        });

        const data = await response.json();
        
        document.getElementById(typingId).remove();
        
        if (data.result) {
            const content = JSON.parse(data.result.content[0].text);
            const formattedResponse = formatResponse(content, toolName);
            addMessage('agent', formattedResponse);
            
            // Add to conversation history
            conversationHistory.push({
                role: 'agent',
                content: formattedResponse,
                rawData: content
            });
        } else {
            addMessage('agent', 'Sorry, I encountered an error.');
        }
    } catch (error) {
        document.getElementById(typingId).remove();
        addMessage('agent', 'Error: ' + error.message);
    }
}

// Build context from conversation history
function buildContext(history) {
    const context = {
        lastPetList: null,
        lastPetDetails: null,
        recentTopics: []
    };
    
    // Extract relevant context from history
    for (let i = history.length - 1; i >= Math.max(0, history.length - 5); i--) {
        const entry = history[i];
        
        if (entry.role === 'agent' && entry.rawData) {
            if (Array.isArray(entry.rawData)) {
                context.lastPetList = entry.rawData;
            } else if (entry.rawData.id) {
                context.lastPetDetails = entry.rawData;
            }
        }
        
        if (entry.role === 'user') {
            context.recentTopics.push(entry.content.toLowerCase());
        }
    }
    
    return context;
}

// Determine tool with context awareness
function determineToolWithContext(message, context) {
    const lowerMessage = message.toLowerCase();
    
    // Handle contextual references
    if (lowerMessage.match(/\b(first|second|third|last|that|it|this)\b/)) {
        // User is referring to something from context
        if (context.lastPetList && context.lastPetList.length > 0) {
            // Extract position reference
            if (lowerMessage.includes('first')) {
                return {
                    toolName: 'PetStoreTarget___GetPetById',
                    toolArgs: { petId: String(context.lastPetList[0].id) }
                };
            } else if (lowerMessage.includes('second') && context.lastPetList.length > 1) {
                return {
                    toolName: 'PetStoreTarget___GetPetById',
                    toolArgs: { petId: String(context.lastPetList[1].id) }
                };
            } else if (lowerMessage.includes('last')) {
                const lastPet = context.lastPetList[context.lastPetList.length - 1];
                return {
                    toolName: 'PetStoreTarget___GetPetById',
                    toolArgs: { petId: String(lastPet.id) }
                };
            } else if (lowerMessage.match(/\b(that|it|this)\b/)) {
                // Refer to last mentioned pet
                if (context.lastPetDetails) {
                    return {
                        toolName: 'PetStoreTarget___GetPetById',
                        toolArgs: { petId: String(context.lastPetDetails.id) }
                    };
                }
            }
        }
    }
    
    // Standard tool determination
    if (lowerMessage.includes('add') && lowerMessage.includes('pet')) {
        const nameMatch = message.match(/named?\s+(\w+)/i);
        const typeMatch = message.match(/\b(dog|cat|fish|bird|hamster|rabbit|turtle|lizard|parrot|frog)\b/i);
        const priceMatch = message.match(/\$?(\d+\.?\d*)/);
        
        if (nameMatch && typeMatch && priceMatch) {
            return {
                toolName: 'PetStoreTarget___AddPet',
                toolArgs: {
                    name: nameMatch[1],
                    type: typeMatch[1],
                    price: parseFloat(priceMatch[1])
                }
            };
        }
    } else if (lowerMessage.includes('pet') && /\b\d+\b/.test(message)) {
        const idMatch = message.match(/\b(\d+)\b/);
        return {
            toolName: 'PetStoreTarget___GetPetById',
            toolArgs: { petId: idMatch[1] }
        };
    }
    
    // Default to list
    return {
        toolName: 'PetStoreTarget___ListPets',
        toolArgs: {}
    };
}

// Clear history on logout
function logout() {
    accessToken = null;
    conversationHistory = []; // Clear memory
    document.getElementById('chatMessages').innerHTML = '';
    document.getElementById('chatContainer').style.display = 'none';
    document.getElementById('loginContainer').style.display = 'block';
}
```

### Example with Memory

```
User: "What pets do you have?"
Agent: "We have 15 pets: Buddy (dog), Whiskers (cat)..."
[Stores: lastPetList = [15 pets]]

User: "Tell me about the first one"
Agent: "Here's Buddy: Type: dog, Price: $249.99"
[Uses context.lastPetList[0] to get Buddy's ID]

User: "What about the second one?"
Agent: "Here's Whiskers: Type: cat, Price: $124.99"
[Uses context.lastPetList[1] to get Whiskers' ID]
```

---

## Option 2: DynamoDB Sessions

### Architecture

```
User → Web Interface → DynamoDB (Save/Load Session) → AgentCore Gateway
```

### Implementation

**1. Create DynamoDB Table**

```bash
aws dynamodb create-table \
  --table-name ChatSessions \
  --attribute-definitions \
    AttributeName=session_id,AttributeType=S \
  --key-schema \
    AttributeName=session_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --time-to-live-specification \
    Enabled=true,AttributeName=ttl
```

**2. Create Lambda Function for Session Management**

```python
import json
import boto3
from datetime import datetime, timedelta

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('ChatSessions')

def lambda_handler(event, context):
    """
    Manage chat sessions
    """
    action = event.get('action')
    session_id = event.get('session_id')
    user_id = event.get('user_id')
    
    if action == 'load':
        # Load session
        response = table.get_item(Key={'session_id': session_id})
        if 'Item' in response:
            return {
                'statusCode': 200,
                'body': json.dumps(response['Item'])
            }
        return {
            'statusCode': 404,
            'body': json.dumps({'messages': []})
        }
    
    elif action == 'save':
        # Save session
        messages = event.get('messages', [])
        ttl = int((datetime.now() + timedelta(days=30)).timestamp())
        
        table.put_item(
            Item={
                'session_id': session_id,
                'user_id': user_id,
                'messages': messages,
                'updated_at': datetime.now().isoformat(),
                'ttl': ttl
            }
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({'success': True})
        }
```

**3. Update Web Interface**

```javascript
// Add session management
const SESSION_API = 'https://YOUR_API.execute-api.us-east-1.amazonaws.com/prod/session';
let sessionId = generateSessionId();

// Load session on login
async function loadSession() {
    const response = await fetch(SESSION_API, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            action: 'load',
            session_id: sessionId,
            user_id: userId
        })
    });
    
    const data = await response.json();
    conversationHistory = data.messages || [];
    
    // Display previous messages
    conversationHistory.forEach(msg => {
        addMessage(msg.role, msg.content);
    });
}

// Save session after each message
async function saveSession() {
    await fetch(SESSION_API, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            action: 'save',
            session_id: sessionId,
            user_id: userId,
            messages: conversationHistory
        })
    });
}

// Call after each interaction
async function sendMessage() {
    // ... existing code ...
    
    // Save session
    await saveSession();
}
```

**Cost:** ~$0.50/month for 1000 sessions

---

## Option 3: AgentCore Memory

### Architecture

```
User → Web Interface → AgentCore Memory → AgentCore Gateway
```

### Implementation

**1. Create AgentCore Memory**

```bash
aws bedrock-agentcore-control create-memory \
  --name PetStoreChatMemory \
  --description "Conversation history for pet store chatbot" \
  --memory-type SEMANTIC \
  --region us-east-1

# Get memory ID
MEMORY_ID=$(aws bedrock-agentcore-control list-memories \
  --query 'memories[?name==`PetStoreChatMemory`].memoryId' \
  --output text)
```

**2. Store Conversations**

```javascript
// Store message in AgentCore Memory
async function storeInMemory(message, response) {
    await fetch(`https://bedrock-agentcore.us-east-1.amazonaws.com/memories/${MEMORY_ID}/messages`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            sessionId: sessionId,
            messages: [
                { role: 'user', content: message },
                { role: 'assistant', content: response }
            ]
        })
    });
}

// Retrieve relevant context
async function getMemoryContext(query) {
    const response = await fetch(`https://bedrock-agentcore.us-east-1.amazonaws.com/memories/${MEMORY_ID}/search`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${accessToken}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            query: query,
            sessionId: sessionId,
            maxResults: 5
        })
    });
    
    return await response.json();
}
```

**Cost:** ~$2/month for 1000 conversations

---

## Comparison

| Feature | Client-Side | DynamoDB | AgentCore Memory |
|---------|------------|----------|------------------|
| **Cost** | $0 | $0.50/month | $2/month |
| **Complexity** | Low | Medium | Medium |
| **Multi-device** | ❌ No | ✅ Yes | ✅ Yes |
| **Semantic Search** | ❌ No | ❌ No | ✅ Yes |
| **Setup Time** | 5 min | 20 min | 15 min |
| **Persistence** | Browser only | 30 days | Configurable |
| **Best For** | Simple demos | Production | Enterprise |

---

## Recommendation

### For Your Use Case: **Client-Side Memory** ✅

**Why:**
1. **Zero cost** - No additional infrastructure
2. **Simple** - Just JavaScript code
3. **Fast** - No API calls for memory
4. **Sufficient** - Handles contextual references
5. **Easy to implement** - Copy-paste code

**When to upgrade:**
- Need multi-device access → Use DynamoDB
- Need semantic search → Use AgentCore Memory
- Need long-term persistence → Use DynamoDB

---

## Complete Updated chat.html

I'll create a complete version with client-side memory:

```html
<!-- Full implementation in next section -->
```

---

## Testing Memory

```
Conversation 1:
User: "What pets do you have?"
Agent: Lists 15 pets
Memory: Stores pet list

User: "Tell me about the first one"
Agent: Shows Buddy details ✅ (uses memory)

User: "What about the second?"
Agent: Shows Whiskers details ✅ (uses memory)

Conversation 2 (after logout/login):
User: "Tell me about the first one"
Agent: "Which pet?" ❌ (memory cleared)
```

---

## Summary

**Current:** No memory - each request is independent

**Recommended:** Client-side memory
- Cost: $0
- Complexity: Low
- Handles: "first one", "that pet", "it"
- Limitation: Lost on logout/refresh

**Alternative:** DynamoDB sessions
- Cost: $0.50/month
- Complexity: Medium
- Handles: Multi-device, persistence
- Limitation: Requires Lambda function

**Enterprise:** AgentCore Memory
- Cost: $2/month
- Complexity: Medium
- Handles: Semantic search, managed
- Limitation: Higher cost

---

## Next Steps

1. **Add client-side memory** to your chat.html (5 minutes)
2. **Test contextual queries** ("first one", "that pet")
3. **Upgrade to DynamoDB** if you need multi-device access
4. **Consider AgentCore Memory** for enterprise features
