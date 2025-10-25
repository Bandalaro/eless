# ELESS API Reference

**Version**: 1.0.0  
**Package**: `eless`

---

## Table of Contents

1. [Core Classes](#core-classes)
2. [Processing Components](#processing-components)
3. [Embedding Components](#embedding-components)
4. [Database Components](#database-components)
5. [Utility Components](#utility-components)
6. [CLI Reference](#cli-reference)
7. [Configuration](#configuration)
8. [Available Functions](#available-functions)

---

## Core Classes

### ElessPipeline

**Module**: `eless.eless_pipeline`

The main orchestrator class for the entire ELESS workflow.

```python
from eless import ElessPipeline

class ElessPipeline:
    """
    Orchestrates the complete pipeline: 
    Scanning → Parsing & Chunking → Embedding → Database Loading
    """
    
    def __init__(self, config: Dict[str, Any])
    def run_process(self, source_path: str)
    def run_resume(self)
```

#### Constructor

```python
ElessPipeline(config: Dict[str, Any])
```

**Parameters**:
- `config` (dict): Configuration dictionary containing all pipeline settings

**Attributes**:
- `state_manager` (StateManager): Manages file processing states
- `archiver` (Archiver): Handles caching of chunks and vectors
- `scanner` (FileScanner): Discovers files for processing
- `dispatcher` (Dispatcher): Routes files to appropriate parsers
- `embedder` (Embedder): Generates vector embeddings
- `db_loader` (DatabaseLoader): Loads vectors into databases
- `resource_monitor` (ResourceMonitor): Monitors system resources

#### Methods

##### run_process()

```python
def run_process(self, source_path: str) -> None
```

Executes the full pipeline for new document processing.

**Parameters**:
- `source_path` (str): File or directory path containing documents to process

**Process Flow**:
1. Initialize database connections
2. Scan input files
3. Parse and chunk documents
4. Generate embeddings
5. Load vectors into databases

**Raises**:
- `FileNotFoundError`: If source_path doesn't exist
- `RuntimeError`: If critical components fail to load

**Example**:
```python
pipeline = ElessPipeline(config)
pipeline.run_process("/path/to/documents")
```

##### run_resume()

```python
def run_resume(self) -> None
```

Resumes processing by loading cached vectors into databases.

**Use Case**: When database loading was interrupted but embeddings are cached

**Example**:
```python
pipeline = ElessPipeline(config)
pipeline.run_resume()
```

---

### StateManager

**Module**: `eless.core.state_manager`

Manages the processing state of all files via a persistent manifest.

```python
from eless import StateManager, FileStatus

class StateManager:
    """
    Tracks file processing states for checkpointing and resumption.
    """
    
    def __init__(self, config: Dict[str, Any])
    def get_status(self, file_hash: str) -> str
    def is_file_known(self, file_hash: str) -> bool
    def add_or_update_file(self, file_hash: str, status: str, 
                          file_path: Optional[str] = None,
                          metadata: Optional[Dict] = None)
    def get_all_files(self, status: Optional[str] = None) -> List[Dict]
    def get_file_info(self, file_hash: str) -> Optional[Dict]
```

#### FileStatus Constants

```python
class FileStatus:
    PENDING = "PENDING"      # Known but not started
    SCANNED = "SCANNED"      # Hash generated, ready for processing
    CHUNKED = "CHUNKED"      # Text extracted and chunked
    EMBEDDED = "EMBEDDED"    # Vectors generated
    LOADED = "LOADED"        # Loaded into all target databases
    ERROR = "ERROR"          # Processing error occurred
```

#### Methods

##### get_status()

```python
def get_status(self, file_hash: str) -> str
```

**Returns**: Current status of a file (default: `FileStatus.PENDING`)

##### add_or_update_file()

```python
def add_or_update_file(
    self, 
    file_hash: str, 
    status: str,
    file_path: Optional[str] = None,
    metadata: Optional[Dict] = None
) -> None
```

**Parameters**:
- `file_hash` (str): SHA-256 hash of the file
- `status` (str): New status (use FileStatus constants)
- `file_path` (str, optional): File path (required for new files)
- `metadata` (dict, optional): Additional metadata to merge

**Example**:
```python
state_manager = StateManager(config)
state_manager.add_or_update_file(
    file_hash="abc123...",
    status=FileStatus.CHUNKED,
    file_path="/path/to/doc.pdf"
)
```

##### get_all_files()

```python
def get_all_files(self, status: Optional[str] = None) -> List[Dict]
```

**Parameters**:
- `status` (str, optional): Filter by status

**Returns**: List of file information dictionaries

---

### ConfigLoader

**Module**: `eless.core.config_loader`

Loads and validates configuration from files or defaults.

```python
from eless import ConfigLoader

class ConfigLoader:
    def __init__(self, config_path: Optional[Path] = None)
    def get_final_config(self, cli_config: Optional[Dict] = None, 
                        **overrides) -> Dict[str, Any]
    def validate_config(self, config: Dict[str, Any]) -> bool
```

#### Methods

##### get_final_config()

```python
def get_final_config(
    self, 
    cli_config: Optional[Dict] = None,
    **overrides
) -> Dict[str, Any]
```

**Returns**: Final merged configuration dictionary

**Example**:
```python
config_loader = ConfigLoader(Path("config.yaml"))
config = config_loader.get_final_config(
    logging={"level": "DEBUG"}
)
```

---

## Processing Components

### FileScanner

**Module**: `eless.processing.file_scanner`

Discovers and filters files for processing.

```python
class FileScanner:
    def __init__(self, config: Dict[str, Any])
    def scan_input(self, source_path: str) -> Generator[Dict, None, None]
```

#### scan_input()

```python
def scan_input(self, source_path: str) -> Generator[Dict, None, None]
```

**Yields**: Dictionaries with keys: `path`, `hash`, `extension`

**Example**:
```python
scanner = FileScanner(config)
for file_data in scanner.scan_input("/docs"):
    print(f"Found: {file_data['path']}")
```

---

### Dispatcher

**Module**: `eless.processing.dispatcher`

Routes documents to appropriate parsers and handles chunking.

```python
class Dispatcher:
    def __init__(self, config: Dict[str, Any], 
                 state_manager: StateManager,
                 archiver: Archiver)
    def process_document(self, file_data: Dict) -> Generator[Dict, None, None]
```

#### process_document()

```python
def process_document(self, file_data: Dict) -> Generator[Dict, None, None]
```

**Parameters**:
- `file_data` (dict): File information from FileScanner

**Yields**: Chunk dictionaries with `text` and `metadata`

---

## Embedding Components

### Embedder

**Module**: `eless.embedding.embedder`

Converts text chunks to vector embeddings.

```python
from eless.embedding.embedder import Embedder

class Embedder:
    def __init__(self, config: Dict[str, Any],
                 state_manager: StateManager,
                 archiver: Archiver,
                 model_loader: ModelLoader = None,
                 resource_monitor = None,
                 batch_processor: BatchProcessor = None)
    
    def embed_file_chunks(self, file_hash: str, 
                         chunks: List[Dict]) -> List[Dict]
    def embed_and_archive_chunks(self, chunk_generator) -> Generator
    def encode(self, texts: List[str]) -> np.ndarray
```

#### embed_file_chunks()

```python
def embed_file_chunks(
    self, 
    file_hash: str, 
    chunks: List[Dict[str, Any]]
) -> List[Dict[str, Any]]
```

**Parameters**:
- `file_hash` (str): Unique file identifier
- `chunks` (list): List of chunk dicts with `text` and `metadata`

**Returns**: Chunks with `vector` field added

**Features**:
- Automatic caching and resume
- Adaptive batching
- Error handling and retry logic

---

### ModelLoader

**Module**: `eless.embedding.model_loader`

Manages embedding model initialization and loading.

```python
from eless.embedding.model_loader import ModelLoader

class ModelLoader:
    def __init__(self, config: Dict[str, Any])
    def get_dimension(self) -> int
```

**Supported Models**:
- All sentence-transformers models
- Default: `all-MiniLM-L6-v2` (384 dimensions)

---

## Database Components

### DatabaseLoader

**Module**: `eless.database.db_loader`

Manages connections and loading to multiple vector databases.

```python
from eless.database.db_loader import DatabaseLoader

class DatabaseLoader:
    def __init__(self, config: Dict[str, Any],
                 state_manager: StateManager,
                 embedder: Embedder)
    
    def initialize_database_connections(self) -> None
    def load_data(self, embedded_chunk_generator) -> None
    def batch_upsert(self, vectors: List[Dict]) -> None
    def close(self) -> None
```

#### initialize_database_connections()

```python
def initialize_database_connections(self) -> None
```

Initializes all configured database connectors.

**Supported Databases**:
- ChromaDB
- Qdrant
- FAISS
- PostgreSQL (with pgvector)
- Cassandra

---

### DBConnectorBase

**Module**: `eless.database.db_connector_base`

Abstract base class for all database connectors.

```python
from eless.database.db_connector_base import DBConnectorBase

class DBConnectorBase(ABC):
    def __init__(self, config: Dict[str, Any], 
                 connection_name: str, 
                 dimension: int)
    
    @abstractmethod
    def connect(self) -> None
    
    @abstractmethod
    def upsert_batch(self, vectors: List[Dict[str, Any]]) -> None
    
    @abstractmethod
    def search(self, query_vector: List[float], 
               limit: int = 10) -> List[Dict[str, Any]]
    
    @abstractmethod
    def close(self) -> None
    
    @abstractmethod
    def check_connection(self) -> bool
```

#### Custom Database Connector

**Example Implementation**:

```python
from eless.database.db_connector_base import DBConnectorBase

class MyCustomConnector(DBConnectorBase):
    def connect(self):
        # Initialize connection
        self.client = MyVectorDB.connect(
            host=self.db_config["host"],
            port=self.db_config["port"]
        )
    
    def upsert_batch(self, vectors):
        # Insert vectors
        for vec in vectors:
            self.client.insert(
                id=vec["id"],
                vector=vec["vector"],
                metadata=vec["metadata"]
            )
    
    def search(self, query_vector, limit=10):
        return self.client.search(query_vector, k=limit)
    
    def close(self):
        self.client.disconnect()
    
    def check_connection(self):
        return self.client.ping()
```

---

## Utility Components

### Archiver

**Module**: `eless.core.archiver`

Handles caching of chunks and vectors to disk.

```python
from eless.core.archiver import Archiver

class Archiver:
    def __init__(self, config: Dict[str, Any])
    def save_chunks(self, file_hash: str, chunks: List[Dict]) -> None
    def load_chunks(self, file_hash: str) -> Optional[List[Dict]]
    def save_vectors(self, file_hash: str, vectors: np.ndarray) -> None
    def load_vectors(self, file_hash: str) -> Optional[np.ndarray]
```

---

### ResourceMonitor

**Module**: `eless.core.resource_monitor`

Monitors system resources (CPU, memory, disk).

```python
from eless.core.resource_monitor import ResourceMonitor

class ResourceMonitor:
    def __init__(self, config: Dict[str, Any])
    def get_current_stats(self) -> Dict[str, Any]
    def is_resource_available(self, memory_mb: int = 0) -> bool
```

---

## CLI Reference

### Main Command

```bash
eless [OPTIONS] COMMAND [ARGS]...
```

**Global Options**:
- `--log-level LEVEL`: Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--log-dir PATH`: Custom log directory
- `--cache-dir PATH`: Custom cache directory
- `--data-dir PATH`: Custom data directory (parent for cache, logs, databases)

### Commands

#### process

```bash
eless process [OPTIONS] SOURCE_PATH
```

Process documents with full configuration options.

**Options**:
- `--config PATH`: Configuration file path
- `--databases TEXT`: Comma-separated database targets
- `--chunk-size INTEGER`: Chunk size for text splitting
- `--resume`: Resume from last checkpoint
- `-i, --interactive`: Interactive mode with prompts

**Example**:
```bash
eless process /docs --databases chroma,faiss --chunk-size 1000
```

#### go

```bash
eless go [OPTIONS] SOURCE_PATH
```

Quick processing with auto-configuration.

**Example**:
```bash
eless go /path/to/documents
```

#### test

```bash
eless test [OPTIONS]
```

Test system components and database connections.

**Options**:
- `--test-db DATABASE`: Test specific database
- `--config PATH`: Configuration file

**Example**:
```bash
eless test --test-db chroma
```

#### status

```bash
eless status [OPTIONS]
```

Check processing status of files.

**Options**:
- `--all`: Show all files
- `--status STATUS`: Filter by status

#### init

```bash
eless init
```

Run configuration wizard for initial setup.

#### health

```bash
eless health
```

Run comprehensive health check.

#### doctor

```bash
eless doctor
```

Diagnose installation and configuration issues.

#### tutorial

```bash
eless tutorial
```

Interactive learning guide.

#### demo

```bash
eless demo
```

Process sample documents for testing.

---

## Configuration

### Configuration Structure

```yaml
# Caching
cache:
  directory: ".eless_cache"
  manifest_file: "manifest.json"

# Chunking
chunking:
  chunk_size: 512
  chunk_overlap: 50
  method: "recursive"

# Embedding
embedding:
  model_name: "all-MiniLM-L6-v2"
  batch_size: 32
  device: "cpu"

# Databases
databases:
  targets:
    - chroma
    - faiss
  connections:
    chroma:
      host: "localhost"
      port: 8000
      collection_name: "eless_collection"
    qdrant:
      host: "localhost"
      port: 6333
      collection_name: "eless_collection"
    faiss:
      index_path: ".eless_data/faiss_index"

# Logging
logging:
  level: "INFO"
  directory: ".eless_logs"
  max_file_size_mb: 10
  backup_count: 5
```

### Configuration Loading Priority

1. CLI overrides (highest priority)
2. Custom config file (--config)
3. Default config file (config/default_config.yaml)
4. Embedded defaults (lowest priority)

---

## Error Handling

### Common Exceptions

**FileNotFoundError**:
- Raised when source path doesn't exist
- Check file path before calling `run_process()`

**RuntimeError**:
- Critical component initialization failure
- Check dependencies with `eless doctor`

**ImportError**:
- Missing optional dependencies
- Install required extras: `pip install eless[full]`

### Error Recovery

ELESS implements automatic error recovery:
- State tracking via manifest.json
- Checkpoint-based resumption
- Automatic backup of manifest files
- Graceful degradation for missing dependencies

---

## Examples

### Basic Pipeline Usage

```python
import yaml
from eless import ElessPipeline

# Load configuration
with open("config.yaml") as f:
    config = yaml.safe_load(f)

# Create and run pipeline
pipeline = ElessPipeline(config)
pipeline.run_process("/path/to/documents")
```

### Custom Processing

```python
from eless import StateManager, ConfigLoader, FileStatus

# Load config
config_loader = ConfigLoader()
config = config_loader.get_final_config()

# Check file status
state_manager = StateManager(config)
files = state_manager.get_all_files(status=FileStatus.LOADED)

for file_info in files:
    print(f"{file_info['path']}: {file_info['status']}")
```

### Programmatic Resume

```python
from eless import ElessPipeline

pipeline = ElessPipeline(config)

# Resume interrupted processing
pipeline.run_resume()
```

---

## Version History

**1.0.0** (Current)
- Initial stable release
- Multi-database support
- Comprehensive CLI
- Production-ready pipeline

---

## Available Functions

This section lists key functions available in the ELESS package and how to use them.

### Core Functions

#### ElessPipeline.run_process(source_path: str)

Processes documents from a given path.

```python
from eless import ElessPipeline

pipeline = ElessPipeline(config)
pipeline.run_process("/path/to/documents")
```

#### ElessPipeline.run_resume()

Resumes processing from cached state.

```python
pipeline.run_resume()
```

#### StateManager.get_all_files(status: Optional[str] = None)

Retrieves all files, optionally filtered by status.

```python
from eless import StateManager

state_manager = StateManager(config)
files = state_manager.get_all_files(status="LOADED")
```

#### Embedder.encode(texts: List[str])

Encodes a list of texts into vectors.

```python
from eless.embedding.embedder import Embedder

embedder = Embedder(config, state_manager, archiver)
vectors = embedder.encode(["Hello world"])
```

#### DatabaseLoader.load_data(embedded_chunk_generator)

Loads embedded data into configured databases.

```python
db_loader = DatabaseLoader(config, state_manager, embedder)
db_loader.load_data(chunk_generator)
```

### Processing Functions

#### FileScanner.scan_input(source_path: str)

Scans and yields file information.

```python
from eless.processing.file_scanner import FileScanner

scanner = FileScanner(config)
for file_data in scanner.scan_input("/docs"):
    print(file_data)
```

#### Dispatcher.process_document(file_data: Dict)

Processes a single document into chunks.

```python
dispatcher = Dispatcher(config, state_manager, archiver)
chunks = list(dispatcher.process_document(file_data))
```

### Database Functions

#### DBConnectorBase.search(query_vector: List[float], limit: int = 10)

Searches for similar vectors in the database.

```python
results = connector.search(query_vector, limit=5)
```

#### DBConnectorBase.upsert_batch(vectors: List[Dict])

Inserts or updates vectors in batch.

```python
connector.upsert_batch(vectors)
```

### Utility Functions

#### ConfigLoader.get_final_config(cli_config: Optional[Dict] = None, **overrides)

Merges configuration sources.

```python
config_loader = ConfigLoader()
config = config_loader.get_final_config(logging={"level": "DEBUG"})
```

#### ResourceMonitor.get_current_stats()

Returns current system resource usage.

```python
from eless.core.resource_monitor import ResourceMonitor

monitor = ResourceMonitor(config)
stats = monitor.get_current_stats()
```

For more detailed usage, refer to the examples in EXAMPLES_AND_USAGE.md.

---

**Documentation Version**: 1.0  
**Last Updated**: 2025-10-25
