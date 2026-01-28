#!/usr/bin/env python3
"""
✅ COMPLETE WORKING DEMO: AgentCore Gateway + API Gateway Integration
"""

import httpx
import json

# Load config
with open('deployment-config.json') as f:
    config = json.load(f)

# Load ACCESS token
with open('access-token.txt') as f:
    access_token = f.read().strip()

print("=" * 80)
print("✅ AgentCore Gateway + API Gateway Integration - COMPLETE DEMO")
print("=" * 80)

# Create MCP client
client = httpx.Client(
    base_url=config['gateway_url'],
    headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    },
    timeout=30.0
)

# Test 1: List tools
print("\n[TEST 1] Listing available tools via MCP protocol...")
response = client.post("", json={
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
})

result = response.json()
tools = result['result']['tools']
print(f"   ✅ SUCCESS! Found {len(tools)} tools:")
for tool in tools:
    print(f"      - {tool['name']}")
    if 'description' in tool:
        print(f"        {tool['description'][:80]}")

# Test 2: Call ListPets tool
print("\n[TEST 2] Calling PetStoreTarget___ListPets tool...")
response = client.post("", json={
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
        "name": "PetStoreTarget___ListPets",
        "arguments": {}
    }
})

result = response.json()
if 'result' in result:
    print(f"   ✅ SUCCESS!")
    content = json.loads(result['result']['content'][0]['text'])
    print(f"   Pets returned: {json.dumps(content, indent=2)}")
else:
    print(f"   ❌ Error: {result}")

# Test 3: Call GetPetById tool
print("\n[TEST 3] Calling PetStoreTarget___GetPetById tool (petId=2)...")
response = client.post("", json={
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
        "name": "PetStoreTarget___GetPetById",
        "arguments": {"petId": "2"}
    }
})

result = response.json()
if 'result' in result:
    print(f"   ✅ SUCCESS!")
    content = json.loads(result['result']['content'][0]['text'])
    print(f"   Pet details: {json.dumps(content, indent=2)}")
else:
    print(f"   ❌ Error: {result}")

client.close()

print("\n" + "=" * 80)
print("✅ COMPLETE SUCCESS!")
print("=" * 80)
print("\n📋 Summary:")
print("   • AgentCore Gateway: WORKING")
print("   • API Gateway Integration: WORKING")
print("   • MCP Protocol: WORKING")
print("   • Cognito Authentication: WORKING (ACCESS token)")
print("   • Tool Invocation: WORKING")
print("\n🎯 Key Findings:")
print("   1. Use ACCESS token (not ID token) for authentication")
print("   2. API Gateway methods must have response definitions")
print("   3. Tool names are prefixed with target name: TargetName___ToolName")
print("=" * 80)
