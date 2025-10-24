# ELESS Function Documentation

This document provides detailed documentation for all public functions and methods in the ELESS package.

## Core Components

### ElessPipeline

**Location:** `src/eless/eless_pipeline.py`

#### `ElessPipeline(config: Dict[str, Any])`

Initializes the ELESS pipeline with the given configuration.

**Parameters:**
- `config` (Dict[str, Any]): Configuration dictionary.

#### `run_process(source_path: str)`

Executes the full pipeline for processing documents.

**Parameters:**
- `source_path` (str): Path to the file or directory to process.

#### `run_resume()`

Resumes processing from the last checkpoint.

### StateManager

**Location:** `src/eless/core/state_manager.py`

#### `StateManager(config: Dict[str, Any])`

Initializes the state manager.

**Parameters:**
- `config` (Dict[str, Any]): Configuration with cache settings.

#### `get_status(file_hash: str) -> str`

Returns the current status of a file.

**Parameters:**
- `file_hash` (str): SHA-256 hash of the file.

#### `add_or_update_file(file_hash: str, status: str, file_path: Optional[str] = None, metadata: Optional[Dict] = None)`

Adds or updates a file's status.

**Parameters:**
- `file_hash` (str): SHA-256 hash of the file.
- `status` (str): New status.
- `file_path` (Optional[str]): File path.
- `metadata` (Optional[Dict]): Additional metadata.

#### `get_all_files() -> List[Dict[str, Any]]`

Returns all tracked files.

#### `get_all_hashes() -> List[str]`

Returns all file hashes.

#### `get_file_hash(file_path: str) -> str`

Generates SHA-256 hash for a file.

**Parameters:**
- `file_path` (str): Path to the file.

### ConfigLoader

**Location:** `src/eless/core/config_loader.py`

#### `ConfigLoader(default_config_path: Optional[Path] = None)`

Initializes the config loader.

**Parameters:**
- `default_config_path` (Optional[Path]): Path to default config file.

#### `get_final_config(user_config_path: Optional[str] = None, **cli_args) -> Dict[str, Any]`

Loads and merges configuration.

**Parameters:**
- `user_config_path` (Optional[str]): Path to user config.
- `cli_args`: CLI arguments.

#### `load_config(config_path: Path) -> Dict[str, Any]`

Loads configuration from a file.

**Parameters:**
- `config_path` (Path): Path to config file.

#### `validate_config(config: Dict[str, Any])`

Validates configuration.

**Parameters:**
- `config` (Dict[str, Any]): Configuration to validate.

### Archiver

**Location:** `src/eless/core/archiver.py`

#### `Archiver(config: Dict[str, Any])`

Initializes the archiver.

**Parameters:**
- `config` (Dict[str, Any]): Configuration with cache settings.

#### `save_chunks(file_hash: str, chunks: List[Dict[str, Any]])`

Saves chunks to cache.

**Parameters:**
- `file_hash` (str): File hash.
- `chunks` (List[Dict[str, Any]]): List of chunks.

#### `load_chunks(file_hash: str) -> Optional[List[Dict[str, Any]]]`

Loads chunks from cache.

**Parameters:**
- `file_hash` (str): File hash.

#### `save_vectors(file_hash: str, vectors: np.ndarray)`

Saves vectors to cache.

**Parameters:**
- `file_hash` (str): File hash.
- `vectors` (np.ndarray): Vector array.

#### `load_vectors(file_hash: str) -> Optional[np.ndarray]`

Loads vectors from cache.

**Parameters:**
- `file_hash` (str): File hash.

### ResourceMonitor

**Location:** `src/eless/core/resource_monitor.py`

#### `ResourceMonitor(config: Dict[str, Any])`

Initializes the resource monitor.

**Parameters:**
- `config` (Dict[str, Any]): Configuration.

#### `get_memory_usage() -> float`

Returns current memory usage percentage.

#### `get_cpu_usage() -> float`

Returns current CPU usage percentage.

## Processing Components

### FileScanner

**Location:** `src/eless/processing/file_scanner.py`

#### `FileScanner(config: Dict[str, Any])`

Initializes the file scanner.

**Parameters:**
- `config` (Dict[str, Any]): Configuration.

#### `scan_input(input_path: Union[str, Path]) -> List[Dict[str, Union[str, Path]]]`

Scans input path for files.

**Parameters:**
- `input_path` (Union[str, Path]): Path to scan.

#### `get_supported_extensions() -> List[str]`

Returns list of supported file extensions.

### Dispatcher

**Location:** `src/eless/processing/dispatcher.py`

#### `Dispatcher(config: Dict[str, Any], state_manager: StateManager, archiver: Archiver)`

Initializes the dispatcher.

**Parameters:**
- `config` (Dict[str, Any]): Configuration.
- `state_manager` (StateManager): State manager instance.
- `archiver` (Archiver): Archiver instance.

#### `process_document(file_data: Dict[str, Any]) -> Generator[Dict[str, Any], None, None]`

Processes a single document.

**Parameters:**
- `file_data` (Dict[str, Any]): File data dictionary.

#### `parse_and_chunk(file_path: Path, file_meta: Dict[str, Any]) -> List[Dict[str, Any]]`

Parses and chunks a file.

**Parameters:**
- `file_path` (Path): Path to file.
- `file_meta` (Dict[str, Any]): File metadata.

## Embedding Components

### Embedder

**Location:** `src/eless/embedding/embedder.py`

#### `Embedder(config: Dict[str, Any], state_manager: StateManager, archiver: Archiver)`

Initializes the embedder.

**Parameters:**
- `config` (Dict[str, Any]): Configuration.
- `state_manager` (StateManager): State manager instance.
- `archiver` (Archiver): Archiver instance.

#### `embed_file_chunks(file_hash: str, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]`

Embeds chunks for a file.

**Parameters:**
- `file_hash` (str): File hash.
- `chunks` (List[Dict[str, Any]]): List of chunks.

#### `embed_and_archive_chunks(chunks_generator: Generator[Dict[str, Any], None, None]) -> Generator[Dict[str, Any], None, None]`

Embeds and archives chunks from generator.

**Parameters:**
- `chunks_generator` (Generator[Dict[str, Any], None, None]): Generator of chunks.

### ModelLoader

**Location:** `src/eless/embedding/model_loader.py`

#### `ModelLoader(config: Dict[str, Any])`

Initializes the model loader.

**Parameters:**
- `config` (Dict[str, Any]): Configuration.

#### `embed_chunks(texts: List[str]) -> np.ndarray`

Embeds a list of texts.

**Parameters:**
- `texts` (List[str]): List of text strings.

## Database Components

### DatabaseLoader

**Location:** `src/eless/database/db_loader.py`

#### `DatabaseLoader(config: Dict[str, Any], state_manager: StateManager, embedding_model)`

Initializes the database loader.

**Parameters:**
- `config` (Dict[str, Any]): Configuration.
- `state_manager` (StateManager): State manager instance.
- `embedding_model`: Embedding model instance.

#### `load_data(embedded_chunk_generator: Generator[Dict[str, Any], None, None])`

Loads data into databases.

**Parameters:**
- `embedded_chunk_generator` (Generator[Dict[str, Any], None, None]): Generator of embedded chunks.

#### `search(query: str, limit: int = 10) -> List[Dict[str, Any]]`

Searches across databases.

**Parameters:**
- `query` (str): Search query.
- `limit` (int): Maximum results.

#### `batch_upsert(batch: List[Dict[str, Any]])`

Upserts a batch to databases.

**Parameters:**
- `batch` (List[Dict[str, Any]]): List of data entries.

### DBConnectorBase

**Location:** `src/eless/database/db_connector_base.py`

#### `DBConnectorBase(config: Dict[str, Any], connection_name: str, dimension: int)`

Initializes the base connector.

**Parameters:**
- `config` (Dict[str, Any]): Configuration.
- `connection_name` (str): Connection name.
- `dimension` (int): Embedding dimension.

#### `connect()`

Establishes connection.

#### `upsert_batch(vectors: List[Dict[str, Any]])`

Upserts a batch of vectors.

**Parameters:**
- `vectors` (List[Dict[str, Any]]): List of vectors.

#### `search(query_vector: List[float], limit: int = 10) -> List[Dict[str, Any]]`

Searches for similar vectors.

**Parameters:**
- `query_vector` (List[float]): Query vector.
- `limit` (int): Maximum results.

#### `close()`

Closes the connection.

#### `check_connection() -> bool`

Checks if connection is active.

## CLI Interface

The CLI is accessed via the `eless` command. See QUICK_START.md for command reference.

### Main Commands

- `eless process <path>`: Process documents.
- `eless status`: Check processing status.
- `eless config-info`: View configuration.
- `eless test`: Run tests.
- `eless logs`: Manage logs.

### Options

- `--databases, -db <name>`: Select database.
- `--config <path>`: Custom config file.
- `--resume`: Resume processing.
- `--chunk-size <size>`: Override chunk size.
- `--batch-size <size>`: Override batch size.
- `--log-level <level>`: Set log level.

## Usage Examples

### Basic Processing

```python
from eless import ElessPipeline
import yaml

config = yaml.safe_load(open("config/default_config.yaml"))
pipeline = ElessPipeline(config)
pipeline.run_process("/path/to/documents")
```

### Checking Status

```python
state_manager = pipeline.state_manager
files = state_manager.get_all_files()
for file in files:
    print(f"{file['path']}: {file['status']}")
```

### Searching

```python
results = pipeline.db_loader.search("your query", limit=10)
for result in results:
    print(result['content'])
```

For more examples, see QUICK_START.md and API_REFERENCE.md.