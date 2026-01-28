# Detailed Setup Guide

## Prerequisites

### AWS Account Setup
- AWS Account with admin access
- AWS CLI installed and configured
- Region: us-east-1 (recommended)

### Local Environment
```bash
python --version  # 3.8 or higher
aws --version     # AWS CLI 2.x
```

### Install Dependencies
```bash
pip install boto3 httpx strands-agents
```

## Step-by-Step Deployment

### Step 1: Clone and Configure

```bash
git clone <your-repo>
cd agentcore-gateway-demo
```

### Step 2: Run Deployment Script

```bash
python deploy.py
```

This will:
1. Create Lambda function with Pet Store code
2. Create API Gateway with 2 endpoints
3. Add response definitions to API methods
4. Create Cognito User Pool and test user
5. Create IAM roles with proper permissions
6. Create AgentCore Gateway
7. Wait for gateway to be READY
8. Create Gateway Target for API Gateway
9. Save configuration to `deployment-config.json`

**Expected time**: 2-3 minutes

### Step 3: Verify Deployment

```bash
# Check gateway status
aws bedrock-agentcore-control get-gateway \
  --gateway-identifier $(jq -r .gateway_id deployment-config.json) \
  --query 'status' --output text
# Should return: READY

# Check target status  
aws bedrock-agentcore-control get-gateway-target \
  --gateway-identifier $(jq -r .gateway_id deployment-config.json) \
  --target-id $(jq -r .target_id deployment-config.json) \
  --query 'status' --output text
# Should return: READY
```

### Step 4: Get Authentication Token

```bash
# Extract client ID from config
CLIENT_ID=$(jq -r .client_id deployment-config.json)

# Get ACCESS token
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id $CLIENT_ID \
  --auth-parameters USERNAME=testuser,PASSWORD=MySecurePass123! \
  --query 'AuthenticationResult.AccessToken' \
  --output text > access-token.txt
```

**Important**: Token expires in 1 hour. Regenerate as needed.

### Step 5: Run Tests

```bash
# Test MCP protocol
python test-final.py

# Expected output:
# ✅ Found 3 tools
# ✅ ListPets returned 3 pets  
# ✅ GetPetById returned pet details

# Test AI chatbot
python chatbot-final.py

# Expected output:
# 🤖 AI Pet Store Assistant
# ✅ Query 1: What pets do you have available?
# ✅ Query 2: Tell me about pet ID 2
# ✅ Query 3: What's the cheapest pet?
```

## Manual Deployment (Alternative)

If automated deployment fails, follow these manual steps:

### 1. Create Lambda Function

```bash
# Create role
aws iam create-role \
  --role-name PetStoreLambdaRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Attach policy
aws iam attach-role-policy \
  --role-name PetStoreLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Create function code
cat > lambda_function.py << 'EOF'
import json

def lambda_handler(event, context):
    pets = [
        {"id": 1, "type": "dog", "name": "Buddy", "price": 249.99},
        {"id": 2, "type": "cat", "name": "Whiskers", "price": 124.99},
        {"id": 3, "type": "fish", "name": "Nemo", "price": 0.99}
    ]
    
    path = event.get('path', '')
    method = event.get('httpMethod', 'GET')
    
    if path == '/pets' and method == 'GET':
        return {'statusCode': 200, 'body': json.dumps(pets)}
    
    if path.startswith('/pets/') and method == 'GET':
        pet_id = int(path.split('/')[-1])
        pet = next((p for p in pets if p['id'] == pet_id), None)
        if pet:
            return {'statusCode': 200, 'body': json.dumps(pet)}
        return {'statusCode': 404, 'body': json.dumps({'error': 'Pet not found'})}
    
    return {'statusCode': 400, 'body': json.dumps({'error': 'Invalid request'})}
EOF

# Package and deploy
zip function.zip lambda_function.py

aws lambda create-function \
  --function-name PetStoreFunction \
  --runtime python3.12 \
  --role arn:aws:iam::ACCOUNT_ID:role/PetStoreLambdaRole \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://function.zip
```

### 2. Create API Gateway

```bash
# Create REST API
API_ID=$(aws apigateway create-rest-api \
  --name PetStoreAPI \
  --query 'id' --output text)

# Get root resource
ROOT_ID=$(aws apigateway get-resources \
  --rest-api-id $API_ID \
  --query 'items[0].id' --output text)

# Create /pets resource
PETS_ID=$(aws apigateway create-resource \
  --rest-api-id $API_ID \
  --parent-id $ROOT_ID \
  --path-part pets \
  --query 'id' --output text)

# Create GET /pets method
aws apigateway put-method \
  --rest-api-id $API_ID \
  --resource-id $PETS_ID \
  --http-method GET \
  --authorization-type NONE

# Add response definition
aws apigateway put-method-response \
  --rest-api-id $API_ID \
  --resource-id $PETS_ID \
  --http-method GET \
  --status-code 200 \
  --response-models '{"application/json": "Empty"}'

# Create integration
aws apigateway put-integration \
  --rest-api-id $API_ID \
  --resource-id $PETS_ID \
  --http-method GET \
  --type AWS_PROXY \
  --integration-http-method POST \
  --uri arn:aws:apigateway:us-east-1:lambda:path/2015-03-31/functions/arn:aws:lambda:us-east-1:ACCOUNT_ID:function:PetStoreFunction/invocations

# Deploy
aws apigateway create-deployment \
  --rest-api-id $API_ID \
  --stage-name prod
```

### 3. Create Cognito User Pool

```bash
# Create pool
POOL_ID=$(aws cognito-idp create-user-pool \
  --pool-name PetStoreUsers \
  --query 'UserPool.Id' --output text)

# Create client
CLIENT_ID=$(aws cognito-idp create-user-pool-client \
  --user-pool-id $POOL_ID \
  --client-name PetStoreClient \
  --explicit-auth-flows ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH \
  --query 'UserPoolClient.ClientId' --output text)

# Create test user
aws cognito-idp admin-create-user \
  --user-pool-id $POOL_ID \
  --username testuser \
  --temporary-password TempPass123! \
  --message-action SUPPRESS

# Set permanent password
aws cognito-idp admin-set-user-password \
  --user-pool-id $POOL_ID \
  --username testuser \
  --password MySecurePass123! \
  --permanent
```

### 4. Create AgentCore Gateway

```bash
# Create gateway role
aws iam create-role \
  --role-name AgentCoreGatewayRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "bedrock-agentcore.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

# Add API Gateway invoke permission
aws iam put-role-policy \
  --role-name AgentCoreGatewayRole \
  --policy-name APIGatewayInvoke \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": "execute-api:Invoke",
      "Resource": "arn:aws:execute-api:us-east-1:ACCOUNT_ID:API_ID/*"
    }]
  }'

# Create gateway
GATEWAY_ID=$(aws bedrock-agentcore-control create-gateway \
  --name petstoregateway \
  --protocol-version MCP_2025_03_26 \
  --inbound-auth-configuration '{
    "customJWTAuthorizer": {
      "allowedClients": ["CLIENT_ID"],
      "discoveryUrl": "https://cognito-idp.us-east-1.amazonaws.com/POOL_ID/.well-known/openid-configuration"
    }
  }' \
  --query 'gatewayId' --output text)

# Wait for READY status
aws bedrock-agentcore-control get-gateway \
  --gateway-identifier $GATEWAY_ID \
  --query 'status' --output text
```

### 5. Create Gateway Target

```bash
# Create target
aws bedrock-agentcore-control create-gateway-target \
  --gateway-identifier $GATEWAY_ID \
  --name PetStoreTarget \
  --target-configuration '{
    "mcp": {
      "apiGateway": {
        "restApiId": "API_ID",
        "stage": "prod",
        "apiGatewayToolConfiguration": {
          "toolFilters": [
            {"filterPath": "/pets", "methods": ["GET"]},
            {"filterPath": "/pets/{petId}", "methods": ["GET"]}
          ],
          "toolOverrides": [
            {
              "name": "ListPets",
              "path": "/pets",
              "method": "GET",
              "description": "Retrieves all available pets"
            },
            {
              "name": "GetPetById",
              "path": "/pets/{petId}",
              "method": "GET",
              "description": "Retrieve a specific pet by ID"
            }
          ]
        }
      }
    }
  }' \
  --credential-provider-configurations '[{
    "credentialProviderType": "GATEWAY_IAM_ROLE"
  }]'
```

## Verification Checklist

- [ ] Lambda function created and working
- [ ] API Gateway deployed with 2 endpoints
- [ ] API methods have response definitions
- [ ] Cognito user pool created with test user
- [ ] IAM roles created with proper permissions
- [ ] AgentCore Gateway status: READY
- [ ] Gateway Target status: READY
- [ ] ACCESS token generated successfully
- [ ] MCP test passes
- [ ] Chatbot test passes

## Next Steps

After successful deployment:
1. Review `deployment-config.json` for all resource IDs
2. Test with `test-final.py`
3. Try the chatbot with `chatbot-final.py`
4. Explore modifying the Lambda function
5. Add more API endpoints
6. Customize the AI agent behavior

## Cleanup

When done testing:
```bash
python cleanup.py
```

This removes all created resources and stops charges.
