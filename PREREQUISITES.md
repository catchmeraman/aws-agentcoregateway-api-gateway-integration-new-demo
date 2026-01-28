# Prerequisites and Setup Requirements

## System Requirements

### Local Development Environment

**Operating System:**
- macOS (tested on macOS)
- Linux (Ubuntu 20.04+, Amazon Linux 2)
- Windows (with WSL2 recommended)

**Required Software:**
```bash
# Python
Python 3.8 or higher
pip (Python package manager)

# AWS CLI
AWS CLI version 2.x
Configured with credentials (aws configure)

# Git
Git 2.x or higher

# Optional but Recommended
jq (JSON processor for command-line)
```

### AWS Account Requirements

**Account Setup:**
- Active AWS account
- IAM user or role with appropriate permissions
- AWS CLI configured with credentials
- Access to us-east-1 region (or modify for your region)

**Required AWS Permissions:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "lambda:*",
        "apigateway:*",
        "cognito-idp:*",
        "iam:CreateRole",
        "iam:PutRolePolicy",
        "iam:AttachRolePolicy",
        "iam:GetRole",
        "iam:PassRole",
        "bedrock-agentcore-control:*",
        "logs:*"
      ],
      "Resource": "*"
    }
  ]
}
```

**Service Quotas:**
- Lambda functions: At least 1 available
- API Gateway REST APIs: At least 1 available
- Cognito User Pools: At least 1 available
- AgentCore Gateways: At least 1 available

---

## Installation Steps

### Step 1: Install Python Dependencies

```bash
# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install required packages
pip install boto3 httpx strands-agents

# Or use requirements.txt
pip install -r requirements.txt
```

**Package Versions:**
- boto3 >= 1.34.0
- httpx >= 0.25.0
- strands-agents >= 0.1.0

### Step 2: Configure AWS CLI

```bash
# Configure AWS credentials
aws configure

# Enter when prompted:
AWS Access Key ID: YOUR_ACCESS_KEY
AWS Secret Access Key: YOUR_SECRET_KEY
Default region name: us-east-1
Default output format: json

# Verify configuration
aws sts get-caller-identity
```

**Expected Output:**
```json
{
    "UserId": "AIDAXXXXXXXXXXXXXXXXX",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/your-username"
}
```

### Step 3: Clone Repository

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/agentcore-gateway-demo.git
cd agentcore-gateway-demo

# Verify files
ls -la
```

### Step 4: Verify Prerequisites

```bash
# Check Python version
python3 --version
# Should be 3.8 or higher

# Check AWS CLI version
aws --version
# Should be aws-cli/2.x.x

# Check pip packages
pip list | grep -E "boto3|httpx|strands"

# Check AWS credentials
aws sts get-caller-identity
```

---

## Execution Steps

### Quick Start (Automated Deployment)

```bash
# 1. Navigate to project directory
cd agentcore-gateway-demo

# 2. Run deployment script
python3 deploy.py

# Expected output:
# ✅ Creating Lambda function...
# ✅ Creating API Gateway...
# ✅ Creating Cognito User Pool...
# ✅ Creating AgentCore Gateway...
# ✅ Creating Gateway Target...
# ✅ Deployment complete!

# 3. Generate authentication token
aws cognito-idp initiate-auth \
  --auth-flow USER_PASSWORD_AUTH \
  --client-id $(jq -r .client_id deployment-config.json) \
  --auth-parameters USERNAME=testuser,PASSWORD=MySecurePass123! \
  --query 'AuthenticationResult.AccessToken' \
  --output text > access-token.txt

# 4. Run MCP protocol test
python3 test-final.py

# Expected output:
# ✅ Found 3 tools
# ✅ ListPets returned 3 pets
# ✅ GetPetById returned pet details

# 5. Run AI chatbot demo
python3 chatbot-final.py

# Expected output:
# 🤖 AI Pet Store Assistant
# [Query 1] What pets do you have available?
# [Query 2] Tell me about pet ID 2
# [Query 3] What's the cheapest pet?

# 6. Run interactive chatbot
python3 interactive-chat.py

# Type your questions and interact with the AI
```

### Manual Deployment (Step-by-Step)

If automated deployment fails, follow manual steps in `SETUP.md`:

```bash
# 1. Create IAM roles
# See SETUP.md section "Manual Deployment" step 1

# 2. Create Lambda function
# See SETUP.md section "Manual Deployment" step 2

# 3. Create API Gateway
# See SETUP.md section "Manual Deployment" step 3

# 4. Create Cognito User Pool
# See SETUP.md section "Manual Deployment" step 4

# 5. Create AgentCore Gateway
# See SETUP.md section "Manual Deployment" step 5

# 6. Create Gateway Target
# See SETUP.md section "Manual Deployment" step 6
```

---

## Verification Checklist

### Pre-Deployment Verification

- [ ] Python 3.8+ installed
- [ ] AWS CLI 2.x installed and configured
- [ ] AWS credentials valid (aws sts get-caller-identity works)
- [ ] Required Python packages installed
- [ ] Repository cloned successfully
- [ ] In correct directory (agentcore-gateway-demo)

### Post-Deployment Verification

```bash
# Check Lambda function
aws lambda get-function --function-name PetStoreFunction
# Should return function configuration

# Check API Gateway
aws apigateway get-rest-api --rest-api-id $(jq -r .api_gateway_id deployment-config.json)
# Should return API details

# Check Cognito User Pool
aws cognito-idp describe-user-pool --user-pool-id $(jq -r .user_pool_id deployment-config.json)
# Should return pool details

# Check AgentCore Gateway
aws bedrock-agentcore-control get-gateway \
  --gateway-identifier $(jq -r .gateway_id deployment-config.json) \
  --query 'status' --output text
# Should return: READY

# Check Gateway Target
aws bedrock-agentcore-control get-gateway-target \
  --gateway-identifier $(jq -r .gateway_id deployment-config.json) \
  --target-id $(jq -r .target_id deployment-config.json) \
  --query 'status' --output text
# Should return: READY
```

### Functional Verification

- [ ] Lambda function responds to test invocation
- [ ] API Gateway endpoints accessible
- [ ] Cognito generates ACCESS tokens
- [ ] AgentCore Gateway status: READY
- [ ] Gateway Target status: READY
- [ ] MCP test passes (test-final.py)
- [ ] Chatbot demo works (chatbot-final.py)
- [ ] Interactive chat functional (interactive-chat.py)

---

## Troubleshooting Common Setup Issues

### Issue 1: AWS CLI Not Configured

**Error:**
```
Unable to locate credentials. You can configure credentials by running "aws configure".
```

**Solution:**
```bash
aws configure
# Enter your AWS credentials
```

### Issue 2: Python Package Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'boto3'
```

**Solution:**
```bash
pip install -r requirements.txt
```

### Issue 3: Permission Denied Errors

**Error:**
```
An error occurred (AccessDeniedException) when calling the CreateGateway operation
```

**Solution:**
- Verify IAM user/role has required permissions
- Check AWS account has AgentCore service enabled
- Ensure region supports AgentCore (use us-east-1)

### Issue 4: Region Not Supported

**Error:**
```
Service bedrock-agentcore-control not available in region
```

**Solution:**
```bash
# Use us-east-1 region
aws configure set region us-east-1

# Or specify in commands
aws bedrock-agentcore-control ... --region us-east-1
```

### Issue 5: Deployment Script Fails

**Error:**
```
Various errors during deploy.py execution
```

**Solution:**
1. Check all prerequisites are met
2. Review error message for specific issue
3. Try manual deployment steps in SETUP.md
4. Check TROUBLESHOOTING.md for specific error

---

## Environment Variables (Optional)

For advanced users, you can set environment variables:

```bash
# AWS Configuration
export AWS_REGION=us-east-1
export AWS_PROFILE=default

# Project Configuration
export GATEWAY_NAME=petstoregateway
export API_STAGE=prod
export COGNITO_USERNAME=testuser
export COGNITO_PASSWORD=MySecurePass123!

# Use in scripts
python3 deploy.py
```

---

## Next Steps After Setup

1. **Review Documentation:**
   - Read `README.md` for overview
   - Check `ARCHITECTURE_DIAGRAMS.md` for visual understanding
   - Review `PROJECT_WRITEUP.md` for detailed analysis

2. **Run Tests:**
   - Execute `test-final.py` for MCP protocol validation
   - Run `chatbot-final.py` for demo scenarios
   - Try `interactive-chat.py` for hands-on experience

3. **Explore Code:**
   - Review `deploy.py` for infrastructure setup
   - Study `test-final.py` for MCP implementation
   - Examine `chatbot-final.py` for AI agent integration

4. **Customize:**
   - Modify Lambda function for your use case
   - Add more API endpoints
   - Customize AI agent behavior
   - Implement additional tools

5. **Production Readiness:**
   - Enable CloudWatch logging
   - Implement proper error handling
   - Add monitoring and alerts
   - Configure backup and recovery
   - Review security best practices

---

## Cost Considerations

**Estimated Monthly Costs (Light Usage):**
- Lambda: $0.20 (1M requests free tier)
- API Gateway: $3.50 (1M requests)
- Cognito: Free (50,000 MAU free tier)
- AgentCore Gateway: ~$3.00 (usage-based)
- **Total: ~$7.20/month**

**Cost Optimization:**
- Use free tier where available
- Delete resources when not in use (run cleanup.py)
- Monitor usage with AWS Cost Explorer
- Set up billing alerts

---

## Support and Resources

**Documentation:**
- `README.md` - Quick start guide
- `SETUP.md` - Detailed setup instructions
- `TROUBLESHOOTING.md` - Common issues and solutions
- `DEMO.md` - Demo instructions
- `ARCHITECTURE_DIAGRAMS.md` - Visual architecture
- `PROJECT_WRITEUP.md` - STAR method analysis

**AWS Resources:**
- [AgentCore Gateway Documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway.html)
- [MCP Specification](https://spec.modelcontextprotocol.io/)
- [AWS CLI Reference](https://docs.aws.amazon.com/cli/)

**Community:**
- GitHub Issues for bug reports
- GitHub Discussions for questions
- AWS Support for service issues

---

## Cleanup

When done testing, remove all resources:

```bash
# Run cleanup script
python3 cleanup.py

# Verify all resources deleted
aws lambda list-functions | grep PetStoreFunction
aws apigateway get-rest-apis | grep PetStoreAPI
aws cognito-idp list-user-pools --max-results 10 | grep PetStoreUsers
aws bedrock-agentcore-control list-gateways | grep petstoregateway

# All should return empty results
```

This ensures no ongoing charges for unused resources.
