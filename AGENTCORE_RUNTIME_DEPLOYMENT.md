# Deploy Pet Store Chatbot to AgentCore Runtime

Complete guide to deploy the chatbot as a web-accessible chat interface with authentication, memory, and monitoring.

---

## Overview

This deployment will create:
- **AgentCore Runtime Agent** - Serverless chatbot deployment
- **AgentCore Memory** - Persistent conversation history
- **Cognito Authentication** - Secure user login
- **CloudWatch Monitoring** - Logs and metrics
- **Web Chat Interface** - Accessible via URL

---

## Architecture

```
User (Browser) → Cognito Auth → AgentCore Runtime Agent → AgentCore Gateway → API Gateway → Lambda → DynamoDB
                                        ↓
                                 AgentCore Memory
                                        ↓
                                 CloudWatch Logs
```

---

## Prerequisites

1. **Existing Infrastructure** (from previous deployment):
   - DynamoDB table: PetStore
   - Lambda function: PetStoreFunction
   - API Gateway: 66gd6g08ie
   - AgentCore Gateway: petstoregateway-remqjziohl
   - Cognito User Pool: us-east-1_RNmMBC87g

2. **New Requirements**:
   - AWS CLI configured
   - Python 3.8+
   - AgentCore CLI installed

---

## Step 1: Install AgentCore CLI

```bash
# Install AgentCore CLI
pip install agentcore-cli

# Verify installation
agentcore --version
```

---

## Step 2: Prepare Agent Code

Create `agent_runtime.py`:

```python
"""
Pet Store Agent for AgentCore Runtime
Supports natural language queries with persistent memory
"""

import json
import httpx
from strands import Agent
from strands.tools import tool

# Configuration from environment variables
import os
GATEWAY_URL = os.environ['GATEWAY_URL']
ACCESS_TOKEN = os.environ['ACCESS_TOKEN']

# MCP Client
mcp_client = httpx.Client(
    base_url=GATEWAY_URL,
    headers={
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    },
    timeout=30.0
)

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

# Create agent
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

# Handler for AgentCore Runtime
def handler(event, context):
    """
    AgentCore Runtime handler
    Processes user messages and returns agent responses
    """
    # Extract user message
    user_message = event.get('message', '')
    session_id = event.get('session_id', 'default')
    
    # Process with agent
    response = agent(user_message)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'response': response,
            'session_id': session_id
        })
    }
```

---

## Step 3: Create AgentCore Memory

```bash
# Create memory store for conversation history
aws bedrock-agentcore-control create-memory \
  --name PetStoreMemory \
  --description "Conversation history for Pet Store chatbot" \
  --memory-type SEMANTIC \
  --region us-east-1

# Save memory ID
MEMORY_ID=$(aws bedrock-agentcore-control list-memories \
  --query 'memories[?name==`PetStoreMemory`].memoryId' \
  --output text)

echo "Memory ID: $MEMORY_ID"
```

---

## Step 4: Create AgentCore Runtime Agent

Create `agent-config.json`:

```json
{
  "agentName": "PetStoreAgent",
  "description": "AI-powered pet store assistant with natural language interface",
  "instruction": "You are a helpful pet store assistant that helps customers browse pets, get details, and add new pets.",
  "foundationModel": "anthropic.claude-3-5-sonnet-20241022-v2:0",
  "memoryConfiguration": {
    "memoryId": "MEMORY_ID_HERE",
    "enabledMemoryTypes": ["SESSION_SUMMARY"]
  },
  "guardrailConfiguration": {
    "guardrailIdentifier": "OPTIONAL_GUARDRAIL_ID",
    "guardrailVersion": "DRAFT"
  }
}
```

Deploy agent:

```bash
# Create agent
aws bedrock-agentcore-control create-agent \
  --cli-input-json file://agent-config.json \
  --region us-east-1

# Get agent ID
AGENT_ID=$(aws bedrock-agentcore-control list-agents \
  --query 'agents[?agentName==`PetStoreAgent`].agentId' \
  --output text)

echo "Agent ID: $AGENT_ID"
```

---

## Step 5: Deploy Agent Code

Create `requirements.txt`:

```
strands-agents>=0.1.0
httpx>=0.24.0
```

Package and deploy:

```bash
# Create deployment package
mkdir -p deployment
cp agent_runtime.py deployment/
cp requirements.txt deployment/
cd deployment

# Install dependencies
pip install -r requirements.txt -t .

# Create zip
zip -r ../agent-deployment.zip .
cd ..

# Upload to S3
aws s3 cp agent-deployment.zip s3://YOUR-BUCKET/agent-deployment.zip

# Update agent with code
aws bedrock-agentcore-control update-agent \
  --agent-id $AGENT_ID \
  --agent-resource-role-arn arn:aws:iam::ACCOUNT_ID:role/AgentCoreRuntimeRole \
  --region us-east-1
```

---

## Step 6: Configure Authentication

### Option A: Cognito User Pool (Recommended)

Use existing Cognito User Pool:

```bash
# Get User Pool details
USER_POOL_ID="us-east-1_RNmMBC87g"
CLIENT_ID="435iqd7cgbn2slmgn0a36fo9lf"

# Create app client for web interface
aws cognito-idp create-user-pool-client \
  --user-pool-id $USER_POOL_ID \
  --client-name PetStoreChatWeb \
  --generate-secret \
  --allowed-o-auth-flows authorization_code implicit \
  --allowed-o-auth-scopes openid email profile \
  --callback-urls https://YOUR-DOMAIN/callback \
  --logout-urls https://YOUR-DOMAIN/logout \
  --supported-identity-providers COGNITO

# Save new client ID
WEB_CLIENT_ID=$(aws cognito-idp list-user-pool-clients \
  --user-pool-id $USER_POOL_ID \
  --query 'UserPoolClients[?ClientName==`PetStoreChatWeb`].ClientId' \
  --output text)
```

### Option B: IAM Authentication

```bash
# Create IAM role for authenticated users
aws iam create-role \
  --role-name PetStoreChatUserRole \
  --assume-role-policy-document file://user-trust-policy.json

# Attach policy
aws iam put-role-policy \
  --role-name PetStoreChatUserRole \
  --policy-name InvokeAgentPolicy \
  --policy-document file://invoke-agent-policy.json
```

---

## Step 7: Create Web Chat Interface

Create `chat-interface.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pet Store AI Assistant</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .login-container {
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            width: 400px;
        }
        
        .chat-container {
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            width: 800px;
            height: 600px;
            display: none;
            flex-direction: column;
        }
        
        .chat-header {
            background: #667eea;
            color: white;
            padding: 20px;
            border-radius: 10px 10px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f5f5f5;
        }
        
        .message {
            margin-bottom: 15px;
            padding: 10px 15px;
            border-radius: 10px;
            max-width: 70%;
        }
        
        .user-message {
            background: #667eea;
            color: white;
            margin-left: auto;
        }
        
        .agent-message {
            background: white;
            color: #333;
        }
        
        .chat-input {
            display: flex;
            padding: 20px;
            border-top: 1px solid #ddd;
        }
        
        input[type="text"], input[type="password"] {
            flex: 1;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        
        button {
            padding: 12px 24px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            margin-left: 10px;
        }
        
        button:hover {
            background: #5568d3;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 5px;
            color: #333;
            font-weight: 500;
        }
        
        h2 {
            margin-bottom: 30px;
            color: #333;
            text-align: center;
        }
        
        .error {
            color: #e74c3c;
            font-size: 12px;
            margin-top: 5px;
        }
        
        .logout-btn {
            background: #e74c3c;
            padding: 8px 16px;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <!-- Login Form -->
    <div class="login-container" id="loginContainer">
        <h2>🐾 Pet Store AI Assistant</h2>
        <form id="loginForm">
            <div class="form-group">
                <label for="username">Username</label>
                <input type="text" id="username" required>
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" required>
            </div>
            <div class="error" id="loginError"></div>
            <button type="submit">Login</button>
        </form>
    </div>

    <!-- Chat Interface -->
    <div class="chat-container" id="chatContainer">
        <div class="chat-header">
            <h3>🐾 Pet Store AI Assistant</h3>
            <button class="logout-btn" onclick="logout()">Logout</button>
        </div>
        <div class="chat-messages" id="chatMessages"></div>
        <div class="chat-input">
            <input type="text" id="messageInput" placeholder="Ask me about pets..." onkeypress="handleKeyPress(event)">
            <button onclick="sendMessage()">Send</button>
        </div>
    </div>

    <script>
        // Configuration
        const CONFIG = {
            cognitoUserPoolId: 'us-east-1_RNmMBC87g',
            cognitoClientId: 'WEB_CLIENT_ID_HERE',
            agentId: 'AGENT_ID_HERE',
            region: 'us-east-1'
        };

        let accessToken = null;
        let sessionId = generateSessionId();

        // Generate session ID
        function generateSessionId() {
            return 'session-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
        }

        // Login
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            try {
                // Authenticate with Cognito
                const response = await fetch(`https://cognito-idp.${CONFIG.region}.amazonaws.com/`, {
                    method: 'POST',
                    headers: {
                        'X-Amz-Target': 'AWSCognitoIdentityProviderService.InitiateAuth',
                        'Content-Type': 'application/x-amz-json-1.1'
                    },
                    body: JSON.stringify({
                        AuthFlow: 'USER_PASSWORD_AUTH',
                        ClientId: CONFIG.cognitoClientId,
                        AuthParameters: {
                            USERNAME: username,
                            PASSWORD: password
                        }
                    })
                });

                const data = await response.json();
                
                if (data.AuthenticationResult) {
                    accessToken = data.AuthenticationResult.AccessToken;
                    showChat();
                } else {
                    document.getElementById('loginError').textContent = 'Invalid credentials';
                }
            } catch (error) {
                document.getElementById('loginError').textContent = 'Login failed: ' + error.message;
            }
        });

        // Show chat interface
        function showChat() {
            document.getElementById('loginContainer').style.display = 'none';
            document.getElementById('chatContainer').style.display = 'flex';
            addMessage('agent', 'Hello! I\'m your Pet Store AI Assistant. How can I help you today?');
        }

        // Send message
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            // Add user message
            addMessage('user', message);
            input.value = '';
            
            // Show typing indicator
            const typingId = addMessage('agent', 'Typing...');
            
            try {
                // Call AgentCore Runtime
                const response = await fetch(`https://bedrock-agentcore-runtime.${CONFIG.region}.amazonaws.com/agents/${CONFIG.agentId}/sessions/${sessionId}/text`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${accessToken}`,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        inputText: message,
                        enableTrace: false
                    })
                });

                const data = await response.json();
                
                // Remove typing indicator
                document.getElementById(typingId).remove();
                
                // Add agent response
                if (data.completion) {
                    addMessage('agent', data.completion);
                } else {
                    addMessage('agent', 'Sorry, I encountered an error. Please try again.');
                }
            } catch (error) {
                document.getElementById(typingId).remove();
                addMessage('agent', 'Error: ' + error.message);
            }
        }

        // Add message to chat
        function addMessage(type, text) {
            const messagesDiv = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            const messageId = 'msg-' + Date.now();
            
            messageDiv.id = messageId;
            messageDiv.className = `message ${type}-message`;
            messageDiv.textContent = text;
            
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            
            return messageId;
        }

        // Handle Enter key
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }

        // Logout
        function logout() {
            accessToken = null;
            sessionId = generateSessionId();
            document.getElementById('chatMessages').innerHTML = '';
            document.getElementById('chatContainer').style.display = 'none';
            document.getElementById('loginContainer').style.display = 'block';
            document.getElementById('username').value = '';
            document.getElementById('password').value = '';
        }
    </script>
</body>
</html>
```

---

## Step 8: Deploy Web Interface

### Option A: S3 + CloudFront

```bash
# Create S3 bucket for website
aws s3 mb s3://petstore-chat-interface

# Enable static website hosting
aws s3 website s3://petstore-chat-interface \
  --index-document chat-interface.html

# Upload HTML file
aws s3 cp chat-interface.html s3://petstore-chat-interface/

# Create CloudFront distribution
aws cloudfront create-distribution \
  --origin-domain-name petstore-chat-interface.s3.amazonaws.com \
  --default-root-object chat-interface.html

# Get CloudFront URL
CLOUDFRONT_URL=$(aws cloudfront list-distributions \
  --query 'DistributionList.Items[0].DomainName' \
  --output text)

echo "Chat Interface URL: https://$CLOUDFRONT_URL"
```

### Option B: Amplify Hosting

```bash
# Initialize Amplify app
amplify init

# Add hosting
amplify add hosting

# Publish
amplify publish
```

---

## Step 9: Configure Monitoring

```bash
# Enable CloudWatch Logs for AgentCore Runtime
aws logs create-log-group \
  --log-group-name /aws/bedrock-agentcore/agents/$AGENT_ID

# Create CloudWatch Dashboard
aws cloudwatch put-dashboard \
  --dashboard-name PetStoreAgentDashboard \
  --dashboard-body file://dashboard-config.json
```

Create `dashboard-config.json`:

```json
{
  "widgets": [
    {
      "type": "metric",
      "properties": {
        "metrics": [
          ["AWS/BedrockAgentCore", "Invocations", {"stat": "Sum"}],
          [".", "Errors", {"stat": "Sum"}],
          [".", "Duration", {"stat": "Average"}]
        ],
        "period": 300,
        "stat": "Average",
        "region": "us-east-1",
        "title": "Agent Metrics"
      }
    },
    {
      "type": "log",
      "properties": {
        "query": "SOURCE '/aws/bedrock-agentcore/agents/$AGENT_ID' | fields @timestamp, @message | sort @timestamp desc | limit 20",
        "region": "us-east-1",
        "title": "Recent Logs"
      }
    }
  ]
}
```

---

## Step 10: Test Deployment

```bash
# Test agent invocation
aws bedrock-agentcore-runtime invoke-agent \
  --agent-id $AGENT_ID \
  --session-id test-session \
  --input-text "What pets do you have?" \
  --region us-east-1
```

---

## Complete Deployment Script

Create `deploy-runtime.sh`:

```bash
#!/bin/bash

set -e

echo "🚀 Deploying Pet Store Agent to AgentCore Runtime..."

# Variables
REGION="us-east-1"
AGENT_NAME="PetStoreAgent"
MEMORY_NAME="PetStoreMemory"
BUCKET_NAME="petstore-agent-deployment"

# Step 1: Create Memory
echo "📝 Creating AgentCore Memory..."
MEMORY_ID=$(aws bedrock-agentcore-control create-memory \
  --name $MEMORY_NAME \
  --description "Conversation history for Pet Store chatbot" \
  --memory-type SEMANTIC \
  --region $REGION \
  --query 'memoryId' \
  --output text)

echo "Memory ID: $MEMORY_ID"

# Step 2: Create Agent
echo "🤖 Creating AgentCore Runtime Agent..."
AGENT_ID=$(aws bedrock-agentcore-control create-agent \
  --agent-name $AGENT_NAME \
  --description "AI-powered pet store assistant" \
  --foundation-model "anthropic.claude-3-5-sonnet-20241022-v2:0" \
  --instruction "You are a helpful pet store assistant" \
  --region $REGION \
  --query 'agentId' \
  --output text)

echo "Agent ID: $AGENT_ID"

# Step 3: Package and upload code
echo "📦 Packaging agent code..."
mkdir -p deployment
cp agent_runtime.py deployment/
cp requirements.txt deployment/
cd deployment
pip install -r requirements.txt -t .
zip -r ../agent-deployment.zip .
cd ..

# Upload to S3
aws s3 mb s3://$BUCKET_NAME 2>/dev/null || true
aws s3 cp agent-deployment.zip s3://$BUCKET_NAME/

# Step 4: Deploy web interface
echo "🌐 Deploying web interface..."
aws s3 mb s3://petstore-chat-interface 2>/dev/null || true
aws s3 website s3://petstore-chat-interface --index-document chat-interface.html
aws s3 cp chat-interface.html s3://petstore-chat-interface/

# Step 5: Get URLs
WEBSITE_URL="http://petstore-chat-interface.s3-website-$REGION.amazonaws.com"

echo ""
echo "✅ Deployment Complete!"
echo ""
echo "Agent ID: $AGENT_ID"
echo "Memory ID: $MEMORY_ID"
echo "Chat Interface: $WEBSITE_URL"
echo ""
echo "Next steps:"
echo "1. Update chat-interface.html with Agent ID"
echo "2. Configure Cognito callback URLs"
echo "3. Test the chat interface"
```

---

## Usage

### For End Users:

1. Navigate to chat interface URL
2. Login with Cognito credentials
3. Start chatting with the AI assistant
4. Ask about pets, get details, add new pets

### Example Queries:

```
"What pets do you have?"
"Tell me about the cat"
"Add a parrot named Rio for $79.99"
"What's the cheapest pet?"
"Show me all dogs"
```

---

## Monitoring & Maintenance

### View Logs:

```bash
# View agent logs
aws logs tail /aws/bedrock-agentcore/agents/$AGENT_ID --follow

# View memory logs
aws logs tail /aws/bedrock-agentcore/memory/$MEMORY_ID --follow
```

### View Metrics:

```bash
# Get invocation count
aws cloudwatch get-metric-statistics \
  --namespace AWS/BedrockAgentCore \
  --metric-name Invocations \
  --dimensions Name=AgentId,Value=$AGENT_ID \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Sum
```

### Update Agent:

```bash
# Update agent code
aws bedrock-agentcore-control update-agent \
  --agent-id $AGENT_ID \
  --instruction "Updated instructions..." \
  --region us-east-1
```

---

## Cost Estimate

Monthly costs (1000 conversations):
- AgentCore Runtime: ~$10
- AgentCore Memory: ~$2
- Cognito: Free (under 50K MAU)
- S3 + CloudFront: ~$1
- CloudWatch: ~$1
- **Total: ~$14/month**

---

## Security Best Practices

1. **Authentication**: Always use Cognito or IAM
2. **HTTPS Only**: Enforce SSL/TLS
3. **Token Expiry**: Implement token refresh
4. **Rate Limiting**: Configure API throttling
5. **Input Validation**: Sanitize user inputs
6. **Monitoring**: Enable CloudWatch alarms

---

## Troubleshooting

### Issue: "Unauthorized" error
→ Check Cognito token is valid and not expired

### Issue: Agent not responding
→ Check CloudWatch logs for errors

### Issue: Memory not persisting
→ Verify memory ID is correct in agent config

### Issue: Web interface not loading
→ Check S3 bucket permissions and CORS settings

---

## Next Steps

1. **Custom Domain**: Add Route53 domain
2. **SSL Certificate**: Use ACM for HTTPS
3. **Advanced Memory**: Configure semantic search
4. **Guardrails**: Add content filtering
5. **Analytics**: Track user interactions

---

## Resources

- [AgentCore Runtime Docs](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/runtime.html)
- [AgentCore Memory Docs](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/memory.html)
- [Cognito Authentication](https://docs.aws.amazon.com/cognito/latest/developerguide/)
- [CloudWatch Monitoring](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/)
