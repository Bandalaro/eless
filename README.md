# ELESS - Evolving Low-resource Embedding and Storage System

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-56%20passing-brightgreen.svg)](https://github.com/Bandalaro/eless)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A resilient RAG (Retrieval-Augmented Generation) data processing pipeline with comprehensive logging, multi-database support, and an intuitive CLI interface. Built for efficiency on low-resource systems while maintaining production-grade reliability.

## Features

- **Multi-Database Support**: ChromaDB, Qdrant, FAISS, PostgreSQL, Cassandra (install extras for full support)
- **Multiple File Formats**: PDF, DOCX, TXT, MD, HTML, and more (install parsers extra)
- **Resumable Processing**: Checkpoint-based system for interrupted workflows
- **Comprehensive Logging**: Structured logs with rotation and performance tracking
- **Smart Caching**: Content-based hashing and atomic manifest writes
- **Flexible Embeddings**: Support for various sentence-transformers models (install embeddings extra)
- **Memory Efficient**: Streaming processing for large files
- **Production Ready**: Graceful error handling and data safety features
- **CLI Interface**: Easy-to-use command-line tools
- **Modular Design**: Extensible architecture for custom parsers and databases

**Note**: ELESS gracefully handles missing optional dependencies with warnings. Install extras for full features. For Qdrant and PostgreSQL, ensure the database instances are running on the specified ports (default: Qdrant 6333, PostgreSQL 5432).

## Project Structure

For contributors, the project is organized as follows:

- `src/`: Source code for the ELESS package
- `tests/`: Unit and integration tests
- `docs/`: Documentation, including user guides, API reference, and contributing guidelines
- `tools/`: Utility scripts for deployment, packaging, and verification
- `config/`: Configuration files and templates
- `build/`: Build configuration files (setup.py, pyproject.toml, etc.)

## Quick Start

### Installation

```bash
# Install from source
git clone https://github.com/Bandalaro/eless.git
cd eless
pip install -e .

# Install with all features (recommended for full functionality)
pip install -e ".[full]"

# Or install specific extras
pip install -e ".[embeddings,databases,parsers]"
```

### Basic Usage

```bash
# Process documents with default settings
eless process /path/to/documents

# Process with specific database
eless process /path/to/documents --databases chroma

# Process with custom settings
eless process /path/to/documents --chunk-size 1000 --log-level DEBUG

# Check processing status
eless status --all

# Resume interrupted processing
eless process /path/to/documents --resume
```

### Python API

```python
from eless import ElessPipeline
import yaml

# Load configuration
with open("config/default_config.yaml") as f:
    config = yaml.safe_load(f)

# Create and run pipeline
pipeline = ElessPipeline(config)
pipeline.run_process("/path/to/documents")

# Check status
files = pipeline.state_manager.get_all_files()
for file in files:
    print(f"{file['path']}: {file['status']}")
```

## 📋 Requirements

### Core Dependencies
- Python 3.8+
- click >= 8.0.0
- PyYAML >= 6.0
- numpy >= 1.21.0
- psutil >= 5.8.0

### Optional Dependencies

**Embeddings:**
```bash
pip install sentence-transformers torch
```

**Databases:**
```bash
# ChromaDB
pip install chromadb langchain-community langchain-core

# Qdrant
pip install qdrant-client

# FAISS
pip install faiss-cpu  # or faiss-gpu for GPU support

# PostgreSQL
pip install psycopg2-binary

# Cassandra
pip install cassandra-driver
```

**Document Parsers:**
```bash
pip install pypdf python-docx openpyxl pandas beautifulsoup4 lxml
```

**All Features:**
```bash
pip install -e ".[full]"
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│         CLI Interface (Click)           │
├─────────────────────────────────────────┤
│      ElessPipeline (Orchestrator)       │
├──────────┬──────────┬───────────────────┤
│ Scanner  │Dispatcher│  State Manager    │
├──────────┼──────────┼───────────────────┤
│ Parsers  │ Chunker  │  Archiver         │
├──────────┴──────────┼───────────────────┤
│      Embedder       │  Resource Monitor │
├─────────────────────┼───────────────────┤
│  Database Loader    │  Logging System   │
└─────────────────────┴───────────────────┘
```

### Key Components

- **FileScanner**: Discovers and hashes files using SHA-256
- **Dispatcher**: Routes files to appropriate parsers
- **TextChunker**: Intelligent text segmentation with overlap
- **Embedder**: Generates vector embeddings with caching
- **DatabaseLoader**: Multi-database coordination
- **StateManager**: Tracks processing state with atomic writes
- **ResourceMonitor**: Adaptive resource management

## 🎛️ Configuration

Create a `config.yaml` file or modify `config/default_config.yaml`:

```yaml
# Logging
logging:
  directory: .eless_logs
  level: INFO
  enable_console: true

# Embedding
embedding:
  model_name: all-MiniLM-L6-v2
  device: cpu
  batch_size: 32

# Chunking
chunking:
  chunk_size: 500
  overlap: 50
  strategy: semantic

# Databases
databases:
  targets:
    - chroma
  connections:
    chroma:
      type: chroma
      path: .eless_chroma
      collection_name: eless_vectors

# Resource Limits
resource_limits:
  max_memory_mb: 512
  enable_adaptive_batching: true

# Streaming
streaming:
  buffer_size: 8192
  max_file_size_mb: 100
  auto_streaming_threshold: 0.7
```

## Documentation

- **[Quick Start Guide](docs/QUICK_START.md)** - Get started in 5 minutes
- **[API Reference](docs/API_REFERENCE.md)** - Complete API documentation
- **[Developer Guide](docs/DEVELOPER_GUIDE.md)** - Contributing and development
- **[Documentation Index](docs/README.md)** - All documentation

## Use Cases

### Document Processing Pipeline
```bash
# Process research papers
eless process papers/ \
  --databases chroma \
  --chunk-size 1000 \
  --log-level INFO
```

### RAG System Setup
```bash
# Index documentation
eless process docs/ \
  --databases qdrant \
  --databases faiss

# Query your RAG application
python query_rag.py "machine learning techniques"
```

### Batch Processing
```bash
# Process multiple directories
for dir in dataset1 dataset2 dataset3; do
  eless process "$dir" --databases chroma --resume
done
```

## CLI Commands

### Process Documents
```bash
eless process <path> [OPTIONS]

Options:
  --databases, -db <name>    Select databases (repeatable)
  --config <file>            Custom configuration file
  --resume                   Resume interrupted processing
  --chunk-size <size>        Override chunk size
  --batch-size <size>        Override batch size
  --log-level <level>        Set log level
  --log-dir <path>           Custom log directory
```

### Check Status
```bash
eless status [OPTIONS]

Options:
  --all                      Show all tracked files
  <file_id>                  Show specific file details
```

### System Management
```bash
eless config-info          # Display configuration
eless test                 # Run system tests
eless logs [--days N]      # Manage log files
```

## Testing

```bash
# Run all tests
pytest tests/

# Run specific test suite
pytest tests/test_cli.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Test results: 56/56 passing ✅
```

## Contributing

We welcome contributions! Please see [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone and setup
git clone https://github.com/Bandalaro/eless.git
cd eless
python3 -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -e ".[dev,full]"

# Run tests
pytest tests/

# Format code
black src/ tests/

# Check linting
flake8 src/ tests/
```

## Performance

### Optimized for Low-Resource Systems
```yaml
resource_limits:
  max_memory_mb: 256
  enable_adaptive_batching: true

embedding:
  batch_size: 8

streaming:
  auto_streaming_threshold: 0.5
```

### High-Performance Configuration
```yaml
resource_limits:
  max_memory_mb: 4096

embedding:
  batch_size: 128
  device: cuda

parallel:
  enable: true
  max_workers: 8
```

## Troubleshooting

### Common Issues

**Missing Dependencies:**
```bash
# Install embedding support
pip install sentence-transformers

# Install database support
pip install chromadb langchain-community
```

**Memory Issues:**
```yaml
# Reduce memory usage
embedding:
  batch_size: 8
streaming:
  auto_streaming_threshold: 0.5
```

**Slow Processing:**
```yaml
# Increase performance
embedding:
  batch_size: 64
parallel:
  enable: true
  max_workers: 4
```

See [docs/QUICK_START.md](docs/QUICK_START.md#troubleshooting) for more solutions.

## Project Status

- **56/56 tests passing**
- **Zero warnings**
- **Production ready**
- **Comprehensive documentation**
- **Active development**

## Roadmap

- [ ] PyPI publication
- [ ] Additional database connectors (Milvus, Weaviate)
- [ ] Web interface
- [ ] Docker support
- [ ] Distributed processing
- [ ] Advanced query capabilities

## License

This project is licensed under the MIT License - see the [docs/LICENSE](docs/LICENSE) file for details.

## Acknowledgments

- Built with [sentence-transformers](https://www.sbert.net/)
- Supports [ChromaDB](https://www.trychroma.com/), [Qdrant](https://qdrant.tech/), and more
- Powered by the Python ecosystem

## Support

- **Issues**: [GitHub Issues](https://github.com/Bandalaro/eless/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Bandalaro/eless/discussions)
- **Documentation**: [docs/](docs/)

## Star History

If you find ELESS useful, please consider giving it a star on GitHub!

---

**Made with love by [Bandalaro](https://github.com/Bandalaro)**

**Status: Production Ready** | **Version: 1.0.0**
