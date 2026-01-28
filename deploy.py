#!/usr/bin/env python3
"""
Complete AgentCore Gateway Deployment Script
Deploys: Lambda, API Gateway, Cognito, IAM Roles, AgentCore Gateway
Account: 114805761158
Region: us-east-1
"""

import boto3
import json
import time
import zipfile
from io import BytesIO

# Configuration
ACCOUNT_ID = "114805761158"
REGION = "us-east-1"

# Initialize AWS clients
iam = boto3.client('iam', region_name=REGION)
apigw = boto3.client('apigateway', region_name=REGION)
cognito = boto3.client('cognito-idp', region_name=REGION)
lambda_client = boto3.client('lambda', region_name=REGION)
agentcore = boto3.client('bedrock-agentcore-control', region_name=REGION)

print("=" * 70)
print("🚀 AgentCore Gateway Deployment")
print("=" * 70)
print(f"Account: {ACCOUNT_ID}")
print(f"Region: {REGION}")
print("=" * 70)

# ============================================================================
# STEP 1: Create Lambda Function for Pet Store Backend
# ============================================================================
print("\n[1/6] Creating Lambda Function...")

lambda_code = '''import json

def lambda_handler(event, context):
    path = event.get('path', '')
    method = event.get('httpMethod', '')
    
    pets = [
        {"id": 1, "type": "dog", "name": "Buddy", "price": 249.99},
        {"id": 2, "type": "cat", "name": "Whiskers", "price": 124.99},
        {"id": 3, "type": "fish", "name": "Nemo", "price": 0.99}
    ]
    
    if path == '/pets' and method == 'GET':
        return {
            'statusCode': 200,
            'body': json.dumps(pets),
            'headers': {'Content-Type': 'application/json'}
        }
    elif path.startswith('/pets/') and method == 'GET':
        pet_id = int(path.split('/')[-1])
        pet = next((p for p in pets if p['id'] == pet_id), None)
        if pet:
            return {
                'statusCode': 200,
                'body': json.dumps(pet),
                'headers': {'Content-Type': 'application/json'}
            }
        return {'statusCode': 404, 'body': json.dumps({'error': 'Pet not found'})}
    
    return {'statusCode': 404, 'body': json.dumps({'error': 'Not found'})}
'''

# Create Lambda execution role
lambda_trust_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "lambda.amazonaws.com"},
        "Action": "sts:AssumeRole"
    }]
}

try:
    lambda_role = iam.create_role(
        RoleName='PetStoreLambdaRole',
        AssumeRolePolicyDocument=json.dumps(lambda_trust_policy),
        Description='Execution role for Pet Store Lambda function'
    )
    lambda_role_arn = lambda_role['Role']['Arn']
    print(f"   ✅ Lambda role created: {lambda_role_arn}")
    
    iam.attach_role_policy(
        RoleName='PetStoreLambdaRole',
        PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
    )
    time.sleep(10)
except iam.exceptions.EntityAlreadyExistsException:
    lambda_role_arn = f"arn:aws:iam::{ACCOUNT_ID}:role/PetStoreLambdaRole"
    print(f"   ℹ️  Lambda role already exists: {lambda_role_arn}")

# Package Lambda code
zip_buffer = BytesIO()
with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
    zip_file.writestr('lambda_function.py', lambda_code)
zip_buffer.seek(0)

try:
    lambda_func = lambda_client.create_function(
        FunctionName='PetStoreFunction',
        Runtime='python3.12',
        Role=lambda_role_arn,
        Handler='lambda_function.lambda_handler',
        Code={'ZipFile': zip_buffer.read()},
        Timeout=30,
        Description='Pet Store API backend'
    )
    lambda_arn = lambda_func['FunctionArn']
    print(f"   ✅ Lambda function created: {lambda_arn}")
except lambda_client.exceptions.ResourceConflictException:
    lambda_arn = f"arn:aws:lambda:{REGION}:{ACCOUNT_ID}:function:PetStoreFunction"
    print(f"   ℹ️  Lambda function already exists: {lambda_arn}")

# ============================================================================
# STEP 2: Create API Gateway REST API
# ============================================================================
print("\n[2/6] Creating API Gateway...")

api = apigw.create_rest_api(
    name='PetStoreAPI',
    description='Sample Pet Store API for AgentCore Gateway',
    endpointConfiguration={'types': ['REGIONAL']}
)
api_id = api['id']
print(f"   ✅ API Gateway created: {api_id}")

# Get root resource
resources = apigw.get_resources(restApiId=api_id)
root_id = resources['items'][0]['id']

# Create /pets resource
pets_resource = apigw.create_resource(
    restApiId=api_id,
    parentId=root_id,
    pathPart='pets'
)
pets_resource_id = pets_resource['id']

# Create /pets/{petId} resource
pet_id_resource = apigw.create_resource(
    restApiId=api_id,
    parentId=pets_resource_id,
    pathPart='{petId}'
)
pet_id_resource_id = pet_id_resource['id']

# Add GET method to /pets
apigw.put_method(
    restApiId=api_id,
    resourceId=pets_resource_id,
    httpMethod='GET',
    authorizationType='AWS_IAM'
)

apigw.put_integration(
    restApiId=api_id,
    resourceId=pets_resource_id,
    httpMethod='GET',
    type='AWS_PROXY',
    integrationHttpMethod='POST',
    uri=f'arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'
)

# Add GET method to /pets/{petId}
apigw.put_method(
    restApiId=api_id,
    resourceId=pet_id_resource_id,
    httpMethod='GET',
    authorizationType='AWS_IAM'
)

apigw.put_integration(
    restApiId=api_id,
    resourceId=pet_id_resource_id,
    httpMethod='GET',
    type='AWS_PROXY',
    integrationHttpMethod='POST',
    uri=f'arn:aws:apigateway:{REGION}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations'
)

# Grant API Gateway permission to invoke Lambda
try:
    lambda_client.add_permission(
        FunctionName='PetStoreFunction',
        StatementId='apigateway-invoke',
        Action='lambda:InvokeFunction',
        Principal='apigateway.amazonaws.com',
        SourceArn=f'arn:aws:execute-api:{REGION}:{ACCOUNT_ID}:{api_id}/*/*'
    )
except lambda_client.exceptions.ResourceConflictException:
    pass

# Deploy API
deployment = apigw.create_deployment(
    restApiId=api_id,
    stageName='prod',
    description='Production deployment'
)
print(f"   ✅ API deployed to stage: prod")
print(f"   🔗 Endpoint: https://{api_id}.execute-api.{REGION}.amazonaws.com/prod")

# ============================================================================
# STEP 3: Create IAM Role for AgentCore Gateway
# ============================================================================
print("\n[3/6] Creating IAM Role for AgentCore Gateway...")

gateway_trust_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "bedrock-agentcore.amazonaws.com"},
        "Action": "sts:AssumeRole"
    }]
}

gateway_policy = {
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Action": ["execute-api:Invoke"],
        "Resource": f"arn:aws:execute-api:{REGION}:{ACCOUNT_ID}:{api_id}/prod/*/*"
    }]
}

try:
    gateway_role = iam.create_role(
        RoleName='AgentCoreGatewayRole',
        AssumeRolePolicyDocument=json.dumps(gateway_trust_policy),
        Description='Service role for AgentCore Gateway'
    )
    gateway_role_arn = gateway_role['Role']['Arn']
    
    iam.put_role_policy(
        RoleName='AgentCoreGatewayRole',
        PolicyName='APIGatewayAccess',
        PolicyDocument=json.dumps(gateway_policy)
    )
    print(f"   ✅ Gateway role created: {gateway_role_arn}")
    time.sleep(10)
except iam.exceptions.EntityAlreadyExistsException:
    gateway_role_arn = f"arn:aws:iam::{ACCOUNT_ID}:role/AgentCoreGatewayRole"
    print(f"   ℹ️  Gateway role already exists: {gateway_role_arn}")

# ============================================================================
# STEP 4: Create Cognito User Pool
# ============================================================================
print("\n[4/6] Creating Cognito User Pool...")

try:
    user_pool = cognito.create_user_pool(
        PoolName='AgentCoreUserPool',
        AutoVerifiedAttributes=['email'],
        Policies={
            'PasswordPolicy': {
                'MinimumLength': 8,
                'RequireUppercase': True,
                'RequireLowercase': True,
                'RequireNumbers': True,
                'RequireSymbols': True
            }
        }
    )
    user_pool_id = user_pool['UserPool']['Id']
    
    app_client = cognito.create_user_pool_client(
        UserPoolId=user_pool_id,
        ClientName='AgentCoreClient',
        GenerateSecret=False,
        ExplicitAuthFlows=['ALLOW_USER_PASSWORD_AUTH', 'ALLOW_REFRESH_TOKEN_AUTH']
    )
    client_id = app_client['UserPoolClient']['ClientId']
    
    discovery_url = f"https://cognito-idp.{REGION}.amazonaws.com/{user_pool_id}/.well-known/openid-configuration"
    print(f"   ✅ Cognito User Pool created: {user_pool_id}")
    print(f"   ✅ Client ID: {client_id}")
except Exception as e:
    print(f"   ⚠️  Cognito creation error: {e}")
    user_pool_id = "us-east-1_RNmMBC87g"
    client_id = "435iqd7cgbn2slmgn0a36fo9lf"
    discovery_url = f"https://cognito-idp.{REGION}.amazonaws.com/{user_pool_id}/.well-known/openid-configuration"
    print(f"   ℹ️  Using existing pool: {user_pool_id}")

# ============================================================================
# STEP 5: Create AgentCore Gateway
# ============================================================================
print("\n[5/6] Creating AgentCore Gateway...")

auth_config = {
    "customJWTAuthorizer": {
        "allowedClients": [client_id],
        "discoveryUrl": discovery_url
    }
}

gateway = agentcore.create_gateway(
    name='PetStoreGateway',
    roleArn=gateway_role_arn,
    protocolType='MCP',
    protocolConfiguration={
        'mcp': {
            'supportedVersions': ['2025-03-26'],
            'searchType': 'SEMANTIC'
        }
    },
    authorizerType='CUSTOM_JWT',
    authorizerConfiguration=auth_config,
    description='AgentCore Gateway for Pet Store API'
)

gateway_id = gateway['gatewayId']
gateway_url = gateway['gatewayUrl']
print(f"   ✅ Gateway created: {gateway_id}")
print(f"   🔗 Gateway URL: {gateway_url}")

# Wait for gateway to be ready
print("   ⏳ Waiting for gateway to be READY...")
for i in range(20):
    time.sleep(10)
    gw = agentcore.get_gateway(gatewayIdentifier=gateway_id)
    status = gw['status']
    print(f"      Attempt {i+1}/20: Status = {status}")
    if status == 'READY':
        print("   ✅ Gateway is READY!")
        break
    elif status == 'FAILED':
        print("   ❌ Gateway creation failed")
        exit(1)

# ============================================================================
# STEP 6: Create Gateway Target
# ============================================================================
print("\n[6/6] Creating Gateway Target...")

target_config = {
    "mcp": {
        "apiGateway": {
            "restApiId": api_id,
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
                        "description": "Retrieves all available pets in the store"
                    },
                    {
                        "name": "GetPetById",
                        "path": "/pets/{petId}",
                        "method": "GET",
                        "description": "Retrieve a specific pet by its ID"
                    }
                ]
            }
        }
    }
}

target = agentcore.create_gateway_target(
    name='PetStoreTarget',
    gatewayIdentifier=gateway_id,
    targetConfiguration=target_config,
    credentialProviderConfigurations=[{"credentialProviderType": "GATEWAY_IAM_ROLE"}]
)

target_id = target['targetId']
print(f"   ✅ Target created: {target_id}")

# ============================================================================
# Save Configuration
# ============================================================================
config = {
    "account_id": ACCOUNT_ID,
    "region": REGION,
    "api_gateway_id": api_id,
    "api_gateway_stage": "prod",
    "api_gateway_endpoint": f"https://{api_id}.execute-api.{REGION}.amazonaws.com/prod",
    "lambda_function_name": "PetStoreFunction",
    "lambda_arn": lambda_arn,
    "lambda_role_arn": lambda_role_arn,
    "gateway_role_arn": gateway_role_arn,
    "user_pool_id": user_pool_id,
    "client_id": client_id,
    "discovery_url": discovery_url,
    "gateway_id": gateway_id,
    "gateway_url": gateway_url,
    "target_id": target_id
}

with open('deployment-config.json', 'w') as f:
    json.dump(config, f, indent=2)

print("\n" + "=" * 70)
print("✨ DEPLOYMENT COMPLETE!")
print("=" * 70)
print(f"\n📋 Configuration saved to: deployment-config.json")
print(f"\n🔗 Resources:")
print(f"   API Gateway: {api_id}")
print(f"   Gateway ID: {gateway_id}")
print(f"   Gateway URL: {gateway_url}")
print(f"   User Pool: {user_pool_id}")
print(f"   Client ID: {client_id}")
print("\n" + "=" * 70)
