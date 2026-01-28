# Demo Instructions

Quick guide to demonstrate the working integration.

## Prerequisites
- All infrastructure deployed (run `deploy.py` if not)
- Fresh ACCESS token generated

## Demo Flow

### 1. Show Architecture
```
User Query → AI Agent → AgentCore Gateway (MCP) → API Gateway → Lambda
                              ↓
                       Cognito AUTH
```

### 2. Generate Token
```bash
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id $(jq -r .client_id deployment-config.json) \
  --auth-parameters USERNAME=testuser,PASSWORD=MySecurePass123! \
  --query 'AuthenticationResult.AccessToken' \
  --output text > access-token.txt

echo "✅ Token generated"
```

### 3. Demo MCP Protocol
```bash
python3 test-final.py
```

**What it shows**:
- ✅ MCP protocol communication
- ✅ Tool discovery (3 tools found)
- ✅ Tool invocation with parameters
- ✅ API Gateway integration working

**Expected output**:
```
[TEST 1] Listing available tools via MCP protocol...
   ✅ SUCCESS! Found 3 tools:
      - x_amz_bedrock_agentcore_search
      - PetStoreTarget___GetPetById
      - PetStoreTarget___ListPets

[TEST 2] Calling PetStoreTarget___ListPets tool...
   ✅ SUCCESS!
   Pets returned: [
     {"id": 1, "type": "dog", "name": "Buddy", "price": 249.99},
     {"id": 2, "type": "cat", "name": "Whiskers", "price": 124.99},
     {"id": 3, "type": "fish", "name": "Nemo", "price": 0.99}
   ]

[TEST 3] Calling PetStoreTarget___GetPetById tool (petId=2)...
   ✅ SUCCESS!
   Pet details: {
     "id": 2,
     "type": "cat",
     "name": "Whiskers",
     "price": 124.99
   }
```

### 4. Demo AI Chatbot
```bash
python3 chatbot-final.py
```

**What it shows**:
- ✅ Natural language understanding
- ✅ AI agent using tools automatically
- ✅ Context-aware responses
- ✅ Complete end-to-end workflow

**Expected output**:
```
🤖 AI Pet Store Assistant

[Query 1] What pets do you have available?
Great! We currently have 3 wonderful pets available:
🐕 Buddy - Dog (ID: 1) - $249.99
🐱 Whiskers - Cat (ID: 2) - $124.99  
🐠 Nemo - Fish (ID: 3) - $0.99

[Query 2] Tell me about pet ID 2
Here are the details about Whiskers (Pet ID: 2):
🐱 Name: Whiskers
Type: Cat
Price: $124.99

[Query 3] What's the cheapest pet?
The cheapest pet is Nemo the fish at only $0.99!
```

## Key Points to Highlight

### 1. MCP Protocol
- Standard protocol for AI tool integration
- JSON-RPC 2.0 based
- Tool discovery and invocation

### 2. AgentCore Gateway
- Managed MCP server
- Handles authentication
- Exposes API Gateway as tools

### 3. API Gateway Integration
- Existing APIs become AI tools
- No code changes needed
- Automatic OpenAPI parsing

### 4. Authentication
- Cognito JWT (ACCESS token)
- Secure, managed authentication
- Token-based access control

### 5. AI Agent
- Strands framework
- Natural language queries
- Automatic tool selection

## Troubleshooting During Demo

### Token expired
```bash
# Regenerate (takes 2 seconds)
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id $(jq -r .client_id deployment-config.json) \
  --auth-parameters USERNAME=testuser,PASSWORD=MySecurePass123! \
  --query 'AuthenticationResult.AccessToken' \
  --output text > access-token.txt
```

### Check status
```bash
# Gateway status
aws bedrock-agentcore-control get-gateway \
  --gateway-identifier $(jq -r .gateway_id deployment-config.json) \
  --query 'status' --output text

# Target status
aws bedrock-agentcore-control get-gateway-target \
  --gateway-identifier $(jq -r .gateway_id deployment-config.json) \
  --target-id $(jq -r .target_id deployment-config.json) \
  --query 'status' --output text
```

Both should return: `READY`

## Q&A Preparation

**Q: Why use AgentCore Gateway instead of direct Lambda calls?**
A: Gateway provides:
- Standard MCP protocol
- Managed authentication
- Tool discovery
- Multi-target support
- Observability

**Q: Can I use my existing APIs?**
A: Yes! Any API Gateway REST API can be integrated as a target.

**Q: What about security?**
A: Multiple layers:
- Cognito JWT authentication
- IAM role-based API access
- Gateway-level authorization
- API Gateway resource policies

**Q: How does it scale?**
A: All components are serverless and auto-scale:
- Lambda: Concurrent executions
- API Gateway: Unlimited requests
- AgentCore Gateway: Managed scaling

**Q: What's the cost?**
A: Pay-per-use:
- Lambda: $0.20 per 1M requests
- API Gateway: $3.50 per 1M requests
- AgentCore Gateway: Based on usage
- Cognito: Free tier available

**Q: Can I add more tools?**
A: Yes! Add more API endpoints and they automatically become tools.

## Demo Variations

### Show Tool Discovery
```python
import httpx, json

with open('deployment-config.json') as f:
    config = json.load(f)
with open('access-token.txt') as f:
    token = f.read().strip()

r = httpx.post(
    config['gateway_url'],
    headers={"Authorization": f"Bearer {token}"},
    json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"}
)
print(json.dumps(r.json(), indent=2))
```

### Show Direct Tool Call
```python
r = httpx.post(
    config['gateway_url'],
    headers={"Authorization": f"Bearer {token}"},
    json={
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "PetStoreTarget___ListPets",
            "arguments": {}
        }
    }
)
print(json.dumps(r.json(), indent=2))
```

### Show Custom Query
Modify `chatbot-final.py` to accept user input:
```python
while True:
    query = input("\nYou: ")
    if query.lower() == 'quit':
        break
    response = agent(query)
    print(f"Assistant: {response}")
```

## Cleanup After Demo
```bash
python cleanup.py
```

Removes all resources and stops charges.
