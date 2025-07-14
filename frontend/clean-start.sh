#!/bin/bash

echo "Cleaning Next.js build files..."

# Try to remove .next directory
if [ -d ".next" ]; then
    echo "Removing .next directory..."
    rm -rf .next 2>/dev/null || echo "Could not remove .next (permission issue)"
fi

# Clear Node.js cache
echo "Clearing npm cache..."
npm cache clean --force

# Install dependencies
echo "Installing dependencies..."
npm install

# Start dev server
echo "Starting development server..."
npm run dev