#!/bin/bash

# Quick Git Workflow Script
# Make this executable with: chmod +x quick-git.sh

echo "📊 Checking Git status..."
git status

echo ""
echo "📥 Pulling latest changes from GitHub..."
git pull origin main

echo ""
echo "Would you like to commit and push your changes? (y/n)"
read -r response

if [[ "$response" == "y" ]]; then
    echo ""
    echo "Enter your commit message:"
    read -r commit_message
    
    echo ""
    echo "📝 Adding files..."
    git add .
    
    echo "💾 Committing..."
    git commit -m "$commit_message"
    
    echo "🚀 Pushing to GitHub..."
    git push origin main
    
    echo "✅ Done!"
else
    echo "Skipping commit and push."
fi
