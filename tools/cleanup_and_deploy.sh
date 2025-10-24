#!/bin/bash
set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Print colored output
info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Function to check command exists
check_command() {
    if ! command -v "$1" &> /dev/null; then
        error "$1 could not be found. Please install it first."
        exit 1
    fi
}

# Check required commands
check_command git
check_command python3
check_command pip

# Directory cleanup
cleanup() {
    info "Cleaning up build and test artifacts..."
    
    # Remove Python cache files
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null || true
    
    # Remove build directories
    rm -rf build/ dist/ 2>/dev/null || true
    
    # Clean test environments
    rm -rf .tox/ .eggs/ 2>/dev/null || true
    find . -type d -name "test_env_*" -exec rm -rf {} + 2>/dev/null || true
    
    # Remove temporary test files
    find tests/ -type f -name "temp_*" -delete 2>/dev/null || true
    find tests/ -type f -name "test_*.log" -delete 2>/dev/null || true
    
    # Clean virtual environments (ask first)
    if [ -d "venv" ] || [ -d "test_env" ]; then
        read -p "Remove virtual environments (venv/test_env)? [y/N] " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf venv/ test_env/ 2>/dev/null || true
            info "Virtual environments removed."
        fi
    fi

    info "Cleanup completed."
}

# Git operations
git_operations() {
    info "Checking Git status..."
    
    # Check if we're in a git repository
    if ! git rev-parse --is-inside-work-tree > /dev/null 2>&1; then
        info "Initializing Git repository..."
        git init
    fi

    # Check for .gitignore
    if [ ! -f .gitignore ]; then
        info "Creating .gitignore file..."
        cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual Environment
venv/
test_env/
ENV/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Test
.pytest_cache/
.coverage
htmlcov/
.tox/
.nox/

# Logs
*.log
.eless_logs/

# Cache
.cache/
.eless_cache/

# Local config
config/local_*.yaml
EOF
    fi

    # Check if there are changes to commit
    if [ -n "$(git status --porcelain)" ]; then
        info "Changes detected. Preparing commit..."
        
        # Stage files
        git add .
        
        # Prompt for commit message
        echo "Enter commit message (or press Enter for default message):"
        read commit_msg
        if [ -z "$commit_msg" ]; then
            commit_msg="Update package and test suite"
        fi
        
        # Commit changes
        git commit -m "$commit_msg"
    else
        info "No changes to commit."
    fi
}

# Package verification
verify_package() {
    info "Verifying package..."
    
    # Check package structure
    python3 -m pip install --quiet check-manifest
    if ! check-manifest; then
        error "Package manifest verification failed."
        exit 1
    fi
    
    # Run tests
    python3 -m pip install --quiet pytest pytest-cov
    if ! python3 -m pytest tests/ -v --cov=src; then
        error "Tests failed."
        exit 1
    fi
    
    info "Package verification completed."
}

# Build package
build_package() {
    info "Building package..."
    
    # Install build dependencies
    python3 -m pip install --quiet build twine
    
    # Build package
    python3 -m build
    
    # Verify built files
    if [ ! -d "dist" ]; then
        error "Build failed - no dist directory."
        exit 1
    fi
    
    info "Package built successfully."
}

# GitHub operations
github_setup() {
    # Check if remote already exists
    if ! git remote | grep -q "^origin$"; then
        echo "Enter GitHub repository URL (or press Enter to skip):"
        read github_url
        if [ -n "$github_url" ]; then
            git remote add origin "$github_url"
            info "GitHub remote added."
        fi
    fi
    
    # Push if remote exists
    if git remote | grep -q "^origin$"; then
        echo "Push to GitHub? [y/N]"
        read -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # Ensure main branch exists
            if ! git rev-parse --verify main >/dev/null 2>&1; then
                git checkout -b main
            fi
            git push -u origin main
            info "Pushed to GitHub."
        fi
    fi
}

# PyPI operations
pypi_upload() {
    echo "Upload to PyPI? [y/N]"
    read -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Use Test PyPI first? [Y/n]"
        read -n 1 -r
        echo
        if [[ $REPLY =~ ^[Nn]$ ]]; then
            python3 -m twine upload dist/*
            info "Uploaded to PyPI."
        else
            python3 -m twine upload --repository testpypi dist/*
            info "Uploaded to Test PyPI."
        fi
    fi
}

# Main execution
main() {
    info "Starting deployment process..."
    
    cleanup
    git_operations
    verify_package
    build_package
    github_setup
    pypi_upload
    
    info "Deployment process completed."
}

# Execute main if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main
fi