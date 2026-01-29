# Configuration Guide - deployment-config.json

## Overview

The `deployment-config.json` file contains all AWS resource identifiers needed to run the AI Pet Store chatbot with AgentCore Memory.

---

## Configuration Fields

### AWS Account Information

```json
"account_id": "YOUR_AWS_ACCOUNT_ID"
```
**What it is:** Your 12-digit AWS account ID  
**How to get it:**
```bash
aws sts get-caller-identity --query Account --output text
```
**Example:** `114805761158`

---

### Region

```json
"region": "us-east-1"
```
**What it is:** AWS region where resources are deployed  
**Options:** `us-east-1`, `us-west-2`, `eu-west-1`, etc.  
**Note:** AgentCore services are only available in specific regions

---

### API Gateway

```json
"api_gateway_id": "YOUR_API_GATEWAY_ID",
"api_gateway_stage": "prod",
"api_gateway_endpoint": "https://YOUR_API_GATEWAY_ID.execute-api.us-east-1.amazonaws.com/prod"
```

**What it is:** REST API Gateway that exposes Lambda functions  
**How to get it:**
```bash
aws apigateway get-rest-apis --query 'items[?name==`PetStoreAPI`].id' --output text
```
**Example:** `66gd6g08ie`

---

### Lambda Function

```json
"lambda_function_name": "PetStoreFunction",
"lambda_arn": "arn:aws:lambda:us-east-1:YOUR_AWS_ACCOUNT_ID:function:PetStoreFunction",
"lambda_role_arn": "arn:aws:iam::YOUR_AWS_ACCOUNT_ID:role/PetStoreLambdaRole"
```

**What it is:** Lambda function that handles pet store operations  
**How to get it:**
```bash
aws lambda get-function --function-name PetStoreFunction --query 'Configuration.FunctionArn' --output text
```

---

### Cognito User Pool

```json
"user_pool_id": "YOUR_COGNITO_USER_POOL_ID",
"client_id": "YOUR_COGNITO_CLIENT_ID",
"discovery_url": "https://cognito-idp.us-east-1.amazonaws.com/YOUR_COGNITO_USER_POOL_ID/.well-known/openid-configuration"
```

**What it is:** Cognito User Pool for authentication  
**How to get it:**
```bash
# User Pool ID
aws cognito-idp list-user-pools --max-results 10 --query 'UserPools[?Name==`PetStoreUserPool`].Id' --output text

# Client ID
aws cognito-idp list-user-pool-clients --user-pool-id YOUR_USER_POOL_ID --query 'UserPoolClients[0].ClientId' --output text
```
**Example:** `us-east-1_RNmMBC87g`

---

### AgentCore Gateway

```json
"gateway_id": "YOUR_AGENTCORE_GATEWAY_ID",
"gateway_url": "https://YOUR_AGENTCORE_GATEWAY_ID.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp",
"target_id": "YOUR_GATEWAY_TARGET_ID",
"gateway_role_arn": "arn:aws:iam::YOUR_AWS_ACCOUNT_ID:role/AgentCoreGatewayRole"
```

**What it is:** AgentCore Gateway that converts APIs to MCP tools  
**How to get it:**
```bash
# Gateway ID
aws bedrock-agentcore-control list-gateways --query 'gateways[?name==`petstoregateway`].id' --output text

# Target ID
aws bedrock-agentcore-control list-targets --gateway-id YOUR_GATEWAY_ID --query 'targets[0].id' --output text
```
**Example Gateway ID:** `petstoregateway-remqjziohl`  
**Example Target ID:** `89372YIO3X`

---

### DynamoDB Table

```json
"dynamodb_table": "PetStore"
```

**What it is:** DynamoDB table storing pet data  
**How to verify:**
```bash
aws dynamodb describe-table --table-name PetStore --query 'Table.TableName' --output text
```

---

### AgentCore Memory

```json
"memory_id": "YOUR_AGENTCORE_MEMORY_ID"
```

**What it is:** AgentCore Memory for persistent conversations  
**How to get it:**
```bash
aws bedrock-agentcore-control list-memories --query 'memories[?name==`PetStoreChatMemory`].id' --output text
```
**Example:** `PetStoreChatMemory-Zhm3u49PiK`

---

### Cognito Identity Pool

```json
"identity_pool_id": "YOUR_COGNITO_IDENTITY_POOL_ID"
```

**What it is:** Cognito Identity Pool for unauthenticated memory access  
**How to get it:**
```bash
aws cognito-identity list-identity-pools --max-results 10 --query 'IdentityPools[?IdentityPoolName==`PetStoreChatPool`].IdentityPoolId' --output text
```
**Example:** `us-east-1:beef0a8b-da2e-4da4-8282-37455aaa57e7`

---

## How to Use

### Step 1: Copy Template
```bash
cp deployment-config.template.json deployment-config.json
```

### Step 2: Fill in Your Values
Replace all `YOUR_*` placeholders with actual values from your AWS account.

### Step 3: Verify Configuration
```bash
# Test that all resources exist
python3 << EOF
import json
import boto3

with open('deployment-config.json') as f:
    config = json.load(f)

# Verify each resource
print(f"✓ Account: {config['account_id']}")
print(f"✓ Region: {config['region']}")
print(f"✓ Gateway: {config['gateway_id']}")
print(f"✓ Memory: {config['memory_id']}")
EOF
```

---

## Complete Example

```json
{
  "account_id": "114805761158",
  "region": "us-east-1",
  "api_gateway_id": "66gd6g08ie",
  "api_gateway_stage": "prod",
  "api_gateway_endpoint": "https://66gd6g08ie.execute-api.us-east-1.amazonaws.com/prod",
  "lambda_function_name": "PetStoreFunction",
  "lambda_arn": "arn:aws:lambda:us-east-1:114805761158:function:PetStoreFunction",
  "lambda_role_arn": "arn:aws:iam::114805761158:role/PetStoreLambdaRole",
  "gateway_role_arn": "arn:aws:iam::114805761158:role/AgentCoreGatewayRole",
  "user_pool_id": "us-east-1_RNmMBC87g",
  "client_id": "435iqd7cgbn2slmgn0a36fo9lf",
  "discovery_url": "https://cognito-idp.us-east-1.amazonaws.com/us-east-1_RNmMBC87g/.well-known/openid-configuration",
  "gateway_id": "petstoregateway-remqjziohl",
  "gateway_url": "https://petstoregateway-remqjziohl.gateway.bedrock-agentcore.us-east-1.amazonaws.com/mcp",
  "target_id": "89372YIO3X",
  "dynamodb_table": "PetStore",
  "memory_id": "PetStoreChatMemory-Zhm3u49PiK",
  "identity_pool_id": "us-east-1:beef0a8b-da2e-4da4-8282-37455aaa57e7"
}
```

---

## Troubleshooting

### "Resource not found" errors

**Check if resource exists:**
```bash
# For Gateway
aws bedrock-agentcore-control get-gateway --gateway-id YOUR_GATEWAY_ID

# For Memory
aws bedrock-agentcore-control get-memory --memory-id YOUR_MEMORY_ID

# For DynamoDB
aws dynamodb describe-table --table-name PetStore
```

### "Access denied" errors

**Check IAM permissions:**
```bash
# Verify your AWS credentials
aws sts get-caller-identity

# Check if you have required permissions
aws iam get-user
```

### Wrong region

**Verify resource region:**
```bash
# Most resources show region in their ARN
aws lambda get-function --function-name PetStoreFunction --query 'Configuration.FunctionArn'
```

---

## Security Notes

⚠️ **NEVER commit `deployment-config.json` to Git!**

- The `.gitignore` file excludes it by default
- Only commit `deployment-config.template.json`
- Share actual config securely (AWS Secrets Manager, encrypted files)

---

## Quick Setup Script

```bash
#!/bin/bash
# Auto-populate deployment-config.json

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION="us-east-1"
GATEWAY_ID=$(aws bedrock-agentcore-control list-gateways --query 'gateways[0].id' --output text)
MEMORY_ID=$(aws bedrock-agentcore-control list-memories --query 'memories[0].id' --output text)

cat > deployment-config.json << EOF
{
  "account_id": "$ACCOUNT_ID",
  "region": "$REGION",
  "gateway_id": "$GATEWAY_ID",
  "memory_id": "$MEMORY_ID"
}
EOF

echo "✅ Config created! Edit deployment-config.json to add remaining values."
```

---

## Related Files

- `deployment-config.template.json` - Template with placeholders
- `interactive-chat-with-memory.py` - Uses this config
- `web-chat-with-memory.html` - Uses these values (hardcoded in HTML)
