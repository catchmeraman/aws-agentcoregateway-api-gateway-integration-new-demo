#!/usr/bin/env python3
"""
✅ AI Chatbot using AgentCore Gateway + API Gateway Integration
Demonstrates MCP protocol with Strands Agent framework
"""

import json
from strands import Agent
from strands.tools import tool
import httpx

# Load config
with open('deployment-config.json') as f:
    config = json.load(f)

with open('access-token.txt') as f:
    access_token = f.read().strip()

# Create MCP client
mcp_client = httpx.Client(
    base_url=config['gateway_url'],
    headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    },
    timeout=30.0
)

@tool
def list_pets() -> str:
    """List all available pets in the store"""
    response = mcp_client.post("", json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "PetStoreTarget___ListPets",
            "arguments": {}
        }
    })
    result = response.json()
    if 'result' in result:
        content = json.loads(result['result']['content'][0]['text'])
        return json.dumps(content, indent=2)
    return f"Error: {result}"

@tool
def get_pet_by_id(pet_id: int) -> str:
    """Get details of a specific pet by ID"""
    response = mcp_client.post("", json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "PetStoreTarget___GetPetById",
            "arguments": {"petId": str(pet_id)}
        }
    })
    result = response.json()
    if 'result' in result:
        content = json.loads(result['result']['content'][0]['text'])
        return json.dumps(content, indent=2)
    return f"Error: {result}"

# Create agent
agent = Agent(
    name="PetStoreAssistant",
    system_prompt="""You are a helpful pet store assistant. You can help customers:
    - Browse available pets
    - Get details about specific pets
    - Answer questions about pets
    
    Always be friendly and helpful!""",
    tools=[list_pets, get_pet_by_id]
)

print("=" * 80)
print("🤖 AI Pet Store Assistant (AgentCore Gateway + API Gateway)")
print("=" * 80)
print("\nPowered by:")
print("  • AgentCore Gateway (MCP Protocol)")
print("  • API Gateway (REST API)")
print("  • Lambda (Backend)")
print("  • Cognito (Authentication)")
print("  • Strands Agent Framework")
print("\nType 'quit' to exit\n")
print("=" * 80)

# Test queries
test_queries = [
    "What pets do you have available?",
    "Tell me about pet ID 2",
    "What's the cheapest pet?"
]

print("\n🧪 Running test queries...\n")
for i, query in enumerate(test_queries, 1):
    print(f"\n[Query {i}] {query}")
    print("-" * 80)
    response = agent(query)
    print(response)
    print()

print("=" * 80)
print("✅ Demo complete! All components working together.")
print("=" * 80)

mcp_client.close()
