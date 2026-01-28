# AWS Architecture Diagrams

This directory contains visual architecture diagrams for the AgentCore Gateway + API Gateway integration project.

## Diagrams

### 1. AWS Architecture Overview
**File:** `aws_architecture_overview.png`

**Shows:**
- Complete end-to-end flow from user to Lambda
- All AWS services involved
- Data flow and communication protocols
- Integration points

**Key Components:**
- User → Strands Agent → AgentCore Gateway → API Gateway → Lambda
- Cognito for authentication
- MCP protocol for agent-gateway communication
- IAM SigV4 for gateway-API communication

---

### 2. Authentication Flow
**File:** `aws_authentication_flow.png`

**Shows:**
- Cognito token generation process
- JWT validation steps
- IAM role assumption
- Permission flow

**Key Steps:**
1. User authenticates with Cognito
2. Receives ACCESS token (1 hour expiry)
3. Sends token to AgentCore Gateway
4. Gateway validates JWT with Cognito
5. Gateway assumes IAM role
6. Gets execute-api:Invoke permission

---

### 3. IAM Roles and Permissions
**File:** `aws_iam_roles.png`

**Shows:**
- Two IAM roles in the system
- Trust relationships
- Permission boundaries
- Service-to-service access

**Roles:**
1. **PetStoreLambdaRole**
   - Trusted by: Lambda service
   - Permissions: CloudWatch Logs

2. **AgentCoreGatewayRole**
   - Trusted by: AgentCore service
   - Permissions: execute-api:Invoke

---

### 4. Interactive Chat Flow
**File:** `aws_interactive_chat_flow.png`

**Shows:**
- Step-by-step execution of interactive-chat.py
- How AI agent decides which tool to call
- MCP protocol communication
- Response generation

**Flow:**
1. User asks natural language question
2. AI agent analyzes query
3. Agent selects appropriate tool
4. Tool makes MCP request to gateway
5. Gateway invokes API Gateway
6. Lambda processes request
7. Response flows back through layers
8. AI generates natural language answer

---

### 5. Complete Deployment Architecture
**File:** `aws_complete_deployment.png`

**Shows:**
- All deployed AWS resources
- Authentication and authorization layers
- Monitoring and logging
- Complete request/response flow

**Layers:**
- User Layer: Developer/User
- Auth Layer: Cognito + IAM Roles
- Gateway Layer: AgentCore Gateway + Target
- API Layer: API Gateway
- Compute Layer: Lambda
- Monitoring Layer: CloudWatch Logs

---

### 6. MCP Protocol Communication
**File:** `aws_mcp_protocol.png`

**Shows:**
- JSON-RPC 2.0 request format
- MCP server processing
- Response format
- Protocol details

**Protocol:**
- Request: `{"jsonrpc": "2.0", "method": "tools/call", "params": {...}}`
- Response: `{"jsonrpc": "2.0", "result": {...}}`
- Standard: JSON-RPC 2.0

---

## How to View

### In Terminal
```bash
# macOS
open generated-diagrams/aws_architecture_overview.png

# Linux
xdg-open generated-diagrams/aws_architecture_overview.png

# Windows
start generated-diagrams/aws_architecture_overview.png
```

### In Documentation
These diagrams are referenced in:
- `README.md` - Main documentation
- `PROJECT_WRITEUP.md` - STAR method analysis
- `INTERACTIVE_CHAT_EXPLANATION.md` - Code explanation

---

## Diagram Legend

**Colors:**
- Blue boxes: AWS services
- Green edges: Permissions/allowed actions
- Black edges: Data flow
- Dashed edges: Trust relationships or logging

**Labels:**
- Edge labels show data format or action
- Node labels show service name and identifier

---

## Regenerating Diagrams

If you need to regenerate or modify diagrams:

```python
from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import Lambda
from diagrams.aws.network import APIGateway
# ... other imports

with Diagram("Your Diagram Name", show=False):
    # Your diagram code
```

See the Python Diagrams library documentation for more options:
https://diagrams.mingrammer.com/

---

## Use Cases

**For Presentations:**
- Use `aws_architecture_overview.png` for high-level overview
- Use `aws_interactive_chat_flow.png` to explain the demo

**For Documentation:**
- Include diagrams in README or wiki
- Reference in technical specifications

**For Troubleshooting:**
- Use `aws_authentication_flow.png` for auth issues
- Use `aws_iam_roles.png` for permission problems

**For Learning:**
- Study `aws_complete_deployment.png` to understand full architecture
- Review `aws_mcp_protocol.png` to understand protocol details

---

## Related Documentation

- [INTERACTIVE_CHAT_EXPLANATION.md](../INTERACTIVE_CHAT_EXPLANATION.md) - Code walkthrough
- [ARCHITECTURE_DIAGRAMS.md](../ARCHITECTURE_DIAGRAMS.md) - ASCII diagrams
- [PROJECT_WRITEUP.md](../PROJECT_WRITEUP.md) - STAR method analysis
- [README.md](../README.md) - Main documentation
