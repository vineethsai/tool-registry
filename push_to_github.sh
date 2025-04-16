#!/bin/bash
# push_to_github.sh - Script to push new version to GitHub and create a release

set -e  # Exit on any error

VERSION="1.0.9"
BRANCH="main"
REPO_URL="https://github.com/yourusername/tool-registry.git"  # Update this to your actual repository URL

echo "Preparing to push Tool Registry version $VERSION to GitHub..."

# Ensure we're on the correct branch
git checkout $BRANCH || { echo "Error: Failed to checkout branch $BRANCH"; exit 1; }

# Pull latest changes to avoid conflicts
git pull origin $BRANCH || { echo "Warning: Failed to pull latest changes. Continuing anyway..."; }

# Add all changes
git add .

# Commit changes
git commit -m "Release v$VERSION: Comprehensive API endpoint testing and improved compatibility"

# Push to GitHub
git push origin $BRANCH || { echo "Error: Failed to push to GitHub"; exit 1; }

# Create a tag for the release
git tag -a "v$VERSION" -m "Tool Registry v$VERSION"
git push origin "v$VERSION" || { echo "Error: Failed to push tag to GitHub"; exit 1; }

# Create GitHub release using the GitHub CLI (requires gh to be installed)
if command -v gh &> /dev/null; then
    echo "Creating GitHub release using gh CLI..."
    gh release create "v$VERSION" \
        --title "Tool Registry v$VERSION" \
        --notes-file RELEASE_NOTES.md
else
    echo "GitHub CLI (gh) not found. Skipping automatic release creation."
    echo "Please create the release manually in the GitHub web interface."
fi

echo ""
echo "Tool Registry version $VERSION has been pushed to GitHub."
echo "Release tag: v$VERSION"
echo ""
echo "Docker image should now be built automatically by GitHub Actions." 