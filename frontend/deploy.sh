#!/bin/bash
# Frontend deployment script for Vercel

echo "📦 Building frontend for production..."

# Install dependencies
echo "Installing dependencies..."
pnpm install

# Build the project
echo "Building..."
pnpm build

echo "✅ Build complete! Frontend is ready for deployment."
echo "📁 Build output: dist/"
echo ""
echo "To deploy to Vercel:"
echo "   vercel --prod"
