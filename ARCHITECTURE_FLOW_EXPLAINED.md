# Complete Architecture Flow - Pet Store Chat

## YES, We ARE Using AgentCore Gateway! ✅

Here's the complete flow:

```
User Browser (web-chat-simple.html)
    ↓
    Types: "List all pets"
    ↓
JavaScript calls: callGateway(userMessage)
    ↓
Gets Cognito Access Token
    ↓
Calls AgentCore Gateway (MCP Protocol) ← YES, USING THIS!
    URL: https://petstoregateway-remqjziohl.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp
    ↓
AgentCore Gateway has Target: PetStoreTarget
    ↓
Target exposes 3 MCP Tools:
    • PetStoreTarget___ListPets
    • PetStoreTarget___GetPetById
    • PetStoreTarget___AddPet
    ↓
AgentCore Gateway calls API Gateway
    URL: https://66gd6g08ie.execute-api.us-east-1.amazonaws.com/prod
    ↓
API Gateway routes to Lambda Function
    Function: PetStoreFunction
    ↓
Lambda reads/writes DynamoDB
    Table: PetStore (18 pets)
    ↓
Response flows back through the chain
    ↓
User sees: "We have 18 pets: ..."
```

---

## Detailed Flow Breakdown

### 1. User Input
```
User types: "List all pets"
```

### 2. JavaScript in Browser
```javascript
async function callGateway(userMessage) {
    const token = await getToken();  // Get Cognito token
    
    // Call AgentCore Gateway with MCP protocol
    const res = await fetch(CONFIG.gatewayUrl, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            jsonrpc: '2.0',
            id: 1,
            method: 'tools/call',
            params: {
                name: 'PetStoreTarget___ListPets',  // MCP tool name
                arguments: {}
            }
        })
    });
}
```

### 3. AgentCore Gateway (MCP Protocol)
```
Gateway ID: petstoregateway-remqjziohl
Target ID: 89372YIO3X
Target Type: API Gateway

Configuration:
- Exposes API Gateway endpoints as MCP tools
- Handles authentication (Cognito)
- Converts MCP calls to HTTP requests
```

### 4. API Gateway
```
API ID: 66gd6g08ie
Stage: prod
Endpoints:
- GET  /pets       → Lambda (list all)
- GET  /pets/{id}  → Lambda (get one)
- POST /pets       → Lambda (add new)
```

### 5. Lambda Function
```python
def lambda_handler(event, context):
    if method == 'GET' and path == '/pets':
        # Scan DynamoDB
        response = table.scan()
        return items
    
    elif method == 'POST' and path == '/pets':
        # Add to DynamoDB
        table.put_item(Item=new_pet)
        return new_pet
```

### 6. DynamoDB
```
Table: PetStore
Items: 18 pets
Attributes: id, name, type, breed, age, price
```

---

## Why Use AgentCore Gateway?

### Without AgentCore Gateway (Direct API Call):
```javascript
// Would need to know exact API endpoints
fetch('https://66gd6g08ie.execute-api.us-east-1.amazonaws.com/prod/pets')

// Problems:
// - Hard-coded URLs
// - Manual endpoint management
// - No natural language understanding
// - Complex authentication
```

### With AgentCore Gateway (MCP Protocol):
```javascript
// Call tools by name, not URLs
fetch(gatewayUrl, {
    body: JSON.stringify({
        method: 'tools/call',
        params: {
            name: 'PetStoreTarget___ListPets'  // Tool name, not URL
        }
    })
})

// Benefits:
// ✅ Tools abstraction (name-based, not URL-based)
// ✅ MCP protocol standardization
// ✅ Centralized authentication
// ✅ Easy to add more tools
// ✅ Gateway handles routing
```

---

## AgentCore Gateway Configuration

### Gateway Details:
```json
{
  "gateway_id": "petstoregateway-remqjziohl",
  "gateway_url": "https://petstoregateway-remqjziohl.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp",
  "status": "READY",
  "authentication": "Cognito User Pool"
}
```

### Target Configuration:
```json
{
  "target_id": "89372YIO3X",
  "target_type": "API_GATEWAY",
  "api_gateway_id": "66gd6g08ie",
  "stage": "prod",
  "tools_exposed": [
    "PetStoreTarget___ListPets",
    "PetStoreTarget___GetPetById",
    "PetStoreTarget___AddPet"
  ]
}
```

### Tool Filters:
```json
{
  "toolFilters": [
    {
      "filterPath": "/pets",
      "methods": ["GET", "POST"]
    },
    {
      "filterPath": "/pets/*",
      "methods": ["GET"]
    }
  ]
}
```

---

## MCP Protocol Example

### Request to AgentCore Gateway:
```json
POST https://petstoregateway-remqjziohl.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp

Headers:
  Authorization: Bearer <cognito-token>
  Content-Type: application/json

Body:
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "PetStoreTarget___ListPets",
    "arguments": {}
  }
}
```

### AgentCore Gateway Translates To:
```
GET https://66gd6g08ie.execute-api.us-east-1.amazonaws.com/prod/pets
```

### Response from AgentCore Gateway:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "[{\"id\":1,\"name\":\"Buddy\",...}, ...]"
      }
    ]
  }
}
```

---

## Add Pet Flow (Detailed)

### User Action:
```
User types: "Add a dog named Rocky, breed: Bulldog, age: 2, price: $700"
```

### JavaScript Parsing:
```javascript
// Extract pet details from natural language
const nameMatch = userMessage.match(/name[d:\s]+([A-Z][a-z]+)/i);
// Result: "Rocky"

const typeMatch = userMessage.match(/\b(dog|cat|bird|fish)\b/i);
// Result: "dog"

const pet = {
    name: "Rocky",
    type: "dog",
    breed: "Bulldog",
    age: 2,
    price: 700
};
```

### Call AgentCore Gateway:
```javascript
fetch(CONFIG.gatewayUrl, {
    body: JSON.stringify({
        method: 'tools/call',
        params: {
            name: 'PetStoreTarget___AddPet',  // MCP tool
            arguments: pet                     // Pet data
        }
    })
})
```

### AgentCore Gateway → API Gateway:
```
POST https://66gd6g08ie.execute-api.us-east-1.amazonaws.com/prod/pets
Body: {"name":"Rocky","type":"dog","breed":"Bulldog","age":2,"price":700}
```

### Lambda → DynamoDB:
```python
# Generate next ID
next_id = 17

# Create pet
new_pet = {
    'id': 17,
    'name': 'Rocky',
    'type': 'dog',
    'breed': 'Bulldog',
    'age': 2,
    'price': 700
}

# Save to DynamoDB
table.put_item(Item=new_pet)
```

### Response Chain:
```
DynamoDB → Lambda → API Gateway → AgentCore Gateway → Browser
```

### User Sees:
```
✅ Added Rocky!

🐾 Rocky
Type: dog
Breed: Bulldog
Age: 2 years
Price: $700
```

---

## Key Components Summary

| Component | Purpose | ID/URL |
|-----------|---------|--------|
| **AgentCore Gateway** | MCP protocol handler | petstoregateway-remqjziohl |
| **Gateway Target** | API Gateway integration | 89372YIO3X |
| **API Gateway** | REST API endpoints | 66gd6g08ie |
| **Lambda Function** | Business logic | PetStoreFunction |
| **DynamoDB** | Data storage | PetStore (18 pets) |
| **Cognito User Pool** | Authentication | us-east-1_RNmMBC87g |
| **Web Interface** | User interface | petstore-chat-simple.html |

---

## Why This Architecture?

### Benefits:
1. **Abstraction**: Tools instead of URLs
2. **Standardization**: MCP protocol
3. **Security**: Centralized auth via Gateway
4. **Scalability**: Add more tools easily
5. **Flexibility**: Change backend without changing frontend
6. **Natural Language**: Gateway can work with AI models

### Example of Flexibility:
```
Want to add a new feature?

1. Add Lambda function
2. Add API Gateway endpoint
3. Update Gateway target filters
4. New MCP tool automatically available!

No frontend changes needed!
```

---

## Verification Commands

### Check Gateway:
```bash
aws bedrock-agentcore-control list-gateways --region us-east-1
```

### Check Target:
```bash
aws bedrock-agentcore-control list-targets \
  --gateway-id petstoregateway-remqjziohl \
  --region us-east-1
```

### Test MCP Call:
```bash
# Get token
TOKEN=$(aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id 435iqd7cgbn2slmgn0a36fo9lf \
  --auth-parameters USERNAME=testuser,PASSWORD=MySecurePass123! \
  --query 'AuthenticationResult.AccessToken' \
  --output text)

# Call Gateway
curl -X POST \
  https://petstoregateway-remqjziohl.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "PetStoreTarget___ListPets",
      "arguments": {}
    }
  }'
```

---

## Summary

**YES, we ARE using AgentCore Gateway!**

The complete flow is:
```
Browser → AgentCore Gateway (MCP) → API Gateway → Lambda → DynamoDB
```

AgentCore Gateway is the key component that:
- Exposes API Gateway as MCP tools
- Handles authentication
- Provides abstraction layer
- Enables natural language integration

This is a **production-ready architecture** using AWS serverless services with AgentCore Gateway as the intelligent routing layer! 🚀
