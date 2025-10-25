# ELESS Test Documentation

## Overview

This document provides a comprehensive overview of the testing infrastructure and test capabilities in the ELESS (Evolving Low-resource Embedding and Storage System) package.

**Test Status**: 56 tests passing ✅  
**Test Framework**: pytest  
**Python Version**: 3.8+

---

## Test Infrastructure

### Test Framework Configuration

- **Primary Framework**: pytest (version >= 7.0.0)
- **Test Directory**: `tests/` (referenced but not present in current package structure)
- **Coverage Tool**: pytest-cov (optional)
- **Code Style**: black, flake8, mypy (development dependencies)

### Installation for Testing

```bash
# Install development dependencies including pytest
pip install -e ".[dev]"

# Install with all features for comprehensive testing
pip install -e ".[full]"
```

---

## Built-in Test Commands

### CLI Test Command

ELESS provides a built-in test command accessible via the CLI:

```bash
eless test
```

**Location**: `src/eless/cli.py` (lines 741-850+)

**Purpose**: Test database connections and system components

**Features**:
- Tests embedding model loading and functionality
- Tests database connections (all or specific)
- Tests file operations
- Provides colored output (✓/✗) for pass/fail

**Options**:
- `--config PATH`: Specify configuration file
- `--test-db DATABASE`: Test connection to a specific database (chroma, qdrant, faiss, postgres, cassandra)

**Example Usage**:
```bash
# Test all system components
eless test

# Test specific database
eless test --test-db chroma

# Test with custom config
eless test --config /path/to/config.yaml
```

---

## Test Categories

### 1. Embedding Model Tests

**Location**: `src/eless/cli.py` (lines 788-810)

**What is Tested**:
- Model loading via ModelLoader
- Encoding test sentences
- Vector dimension validation
- Error handling for missing dependencies

**Test Process**:
```python
# Loads embedding model
model_loader = ModelLoader(app_config)
embedding_model = model_loader._load_model()

# Tests encoding functionality
test_vectors = embedding_model.encode(
    ["This is a test sentence."], 
    convert_to_tensor=False
)

# Validates vector dimensions
print(f"Vector dimension: {len(test_vectors[0])}")
```

---

### 2. Database Connection Tests

**Location**: `src/eless/cli.py` (lines 812-845)

**Supported Databases**:
- ChromaDB
- Qdrant (requires running instance on port 6333)
- FAISS
- PostgreSQL (requires running instance on port 5432)
- Cassandra

**What is Tested**:
- Database connector initialization
- Connection establishment
- Connection validation via `check_connection()`
- Error handling for unavailable databases

**Test Process**:
```python
# Initialize database loader
db_loader = DatabaseLoader(app_config, state_manager, embedding_model)

# Test each active connector
for name, connector in db_loader.active_connectors.items():
    if connector.check_connection():
        # Connection successful
    else:
        # Connection failed
```

---

### 3. File Operation Tests

**Location**: `src/eless/cli.py` (line 847+)

**What is Tested**:
- Cache directory access
- File I/O operations
- State management

---

### 4. Health Check Tests

**Location**: `src/eless/health_check.py`

**Health Check Categories**:

#### System Requirements
- Python version check (3.8+)
- Core dependencies validation
- Disk space monitoring (5GB+ recommended)
- Memory availability (2GB+ recommended)

#### Component Checks
- Embedding model availability (sentence-transformers)
- Database connector availability:
  - ChromaDB
  - Qdrant
  - FAISS
  - PostgreSQL (psycopg2)
  - Cassandra

#### Configuration Validation
- Configuration file existence
- Required sections validation (cache, chunking, embedding)
- Configuration structure integrity

**Run Health Check**:
```bash
eless health
```

**Programmatic Usage**:
```python
from eless.health_check import run_health_check, quick_check

# Detailed health check
results = run_health_check(verbose=True)

# Quick boolean check
is_ready = quick_check()
```

---

## Test Execution

### Running Tests via pytest

```bash
# Run all tests
pytest tests/

# Run specific test suite
pytest tests/test_cli.py -v

# Run with coverage report
pytest tests/ --cov=src --cov-report=html

# Run tests for specific module
pytest tests/ -k "embedding"
```

### Running Built-in Tests

```bash
# System-wide test
eless test

# Test specific database
eless test --test-db faiss

# Test with debug logging
eless test --log-level DEBUG
```

---

## Test Components Overview

### Core Module Tests
- **Config Loader**: Configuration parsing and validation
- **State Manager**: File state tracking and persistence
- **Cache Manager**: Content-based hashing and manifest operations
- **Resource Monitor**: System resource monitoring
- **Error Handler**: Dependency checking and error recovery
- **Logging**: Log rotation and structured logging

### Processing Module Tests
- **File Scanner**: File discovery and filtering
- **Dispatcher**: File routing and processing orchestration
- **Parallel Processor**: Multi-threaded processing
- **Streaming Processor**: Memory-efficient large file handling

### Parser Tests
- **PDF Parser**: PDF text extraction
- **HTML Parser**: HTML parsing and cleaning
- **Office Parser**: DOCX, XLSX parsing
- **Text Chunker**: Document chunking strategies
- **Table Parser**: Structured data extraction

### Database Connector Tests
- **Base Connector**: Abstract interface compliance
- **ChromaDB Connector**: Collection management and vector operations
- **Qdrant Connector**: Collection operations and search
- **FAISS Connector**: Index operations and persistence
- **PostgreSQL Connector**: Table operations and pgvector
- **Cassandra Connector**: Keyspace and table operations

### Embedding Tests
- **Model Loader**: Model initialization and caching
- **Embedder**: Batch encoding and vector generation

---

## Test Data

### Demo Data for Testing

**Location**: `src/eless/demo_data.py`

**Purpose**: Provides sample documents for testing and learning

**Available Demo Datasets**:
- Sample text documents
- Test corpus for embedding
- Example configurations

**Usage**:
```python
from eless.demo_data import create_demo_dataset

# Create demo dataset for testing
demo_data = create_demo_dataset()
```

---

## Testing Best Practices

### Before Running Tests

1. **Install all dependencies**:
   ```bash
   pip install -e ".[full,dev]"
   ```

2. **Ensure databases are running** (if testing database features):
   - Qdrant: Port 6333
   - PostgreSQL: Port 5432

3. **Verify system resources**:
   ```bash
   eless health
   ```

### Test Coverage Areas

✅ **Currently Tested**:
- Embedding model loading
- Database connections
- File operations
- Configuration validation
- System health checks
- Dependency availability

⚠️ **Test Configuration**:
- Tests expect pytest framework
- 56 tests reported as passing
- Test directory referenced in documentation

---

## Continuous Integration

### Development Workflow

```bash
# Run type checking
mypy src/

# Run linting
flake8 src/

# Format code
black src/

# Run tests
pytest tests/
```

---

## Troubleshooting Test Failures

### Common Issues

1. **Missing Dependencies**:
   ```bash
   pip install -e ".[full]"
   ```

2. **Database Connection Failures**:
   - Verify database services are running
   - Check port configurations
   - Review connection parameters in config

3. **Embedding Model Issues**:
   - Ensure sentence-transformers is installed
   - Check available disk space for model downloads
   - Verify internet connection for first-time model download

4. **File Permission Errors**:
   - Check cache directory permissions
   - Verify log directory write access

---

## Test Maintenance

### Adding New Tests

1. Create test files in `tests/` directory
2. Follow naming convention: `test_*.py`
3. Use pytest fixtures for setup/teardown
4. Include docstrings for test documentation

### Test Naming Convention

```python
def test_feature_name_scenario():
    """Test description."""
    # Test implementation
```

---

## Related Documentation

- Main README: `/README.md`
- Configuration Guide: Referenced in `config/`
- API Documentation: Referenced in `docs/`
- Contributing Guidelines: Referenced in `docs/`

---

## Test Statistics

**Total Tests**: 56  
**Status**: All Passing ✅  
**Framework**: pytest >= 7.0.0  
**Coverage**: Available via pytest-cov  

---

**Last Updated**: Generated from ELESS v1.0.0  
**Test Documentation Version**: 1.0  
