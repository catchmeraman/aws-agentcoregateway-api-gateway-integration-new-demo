#!/usr/bin/env python3
"""
Interactive AI Chatbot - Ask questions about pets
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

@tool
def add_pet(name: str, pet_type: str, price: float) -> str:
    """Add a new pet to the store"""
    response = mcp_client.post("", json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "PetStoreTarget___AddPet",
            "arguments": {
                "name": name,
                "type": pet_type,
                "price": price
            }
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
    - Add new pets to the store
    - Answer questions about pets
    
    Always be friendly and helpful!""",
    tools=[list_pets, get_pet_by_id, add_pet]
)

print("=" * 70)
print("🤖 AI Pet Store Assistant")
print("=" * 70)
print("\nAsk me anything about pets! Type 'quit' to exit.\n")

while True:
    try:
        question = input("You: ").strip()
        
        if not question:
            continue
            
        if question.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Goodbye!")
            break
        
        print("\nAssistant: ", end="", flush=True)
        response = agent(question)
        print(response)
        print()
        
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        break
    except Exception as e:
        print(f"\n❌ Error: {e}\n")

mcp_client.close()
