# ELESS Configuration Guide

This guide explains how to configure the `config.yaml` file for the ELESS package. The configuration is in YAML format and controls various aspects of the pipeline, including caching, logging, embeddings, chunking, and databases.

## Configuration File Structure

Create a `config.yaml` file in your project root or specify its path via the CLI. It should follow the structure of `config/default_config.yaml`. Below are all available options with descriptions.

### Cache Configuration

Controls file caching and state management.

```yaml
cache:
  directory: .eless_cache          # Directory for storing cached files and manifest
  manifest_file: manifest.json     # File to track processing state
```

- **directory**: Path to the cache directory (relative or absolute). Stores chunks, vectors, and logs.
- **manifest_file**: Name of the JSON file that tracks file processing status (e.g., PENDING, CHUNKED, EMBEDDED).

### Logging Configuration

Manages logging behavior.

```yaml
logging:
  directory: .eless_logs           # Directory for log files
  level: INFO                      # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
  enable_console: true             # Whether to output logs to console
  max_file_size_mb: 10             # Max size of each log file before rotation (MB)
  backup_count: 5                  # Number of backup log files to keep
```

- **directory**: Path to log directory.
- **level**: Minimum log level to record.
- **enable_console**: If true, logs appear in terminal.
- **max_file_size_mb**: Log files rotate when exceeding this size.
- **backup_count**: Number of rotated log files retained.

### Embedding Configuration

Settings for the embedding model.

```yaml
embedding:
  model: "sentence-transformers/all-MiniLM-L6-v2"  # Model name or path
  dimension: 384                                    # Embedding vector dimension
  device: "cpu"                                     # Device: cpu or cuda
  batch_size: 32                                    # Batch size for inference
```

- **model**: Hugging Face model name or local path.
- **dimension**: Output dimension of embeddings (must match model).
- **device**: Computation device (cpu for low-resource, cuda for GPU).
- **batch_size**: Number of texts processed per batch (lower for memory constraints).

### Chunking Configuration

Controls text splitting into chunks.

```yaml
chunking:
  chunk_size: 500                  # Maximum characters per chunk
  chunk_overlap: 50                # Overlap between chunks (characters)
```

- **chunk_size**: Max length of each text chunk.
- **chunk_overlap**: Characters overlapping between consecutive chunks for context.

### Databases Configuration

Settings for vector databases.

```yaml
databases:
  batch_size: 64                   # Batch size for database operations
  default:
    drop_existing: false           # Whether to drop existing collections on init
  targets:                         # List of databases to use
    - chroma
    # - faiss
    # - qdrant
    # - postgresql
    # - cassandra
  connections:                     # Per-database settings
    chroma:
      type: chroma
      path: .eless_chroma
    faiss:
      type: faiss
      index_path: .eless_faiss/index.faiss
      metadata_path: .eless_faiss/metadata.json
    qdrant:
      type: qdrant
      host: localhost
      port: 6333
      api_key: null
      collection_name: eless_embeddings
      timeout: 30
    postgresql:
      type: postgresql
      host: localhost
      port: 5432
      user: your_user
      password: your_password
      database: your_db
      table_name: eless_embeddings
      vector_column: embedding
    cassandra:
      type: cassandra
      hosts: [localhost]
      port: 9042
      keyspace: eless_keyspace
      table_name: eless_embeddings
      replication_factor: 1
```

- **batch_size**: Number of vectors upserted per batch.
- **drop_existing**: If true, drops existing data on database init.
- **targets**: List of enabled databases (uncomment to enable).
- **connections**: Specific settings per database (e.g., paths, hosts, credentials).

## How to Use

1. Copy `config/default_config.yaml` to `config.yaml` and modify as needed.
2. Run ELESS with: `eless process /path/to/documents --config config.yaml`.
3. For resume: `eless process /path/to/documents --config config.yaml --resume`.

## Best Practices

- Use absolute paths for directories to avoid issues.
- Set lower batch sizes for low-memory systems.
- Enable only needed databases in `targets`.
- Secure credentials (e.g., passwords) in production.
- Test with small datasets first.

For more examples, see `docs/EXAMPLES_AND_USAGE.md`.