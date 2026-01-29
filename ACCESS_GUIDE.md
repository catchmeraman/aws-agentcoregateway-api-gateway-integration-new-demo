# 🎉 WEB INTERFACE ACCESS GUIDE

## 🌐 Live Demo URL

**Primary Access:**
```
http://petstore-chat-web.s3-website-us-east-1.amazonaws.com
```

**Alternative (Local):**
```
file:///Users/ramandeep_chandna/agentcore-gateway-demo/web-chat-with-memory.html
```

---

## 🔑 Credentials & Configuration

### AWS Resources
```json
{
  "region": "us-east-1",
  "account_id": "114805761158",
  
  "memory": {
    "memory_id": "PetStoreChatMemory-Zhm3u49PiK",
    "status": "ACTIVE",
    "type": "Persistent conversation storage"
  },
  
  "authentication": {
    "user_pool_id": "us-east-1_RNmMBC87g",
    "client_id": "435iqd7cgbn2slmgn0a36fo9lf",
    "identity_pool_id": "us-east-1:beef0a8b-da2e-4da4-8282-37455aaa57e7",
    "test_user": "testuser",
    "test_password": "MySecurePass123!"
  },
  
  "gateway": {
    "gateway_id": "petstoregateway-remqjziohl",
    "gateway_url": "https://petstoregateway-remqjziohl.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp",
    "target_id": "89372YIO3X"
  },
  
  "backend": {
    "api_gateway_id": "66gd6g08ie",
    "api_endpoint": "https://66gd6g08ie.execute-api.us-east-1.amazonaws.com/prod",
    "lambda_function": "PetStoreFunction",
    "dynamodb_table": "PetStore"
  }
}
```

---

## 🚀 Quick Start

### Option 1: S3 Static Website (Recommended)

**Step 1: Create S3 Bucket**
```bash
aws s3 mb s3://petstore-chat-web --region us-east-1
```

**Step 2: Enable Static Website Hosting**
```bash
aws s3 website s3://petstore-chat-web \
  --index-document web-chat-with-memory.html \
  --region us-east-1
```

**Step 3: Upload File**
```bash
cd /Users/ramandeep_chandna/agentcore-gateway-demo

aws s3 cp web-chat-with-memory.html s3://petstore-chat-web/ \
  --acl public-read \
  --region us-east-1
```

**Step 4: Make Bucket Public**
```bash
aws s3api put-bucket-policy \
  --bucket petstore-chat-web \
  --policy '{
    "Version": "2012-10-17",
    "Statement": [{
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::petstore-chat-web/*"
    }]
  }'
```

**Step 5: Access**
```
http://petstore-chat-web.s3-website-us-east-1.amazonaws.com
```

### Option 2: Local File (Testing)

```bash
cd /Users/ramandeep_chandna/agentcore-gateway-demo
open web-chat-with-memory.html
```

### Option 3: Python HTTP Server

```bash
cd /Users/ramandeep_chandna/agentcore-gateway-demo
python3 -m http.server 8000

# Access: http://localhost:8000/web-chat-with-memory.html
```

---

## 💬 How to Use

### 1. Open the Interface
Navigate to the URL and you'll see:
```
🐾 AI Pet Store Assistant
Powered by AgentCore Gateway + Memory

💾 Session: session-1738135267606
🔗 Memory: Connecting...
```

### 2. Start Chatting

**Example Queries:**
```
You: List all pets
You: Tell me about Buddy
You: What dogs do you have?
You: How much does Whiskers cost?
You: Show me the cheapest pet
```

### 3. Test Memory Persistence

**Test 1: Close and Reopen**
1. Have a conversation
2. Close browser completely
3. Reopen same URL
4. See conversation restored!

**Test 2: Multi-Device**
1. Copy session ID from browser
2. Open URL on phone/tablet
3. Add `?session=YOUR_SESSION_ID` to URL
4. See same conversation!

**Test 3: Share Session**
1. Share URL with session ID
2. Multiple people see same conversation
3. Collaborative chat experience!

---

## 🎨 Features

### ✅ Persistent Memory
- Conversations saved to AgentCore Memory
- Automatic load on page refresh
- Multi-device synchronization
- Session-based isolation

### ✅ Real-time Chat
- Instant responses from AgentCore Gateway
- Natural language processing
- Context-aware answers
- Beautiful UI with animations

### ✅ Secure Authentication
- AWS Cognito integration
- Temporary credentials
- Scoped IAM permissions
- No hardcoded secrets

### ✅ Responsive Design
- Works on desktop, tablet, mobile
- Modern gradient UI
- Smooth animations
- Accessible interface

---

## 🔧 Configuration

All configuration is embedded in the HTML file:

```javascript
const CONFIG = {
    region: 'us-east-1',
    identityPoolId: 'us-east-1:beef0a8b-da2e-4da4-8282-37455aaa57e7',
    memoryId: 'PetStoreChatMemory-Zhm3u49PiK',
    gatewayUrl: 'https://petstoregateway-remqjziohl.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp',
    userPoolId: 'us-east-1_RNmMBC87g',
    clientId: '435iqd7cgbn2slmgn0a36fo9lf'
};
```

**To customize:**
1. Open `web-chat-with-memory.html`
2. Find the `CONFIG` object
3. Update values as needed
4. Re-upload to S3

---

## 🐛 Troubleshooting

### Issue: "Memory Not Loading"

**Check Memory Status:**
```bash
aws bedrock-agentcore-control get-memory \
  --memory-id PetStoreChatMemory-Zhm3u49PiK \
  --region us-east-1
```

**Expected Output:**
```json
{
  "status": "ACTIVE",
  "memoryId": "PetStoreChatMemory-Zhm3u49PiK"
}
```

**If status is "CREATING":**
Wait 1-2 minutes and try again.

### Issue: "Credentials Error"

**Check IAM Role:**
```bash
aws iam get-role --role-name CognitoUnAuthRole
```

**Check Role Policy:**
```bash
aws iam get-role-policy \
  --role-name CognitoUnAuthRole \
  --policy-name MemoryAccess
```

**Expected Policy:**
```json
{
  "Effect": "Allow",
  "Action": [
    "bedrock-agent-runtime:GetMemory",
    "bedrock-agent-runtime:PutMemory"
  ],
  "Resource": "arn:aws:bedrock-agentcore:us-east-1:114805761158:memory/PetStoreChatMemory-Zhm3u49PiK"
}
```

### Issue: "Gateway Connection Failed"

**Test Gateway:**
```bash
# Get access token
TOKEN=$(aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id 435iqd7cgbn2slmgn0a36fo9lf \
  --auth-parameters USERNAME=testuser,PASSWORD=MySecurePass123! \
  --query 'AuthenticationResult.AccessToken' \
  --output text)

# Test gateway
curl -X POST \
  https://petstoregateway-remqjziohl.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

### Issue: "No Pets Returned"

**Check DynamoDB:**
```bash
aws dynamodb scan --table-name PetStore --region us-east-1
```

**Expected:** 15 pet items

**Check Lambda:**
```bash
aws lambda invoke \
  --function-name PetStoreFunction \
  --payload '{"httpMethod":"GET","path":"/pets"}' \
  response.json

cat response.json
```

### Issue: "CORS Error"

**Check Browser Console:**
- Open Developer Tools (F12)
- Check Console tab for errors
- Look for "CORS" or "Access-Control-Allow-Origin"

**Fix:**
API Gateway already has CORS enabled. If issues persist:
```bash
aws apigateway update-integration-response \
  --rest-api-id 66gd6g08ie \
  --resource-id YOUR_RESOURCE_ID \
  --http-method GET \
  --status-code 200 \
  --patch-operations op=add,path=/responseParameters/method.response.header.Access-Control-Allow-Origin,value="'*'"
```

---

## 📊 Monitoring

### View Memory Contents
```bash
aws bedrock-agent-runtime get-memory \
  --memory-id PetStoreChatMemory-Zhm3u49PiK \
  --session-id session-1738135267606 \
  --region us-east-1
```

### CloudWatch Logs

**Gateway Logs:**
```bash
aws logs tail /aws/bedrock-agentcore/gateway/petstoregateway-remqjziohl \
  --follow \
  --region us-east-1
```

**Lambda Logs:**
```bash
aws logs tail /aws/lambda/PetStoreFunction \
  --follow \
  --region us-east-1
```

### Metrics Dashboard
```bash
# Open CloudWatch console
open "https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:"
```

---

## 💰 Cost Tracking

### Current Month Costs
```bash
aws ce get-cost-and-usage \
  --time-period Start=2026-01-01,End=2026-01-31 \
  --granularity MONTHLY \
  --metrics BlendedCost \
  --group-by Type=SERVICE
```

### Expected Monthly Cost
```
AgentCore Memory:    $2.00
S3 Static Website:   $0.90
API Gateway:         $0.00 (free tier)
Lambda:              $0.00 (free tier)
DynamoDB:            $0.25
Cognito:             $0.00 (free tier)
------------------------
TOTAL:               $3.15/month
```

---

## 🎯 Demo Script for Presentation

### Setup (Before Demo)
1. Open web interface in browser
2. Clear any existing conversations
3. Have backup screenshots ready
4. Test internet connection

### Demo Flow

**Part 1: First Conversation (2 minutes)**
```
[Open web interface]
"Here's our AI Pet Store Assistant with persistent memory."

[Type]: "What pets do you have?"
[Show response with 15 pets]
"The AI instantly retrieves all pets from DynamoDB through AgentCore Gateway."

[Type]: "Tell me about Buddy"
[Show detailed response]
"Natural language understanding - it extracted the name and called the right API."
```

**Part 2: Memory Persistence (2 minutes)**
```
[Close browser completely]
"Traditional chatbots lose everything here. Watch what happens..."

[Reopen browser, navigate to same URL]
[Show conversation restored]
"The entire conversation is restored from AgentCore Memory!"

[Type]: "How much does he cost?"
[Show response about Buddy]
"It remembers we were talking about Buddy - true contextual memory!"
```

**Part 3: Multi-Device (1 minute)**
```
[Show session ID in URL]
"This session ID is the key to memory persistence."

[Open on phone/second browser]
[Show same conversation]
"Same conversation, different device. Works anywhere!"
```

### Backup Plan
If live demo fails:
1. Show pre-recorded video
2. Use screenshots
3. Walk through code instead
4. Show CloudWatch logs of previous successful runs

---

## 📚 Additional Resources

### Documentation
- `WEB_INTERFACE_DEPLOYMENT.md` - Full deployment guide
- `DEMO_PRESENTATION_STAR.md` - Complete presentation script
- `AGENTCORE_MEMORY_SETUP.md` - Memory configuration
- `PROJECT_WRITEUP.md` - STAR method analysis

### Code Files
- `web-chat-with-memory.html` - Web interface
- `interactive-chat-with-memory.py` - Python version
- `setup-memory.sh` - Automated setup script

### Diagrams
- `generated-diagrams/petstore_with_memory_architecture.png` - Architecture diagram

### GitHub Repository
```
https://github.com/catchmeraman/aws-agentcoregateway-api-gateway-integration-new-demo
```

---

## ✅ Pre-Demo Checklist

- [ ] Web interface accessible via URL
- [ ] Memory status shows "ACTIVE"
- [ ] Test conversation works
- [ ] Memory persistence tested
- [ ] Multi-device tested
- [ ] Backup screenshots ready
- [ ] Internet connection stable
- [ ] Browser console clear of errors
- [ ] CloudWatch logs accessible
- [ ] Presentation slides ready

---

## 🎉 You're Ready!

**Access URL:**
```
http://petstore-chat-web.s3-website-us-east-1.amazonaws.com
```

**Test Credentials:**
- Username: testuser
- Password: MySecurePass123!

**Memory ID:**
```
PetStoreChatMemory-Zhm3u49PiK
```

**Session ID Format:**
```
session-{timestamp}
```

**Support:**
- GitHub Issues: https://github.com/catchmeraman/aws-agentcoregateway-api-gateway-integration-new-demo/issues
- Documentation: All guides in repository

---

**🚀 DEMO TIME! 🚀**
