# ELESS API Reference

Complete API documentation for the ELESS (Evolving Low-resource Embedding and Storage System) package.

## Table of Contents

- [Core Components](#core-components)
  - [ElessPipeline](#elesspipeline)
  - [StateManager](#statemanager)
  - [ConfigLoader](#configloader)
  - [Archiver](#archiver)
  - [ResourceMonitor](#resourcemonitor)
- [Processing Components](#processing-components)
  - [FileScanner](#filescanner)
  - [Dispatcher](#dispatcher)
  - [TextChunker](#textchunker)
  - [StreamingProcessor](#streamingprocessor)
- [Embedding Components](#embedding-components)
  - [Embedder](#embedder)
  - [ModelLoader](#modelloader)
- [Database Components](#database-components)
  - [DatabaseLoader](#databaseloader)
  - [DBConnectorBase](#dbconnectorbase)
  - [ChromaConnector](#chromaconnector)
  - [QdrantConnector](#qdrantconnector)
- [CLI Interface](#cli-interface)

---

## Core Components

### ElessPipeline

Main orchestrator for the entire ELESS processing pipeline.

**Location:** `src/eless_pipeline.py`

#### Constructor

```python
ElessPipeline(config: Dict[str, Any])
```

**Parameters:**
- `config` (Dict[str, Any]): Configuration dictionary containing all pipeline settings

**Example:**
```python
from src.eless_pipeline import ElessPipeline
import yaml

with open("config/default_config.yaml") as f:
    config = yaml.safe_load(f)

pipeline = ElessPipeline(config)
```

#### Methods

##### `run_process(source_path: str)`

Executes the full pipeline for document processing.

**Parameters:**
- `source_path` (str): File or directory path to process

**Example:**
```python
pipeline.run_process("/path/to/documents")
```

##### `run_resume()`

Resumes interrupted processing from the last checkpoint.

**Example:**
```python
pipeline.run_resume()
```

---

### StateManager

Manages file processing state and manifest tracking.

**Location:** `src/core/state_manager.py`

#### Constructor

```python
StateManager(config: Dict[str, Any])
```

**Parameters:**
- `config` (Dict[str, Any]): Configuration with cache settings

#### File Statuses

```python
class FileStatus:
    PENDING = "PENDING"       # File known, not yet processed
    SCANNED = "SCANNED"       # File hash generated
    CHUNKED = "CHUNKED"       # Text extracted and chunked
    EMBEDDED = "EMBEDDED"     # Vectors generated
    LOADED = "LOADED"         # Loaded into all target databases
    ERROR = "ERROR"           # Processing error occurred
```

#### Methods

##### `add_or_update_file(file_hash: str, file_path: str, status: str, metadata: Optional[Dict] = None)`

Adds or updates a file's status in the manifest.

**Parameters:**
- `file_hash` (str): SHA-256 hash of the file
- `file_path` (str): Path to the file
- `status` (str): One of the FileStatus values
- `metadata` (Optional[Dict]): Additional metadata

**Example:**
```python
state_manager.add_or_update_file(
    "abc123...",
    "/path/to/file.txt",
    FileStatus.CHUNKED,
    metadata={"chunks": 10}
)
```

##### `get_status(file_hash: str) -> str`

Returns the current status of a file.

**Parameters:**
- `file_hash` (str): File hash identifier

**Returns:**
- str: Current status of the file

##### `get_all_files() -> List[Dict[str, Any]]`

Returns all tracked files with their status and path.

**Returns:**
- List[Dict]: List of file information dictionaries

**Example:**
```python
files = state_manager.get_all_files()
for file in files:
    print(f"{file['path']}: {file['status']}")
```

##### `get_files_by_status(status: str) -> List[str]`

Returns all file hashes with the given status.

**Parameters:**
- `status` (str): Status to filter by

**Returns:**
- List[str]: List of file hashes

##### `clear_state()`

Clears all state by resetting the manifest.

---

### ConfigLoader

Loads and merges configuration from multiple sources.

**Location:** `src/core/config_loader.py`

#### Static Methods

##### `load_config(config_path: Optional[str] = None, cli_overrides: Optional[Dict] = None) -> Dict[str, Any]`

Loads configuration with hierarchical merging.

**Parameters:**
- `config_path` (Optional[str]): Path to custom config file
- `cli_overrides` (Optional[Dict]): CLI overrides to apply

**Returns:**
- Dict[str, Any]: Merged configuration dictionary

**Example:**
```python
from src.core.config_loader import ConfigLoader

config = ConfigLoader.load_config(
    config_path="my_config.yaml",
    cli_overrides={"databases": {"targets": ["chroma"]}}
)
```

---

### Archiver

Manages caching of chunks and vectors to disk.

**Location:** `src/core/archiver.py`

#### Constructor

```python
Archiver(config: Dict[str, Any])
```

#### Methods

##### `save_chunks(file_hash: str, chunks: List[Dict[str, Any]])`

Saves text chunks to disk.

**Parameters:**
- `file_hash` (str): File identifier
- `chunks` (List[Dict]): List of chunk dictionaries

##### `load_chunks(file_hash: str) -> List[Dict[str, Any]]`

Loads cached chunks from disk.

**Parameters:**
- `file_hash` (str): File identifier

**Returns:**
- List[Dict]: List of chunk dictionaries

##### `save_vectors(file_hash: str, vectors: np.ndarray)`

Saves embedding vectors to disk.

**Parameters:**
- `file_hash` (str): File identifier
- `vectors` (np.ndarray): NumPy array of vectors

##### `load_vectors(file_hash: str) -> np.ndarray`

Loads cached vectors from disk.

**Parameters:**
- `file_hash` (str): File identifier

**Returns:**
- np.ndarray: NumPy array of vectors

---

### ResourceMonitor

Monitors system resources for adaptive processing.

**Location:** `src/core/resource_monitor.py`

#### Constructor

```python
ResourceMonitor(config: Dict[str, Any])
```

#### Methods

##### `get_current_usage() -> Dict[str, Any]`

Gets current resource usage metrics.

**Returns:**
- Dict: Resource usage including CPU, memory, disk

**Example:**
```python
usage = resource_monitor.get_current_usage()
print(f"Memory: {usage['memory_percent']}%")
print(f"CPU: {usage['cpu_percent']}%")
```

##### `check_resources() -> bool`

Checks if resources are within safe limits.

**Returns:**
- bool: True if resources are safe, False otherwise

##### `wait_for_resources(timeout: int = 300)`

Waits until resources are available or timeout.

**Parameters:**
- `timeout` (int): Maximum wait time in seconds

---

## Processing Components

### FileScanner

Scans directories and generates file hashes.

**Location:** `src/processing/file_scanner.py`

#### Constructor

```python
FileScanner(config: Dict[str, Any])
```

#### Methods

##### `scan_input(source_path: str) -> List[Dict[str, Any]]`

Scans input path and returns file metadata.

**Parameters:**
- `source_path` (str): Path to scan

**Returns:**
- List[Dict]: List of file metadata dictionaries

**Example:**
```python
files = scanner.scan_input("/path/to/documents")
for file in files:
    print(f"{file['path']}: {file['hash']}")
```

---

### Dispatcher

Routes files to appropriate parsers and manages chunking.

**Location:** `src/processing/dispatcher.py`

#### Constructor

```python
Dispatcher(config: Dict[str, Any], state_manager: StateManager, archiver: Archiver)
```

#### Methods

##### `process_document(file_data: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]`

Processes a single document and yields chunks.

**Parameters:**
- `file_data` (Dict): File metadata from scanner

**Yields:**
- Dict: Chunk dictionaries with text and metadata

---

### TextChunker

Splits text into semantic chunks.

**Location:** `src/processing/parsers/text_chunker.py`

#### Constructor

```python
TextChunker(config: Dict[str, Any])
```

#### Methods

##### `chunk_text(text: str, file_hash: str) -> List[Dict[str, Any]]`

Splits text into chunks with overlap.

**Parameters:**
- `text` (str): Text to chunk
- `file_hash` (str): File identifier

**Returns:**
- List[Dict]: List of chunk dictionaries

---

### StreamingProcessor

Handles memory-efficient streaming of large files.

**Location:** `src/processing/streaming_processor.py`

#### Constructor

```python
StreamingProcessor(config: Dict[str, Any])
```

#### Methods

##### `should_stream_file(file_path: str, file_size: int) -> bool`

Determines if a file should be streamed.

**Parameters:**
- `file_path` (str): Path to file
- `file_size` (int): File size in bytes

**Returns:**
- bool: True if streaming should be used

##### `stream_and_chunk_file(file_path: str, file_hash: str) -> Generator[Dict[str, Any], None, None]`

Streams a file and yields chunks.

**Parameters:**
- `file_path` (str): Path to file
- `file_hash` (str): File identifier

**Yields:**
- Dict: Chunk dictionaries

---

## Embedding Components

### Embedder

Manages embedding generation and caching.

**Location:** `src/embedding/embedder.py`

#### Constructor

```python
Embedder(config: Dict[str, Any], state_manager: StateManager, archiver: Archiver)
```

#### Methods

##### `embed_and_archive_chunks(chunks_generator: Generator) -> Generator[Dict[str, Any], None, None]`

Embeds chunks and archives vectors.

**Parameters:**
- `chunks_generator` (Generator): Generator yielding chunks

**Yields:**
- Dict: Chunks with embedded vectors

**Example:**
```python
for chunk in embedder.embed_and_archive_chunks(chunk_generator):
    print(f"Chunk embedded: {chunk['metadata']['chunk_id']}")
```

##### `embed_file_chunks(file_hash: str, chunks: List[Dict]) -> List[Dict]`

Embeds all chunks for a single file.

**Parameters:**
- `file_hash` (str): File identifier
- `chunks` (List[Dict]): List of chunks

**Returns:**
- List[Dict]: Chunks with vectors attached

---

### ModelLoader

Loads and manages embedding models.

**Location:** `src/embedding/model_loader.py`

#### Constructor

```python
ModelLoader(config: Dict[str, Any])
```

#### Methods

##### `get_embedding_dimension() -> int`

Returns the dimension of the embedding model.

**Returns:**
- int: Vector dimension

##### `embed_chunks(texts: List[str]) -> np.ndarray`

Generates embeddings for text chunks.

**Parameters:**
- `texts` (List[str]): List of text strings

**Returns:**
- np.ndarray: Array of embedding vectors

---

## Database Components

### DatabaseLoader

Manages multiple database connections and loading.

**Location:** `src/database/db_loader.py`

#### Constructor

```python
DatabaseLoader(config: Dict[str, Any], state_manager: StateManager, embedder: Embedder)
```

#### Methods

##### `initialize_database_connections()`

Initializes all configured database connectors.

##### `load_data(chunks_with_vectors: Generator)`

Loads data into all target databases.

**Parameters:**
- `chunks_with_vectors` (Generator): Generator yielding chunks with vectors

**Example:**
```python
db_loader.initialize_database_connections()
db_loader.load_data(embedded_chunks)
```

##### `close_connections()`

Closes all database connections.

---

### DBConnectorBase

Abstract base class for database connectors.

**Location:** `src/database/db_connector_base.py`

#### Abstract Methods

##### `connect() -> bool`

Establishes database connection.

**Returns:**
- bool: True if connection successful

##### `upsert_vectors(data: List[Dict[str, Any]]) -> bool`

Inserts or updates vectors in the database.

**Parameters:**
- `data` (List[Dict]): List of vector data

**Returns:**
- bool: True if operation successful

##### `disconnect()`

Closes the database connection.

---

### ChromaConnector

ChromaDB-specific connector implementation.

**Location:** `src/database/chroma_connector.py`

#### Constructor

```python
ChromaConnector(config: Dict[str, Any], db_config: Dict[str, Any], vector_dim: int)
```

---

### QdrantConnector

Qdrant-specific connector implementation.

**Location:** `src/database/qdrant_connector.py`

#### Constructor

```python
QdrantConnector(config: Dict[str, Any], db_config: Dict[str, Any], vector_dim: int)
```

---

## CLI Interface

The CLI is built with Click and provides multiple commands.

**Location:** `src/cli.py`

### Commands

#### `eless process`

Process documents through the pipeline.

```bash
eless process /path/to/documents [OPTIONS]
```

**Options:**
- `--databases, -db`: Select target databases (repeatable)
- `--config`: Custom configuration file
- `--resume`: Resume interrupted processing
- `--chunk-size`: Override chunk size
- `--batch-size`: Override batch size
- `--log-level`: Set logging level (DEBUG, INFO, WARNING, ERROR)
- `--log-dir`: Custom log directory

**Example:**
```bash
eless process ./documents --databases chroma --databases qdrant --log-level DEBUG
```

#### `eless status`

Check processing status.

```bash
eless status [OPTIONS]
```

**Options:**
- `--all`: Show all tracked files
- `FILE_ID`: Show specific file details

**Example:**
```bash
eless status --all
eless status abc123def
```

#### `eless config-info`

Display current configuration.

```bash
eless config-info
```

#### `eless test`

Run system health checks.

```bash
eless test [OPTIONS]
```

**Options:**
- `--test-db`: Test specific database

**Example:**
```bash
eless test --test-db chroma
```

#### `eless logs`

Manage log files.

```bash
eless logs [OPTIONS]
```

**Options:**
- `--days`: Clean logs older than N days

**Example:**
```bash
eless logs --days 7
```

---

## Configuration Schema

### Full Configuration Example

```yaml
# Logging Configuration
logging:
  directory: .eless_logs
  level: INFO
  enable_console: true
  max_file_size_mb: 10
  backup_count: 5

# Cache Configuration
cache:
  directory: .eless_cache
  manifest_file: cache_manifest.json
  enable_resume: true

# Embedding Configuration
embedding:
  model_name: all-MiniLM-L6-v2
  model_path: ./models/minilm_v2_local
  device: cpu
  batch_size: 32

# Chunking Configuration
chunking:
  chunk_size: 500
  overlap: 50
  strategy: semantic

# Resource Limits
resource_limits:
  max_memory_mb: 512
  max_cpu_percent: 80
  enable_adaptive_batching: true

# Streaming Configuration
streaming:
  buffer_size: 8192
  max_file_size_mb: 100
  auto_streaming_threshold: 0.7

# Database Configuration
databases:
  targets:
    - chroma
  connections:
    chroma:
      type: chroma
      path: .eless_chroma
      collection_name: eless_vectors
    qdrant:
      type: qdrant
      host: localhost
      port: 6333
      collection_name: eless_vectors

# Parallel Processing
parallel:
  enable: false
  max_workers: 4
  mode: thread
```

---

## Error Handling

### Exception Types

#### `ConfigurationError`

Raised when configuration is invalid.

```python
from src.core.exceptions import ConfigurationError

try:
    config = ConfigLoader.load_config("invalid.yaml")
except ConfigurationError as e:
    print(f"Configuration error: {e}")
```

#### `DatabaseConnectionError`

Raised when database connection fails.

```python
from src.database.exceptions import DatabaseConnectionError

try:
    db_loader.initialize_database_connections()
except DatabaseConnectionError as e:
    print(f"Database error: {e}")
```

---

## Best Practices

### 1. Always Use Context Managers

```python
pipeline = ElessPipeline(config)
try:
    pipeline.run_process(source_path)
finally:
    pipeline.cleanup()
```

### 2. Enable Resumption for Long Jobs

```python
config["cache"]["enable_resume"] = True
pipeline = ElessPipeline(config)
pipeline.run_process(source_path)
```

### 3. Monitor Resources

```python
resource_monitor = ResourceMonitor(config)
if resource_monitor.check_resources():
    pipeline.run_process(source_path)
else:
    print("Insufficient resources")
```

### 4. Use Adaptive Batching

```python
config["resource_limits"]["enable_adaptive_batching"] = True
config["embedding"]["batch_size"] = 32  # Starting batch size
```

### 5. Configure Appropriate Log Levels

```python
# Development
config["logging"]["level"] = "DEBUG"

# Production
config["logging"]["level"] = "INFO"
```

---

## Performance Tuning

### Memory-Constrained Systems

```yaml
resource_limits:
  max_memory_mb: 256
  enable_adaptive_batching: true

streaming:
  auto_streaming_threshold: 0.5

embedding:
  batch_size: 8
```

### High-Performance Systems

```yaml
resource_limits:
  max_memory_mb: 4096
  enable_adaptive_batching: true

parallel:
  enable: true
  max_workers: 8
  mode: process

embedding:
  batch_size: 128
  device: cuda
```

---

## Migration Guide

### From Version 0.x to 1.0

1. **Configuration Structure Changes:**
   - `database` renamed to `databases`
   - New `resource_limits` section required
   
2. **API Changes:**
   - `Pipeline.run()` split into `run_process()` and `run_resume()`
   - `StateManager.get_files()` renamed to `get_all_files()`

3. **CLI Changes:**
   - `eless run` renamed to `eless process`
   - New `--databases` flag replaces `--db`

---

## Troubleshooting

### Common Issues

**Issue:** "No active database connections"
```bash
# Solution: Install database dependencies
pip install chromadb langchain-community
```

**Issue:** "Memory error during embedding"
```yaml
# Solution: Reduce batch size and enable streaming
resource_limits:
  max_memory_mb: 512
embedding:
  batch_size: 8
streaming:
  auto_streaming_threshold: 0.5
```

**Issue:** "Corrupted manifest file"
```bash
# Solution: Remove manifest and restart
rm .eless_cache/cache_manifest.json
eless process /path/to/documents
```

---

## License

MIT License - See LICENSE file for details.

## Support

- **GitHub Issues:** https://github.com/Bandalaro/eless/issues
- **Documentation:** https://github.com/Bandalaro/eless#readme
