#!/bin/bash

# Make sure the script terminates on errors
set -e

# Check if Git is installed
if ! command -v git &> /dev/null; then
    echo "Git is not installed. Please install Git and try again."
    exit 1
fi

# Check if the repository has been initialized
if [ ! -d .git ]; then
    echo "Initializing Git repository..."
    git init
fi

# Check if a remote named 'origin' exists
if ! git remote | grep -q "^origin$"; then
    echo "Please enter the GitHub repository URL (e.g., https://github.com/yourusername/tool-registry.git):"
    read repo_url
    git remote add origin $repo_url
fi

# Add all files
git add .

# Commit changes
echo "Enter a commit message (e.g., 'Updated documentation and README'):"
read commit_message
git commit -m "$commit_message"

# Push to GitHub
echo "Pushing to GitHub..."
git push -u origin main || git push -u origin master

echo "Successfully pushed to GitHub!" 