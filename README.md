# AgentCore Gateway + API Gateway Integration Demo

Complete working demonstration of AWS AgentCore Gateway integration with API Gateway using Model Context Protocol (MCP).

## 🎯 What This Demonstrates

- **AgentCore Gateway** as MCP server
- **API Gateway** integration through AgentCore Gateway  
- **Cognito** JWT authentication
- **AI Agent** using Strands framework
- **End-to-end chatbot** with natural language queries
- **Full CRUD operations** - Create (POST) and Read (GET) via natural language ✨

## 🏗️ Architecture

```
User → AI Agent → AgentCore Gateway (MCP) → API Gateway → Lambda → Response
                         ↓
                  Cognito Auth (ACCESS token)
```

## 📋 Prerequisites

- AWS Account with CLI configured
- Python 3.8+
- Permissions: Lambda, API Gateway, Cognito, IAM, AgentCore

## 🚀 Quick Start

### 1. Deploy Infrastructure

```bash
pip install -r requirements.txt
python deploy.py
```

This creates:
- Lambda function (Pet Store API)
- API Gateway (REST API with 2 endpoints)
- Cognito User Pool (authentication)
- AgentCore Gateway (MCP server)
- Gateway Target (API Gateway integration)
- IAM roles (proper permissions)

### 2. Get Authentication Token

```bash
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id <CLIENT_ID> \
  --auth-parameters USERNAME=testuser,PASSWORD=MySecurePass123! \
  --query 'AuthenticationResult.AccessToken' \
  --output text > access-token.txt
```

**CRITICAL**: Use **ACCESS token**, not ID token!

### 3. Run Tests

```bash
# Test MCP protocol
python test-final.py

# Test AI chatbot
python chatbot-final.py
```

## 🧪 What Gets Tested

### MCP Protocol Test (`test-final.py`)
- ✅ List available tools via MCP
- ✅ Call ListPets tool
- ✅ Call GetPetById tool with parameters
- ✅ Call AddPet tool (POST method) ✨

### AI Chatbot Test (`chatbot-final.py`)
- ✅ Natural language query: "What pets do you have?"
- ✅ Natural language query: "Tell me about pet ID 2"
- ✅ Natural language query: "What's the cheapest pet?"
- ✅ Natural language query: "Add a frog named Sweety for $20" ✨

## 🔑 Key Findings

### 1. Use ACCESS Token (Not ID Token)
```bash
# ❌ WRONG
--query 'AuthenticationResult.IdToken'

# ✅ CORRECT  
--query 'AuthenticationResult.AccessToken'
```

### 2. API Gateway Needs Response Definitions
```python
apigw.put_method_response(
    restApiId=api_id,
    resourceId=resource_id,
    httpMethod='GET',
    statusCode='200',
    responseModels={'application/json': 'Empty'}
)
```

### 3. Tool Names Are Prefixed
Tools exposed as: `{TargetName}___{ToolName}`
- Example: `PetStoreTarget___ListPets`
- Example: `PetStoreTarget___GetPetById`
- Example: `PetStoreTarget___AddPet` ✨

## 📁 Project Structure

```
agentcore-gateway-demo/
├── README.md              # This file
├── SETUP.md              # Detailed setup guide
├── TROUBLESHOOTING.md    # Common issues
├── deploy.py             # Full deployment script
├── cleanup.py            # Resource cleanup
├── test-final.py         # MCP protocol test
├── chatbot-final.py      # AI chatbot demo
├── requirements.txt      # Python dependencies
└── deployment-config.json.example  # Config template
```

## 🔧 Configuration

Create `deployment-config.json`:
```json
{
  "account_id": "YOUR_ACCOUNT_ID",
  "region": "us-east-1",
  "gateway_url": "https://YOUR_GATEWAY.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp",
  "api_gateway_id": "YOUR_API_ID",
  "user_pool_id": "YOUR_POOL_ID",
  "client_id": "YOUR_CLIENT_ID"
}
```

## 🐛 Troubleshooting

### "Invalid Bearer token"
→ Regenerate ACCESS token (expires hourly)

### "Unknown tool: ListPets"  
→ Use prefixed name: `PetStoreTarget___ListPets`

### Target status FAILED
→ Check API Gateway has response definitions

See `TROUBLESHOOTING.md` for more details.

## 🧹 Cleanup

```bash
python cleanup.py
```

Deletes all created resources.

## 💰 Cost Estimate

- **Hourly**: ~$0.01
- **Daily**: ~$0.24  
- **Monthly**: ~$7.20

Costs from: Lambda, API Gateway, Cognito, AgentCore Gateway

## 📚 Documentation

### Core Documentation
- **[PROJECT_WRITEUP.md](PROJECT_WRITEUP.md)** - Complete STAR method analysis ⭐
- **[ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md)** - 6 detailed architecture diagrams ⭐
- **[PREREQUISITES.md](PREREQUISITES.md)** - Complete setup requirements and execution steps ⭐

### Additional Guides
- [SETUP.md](SETUP.md) - Detailed step-by-step setup guide
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions
- [DEMO.md](DEMO.md) - Demo instructions with Q&A preparation
- [REPOSITORY.md](REPOSITORY.md) - Repository overview
- [FINAL_SUMMARY.md](FINAL_SUMMARY.md) - Complete project summary

### External Resources
- [AgentCore Gateway Docs](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway.html)
- [MCP Specification](https://spec.modelcontextprotocol.io/)

## ✅ Verification

All tests should pass:
```
✅ MCP Protocol: List tools, call tools
✅ AI Chatbot: Natural language queries
✅ Authentication: Cognito ACCESS token
✅ Integration: Gateway → API Gateway → Lambda
```

## 🎓 What You'll Learn

1. How to create AgentCore Gateway with MCP protocol
2. How to integrate API Gateway as a target
3. How to configure Cognito JWT authentication
4. How to use tools in AI agent workflows
5. How to troubleshoot common integration issues

## 📞 Support

For issues:
1. Check `TROUBLESHOOTING.md`
2. Verify all resources are in READY state
3. Ensure ACCESS token is fresh (< 1 hour old)
4. Check CloudWatch logs for detailed errors

## 📄 License

MIT License - See LICENSE file

## 🙏 Acknowledgments

Built using:
- AWS AgentCore Gateway
- AWS API Gateway
- AWS Lambda
- Amazon Cognito
- Strands Agent Framework
- Model Context Protocol (MCP)

---

**Status**: ✅ Production Ready  
**Last Updated**: January 2026  
**Tested**: Python 3.12, AWS CLI 2.x
