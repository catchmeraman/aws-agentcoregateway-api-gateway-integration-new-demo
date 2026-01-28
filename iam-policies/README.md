# IAM Policies and Roles

This directory contains all IAM policies and trust relationships required for the AgentCore Gateway + API Gateway integration.

## Files

### Trust Policies

**1. lambda-trust-policy.json**
- Allows Lambda service to assume the role
- Used by: PetStoreLambdaRole
- Principal: lambda.amazonaws.com

**2. gateway-trust-policy.json**
- Allows AgentCore Gateway service to assume the role
- Used by: AgentCoreGatewayRole
- Principal: bedrock-agentcore.amazonaws.com

### Permission Policies

**3. lambda-dynamodb-policy.json**
- Grants Lambda access to DynamoDB table
- Permissions: GetItem, PutItem, Scan, Query
- Resource: PetStore table
- **Note:** Replace `ACCOUNT_ID` with your AWS account ID

**4. gateway-apigateway-policy.json**
- Grants AgentCore Gateway access to invoke API Gateway
- Permission: execute-api:Invoke
- Resource: API Gateway REST API
- **Note:** Replace `ACCOUNT_ID` and `API_ID` with your values

## Usage

### Create Lambda Role

```bash
# 1. Create role with trust policy
aws iam create-role \
  --role-name PetStoreLambdaRole \
  --assume-role-policy-document file://iam-policies/lambda-trust-policy.json

# 2. Attach AWS managed policy for CloudWatch Logs
aws iam attach-role-policy \
  --role-name PetStoreLambdaRole \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# 3. Add DynamoDB access (replace ACCOUNT_ID first!)
aws iam put-role-policy \
  --role-name PetStoreLambdaRole \
  --policy-name DynamoDBAccess \
  --policy-document file://iam-policies/lambda-dynamodb-policy.json
```

### Create AgentCore Gateway Role

```bash
# 1. Create role with trust policy
aws iam create-role \
  --role-name AgentCoreGatewayRole \
  --assume-role-policy-document file://iam-policies/gateway-trust-policy.json

# 2. Add API Gateway invoke permission (replace ACCOUNT_ID and API_ID first!)
aws iam put-role-policy \
  --role-name AgentCoreGatewayRole \
  --policy-name APIGatewayInvoke \
  --policy-document file://iam-policies/gateway-apigateway-policy.json
```

## Before Using

### Replace Placeholders

**In lambda-dynamodb-policy.json:**
```bash
# Replace ACCOUNT_ID with your AWS account ID
sed -i 's/ACCOUNT_ID/123456789012/g' iam-policies/lambda-dynamodb-policy.json
```

**In gateway-apigateway-policy.json:**
```bash
# Replace ACCOUNT_ID and API_ID
sed -i 's/ACCOUNT_ID/123456789012/g' iam-policies/gateway-apigateway-policy.json
sed -i 's/API_ID/abc123xyz/g' iam-policies/gateway-apigateway-policy.json
```

### Get Your Values

```bash
# Get AWS Account ID
aws sts get-caller-identity --query Account --output text

# Get API Gateway ID (after creation)
aws apigateway get-rest-apis --query 'items[?name==`PetStoreAPI`].id' --output text
```

## Role Permissions Summary

### PetStoreLambdaRole

**Trust:** Lambda service  
**Permissions:**
- CloudWatch Logs (write logs)
- DynamoDB (read/write PetStore table)

**Used by:** PetStoreFunction Lambda

### AgentCoreGatewayRole

**Trust:** AgentCore service  
**Permissions:**
- API Gateway (invoke endpoints)

**Used by:** AgentCore Gateway

## Security Best Practices

1. **Least Privilege:** Policies grant only required permissions
2. **Resource-Specific:** Policies target specific resources (not `*`)
3. **Service-Specific:** Trust policies limited to AWS services
4. **No Wildcards:** Avoid `*` in Resource ARNs when possible

## Verification

### Check Role Exists
```bash
aws iam get-role --role-name PetStoreLambdaRole
aws iam get-role --role-name AgentCoreGatewayRole
```

### List Attached Policies
```bash
aws iam list-attached-role-policies --role-name PetStoreLambdaRole
aws iam list-role-policies --role-name PetStoreLambdaRole
```

### View Policy Document
```bash
aws iam get-role-policy \
  --role-name PetStoreLambdaRole \
  --policy-name DynamoDBAccess
```

## Troubleshooting

### "AccessDeniedException"
- Verify IAM policy has correct account ID
- Wait 10-15 seconds for IAM propagation
- Check resource ARN format

### "Role not found"
- Ensure role was created successfully
- Check role name spelling
- Verify in correct AWS region

### "Invalid principal"
- Verify service name in trust policy
- Check for typos in service names
- Ensure using correct AWS partition (aws vs aws-cn)

## Related Documentation

- [AWS IAM Roles](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles.html)
- [IAM Policy Reference](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference_policies.html)
- [Lambda Execution Role](https://docs.aws.amazon.com/lambda/latest/dg/lambda-intro-execution-role.html)
- [DynamoDB IAM Permissions](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/iam-policy-specific-table-indexes.html)
