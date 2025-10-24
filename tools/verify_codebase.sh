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

# Directory setup
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
cd "$PROJECT_ROOT"

# Virtual environment setup
setup_venv() {
    info "Setting up virtual environment..."
    python3 -m venv verify_env
    source verify_env/bin/activate
    pip install -e '.[dev]'
    info "Virtual environment ready"
}

# Code formatting
format_code() {
    info "Formatting code with black..."
    black src/ tests/
    info "Code formatting completed"
}

# Lint check
lint_check() {
    info "Running linting checks..."
    flake8 src/ tests/ --max-line-length=100 --ignore=E402,W503
    info "Linting completed"
}

# Type checking
type_check() {
    info "Running type checks..."
    mypy src/ tests/ --ignore-missing-imports
    info "Type checking completed"
}

# Test run
run_tests() {
    info "Running tests..."
    pytest tests/ -v --cov=src
    info "Tests completed"
}

# Check import structure
check_imports() {
    info "Checking import structure..."
    # Look for common import issues
    ! find src/ tests/ -type f -name "*.py" -exec grep -l "import \*" {} \; | while read -r file; do
        warn "Wildcard import found in $file"
    done
    info "Import check completed"
}

# Check file headers
check_headers() {
    info "Checking file headers..."
    find src/ tests/ -type f -name "*.py" -exec grep -L "^#.*\|^\"\"\".*\|^$" {} \; | while read -r file; do
        warn "Missing header documentation in $file"
    done
    info "Header check completed"
}

# Clean up temporary files
cleanup() {
    info "Cleaning up..."
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete
    find . -type f -name ".coverage" -delete
    info "Cleanup completed"
}

# Main execution
main() {
    info "Starting code verification..."
    
    # Setup virtual environment
    setup_venv
    
    # Run all checks
    format_code
    lint_check
    type_check
    check_imports
    check_headers
    run_tests
    
    # Clean up
    cleanup
    
    info "Code verification completed."
}

# Execute main if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main
fi