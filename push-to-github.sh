#!/bin/bash

# GitHub Push Script for AgentCore Gateway Demo

echo "=================================================="
echo "  AgentCore Gateway Demo - GitHub Push Script"
echo "=================================================="
echo ""

# Check if git remote exists
if git remote | grep -q "origin"; then
    echo "✅ Git remote 'origin' already configured"
    git remote -v
else
    echo "❌ No git remote configured"
    echo ""
    echo "Please add your GitHub repository as remote:"
    echo ""
    echo "  git remote add origin https://github.com/YOUR_USERNAME/agentcore-gateway-demo.git"
    echo ""
    echo "Or with SSH:"
    echo "  git remote add origin git@github.com:YOUR_USERNAME/agentcore-gateway-demo.git"
    echo ""
    exit 1
fi

echo ""
echo "Current branch:"
git branch --show-current

echo ""
echo "Recent commits:"
git log --oneline -5

echo ""
read -p "Push to GitHub? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Pushing to GitHub..."
    git push -u origin main
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "=================================================="
        echo "  ✅ Successfully pushed to GitHub!"
        echo "=================================================="
        echo ""
        echo "Your repository is now available at:"
        git remote get-url origin | sed 's/\.git$//'
        echo ""
    else
        echo ""
        echo "❌ Push failed. Please check:"
        echo "  1. GitHub repository exists"
        echo "  2. You have push permissions"
        echo "  3. Remote URL is correct"
        echo ""
    fi
else
    echo ""
    echo "Push cancelled."
fi
