#!/usr/bin/env python3
"""
Interactive AI Chatbot with AgentCore Memory
Conversation history persists across sessions
"""

import json
import boto3
import uuid
from datetime import datetime
from strands import Agent
from strands.tools import tool
import httpx

# Load config
with open('deployment-config.json') as f:
    config = json.load(f)

with open('access-token.txt') as f:
    access_token = f.read().strip()

# AgentCore Memory configuration
MEMORY_ID = config.get('memory_id', 'YOUR_MEMORY_ID')  # Add this to deployment-config.json
REGION = config.get('region', 'us-east-1')
SESSION_ID = str(uuid.uuid4())  # Unique session per run

# Initialize AWS clients
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=REGION)

# Create MCP client
mcp_client = httpx.Client(
    base_url=config['gateway_url'],
    headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    },
    timeout=30.0
)

# Memory functions
def load_memory():
    """Load conversation history from AgentCore Memory"""
    try:
        response = bedrock_agent_runtime.get_memory(
            memoryId=MEMORY_ID,
            sessionId=SESSION_ID,
            maxResults=10
        )
        
        if 'memoryContents' in response and response['memoryContents']:
            print("\n💾 Loading previous conversation...")
            for item in response['memoryContents']:
                if 'userMessage' in item:
                    print(f"You: {item['userMessage']}")
                if 'assistantMessage' in item:
                    print(f"Assistant: {item['assistantMessage']}")
            print()
            return True
        return False
    except Exception as e:
        print(f"⚠️  Memory load failed: {e}")
        return False

def save_to_memory(user_message, assistant_message):
    """Save conversation to AgentCore Memory"""
    try:
        bedrock_agent_runtime.put_memory(
            memoryId=MEMORY_ID,
            sessionId=SESSION_ID,
            memoryContents=[
                {
                    'userMessage': user_message,
                    'assistantMessage': assistant_message
                }
            ]
        )
        return True
    except Exception as e:
        print(f"⚠️  Memory save failed: {e}")
        return False

# Tools
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

# Main
print("=" * 70)
print("🤖 AI Pet Store Assistant with Memory")
print("=" * 70)
print(f"\n📝 Session ID: {SESSION_ID}")

# Load previous conversation
load_memory()

print("\nAsk me anything about pets! Type 'quit' to exit.\n")

while True:
    try:
        question = input("You: ").strip()
        
        if not question:
            continue
            
        if question.lower() in ['quit', 'exit', 'q']:
            print("\n👋 Goodbye! Your conversation has been saved.")
            break
        
        print("\nAssistant: ", end="", flush=True)
        response = agent(question)
        print(response)
        print()
        
        # Save to memory
        save_to_memory(question, response)
        
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye! Your conversation has been saved.")
        break
    except Exception as e:
        print(f"\n❌ Error: {e}\n")

mcp_client.close()
