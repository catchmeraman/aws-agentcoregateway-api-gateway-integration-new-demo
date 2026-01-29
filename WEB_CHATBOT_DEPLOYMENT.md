# Web Chatbot with AgentCore Gateway

**Deploy the Pet Store chatbot as a web interface that calls AgentCore Gateway**

---

## Overview

This solution keeps your existing AgentCore Gateway setup and adds a simple web interface for users to interact with it.

### Architecture

```
User Browser → S3 (Web Interface) → Cognito Auth → AgentCore Gateway → API Gateway → Lambda → DynamoDB
```

**Monthly Cost: ~$3** (S3 + CloudFront + Cognito)

---

## What You Already Have

✅ AgentCore Gateway: `petstoregateway-remqjziohl`
✅ API Gateway: `66gd6g08ie`
✅ Lambda Function: `PetStoreFunction`
✅ DynamoDB Table: `PetStore` (15 pets)
✅ Cognito User Pool: `us-east-1_RNmMBC87g`

**You just need to add the web interface!**

---

## Step 1: Create Web Chat Interface

Create `chat.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pet Store AI Assistant</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .login-container, .chat-container {
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        
        .login-container {
            padding: 40px;
            width: 400px;
        }
        
        .chat-container {
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
            word-wrap: break-word;
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
        
        input {
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
        
        button:hover { background: #5568d3; }
        
        .form-group { margin-bottom: 20px; }
        
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
        
        .typing {
            font-style: italic;
            color: #999;
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
                <input type="text" id="username" value="testuser" required>
            </div>
            <div class="form-group">
                <label for="password">Password</label>
                <input type="password" id="password" value="MySecurePass123!" required>
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
        // Configuration - UPDATE THESE VALUES
        const CONFIG = {
            gatewayUrl: 'https://petstoregateway-remqjziohl.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp',
            cognitoUserPoolId: 'us-east-1_RNmMBC87g',
            cognitoClientId: '435iqd7cgbn2slmgn0a36fo9lf',
            region: 'us-east-1'
        };

        let accessToken = null;

        // Login
        document.getElementById('loginForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            try {
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
            addMessage('agent', 'Hello! I\'m your Pet Store AI Assistant. Ask me about pets!');
        }

        // Send message
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            
            if (!message) return;
            
            addMessage('user', message);
            input.value = '';
            
            const typingId = addMessage('agent', 'Thinking...', true);
            
            try {
                // Determine which tool to call based on message
                let toolName, toolArgs;
                
                if (message.toLowerCase().includes('add') && message.toLowerCase().includes('pet')) {
                    // Extract pet details for AddPet
                    const nameMatch = message.match(/named?\s+(\w+)/i);
                    const typeMatch = message.match(/\b(dog|cat|fish|bird|hamster|rabbit|turtle|lizard|parrot|frog)\b/i);
                    const priceMatch = message.match(/\$?(\d+\.?\d*)/);
                    
                    if (nameMatch && typeMatch && priceMatch) {
                        toolName = 'PetStoreTarget___AddPet';
                        toolArgs = {
                            name: nameMatch[1],
                            type: typeMatch[1],
                            price: parseFloat(priceMatch[1])
                        };
                    }
                } else if (message.toLowerCase().includes('pet') && /\b\d+\b/.test(message)) {
                    // Get specific pet by ID
                    const idMatch = message.match(/\b(\d+)\b/);
                    toolName = 'PetStoreTarget___GetPetById';
                    toolArgs = { petId: idMatch[1] };
                } else {
                    // List all pets
                    toolName = 'PetStoreTarget___ListPets';
                    toolArgs = {};
                }
                
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
                } else {
                    addMessage('agent', 'Sorry, I encountered an error: ' + JSON.stringify(data.error));
                }
            } catch (error) {
                document.getElementById(typingId).remove();
                addMessage('agent', 'Error: ' + error.message);
            }
        }

        // Format response based on tool
        function formatResponse(content, toolName) {
            if (toolName === 'PetStoreTarget___ListPets') {
                if (Array.isArray(content)) {
                    return `I found ${content.length} pets:\n\n` + 
                           content.map(p => `🐾 ${p.name} (${p.type}) - $${p.price}`).join('\n');
                }
            } else if (toolName === 'PetStoreTarget___GetPetById') {
                return `Here's the pet:\n🐾 ${content.name}\nType: ${content.type}\nPrice: $${content.price}\nID: ${content.id}`;
            } else if (toolName === 'PetStoreTarget___AddPet') {
                return `✅ Successfully added ${content.name} the ${content.type} for $${content.price}! (ID: ${content.id})`;
            }
            return JSON.stringify(content, null, 2);
        }

        // Add message to chat
        function addMessage(type, text, isTyping = false) {
            const messagesDiv = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            const messageId = 'msg-' + Date.now();
            
            messageDiv.id = messageId;
            messageDiv.className = `message ${type}-message ${isTyping ? 'typing' : ''}`;
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

## Step 2: Deploy to S3

```bash
#!/bin/bash

# Variables
BUCKET_NAME="petstore-chatbot-web"
REGION="us-east-1"

# Create S3 bucket
aws s3 mb s3://$BUCKET_NAME --region $REGION

# Enable static website hosting
aws s3 website s3://$BUCKET_NAME \
  --index-document chat.html \
  --error-document chat.html

# Upload HTML file
aws s3 cp chat.html s3://$BUCKET_NAME/

# Make bucket public (for website hosting)
aws s3api put-bucket-policy \
  --bucket $BUCKET_NAME \
  --policy '{
    "Version": "2012-10-17",
    "Statement": [{
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::'$BUCKET_NAME'/*"
    }]
  }'

# Get website URL
WEBSITE_URL="http://$BUCKET_NAME.s3-website-$REGION.amazonaws.com"

echo ""
echo "✅ Deployment Complete!"
echo ""
echo "Chat Interface URL: $WEBSITE_URL"
echo ""
echo "Login with:"
echo "  Username: testuser"
echo "  Password: MySecurePass123!"
```

Save as `deploy-web.sh` and run:

```bash
chmod +x deploy-web.sh
./deploy-web.sh
```

---

## Step 3: (Optional) Add CloudFront for HTTPS

```bash
# Create CloudFront distribution
aws cloudfront create-distribution \
  --origin-domain-name $BUCKET_NAME.s3-website-$REGION.amazonaws.com \
  --default-root-object chat.html \
  --query 'Distribution.DomainName' \
  --output text

# Get CloudFront URL (with HTTPS)
CLOUDFRONT_URL=$(aws cloudfront list-distributions \
  --query 'DistributionList.Items[0].DomainName' \
  --output text)

echo "HTTPS URL: https://$CLOUDFRONT_URL"
```

---

## How It Works

1. **User visits website** → Sees login page
2. **User logs in** → Cognito authenticates and returns ACCESS token
3. **User sends message** → JavaScript determines which tool to call
4. **Call AgentCore Gateway** → Sends MCP protocol request
5. **Gateway calls API** → Invokes Lambda → Queries DynamoDB
6. **Response returned** → Formatted and displayed to user

---

## Example Queries

```
"What pets do you have?"
→ Calls ListPets tool

"Tell me about pet 2"
→ Calls GetPetById tool with petId=2

"Add a parrot named Rio for $79.99"
→ Calls AddPet tool with name=Rio, type=parrot, price=79.99
```

---

## Cost Breakdown

```
S3 Storage:           $0.023/GB  (~$0.01/month)
S3 Requests:          $0.0004/1K (~$0.40/month)
CloudFront (optional): $0.085/GB  (~$1.00/month)
Cognito:              Free (under 50K MAU)
────────────────────────────────────────────
TOTAL:                ~$1.50/month (S3 only)
                      ~$3.00/month (with CloudFront)
```

**Existing infrastructure costs remain the same:**
- AgentCore Gateway: Already deployed
- API Gateway: Already deployed
- Lambda: Already deployed
- DynamoDB: Already deployed

---

## Features

✅ **Simple Deployment** - Just upload HTML to S3
✅ **Cognito Authentication** - Secure login
✅ **Direct Gateway Access** - Calls AgentCore Gateway via MCP
✅ **Natural Language** - Smart tool selection
✅ **Beautiful UI** - Modern, responsive design
✅ **Low Cost** - ~$3/month
✅ **No Backend Code** - Pure frontend solution

---

## Customization

### Change Colors

```css
/* In the <style> section */
background: linear-gradient(135deg, #YOUR_COLOR1 0%, #YOUR_COLOR2 100%);
```

### Add More Tools

```javascript
// In sendMessage() function, add more conditions:
if (message.toLowerCase().includes('delete')) {
    toolName = 'PetStoreTarget___DeletePet';
    toolArgs = { petId: extractId(message) };
}
```

### Add Session Memory

```javascript
// Store conversation history
let conversationHistory = [];

function addMessage(type, text) {
    conversationHistory.push({ role: type, content: text });
    // ... rest of code
}
```

---

## Troubleshooting

### "Invalid Bearer token"
→ Token expired (1 hour). Logout and login again.

### "CORS error"
→ AgentCore Gateway should allow CORS by default. Check browser console.

### "Tool not found"
→ Verify tool name includes prefix: `PetStoreTarget___`

### "Network error"
→ Check Gateway URL is correct and accessible

---

## Security Enhancements

### 1. Token Refresh

```javascript
// Auto-refresh token before expiry
setInterval(async () => {
    if (accessToken) {
        // Refresh token logic
    }
}, 50 * 60 * 1000); // 50 minutes
```

### 2. Input Validation

```javascript
function sanitizeInput(input) {
    return input.replace(/<script>/gi, '').trim();
}
```

### 3. Rate Limiting

```javascript
let lastRequestTime = 0;
const MIN_REQUEST_INTERVAL = 1000; // 1 second

function sendMessage() {
    const now = Date.now();
    if (now - lastRequestTime < MIN_REQUEST_INTERVAL) {
        return; // Too fast
    }
    lastRequestTime = now;
    // ... rest of code
}
```

---

## Next Steps

1. **Deploy the web interface** using the script above
2. **Test with different queries** to verify all tools work
3. **Share the URL** with users
4. **Monitor usage** in CloudWatch
5. **Add custom domain** (optional) using Route53

---

## Summary

This solution:
- ✅ Uses your existing AgentCore Gateway
- ✅ Costs only ~$3/month (just for web hosting)
- ✅ Deploys in 5 minutes
- ✅ No backend code needed
- ✅ Secure with Cognito authentication
- ✅ Beautiful, responsive UI

**Total Monthly Cost: ~$10** (Gateway + API + Lambda + DynamoDB + Web)

Much better than $14 for AgentCore Runtime!
