# Publishing ELESS to PyPI

This guide will help you publish ELESS to PyPI so your friends can install it with `pip install eless`.

## 📋 Prerequisites

1. **PyPI Account**: Create accounts at:
   - [PyPI](https://pypi.org/account/register/) (production)
   - [TestPyPI](https://test.pypi.org/account/register/) (testing)

2. **Install build tools**:
   ```bash
   pip install build twine
   ```

## 🔧 Pre-Publishing Setup

### 1. Update Package Information
Edit `pyproject.toml` and update:
- `authors` - Add your email
- `project.urls` - Update GitHub URLs to your repository
- `version` - Increment for new releases

### 2. Create GitHub Repository
```bash
# Initialize git repository
git init
git add .
git commit -m "Initial ELESS package"

# Create GitHub repo and push
git remote add origin https://github.com/yourusername/eless.git
git branch -M main
git push -u origin main
```

### 3. Test the Package Locally
```bash
# Build the package
python -m build

# Install locally to test
pip install dist/eless-1.0.0-py3-none-any.whl

# Test the CLI
eless --help
eless config-info
```

## 🧪 Publish to TestPyPI (Recommended First)

### 1. Build the Package
```bash
# Clean previous builds
rm -rf dist/ build/ src/eless.egg-info/

# Build the distribution
python -m build
```

### 2. Upload to TestPyPI
```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# You'll be prompted for TestPyPI credentials
```

### 3. Test Installation from TestPyPI
```bash
# Install from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ eless

# Test the installation
eless --help
```

## 🚀 Publish to PyPI (Production)

Once testing is successful:

### 1. Upload to PyPI
```bash
# Upload to production PyPI
python -m twine upload dist/*

# You'll be prompted for PyPI credentials
```

### 2. Verify the Package
- Visit https://pypi.org/project/eless/
- Check that all information displays correctly

## 📦 Your Friends Can Now Install ELESS!

After publishing, anyone can install ELESS:

### Basic Installation
```bash
# Install core ELESS (minimal dependencies)
pip install eless
```

### Feature-Specific Installations
```bash
# Install with embedding support
pip install eless[embeddings]

# Install with database support
pip install eless[databases]

# Install with document parsing support
pip install eless[parsers]

# Install everything (full features)
pip install eless[full]
```

### Usage After Installation
```bash
# CLI is available system-wide
eless --help
eless config-info
eless process documents/ --databases chroma
```

## 🔄 Updating the Package

For future updates:

1. **Update version** in `pyproject.toml`
2. **Commit changes** to git
3. **Build and upload**:
   ```bash
   python -m build
   python -m twine upload dist/*
   ```

## 📊 Package Installation Options

Your package provides flexible installation options:

### Minimal Installation (Core Only)
```bash
pip install eless
# Installs: click, PyYAML, numpy
# Features: Basic CLI, configuration, file processing (text only)
```

### Embedding Support
```bash
pip install eless[embeddings]
# Adds: sentence-transformers, torch
# Features: Vector embedding generation
```

### Database Support  
```bash
pip install eless[databases]
# Adds: chromadb, qdrant-client, faiss-cpu, etc.
# Features: Vector storage in multiple databases
```

### Document Parsing Support
```bash
pip install eless[parsers] 
# Adds: PyPDF2, python-docx, pandas, etc.
# Features: PDF, Office, HTML document processing
```

### Full Installation
```bash
pip install eless[full]
# Installs everything for complete functionality
```

## 🎯 Example Friend Usage

Once published, your friends can use ELESS like this:

```bash
# Install with full features
pip install eless[full]

# Create a project directory
mkdir my-rag-project
cd my-rag-project

# Process documents
eless process documents/ --databases chroma --log-level INFO

# Check status
eless status --all

# Test system
eless test
```

## 🔐 Security Best Practices

1. **Use API Tokens**: Set up API tokens instead of passwords
   ```bash
   # Create ~/.pypirc with API tokens
   [distutils]
   index-servers = pypi testpypi
   
   [pypi]
   username = __token__
   password = pypi-your-api-token-here
   
   [testpypi]
   username = __token__
   password = pypi-your-test-api-token-here
   ```

2. **Verify Package**: Always test on TestPyPI first
3. **Version Control**: Tag releases in git
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

## 🎉 Success!

Once published, your ELESS package will be available worldwide! Your friends can:
- Install it with pip
- Use the CLI commands
- Choose which features they need
- Get automatic dependency management
- Receive updates when you publish new versions

The package is designed to be user-friendly with clear error messages and helpful documentation, making it easy for anyone to start using RAG data processing!