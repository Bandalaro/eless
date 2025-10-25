# ELESS Documentation

Welcome to the official documentation for **ELESS** (Evolving Low-resource Embedding and Storage System) - a resilient RAG data processing pipeline designed for efficiency and reliability.

---

## Documentation Overview

This documentation is organized into the following sections:

### **Getting Started**

- [Installation Guide](#installation)
- [Quick Start](#quick-start)
- [Configuration Guide](#configuration)

### **Core Documentation**

- **[API Reference](API_REFERENCE.md)** - Complete API documentation for all classes and methods
- **[Developer Guide](DEVELOPER_GUIDE.md)** - In-depth guide for developers and contributors
- **[Examples & Usage](EXAMPLES_AND_USAGE.md)** - Practical examples and use cases
- **[Test Documentation](TEST_DOCUMENTATION.md)** - Testing infrastructure and test suite documentation

### **Additional Resources**

- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Contributing](#contributing)
- [Changelog](../CHANGELOG.md)

---

## Installation

### Basic Installation

```bash
# Clone the repository
git clone https://github.com/Bandalaro/eless.git
cd eless

# Install core package
pip install -e .
```

### Full Installation (Recommended)

```bash
# Install with all features
pip install -e ".[full]"
```

This includes:
- Embedding models (sentence-transformers, torch)
- Database connectors (ChromaDB, Qdrant, FAISS, PostgreSQL, Cassandra)
- Document parsers (PDF, DOCX, XLSX, HTML)

### Custom Installation

Install only the features you need:

```bash
# Embeddings only
pip install -e ".[embeddings]"

# Databases only
pip install -e ".[databases]"

# Parsers only
pip install -e ".[parsers]"

# Development tools
pip install -e ".[dev]"
```

### Requirements

- **Python**: 3.8 or higher
- **Operating System**: Linux, macOS, Windows
- **Memory**: 2GB+ recommended
- **Disk Space**: 5GB+ recommended (for models and cache)

---

## Quick Start

### 1. Health Check

First, verify your installation:

```bash
eless health
```

This checks:
- Python version
- Core dependencies
- Optional dependencies
- System resources
- Configuration validity

### 2. Initialize Configuration

Run the setup wizard:

```bash
eless init
```

Or use a quick-start template:

```bash
# List available templates
eless template list

# Create config from template
eless template create lightweight
```

### 3. Process Your First Documents

#### Option A: Simple Processing

```bash
eless go /path/to/documents
```

#### Option B: Full Control

```bash
eless process /path/to/documents \
  --databases chroma,faiss \
  --chunk-size 512 \
  --log-level INFO
```

#### Option C: Interactive Mode

```bash
eless process -i
```

### 4. Check Status

```bash
# View all processed files
eless status --all

# View files by status
eless status --status LOADED
```

### 5. Try the Demo

```bash
# Process sample documents
eless demo
```

---

## Configuration

### Configuration File Structure

ELESS uses YAML configuration files. Here's a minimal example:

```yaml
cache:
  directory: ".eless_cache"
  manifest_file: "manifest.json"

chunking:
  chunk_size: 512
  chunk_overlap: 50
  method: "recursive"

embedding:
  model_name: "all-MiniLM-L6-v2"
  batch_size: 32
  device: "cpu"

databases:
  targets:
    - chroma
  connections:
    chroma:
      host: "localhost"
      port: 8000
      collection_name: "eless_collection"

logging:
  level: "INFO"
  directory: ".eless_logs"
```

### Configuration Templates

ELESS provides pre-configured templates:

**Lightweight** (Low resource usage):
- FAISS database
- Small embedding model
- Minimal logging

**Balanced** (Good performance):
- ChromaDB database
- Standard embedding model
- Moderate logging

**Production** (High performance):
- Multiple databases
- Large embedding model
- Comprehensive logging

**Development** (For testing):
- Debug logging
- Frequent checkpoints
- Multiple databases

Create from template:

```bash
eless template create balanced --output my_config.yaml
```

### Custom Configuration

Create your own configuration file or use the wizard:

```bash
# Interactive wizard
eless init

# Use custom config
eless process /docs --config my_config.yaml
```

---

## Architecture Overview

### Pipeline Flow

```
Input Documents
    ↓
[File Scanner] ─→ Discovers files, generates hashes
    ↓
[Dispatcher] ─→ Routes to parsers, chunks text
    ↓
[Embedder] ─→ Generates vector embeddings
    ↓
[Database Loader] ─→ Stores in vector databases
    ↓
Complete
```

### Core Components

**State Manager**: Tracks file processing status via `manifest.json`  
**Archiver**: Caches chunks and vectors for resumability  
**Resource Monitor**: Monitors CPU, memory, and disk usage  
**Config Loader**: Manages configuration with override support  

### Supported Formats

**Documents**:
- PDF (.pdf)
- Microsoft Word (.docx)
- Plain text (.txt)
- Markdown (.md)
- HTML (.html)
- Microsoft Excel (.xlsx)

**Databases**:
- ChromaDB
- Qdrant
- FAISS
- PostgreSQL (with pgvector)
- Apache Cassandra

**Embedding Models**:
- All sentence-transformers models
- Custom model support

---

## Key Features

### Resumable Processing

ELESS automatically checkpoints progress:

```bash
# Start processing
eless process /large/dataset

# If interrupted, resume with:
eless process /large/dataset --resume

# Or programmatically:
pipeline.run_resume()
```

### State Tracking

Every file has a status:

- **PENDING**: Discovered but not processed
- **SCANNED**: Hash generated
- **CHUNKED**: Text extracted and chunked
- **EMBEDDED**: Vectors generated
- **LOADED**: Stored in databases
- **ERROR**: Processing failed

### Smart Caching

- Content-based hashing (SHA-256)
- Atomic manifest writes
- Automatic backup and recovery
- Duplicate detection

### Multi-Database Support

Store vectors in multiple databases simultaneously:

```bash
eless process /docs --databases chroma,faiss,qdrant
```

### Comprehensive Logging

- Structured JSON logs
- Automatic log rotation
- Performance tracking
- Error context capture

---

## Common Use Cases

### 1. Document Ingestion Pipeline

```bash
# Process documents and load to ChromaDB
eless process /documents --databases chroma
```

### 2. RAG System Backend

```python
from eless import ElessPipeline

# Initialize pipeline
pipeline = ElessPipeline(config)

# Process knowledge base
pipeline.run_process("/knowledge_base")

# Query via database connector
# (Use your preferred DB client for queries)
```

### 3. Batch Processing

```bash
# Process multiple directories
for dir in /data/*; do
    eless process "$dir" --databases faiss
done
```

### 4. Development & Testing

```bash
# Use demo data
eless demo

# Run tests
eless test

# Monitor resources
eless monitor
```

---

## Troubleshooting

### Installation Issues

**Problem**: Missing dependencies

```bash
# Solution: Install full dependencies
pip install -e ".[full]"

# Check health
eless health
```

**Problem**: Import errors

```bash
# Solution: Run doctor command
eless doctor
```

### Processing Issues

**Problem**: Database connection failed

```bash
# Check if database is running
# For Qdrant: Ensure port 6333 is accessible
# For PostgreSQL: Ensure port 5432 is accessible

# Test specific database
eless test --test-db chroma
```

**Problem**: Out of memory

```bash
# Reduce batch size in config
embedding:
  batch_size: 16  # Lower from default 32

# Or use streaming mode (automatic for large files)
```

**Problem**: Files not processing

```bash
# Check file status
eless status --all

# View logs
tail -f .eless_logs/eless.log

# Resume processing
eless process /docs --resume
```

### Performance Issues

**Problem**: Slow processing

```bash
# Monitor resources
eless monitor

# Use parallel processing (if available)
# Reduce chunk size for faster processing
# Use FAISS instead of ChromaDB for speed
```

---

## FAQ

### Q: Which database should I use?

**A**: It depends on your needs:

- **ChromaDB**: Best for beginners, easy setup, good for development
- **FAISS**: Fastest search, best for production with large datasets
- **Qdrant**: Good balance, production-ready, features-rich
- **PostgreSQL**: When you need SQL + vectors, existing PostgreSQL infrastructure
- **Cassandra**: Distributed systems, high scalability requirements

### Q: Can I use my own embedding model?

**A**: Yes! Configure in the config file:

```yaml
embedding:
  model_name: "your-model-name"
  # Or local path:
  model_name: "/path/to/model"
```

Any sentence-transformers compatible model works.

### Q: How do I resume interrupted processing?

**A**: Use the `--resume` flag:

```bash
eless process /docs --resume
```

ELESS automatically tracks progress in `manifest.json`.

### Q: Where are cached files stored?

**A**: By default in `.eless_cache/`:

- `.chunks.pkl`: Chunked text
- `.vectors.npy`: Vector embeddings
- `manifest.json`: Processing state

Configure with `--cache-dir` or in config file.

### Q: Can I process files without databases?

**A**: Yes, but vectors won't be persisted. Use for:

- Testing embeddings
- Generating cached vectors
- Pre-processing before database setup

### Q: How do I add a custom database?

**A**: Implement `DBConnectorBase`:

```python
from eless.database.db_connector_base import DBConnectorBase

class MyConnector(DBConnectorBase):
    def connect(self): ...
    def upsert_batch(self, vectors): ...
    def search(self, query_vector, limit): ...
    def close(self): ...
    def check_connection(self): ...
```

See [Developer Guide](DEVELOPER_GUIDE.md) for details.

---

## Contributing

We welcome contributions! Please see:

- [Developer Guide](DEVELOPER_GUIDE.md) - Development setup and guidelines
- [GitHub Repository](https://github.com/Bandalaro/eless) - Source code
- [Issue Tracker](https://github.com/Bandalaro/eless/issues) - Report bugs

### Quick Contribution Guide

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/eless.git
cd eless

# Install development dependencies
pip install -e ".[dev,full]"

# Run tests
pytest tests/

# Code formatting
black src/
flake8 src/

# Type checking
mypy src/
```

---

## Additional Resources

### Documentation Files

- **[API Reference](API_REFERENCE.md)** - Complete API documentation
- **[Developer Guide](DEVELOPER_GUIDE.md)** - Development and architecture
- **[Examples & Usage](EXAMPLES_AND_USAGE.md)** - Practical examples
- **[Test Documentation](TEST_DOCUMENTATION.md)** - Testing guide

### External Links

- [GitHub Repository](https://github.com/Bandalaro/eless)
- [Issue Tracker](https://github.com/Bandalaro/eless/issues)
- [Changelog](https://github.com/Bandalaro/eless/blob/main/CHANGELOG.md)

### Community

- Submit issues on GitHub
- Contribute via pull requests
- Share your use cases

---

## License

ELESS is released under the MIT License. See [LICENSE](../LICENSE) for details.

---

## Support

Need help?

1. Check this documentation
2. Run `eless doctor` for diagnostics
3. Search [existing issues](https://github.com/Bandalaro/eless/issues)
4. Create a new issue with:
   - Output of `eless doctor`
   - Steps to reproduce
   - Error messages and logs

---

**Happy Processing!**

---

**Documentation Version**: 1.0  
**ELESS Version**: 1.0.0  
**Last Updated**: 2025-10-25
