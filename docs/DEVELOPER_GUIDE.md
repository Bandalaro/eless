# ELESS Developer Guide

**Version**: 1.0.0  
**Target Audience**: Contributors, Extension Developers, Advanced Users

---

## Table of Contents

1. [Development Setup](#development-setup)
2. [Architecture Deep Dive](#architecture-deep-dive)
3. [Component Details](#component-details)
4. [Extending ELESS](#extending-eless)
5. [Testing](#testing)
6. [Coding Standards](#coding-standards)
7. [Contributing](#contributing)
8. [Troubleshooting Development Issues](#troubleshooting-development-issues)

---

## Development Setup

### Prerequisites

- Python 3.8+
- Git
- pip and virtualenv (or conda)

### Clone and Setup

```bash
# Clone repository
git clone https://github.com/Bandalaro/eless.git
cd eless

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode with all dependencies
pip install -e ".[full,dev]"
```

### Development Dependencies

```bash
# Development tools (already included in [dev])
pytest>=7.0.0          # Testing framework
black>=22.0.0          # Code formatter
flake8>=5.0.0          # Linter
mypy>=0.991            # Type checker
pre-commit>=2.20.0     # Git hooks
```

### Project Structure

```
eless/
├── src/eless/                    # Main package source
│   ├── core/                     # Core components
│   │   ├── config_loader.py
│   │   ├── state_manager.py
│   │   ├── archiver.py
│   │   ├── resource_monitor.py
│   │   ├── error_handler.py
│   │   ├── logging_config.py
│   │   └── cache_manager.py
│   ├── processing/               # Document processing
│   │   ├── file_scanner.py
│   │   ├── dispatcher.py
│   │   ├── parallel_processor.py
│   │   ├── streaming_processor.py
│   │   └── parsers/
│   │       ├── pdf_parser.py
│   │       ├── html_parser.py
│   │       ├── office_parser.py
│   │       ├── text_chunker.py
│   │       └── table_parser.py
│   ├── embedding/                # Embedding generation
│   │   ├── model_loader.py
│   │   └── embedder.py
│   ├── database/                 # Database connectors
│   │   ├── db_connector_base.py
│   │   ├── db_loader.py
│   │   ├── chroma_connector.py
│   │   ├── qdrant_connector.py
│   │   ├── faiss_connector.py
│   │   ├── postgresql_connector.py
│   │   └── cassandra_connector.py
│   ├── cli.py                    # Command-line interface
│   ├── eless_pipeline.py         # Main pipeline orchestrator
│   ├── health_check.py           # Health diagnostics
│   ├── demo_data.py              # Demo datasets
│   └── __init__.py
├── config/                       # Configuration files
├── docs/                         # Documentation
├── tests/                        # Test suite
├── tools/                        # Utility scripts
├── pyproject.toml               # Project metadata
├── setup.py                     # Setup configuration
└── README.md                    # Main README
```

---

## Architecture Deep Dive

### Design Principles

1. **Modularity**: Each component has a single responsibility
2. **Resilience**: Automatic checkpointing and error recovery
3. **Extensibility**: Plugin architecture for parsers and databases
4. **Efficiency**: Streaming processing and smart caching
5. **Observability**: Comprehensive logging and monitoring

### Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     ElessPipeline                           │
│  (Orchestrates entire workflow)                             │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ StateManager │    │  Archiver    │    │ ResourceMon  │
│              │    │              │    │              │
│ Tracks file  │    │ Caches chunks│    │ Monitors CPU,│
│ status via   │    │ and vectors  │    │ memory, disk │
│ manifest.json│    │              │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ FileScanner  │───→│  Dispatcher  │───→│  Embedder    │
│              │    │              │    │              │
│ Discovers    │    │ Routes files │    │ Generates    │
│ files and    │    │ to parsers,  │    │ embeddings   │
│ generates    │    │ chunks text  │    │              │
│ hashes       │    │              │    │              │
└──────────────┘    └──────────────┘    └──────────────┘
                                                │
                                                ▼
                                        ┌──────────────┐
                                        │ DBLoader     │
                                        │              │
                                        │ Loads vectors│
                                        │ into DBs     │
                                        └──────────────┘
```

### Data Flow

```
File → Hash → Parse → Chunk → Embed → Store
  │      │      │       │       │       │
  └──────┴──────┴───────┴───────┴───────┘
         State tracked at each step
```

### State Machine

Each file progresses through states:

```
PENDING → SCANNED → CHUNKED → EMBEDDED → LOADED
    │         │         │          │         │
    └─────────┴─────────┴──────────┴─────────→ ERROR
```

State transitions are atomic and persisted immediately.

---

## Component Details

### Core Components

#### StateManager

**Location**: `src/eless/core/state_manager.py`

**Responsibilities**:
- Track file processing status
- Persist state to manifest.json
- Enable resumable processing
- Atomic state updates

**Key Methods**:
```python
def add_or_update_file(self, file_hash, status, file_path, metadata)
def get_status(self, file_hash) -> str
def get_all_files(self, status=None) -> List[Dict]
```

**Internal Structure**:
```json
{
  "file_hash": {
    "path": "/path/to/file.pdf",
    "status": "LOADED",
    "timestamp": "2025-10-25T10:30:00",
    "hash": "abc123...",
    "metadata": {},
    "error_count": 0,
    "last_error": null
  }
}
```

**Thread Safety**: Uses atomic file writes with backup

#### Archiver

**Location**: `src/eless/core/archiver.py`

**Responsibilities**:
- Cache chunks and vectors
- Enable skip/resume logic
- Prevent reprocessing

**File Formats**:
- `{hash}.chunks.pkl`: Pickled chunk data
- `{hash}.vectors.npy`: NumPy vector arrays

**Key Methods**:
```python
def save_chunks(self, file_hash, chunks)
def load_chunks(self, file_hash) -> Optional[List[Dict]]
def save_vectors(self, file_hash, vectors)
def load_vectors(self, file_hash) -> Optional[np.ndarray]
```

#### ConfigLoader

**Location**: `src/eless/core/config_loader.py`

**Responsibilities**:
- Load configuration from files
- Merge with defaults
- Apply CLI overrides
- Validate configuration

**Configuration Priority**:
1. CLI arguments (highest)
2. Custom config file
3. Default config file
4. Embedded defaults (lowest)

**Key Methods**:
```python
def get_final_config(self, cli_config, **overrides) -> Dict
def validate_config(self, config) -> bool
```

#### ResourceMonitor

**Location**: `src/eless/core/resource_monitor.py`

**Responsibilities**:
- Monitor CPU, memory, disk
- Adaptive batch sizing
- Prevent system overload

**Key Methods**:
```python
def get_current_stats() -> Dict
def is_resource_available(memory_mb) -> bool
```

### Processing Components

#### FileScanner

**Location**: `src/eless/processing/file_scanner.py`

**Responsibilities**:
- Discover files (recursively)
- Generate content hashes
- Filter by extension
- Yield file metadata

**Output Format**:
```python
{
    "path": "/path/to/file.pdf",
    "hash": "sha256_hash",
    "extension": ".pdf"
}
```

#### Dispatcher

**Location**: `src/eless/processing/dispatcher.py`

**Responsibilities**:
- Route files to appropriate parsers
- Coordinate chunking
- Handle parser errors
- Implement retry logic

**Parser Registry**:
```python
PARSERS = {
    '.pdf': PDFParser,
    '.docx': OfficeParser,
    '.html': HTMLParser,
    '.txt': TextParser,
    '.md': TextParser,
}
```

**Extension Point**: Add new parsers here

#### Parsers

**Base Pattern**: All parsers should return text content

**Example Parser**:
```python
class CustomParser:
    def parse(self, file_path: str) -> str:
        """Extract text from file."""
        # Implementation
        return text_content
```

**Available Parsers**:
- `PDFParser`: PDF extraction
- `HTMLParser`: HTML cleaning and extraction
- `OfficeParser`: DOCX, XLSX extraction
- `TextParser`: Plain text files
- `TableParser`: Structured data extraction

### Embedding Components

#### ModelLoader

**Location**: `src/eless/embedding/model_loader.py`

**Responsibilities**:
- Load sentence-transformers models
- Manage model caching
- Provide dimension info

**Supported Models**: Any sentence-transformers model

**Key Methods**:
```python
def _load_model() -> SentenceTransformer
def get_dimension() -> int
```

#### Embedder

**Location**: `src/eless/embedding/embedder.py`

**Responsibilities**:
- Batch encoding of texts
- Adaptive batch sizing
- Vector caching
- Resume support

**Key Methods**:
```python
def embed_file_chunks(file_hash, chunks) -> List[Dict]
def encode(texts) -> np.ndarray
def embed_and_archive_chunks(chunk_generator) -> Generator
```

**Features**:
- Automatic batching
- GPU support (if available)
- Progress tracking
- Error recovery

### Database Components

#### DBConnectorBase

**Location**: `src/eless/database/db_connector_base.py`

**Abstract Base Class**: All connectors must implement:

```python
class DBConnectorBase(ABC):
    @abstractmethod
    def connect(self): pass
    
    @abstractmethod
    def upsert_batch(self, vectors: List[Dict]): pass
    
    @abstractmethod
    def search(self, query_vector, limit=10): pass
    
    @abstractmethod
    def close(self): pass
    
    @abstractmethod
    def check_connection(self) -> bool: pass
```

**Vector Format**:
```python
{
    "id": "file_hash-chunk_index",
    "vector": [0.1, 0.2, ...],  # List of floats
    "metadata": {
        "source": "file.pdf",
        "chunk_index": 0,
        "text": "Original text..."
    }
}
```

#### DatabaseLoader

**Location**: `src/eless/database/db_loader.py`

**Responsibilities**:
- Initialize multiple database connections
- Route data to all targets
- Handle database-specific errors
- Coordinate batch operations

**Key Methods**:
```python
def initialize_database_connections()
def load_data(embedded_chunk_generator)
def batch_upsert(vectors)
def close()
```

---

## Extending ELESS

### Adding a Custom Parser

**Step 1**: Create parser class

```python
# src/eless/processing/parsers/my_parser.py

import logging
logger = logging.getLogger("ELESS.MyParser")

class MyCustomParser:
    """Parser for .xyz files."""
    
    def __init__(self, config):
        self.config = config
    
    def parse(self, file_path: str) -> str:
        """
        Extract text from .xyz file.
        
        Args:
            file_path: Path to file
            
        Returns:
            Extracted text content
            
        Raises:
            Exception: If parsing fails
        """
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Your parsing logic here
            text = self._extract_text(content)
            
            logger.info(f"Parsed {file_path}")
            return text
            
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {e}")
            raise
    
    def _extract_text(self, content: str) -> str:
        """Custom extraction logic."""
        # Implementation
        return processed_text
```

**Step 2**: Register parser in Dispatcher

```python
# src/eless/processing/dispatcher.py

from .parsers.my_parser import MyCustomParser

PARSERS = {
    '.pdf': PDFParser,
    '.docx': OfficeParser,
    '.xyz': MyCustomParser,  # Add your parser
    # ...
}
```

**Step 3**: Test your parser

```python
# tests/test_my_parser.py

import pytest
from eless.processing.parsers.my_parser import MyCustomParser

def test_my_parser():
    config = {...}
    parser = MyCustomParser(config)
    
    result = parser.parse("test_file.xyz")
    
    assert result is not None
    assert len(result) > 0
```

### Adding a Custom Database Connector

**Step 1**: Implement DBConnectorBase

```python
# src/eless/database/my_db_connector.py

import logging
from typing import Dict, Any, List
from .db_connector_base import DBConnectorBase

logger = logging.getLogger("ELESS.MyDBConnector")


class MyDatabaseConnector(DBConnectorBase):
    """
    Connector for MyVectorDB.
    
    Configuration required:
        host: Database host
        port: Database port
        collection_name: Collection/index name
    """
    
    def __init__(self, config: Dict[str, Any], 
                 connection_name: str, 
                 dimension: int):
        super().__init__(config, connection_name, dimension)
        self.client = None
        self.collection = None
    
    def connect(self):
        """Initialize connection to MyVectorDB."""
        try:
            # Import database client
            from my_vector_db import Client
            
            # Initialize client
            self.client = Client(
                host=self.db_config["host"],
                port=self.db_config["port"],
                # ... other config
            )
            
            # Get or create collection
            collection_name = self.db_config["collection_name"]
            
            if not self.client.collection_exists(collection_name):
                self.client.create_collection(
                    name=collection_name,
                    dimension=self.dimension
                )
                logger.info(f"Created collection: {collection_name}")
            
            self.collection = self.client.get_collection(collection_name)
            logger.info(f"Connected to MyVectorDB: {collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MyVectorDB: {e}")
            raise
    
    def upsert_batch(self, vectors: List[Dict[str, Any]]):
        """Insert/update vectors in batch."""
        if not self.collection:
            raise RuntimeError("Not connected to database")
        
        try:
            # Prepare data in DB-specific format
            ids = [v["id"] for v in vectors]
            embeddings = [v["vector"] for v in vectors]
            metadatas = [v["metadata"] for v in vectors]
            
            # Upsert to database
            self.collection.upsert(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas
            )
            
            logger.info(f"Upserted {len(vectors)} vectors")
            
        except Exception as e:
            logger.error(f"Failed to upsert batch: {e}")
            raise
    
    def search(self, query_vector: List[float], 
               limit: int = 10) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        if not self.collection:
            raise RuntimeError("Not connected to database")
        
        try:
            results = self.collection.search(
                query_vector=query_vector,
                limit=limit
            )
            
            return [
                {
                    "id": r.id,
                    "score": r.score,
                    "metadata": r.metadata
                }
                for r in results
            ]
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    def close(self):
        """Close database connection."""
        if self.client:
            self.client.disconnect()
            logger.info("Disconnected from MyVectorDB")
    
    def check_connection(self) -> bool:
        """Verify connection is active."""
        try:
            if not self.client:
                return False
            return self.client.ping()
        except Exception:
            return False
```

**Step 2**: Register in DatabaseLoader

```python
# src/eless/database/db_loader.py

from .my_db_connector import MyDatabaseConnector

CONNECTOR_CLASSES = {
    "chroma": ChromaDBConnector,
    "qdrant": QdrantConnector,
    "faiss": FAISSConnector,
    "my_db": MyDatabaseConnector,  # Add your connector
    # ...
}
```

**Step 3**: Add configuration

```yaml
# config/default_config.yaml

databases:
  targets:
    - my_db
  connections:
    my_db:
      host: "localhost"
      port: 9000
      collection_name: "eless_collection"
```

**Step 4**: Test connector

```python
# tests/test_my_db_connector.py

import pytest
from eless.database.my_db_connector import MyDatabaseConnector

@pytest.fixture
def connector():
    config = {
        "databases": {
            "connections": {
                "my_db": {
                    "host": "localhost",
                    "port": 9000,
                    "collection_name": "test_collection"
                }
            }
        }
    }
    
    conn = MyDatabaseConnector(config, "my_db", dimension=384)
    conn.connect()
    yield conn
    conn.close()

def test_upsert(connector):
    vectors = [
        {
            "id": "test-1",
            "vector": [0.1] * 384,
            "metadata": {"source": "test"}
        }
    ]
    
    connector.upsert_batch(vectors)
    # Add assertions

def test_search(connector):
    query = [0.1] * 384
    results = connector.search(query, limit=5)
    
    assert isinstance(results, list)
```

### Adding CLI Commands

**Example**: Add a new command

```python
# src/eless/cli.py

@cli.command()
@click.argument('query', required=True)
@click.option('--database', default='chroma', help='Database to query')
@click.option('--limit', default=10, help='Number of results')
@click.pass_context
def search(ctx, query, database, limit):
    """Search for similar documents."""
    # Load config
    config = load_config(ctx)
    
    # Initialize components
    embedder = Embedder(config, ...)
    db_loader = DatabaseLoader(config, ...)
    
    # Generate query vector
    query_vector = embedder.encode([query])[0]
    
    # Search database
    results = db_loader.search(query_vector, limit)
    
    # Display results
    for i, result in enumerate(results, 1):
        click.echo(f"{i}. Score: {result['score']}")
        click.echo(f"   {result['metadata']['source']}")
```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_pipeline.py

# Run specific test
pytest tests/test_pipeline.py::test_basic_processing

# Run with coverage
pytest tests/ --cov=src --cov-report=html
```

### Writing Tests

**Test Structure**:

```python
# tests/test_component.py

import pytest
from eless.core.state_manager import StateManager, FileStatus

@pytest.fixture
def temp_config(tmp_path):
    """Create temporary config for testing."""
    return {
        "cache": {
            "directory": str(tmp_path / "cache"),
            "manifest_file": "manifest.json"
        }
    }

@pytest.fixture
def state_manager(temp_config):
    """Create StateManager instance."""
    return StateManager(temp_config)

def test_add_file(state_manager):
    """Test adding a file to state manager."""
    file_hash = "abc123"
    
    state_manager.add_or_update_file(
        file_hash,
        FileStatus.PENDING,
        file_path="/test/file.pdf"
    )
    
    assert state_manager.is_file_known(file_hash)
    assert state_manager.get_status(file_hash) == FileStatus.PENDING

def test_update_status(state_manager):
    """Test updating file status."""
    file_hash = "abc123"
    
    # Add file
    state_manager.add_or_update_file(
        file_hash, FileStatus.PENDING, file_path="/test.pdf"
    )
    
    # Update status
    state_manager.add_or_update_file(file_hash, FileStatus.LOADED)
    
    assert state_manager.get_status(file_hash) == FileStatus.LOADED
```

### Test Categories

**Unit Tests**: Test individual components in isolation  
**Integration Tests**: Test component interactions  
**End-to-End Tests**: Test complete pipeline workflows  
**Performance Tests**: Test resource usage and speed

---

## Coding Standards

### Python Style Guide

**Follow PEP 8** with these specifics:

- Line length: 88 characters (Black default)
- Indentation: 4 spaces
- Quotes: Double quotes for strings
- Imports: Grouped (stdlib, third-party, local)

### Code Formatting

```bash
# Format code with Black
black src/

# Check formatting
black --check src/

# Format specific file
black src/eless/cli.py
```

### Linting

```bash
# Lint with flake8
flake8 src/

# Lint specific file
flake8 src/eless/cli.py
```

### Type Checking

```bash
# Type check with mypy
mypy src/

# Type check specific module
mypy src/eless/core/
```

### Docstrings

**Use Google-style docstrings**:

```python
def process_file(file_path: str, chunk_size: int = 512) -> List[Dict]:
    """
    Process a file and return chunks.
    
    Args:
        file_path: Path to the file to process
        chunk_size: Size of text chunks (default: 512)
    
    Returns:
        List of chunk dictionaries with text and metadata
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If chunk_size is invalid
    
    Example:
        >>> chunks = process_file("/docs/file.pdf")
        >>> print(len(chunks))
        42
    """
    # Implementation
```

### Logging

**Use structured logging**:

```python
import logging
logger = logging.getLogger("ELESS.ComponentName")

# Info level for normal operations
logger.info(f"Processing file: {file_path}")

# Debug for detailed info
logger.debug(f"Chunk size: {len(chunk)}")

# Warning for recoverable issues
logger.warning(f"Skipping unsupported file: {file_path}")

# Error for failures
logger.error(f"Failed to parse {file_path}: {e}")

# Critical for fatal errors
logger.critical(f"Database connection lost: {e}")
```

### Error Handling

**Be specific with exceptions**:

```python
# Bad
try:
    process_file(path)
except Exception:
    pass

# Good
try:
    process_file(path)
except FileNotFoundError:
    logger.error(f"File not found: {path}")
    raise
except PermissionError:
    logger.error(f"Permission denied: {path}")
    raise
except Exception as e:
    logger.error(f"Unexpected error processing {path}: {e}")
    raise
```

---

## Contributing

### Contribution Workflow

1. **Fork** the repository
2. **Clone** your fork
3. **Create** a feature branch
4. **Make** your changes
5. **Test** thoroughly
6. **Commit** with clear messages
7. **Push** to your fork
8. **Submit** a pull request

### Branch Naming

- `feature/add-xyz-parser` - New features
- `bugfix/fix-state-manager` - Bug fixes
- `docs/update-api-reference` - Documentation
- `refactor/improve-embedder` - Code refactoring

### Commit Messages

**Format**: `<type>: <description>`

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `test`: Tests
- `refactor`: Code refactoring
- `perf`: Performance improvement
- `chore`: Maintenance

**Examples**:
```
feat: add support for .epub files
fix: handle empty documents in parser
docs: update API reference for Embedder
test: add integration tests for database loader
refactor: simplify state manager logic
```

### Pull Request Guidelines

**Include**:
- Clear description of changes
- Link to related issue (if any)
- Test results
- Updated documentation
- Screenshots (if UI changes)

**PR Template**:
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Testing
- [ ] All existing tests pass
- [ ] New tests added
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] No new warnings introduced
- [ ] Self-reviewed code
```

---

## Troubleshooting Development Issues

### Import Errors

**Problem**: Module not found

```bash
# Ensure package is installed in development mode
pip install -e ".[full,dev]"

# Verify installation
python -c "import eless; print(eless.__version__)"
```

### Test Failures

**Problem**: Tests fail locally

```bash
# Update dependencies
pip install --upgrade -e ".[full,dev]"

# Clear cache
rm -rf .pytest_cache
rm -rf .eless_cache

# Run tests with verbose output
pytest tests/ -v -s
```

### Database Connection Issues

**Problem**: Database tests fail

```bash
# Ensure databases are running
# For ChromaDB: Usually embedded, no setup needed
# For Qdrant: docker run -p 6333:6333 qdrant/qdrant
# For PostgreSQL: Ensure PostgreSQL is running with pgvector

# Test specific database
eless test --test-db chroma
```

### Performance Issues

**Problem**: Tests are slow

```bash
# Run tests in parallel
pytest tests/ -n auto

# Skip slow tests
pytest tests/ -m "not slow"

# Profile tests
pytest tests/ --durations=10
```

---

## Additional Resources

### Internal Documentation

- [API Reference](API_REFERENCE.md)
- [Examples & Usage](EXAMPLES_AND_USAGE.md)
- [Test Documentation](TEST_DOCUMENTATION.md)

### External Resources

- [sentence-transformers docs](https://www.sbert.net/)
- [ChromaDB docs](https://docs.trychroma.com/)
- [Qdrant docs](https://qdrant.tech/documentation/)
- [FAISS docs](https://github.com/facebookresearch/faiss)

---

**Happy Developing!**

---

**Guide Version**: 1.0  
**Last Updated**: 2025-10-25
