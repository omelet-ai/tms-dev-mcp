#!/bin/bash

# Define the main branch. Adjust this if your main branch is named differently.
MAIN_BRANCH="main"

# Fetch the latest changes from the remote repository
echo "Fetching the latest changes from the remote repository..."
git fetch --prune

# Switch to the main branch
echo "Switching to the main branch: $MAIN_BRANCH..."
git checkout $MAIN_BRANCH

# Pull the latest changes for the main branch
echo "Pulling the latest changes for the main branch..."
git pull origin $MAIN_BRANCH

# List all local branches excluding the main branch
echo "Listing all local branches..."
LOCAL_BRANCHES=$(git branch --format="%(refname:short)" | grep -v "^${MAIN_BRANCH}$")

# Loop through each local branch
for BRANCH in $LOCAL_BRANCHES; do
    # Check if the branch is merged into the main branch (use `origin/main` if detached at origin/main)
    if git branch --format="%(refname:short)" --merged origin/$MAIN_BRANCH | grep -Fxq "$BRANCH"; then
        # Check if the branch exists on the remote (using regex to account for slashes)
        if git branch -r | grep -Eq "origin/${BRANCH//\//\\/}"; then
            echo "Branch $BRANCH exists on the remote. Keeping it."
        else
            echo "Deleting local branch: $BRANCH..."
            git branch -d "$BRANCH"
        fi
    else
        echo "Branch $BRANCH is not merged into $MAIN_BRANCH. Keeping it."
    fi
done

echo "Cleanup complete!"
