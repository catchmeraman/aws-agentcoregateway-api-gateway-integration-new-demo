# Troubleshooting Guide

## Common Issues and Solutions

### 1. "Invalid Bearer token" Error

**Symptom**: 401 error when calling MCP endpoint

**Causes**:
- Using ID token instead of ACCESS token
- Token expired (> 1 hour old)
- Wrong client ID in token

**Solution**:
```bash
# Generate fresh ACCESS token (not ID token!)
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id $(jq -r .client_id deployment-config.json) \
  --auth-parameters USERNAME=testuser,PASSWORD=MySecurePass123! \
  --query 'AuthenticationResult.AccessToken' \
  --output text > access-token.txt
```

**Verify token**:
```bash
# Check token expiry
python3 << 'EOF'
import jwt
import json
from datetime import datetime

with open('access-token.txt') as f:
    token = f.read().strip()

decoded = jwt.decode(token, options={"verify_signature": False})
exp = datetime.fromtimestamp(decoded['exp'])
print(f"Token expires: {exp}")
print(f"Client ID: {decoded.get('client_id')}")
EOF
```

### 2. "Unknown tool: ListPets" Error

**Symptom**: Tool call fails with "Unknown tool"

**Cause**: Tool names are prefixed with target name

**Solution**: Use full tool name with prefix
```python
# ❌ WRONG
"name": "ListPets"

# ✅ CORRECT
"name": "PetStoreTarget___ListPets"
```

**List available tools**:
```bash
python3 << 'EOF'
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
tools = r.json()['result']['tools']
for t in tools:
    print(f"- {t['name']}")
EOF
```

### 3. Gateway Target Status: FAILED

**Symptom**: Target shows FAILED status

**Cause**: API Gateway methods missing response definitions

**Check status**:
```bash
aws bedrock-agentcore-control get-gateway-target \
  --gateway-identifier $(jq -r .gateway_id deployment-config.json) \
  --target-id $(jq -r .target_id deployment-config.json) \
  --query '[status, statusReasons]'
```

**Solution**: Add response definitions to API methods
```bash
python3 << 'EOF'
import boto3, json

with open('deployment-config.json') as f:
    config = json.load(f)

apigw = boto3.client('apigateway', region_name=config['region'])
api_id = config['api_gateway_id']

# Get resources
resources = apigw.get_resources(restApiId=api_id)

# Add response to each GET method
for resource in resources['items']:
    if 'resourceMethods' in resource and 'GET' in resource['resourceMethods']:
        try:
            apigw.put_method_response(
                restApiId=api_id,
                resourceId=resource['id'],
                httpMethod='GET',
                statusCode='200',
                responseModels={'application/json': 'Empty'}
            )
            print(f"✅ Added response to {resource.get('path', '/')}")
        except:
            pass

# Redeploy
apigw.create_deployment(restApiId=api_id, stageName='prod')
print("✅ API redeployed")
EOF
```

Then recreate the target:
```bash
# Delete old target
aws bedrock-agentcore-control delete-gateway-target \
  --gateway-identifier $(jq -r .gateway_id deployment-config.json) \
  --target-id $(jq -r .target_id deployment-config.json)

# Wait 10 seconds
sleep 10

# Recreate target (use deploy.py or manual commands)
```

### 4. Gateway Status: CREATING (Stuck)

**Symptom**: Gateway stuck in CREATING status

**Check status**:
```bash
aws bedrock-agentcore-control get-gateway \
  --gateway-identifier $(jq -r .gateway_id deployment-config.json) \
  --query '[status, statusReasons]'
```

**Solution**: Wait up to 5 minutes. If still stuck:
```bash
# Delete and recreate
aws bedrock-agentcore-control delete-gateway \
  --gateway-identifier $(jq -r .gateway_id deployment-config.json)

# Wait for deletion
sleep 30

# Run deploy.py again
python deploy.py
```

### 5. Lambda Function Not Responding

**Symptom**: API Gateway returns 500 errors

**Test Lambda directly**:
```bash
aws lambda invoke \
  --function-name PetStoreFunction \
  --payload '{"path": "/pets", "httpMethod": "GET"}' \
  response.json

cat response.json
```

**Check logs**:
```bash
aws logs tail /aws/lambda/PetStoreFunction --follow
```

**Solution**: Verify Lambda code and permissions
```bash
# Check Lambda role
aws lambda get-function \
  --function-name PetStoreFunction \
  --query 'Configuration.Role'

# Update function code if needed
zip function.zip lambda_function.py
aws lambda update-function-code \
  --function-name PetStoreFunction \
  --zip-file fileb://function.zip
```

### 6. API Gateway Permission Denied

**Symptom**: Gateway can't invoke API Gateway

**Check IAM role**:
```bash
aws iam get-role-policy \
  --role-name AgentCoreGatewayRole \
  --policy-name APIGatewayInvoke
```

**Solution**: Add execute-api permission
```bash
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
API_ID=$(jq -r .api_gateway_id deployment-config.json)

aws iam put-role-policy \
  --role-name AgentCoreGatewayRole \
  --policy-name APIGatewayInvoke \
  --policy-document "{
    \"Version\": \"2012-10-17\",
    \"Statement\": [{
      \"Effect\": \"Allow\",
      \"Action\": \"execute-api:Invoke\",
      \"Resource\": \"arn:aws:execute-api:us-east-1:${ACCOUNT_ID}:${API_ID}/*\"
    }]
  }"
```

### 7. Cognito Authentication Failed

**Symptom**: Can't generate token

**Test authentication**:
```bash
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id $(jq -r .client_id deployment-config.json) \
  --auth-parameters USERNAME=testuser,PASSWORD=MySecurePass123!
```

**Common errors**:

**"User does not exist"**:
```bash
# Recreate user
POOL_ID=$(jq -r .user_pool_id deployment-config.json)

aws cognito-idp admin-create-user \
  --user-pool-id $POOL_ID \
  --username testuser \
  --temporary-password TempPass123! \
  --message-action SUPPRESS

aws cognito-idp admin-set-user-password \
  --user-pool-id $POOL_ID \
  --username testuser \
  --password MySecurePass123! \
  --permanent
```

**"Invalid authentication flow"**:
```bash
# Update client to allow USER_PASSWORD_AUTH
CLIENT_ID=$(jq -r .client_id deployment-config.json)
POOL_ID=$(jq -r .user_pool_id deployment-config.json)

aws cognito-idp update-user-pool-client \
  --user-pool-id $POOL_ID \
  --client-id $CLIENT_ID \
  --explicit-auth-flows ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH
```

### 8. Python Dependencies Missing

**Symptom**: ImportError when running scripts

**Solution**:
```bash
pip install -r requirements.txt

# Or install individually
pip install boto3 httpx strands-agents
```

### 9. AWS CLI Not Configured

**Symptom**: "Unable to locate credentials"

**Solution**:
```bash
aws configure
# Enter: Access Key, Secret Key, Region (us-east-1), Output (json)

# Verify
aws sts get-caller-identity
```

### 10. Region Mismatch

**Symptom**: Resources not found

**Check region**:
```bash
aws configure get region
```

**Solution**: Use us-east-1 consistently
```bash
aws configure set region us-east-1

# Or use --region flag
aws bedrock-agentcore-control get-gateway \
  --gateway-identifier GATEWAY_ID \
  --region us-east-1
```

## Debugging Tips

### Enable Verbose Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check All Resource Status

```bash
python3 << 'EOF'
import boto3, json

with open('deployment-config.json') as f:
    config = json.load(f)

# Lambda
lambda_client = boto3.client('lambda', region_name=config['region'])
try:
    r = lambda_client.get_function(FunctionName='PetStoreFunction')
    print(f"✅ Lambda: {r['Configuration']['State']}")
except:
    print("❌ Lambda: Not found")

# API Gateway
apigw = boto3.client('apigateway', region_name=config['region'])
try:
    r = apigw.get_rest_api(restApiId=config['api_gateway_id'])
    print(f"✅ API Gateway: {r['name']}")
except:
    print("❌ API Gateway: Not found")

# Gateway
agentcore = boto3.client('bedrock-agentcore-control', region_name=config['region'])
try:
    r = agentcore.get_gateway(gatewayIdentifier=config['gateway_id'])
    print(f"✅ Gateway: {r['status']}")
except:
    print("❌ Gateway: Not found")

# Target
try:
    r = agentcore.get_gateway_target(
        gatewayIdentifier=config['gateway_id'],
        targetId=config['target_id']
    )
    print(f"✅ Target: {r['status']}")
except:
    print("❌ Target: Not found")
EOF
```

### Test Each Component Separately

1. **Test Lambda**:
```bash
aws lambda invoke --function-name PetStoreFunction \
  --payload '{"path": "/pets", "httpMethod": "GET"}' out.json
cat out.json
```

2. **Test API Gateway**:
```bash
curl https://$(jq -r .api_gateway_id deployment-config.json).execute-api.us-east-1.amazonaws.com/prod/pets
```

3. **Test Cognito**:
```bash
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id $(jq -r .client_id deployment-config.json) \
  --auth-parameters USERNAME=testuser,PASSWORD=MySecurePass123!
```

4. **Test Gateway**:
```bash
python3 test-final.py
```

## Getting Help

If issues persist:

1. Check CloudWatch Logs:
```bash
# Lambda logs
aws logs tail /aws/lambda/PetStoreFunction --follow

# API Gateway logs (if enabled)
aws logs tail API-Gateway-Execution-Logs_API_ID/prod --follow
```

2. Review deployment config:
```bash
cat deployment-config.json | jq
```

3. Verify IAM permissions:
```bash
aws iam get-role --role-name AgentCoreGatewayRole
aws iam get-role --role-name PetStoreLambdaRole
```

4. Check AWS Service Health:
- Visit AWS Service Health Dashboard
- Check for regional outages

5. Contact AWS Support with:
- Gateway ID
- Target ID
- Error messages
- CloudWatch logs
