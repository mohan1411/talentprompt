#!/bin/bash

# Chrome Extension Production Build Script

echo "🚀 Building Promtitude Chrome Extension for Production..."

# Create a temporary build directory
BUILD_DIR="promtitude-extension-production"
rm -rf $BUILD_DIR
mkdir -p $BUILD_DIR

# Copy all necessary files
echo "📁 Copying extension files..."
cp -r assets $BUILD_DIR/
cp -r background $BUILD_DIR/
cp -r content $BUILD_DIR/
cp -r popup $BUILD_DIR/

# Use production manifest
echo "📝 Using production manifest..."
cp manifest-production.json $BUILD_DIR/manifest.json

# Remove any development files
echo "🧹 Cleaning up development files..."
find $BUILD_DIR -name "*.py" -type f -delete
find $BUILD_DIR -name "*.sh" -type f -delete
find $BUILD_DIR -name "*.md" -type f -delete
find $BUILD_DIR -name ".DS_Store" -type f -delete
find $BUILD_DIR -name "test-*" -type f -delete
find $BUILD_DIR -name "debug-*" -type f -delete
find $BUILD_DIR -name "*-test.*" -type f -delete
find $BUILD_DIR -name "generate-*" -type f -delete

# Update API URLs in JavaScript files
echo "🔄 Updating API URLs for production..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    find $BUILD_DIR -name "*.js" -type f -exec sed -i '' 's|http://localhost:8000|https://talentprompt-production.up.railway.app|g' {} \;
    find $BUILD_DIR -name "*.js" -type f -exec sed -i '' 's|http://localhost:3000|https://promtitude.com|g' {} \;
else
    # Linux
    find $BUILD_DIR -name "*.js" -type f -exec sed -i 's|http://localhost:8000|https://talentprompt-production.up.railway.app|g' {} \;
    find $BUILD_DIR -name "*.js" -type f -exec sed -i 's|http://localhost:3000|https://promtitude.com|g' {} \;
fi

# Create the ZIP file
echo "📦 Creating ZIP file..."
ZIP_NAME="promtitude-extension-v1.0.0.zip"
rm -f $ZIP_NAME
cd $BUILD_DIR
zip -r ../$ZIP_NAME * -x "*.DS_Store" "*/\.*"
cd ..

# Clean up
echo "🧹 Cleaning up build directory..."
rm -rf $BUILD_DIR

echo "✅ Production build complete!"
echo "📦 Output: $ZIP_NAME"
echo ""
echo "📋 Next steps:"
echo "1. Generate new icons using chrome-extension-icon-generator.html"
echo "2. Replace the icon files in the ZIP"
echo "3. Take screenshots of the extension in action"
echo "4. Upload to Chrome Web Store"
echo ""
echo "💡 Don't forget to:"
echo "- Test the extension in production mode"
echo "- Pay the $5 developer fee"
echo "- Submit for review"