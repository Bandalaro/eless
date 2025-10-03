#!/bin/bash

# ELESS Packaging and Release Script
# This script helps package and release ELESS to PyPI

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PACKAGE_NAME="eless"
BUILD_DIR="dist"
VENV_DIR="venv"

echo -e "${BLUE}🚀 ELESS Packaging and Release Script${NC}\n"

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if we're in the right directory
if [[ ! -f "pyproject.toml" ]]; then
    print_error "pyproject.toml not found. Make sure you're in the ELESS root directory."
    exit 1
fi

print_info "Current directory: $(pwd)"

# Step 1: Clean previous builds
echo -e "\n${BLUE}Step 1: Cleaning previous builds${NC}"
if [[ -d "$BUILD_DIR" ]]; then
    rm -rf "$BUILD_DIR"
    print_status "Removed existing $BUILD_DIR directory"
fi

if [[ -d "*.egg-info" ]]; then
    rm -rf *.egg-info
    print_status "Removed existing .egg-info directories"
fi

# Step 2: Set up virtual environment (if it doesn't exist)
echo -e "\n${BLUE}Step 2: Setting up virtual environment${NC}"
if [[ ! -d "$VENV_DIR" ]]; then
    python3 -m venv "$VENV_DIR"
    print_status "Created virtual environment"
fi

source "$VENV_DIR/bin/activate"
print_status "Activated virtual environment"

# Step 3: Install/upgrade build tools
echo -e "\n${BLUE}Step 3: Installing build tools${NC}"
pip install --upgrade pip
pip install --upgrade build twine wheel
print_status "Build tools updated"

# Step 4: Install development dependencies
echo -e "\n${BLUE}Step 4: Installing development dependencies${NC}"
pip install -e ".[dev]"
print_status "Development dependencies installed"

# Step 5: Run code quality checks
echo -e "\n${BLUE}Step 5: Running code quality checks${NC}"

# Check if black is available and run it
if command -v black &> /dev/null; then
    echo "Running black formatter..."
    black src/ --check
    print_status "Code formatting check passed"
else
    print_warning "black not available, skipping format check"
fi

# Check if flake8 is available and run it
if command -v flake8 &> /dev/null; then
    echo "Running flake8 linter..."
    flake8 src/ --max-line-length=88 --ignore=E501,W503
    print_status "Linting check passed"
else
    print_warning "flake8 not available, skipping lint check"
fi

# Step 6: Run tests (if test directory exists)
echo -e "\n${BLUE}Step 6: Running tests${NC}"
if [[ -d "tests" ]]; then
    pytest tests/ -v
    print_status "Tests passed"
else
    print_warning "No tests directory found, skipping tests"
fi

# Step 7: Build the package
echo -e "\n${BLUE}Step 7: Building the package${NC}"
python -m build
print_status "Package built successfully"

# Step 8: Check the build
echo -e "\n${BLUE}Step 8: Checking the build${NC}"
twine check "$BUILD_DIR"/*
print_status "Build check passed"

# Step 9: Show what was built
echo -e "\n${BLUE}Step 9: Build artifacts${NC}"
ls -la "$BUILD_DIR"/
print_status "Build artifacts listed above"

# Step 10: Test installation
echo -e "\n${BLUE}Step 10: Testing installation${NC}"
pip install "$BUILD_DIR"/*.whl --force-reinstall
print_status "Test installation successful"

# Verify the installation works
echo -e "\nTesting CLI..."
eless --help > /dev/null
print_status "CLI test passed"

# Step 11: Prompt for PyPI upload
echo -e "\n${BLUE}Step 11: PyPI Upload${NC}"
echo -e "${YELLOW}Build completed successfully!${NC}\n"

echo "Built files:"
ls -la "$BUILD_DIR"/

echo -e "\n${YELLOW}Next steps for PyPI release:${NC}"
echo "1. Test PyPI (recommended first):"
echo "   twine upload --repository testpypi dist/*"
echo ""
echo "2. Production PyPI:"
echo "   twine upload dist/*"
echo ""
echo "3. Install from Test PyPI to verify:"
echo "   pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ eless"
echo ""

read -p "Do you want to upload to Test PyPI now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "\n${BLUE}Uploading to Test PyPI...${NC}"
    twine upload --repository testpypi "$BUILD_DIR"/*
    print_status "Uploaded to Test PyPI"
    
    echo -e "\n${GREEN}🎉 Successfully uploaded to Test PyPI!${NC}"
    echo "Test installation with:"
    echo "pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ eless"
else
    echo -e "\n${BLUE}Skipping Test PyPI upload${NC}"
fi

echo -e "\n${GREEN}✅ Packaging complete!${NC}"

# Step 12: Provide final instructions
echo -e "\n${BLUE}Final Instructions:${NC}"
echo "1. If Test PyPI upload was successful and you've tested the installation:"
echo "   twine upload dist/*"
echo ""
echo "2. After uploading to production PyPI, users can install with:"
echo "   pip install eless                    # Core installation"
echo "   pip install eless[full]             # Full installation with all features"
echo "   pip install eless[embeddings]       # Just embedding models"
echo "   pip install eless[databases]        # Just database connectors"
echo "   pip install eless[parsers]          # Just document parsers"
echo ""
echo "3. Don't forget to:"
echo "   - Create a GitHub release with the same version tag"
echo "   - Update the README with installation instructions"
echo "   - Announce the release"
echo ""

print_status "All done! 🎉"