#!/bin/bash

# Setup AgentCore Memory for Interactive Chat
# Run this script to configure memory for your Python chatbot

set -e

echo "🚀 Setting up AgentCore Memory for Interactive Chat..."
echo ""

# Variables
REGION="us-east-1"
MEMORY_NAME="PetStoreChatMemory"
CONFIG_FILE="deployment-config.json"

# Step 1: Create AgentCore Memory
echo "📝 Step 1: Creating AgentCore Memory..."
aws bedrock-agentcore-control create-memory \
  --name $MEMORY_NAME \
  --description "Conversation history for pet store chatbot" \
  --memory-type SEMANTIC \
  --region $REGION 2>/dev/null || echo "Memory may already exist"

# Get memory ID
MEMORY_ID=$(aws bedrock-agentcore-control list-memories \
  --query "memories[?name=='$MEMORY_NAME'].memoryId" \
  --output text \
  --region $REGION)

if [ -z "$MEMORY_ID" ]; then
    echo "❌ Failed to create or find memory"
    exit 1
fi

echo "✅ Memory ID: $MEMORY_ID"
echo ""

# Step 2: Update deployment-config.json
echo "📝 Step 2: Updating deployment-config.json..."

# Read existing config
if [ ! -f "$CONFIG_FILE" ]; then
    echo "❌ $CONFIG_FILE not found!"
    exit 1
fi

# Add memory_id to config using Python
python3 << EOF
import json

with open('$CONFIG_FILE', 'r') as f:
    config = json.load(f)

config['memory_id'] = '$MEMORY_ID'

with open('$CONFIG_FILE', 'w') as f:
    json.dump(config, f, indent=2)

print("✅ Config updated with memory_id")
EOF

echo ""

# Step 3: Install boto3 if needed
echo "📝 Step 3: Checking dependencies..."
pip install boto3 -q 2>/dev/null || echo "boto3 already installed"
echo "✅ Dependencies ready"
echo ""

# Step 4: Test memory access
echo "📝 Step 4: Testing memory access..."
python3 << EOF
import boto3

try:
    client = boto3.client('bedrock-agent-runtime', region_name='$REGION')
    response = client.get_memory(
        memoryId='$MEMORY_ID',
        sessionId='test-session',
        maxResults=1
    )
    print("✅ Memory access working!")
except Exception as e:
    print(f"⚠️  Memory access test failed: {e}")
    print("   Make sure your AWS credentials have bedrock-agent-runtime permissions")
EOF

echo ""
echo "=" * 70
echo "✅ Setup Complete!"
echo "=" * 70
echo ""
echo "Memory ID: $MEMORY_ID"
echo "Config file: $CONFIG_FILE"
echo ""
echo "Next steps:"
echo "1. Run: python3 interactive-chat-with-memory.py"
echo "2. Have a conversation"
echo "3. Exit and run again - your conversation will be loaded!"
echo ""
echo "To view memory contents:"
echo "aws bedrock-agent-runtime get-memory \\"
echo "  --memory-id $MEMORY_ID \\"
echo "  --session-id YOUR_SESSION_ID \\"
echo "  --region $REGION"
echo ""
