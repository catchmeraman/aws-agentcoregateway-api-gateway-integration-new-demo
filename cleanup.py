#!/usr/bin/env python3
"""
Cleanup Script - Deletes all deployed resources
"""

import boto3
import json
import sys
import time

# Load deployment config
try:
    with open('deployment-config.json', 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    print("❌ deployment-config.json not found. Nothing to clean up.")
    sys.exit(1)

iam = boto3.client('iam', region_name=config['region'])
apigw = boto3.client('apigateway', region_name=config['region'])
cognito = boto3.client('cognito-idp', region_name=config['region'])
lambda_client = boto3.client('lambda', region_name=config['region'])
agentcore = boto3.client('bedrock-agentcore-control', region_name=config['region'])

print("=" * 70)
print("🧹 Cleaning Up AgentCore Gateway Deployment")
print("=" * 70)
print("\n⚠️  This will delete ALL deployed resources!")
confirm = input("Type 'DELETE' to confirm: ")

if confirm != 'DELETE':
    print("❌ Cleanup cancelled")
    sys.exit(0)

# ============================================================================
# Delete Gateway Target
# ============================================================================
print("\n[1/7] Deleting Gateway Target...")
try:
    agentcore.delete_gateway_target(
        gatewayIdentifier=config['gateway_id'],
        targetId=config['target_id']
    )
    print(f"   ✅ Target deleted: {config['target_id']}")
    time.sleep(5)
except Exception as e:
    print(f"   ⚠️  Error: {e}")

# ============================================================================
# Delete Gateway
# ============================================================================
print("\n[2/7] Deleting AgentCore Gateway...")
try:
    agentcore.delete_gateway(gatewayIdentifier=config['gateway_id'])
    print(f"   ✅ Gateway deleted: {config['gateway_id']}")
    time.sleep(5)
except Exception as e:
    print(f"   ⚠️  Error: {e}")

# ============================================================================
# Delete API Gateway
# ============================================================================
print("\n[3/7] Deleting API Gateway...")
try:
    apigw.delete_rest_api(restApiId=config['api_gateway_id'])
    print(f"   ✅ API Gateway deleted: {config['api_gateway_id']}")
except Exception as e:
    print(f"   ⚠️  Error: {e}")

# ============================================================================
# Delete Lambda Function
# ============================================================================
print("\n[4/7] Deleting Lambda Function...")
try:
    lambda_client.delete_function(FunctionName=config['lambda_function_name'])
    print(f"   ✅ Lambda deleted: {config['lambda_function_name']}")
except Exception as e:
    print(f"   ⚠️  Error: {e}")

# ============================================================================
# Delete IAM Roles
# ============================================================================
print("\n[5/7] Deleting IAM Roles...")

# Delete Gateway Role
try:
    iam.delete_role_policy(
        RoleName='AgentCoreGatewayRole',
        PolicyName='APIGatewayAccess'
    )
    iam.delete_role(RoleName='AgentCoreGatewayRole')
    print(f"   ✅ Gateway role deleted")
except Exception as e:
    print(f"   ⚠️  Gateway role error: {e}")

# Delete Lambda Role
try:
    iam.detach_role_policy(
        RoleName='PetStoreLambdaRole',
        PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
    )
    iam.delete_role(RoleName='PetStoreLambdaRole')
    print(f"   ✅ Lambda role deleted")
except Exception as e:
    print(f"   ⚠️  Lambda role error: {e}")

# ============================================================================
# Delete Cognito User Pool
# ============================================================================
print("\n[6/7] Deleting Cognito User Pool...")
try:
    cognito.delete_user_pool(UserPoolId=config['user_pool_id'])
    print(f"   ✅ User pool deleted: {config['user_pool_id']}")
except Exception as e:
    print(f"   ⚠️  Error: {e}")

# ============================================================================
# Delete Config Files
# ============================================================================
print("\n[7/7] Deleting Config Files...")
import os
try:
    os.remove('deployment-config.json')
    print(f"   ✅ Deleted: deployment-config.json")
except:
    pass

try:
    os.remove('jwt-token.txt')
    print(f"   ✅ Deleted: jwt-token.txt")
except:
    pass

print("\n" + "=" * 70)
print("✅ CLEANUP COMPLETE!")
print("=" * 70)
print("\nAll resources have been deleted from your AWS account.")
print("=" * 70)
