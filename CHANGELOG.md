# Changelog

All notable changes to ELESS will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-03

### Added
- **Interactive Configuration Wizard**: `eless config wizard` for guided setup
- **Preset Configurations**: Quick setup for minimal, standard, high-end, and Docker deployments
- **Auto-Detection**: `eless config auto-detect` for optimal system-specific settings
- **Real-time System Monitoring**: `eless monitor` command with live resource tracking
- **Smart Cache Management**: LRU eviction, corruption recovery, and size limits
- **Adaptive Resource Management**: Automatic batch size adjustment based on available memory
- **Complete Storage Control**: CLI options for cache, log, and data directory customization
- **Multi-Database Support**: ChromaDB, FAISS, Qdrant, PostgreSQL, and Cassandra connectors
- **Resource-Aware Processing**: CPU and memory monitoring with throttling capabilities
- **Configuration Validation**: Built-in config file validation and error checking
- **Comprehensive CLI Interface**: Full-featured command-line interface with helpful subcommands

### Core Features
- **Document Processing Pipeline**: Scan → Parse → Chunk → Embed → Store workflow
- **Multiple File Format Support**: PDF, DOCX, TXT, MD, XLSX, CSV, HTML parsing
- **Embedding Model Integration**: Sentence Transformers with configurable models and devices
- **State Management**: Resumable processing with checkpoint support
- **Logging System**: Structured logging with file rotation and multiple log levels
- **Error Recovery**: Graceful handling of failures with automatic retry logic

### Performance Optimizations
- **Low-End System Support**: Optimized for 2GB+ RAM systems
- **Batch Processing**: Configurable batch sizes for embedding and database operations
- **Memory Pressure Detection**: Automatic resource constraint handling
- **Cache Size Limits**: Configurable cache limits with automatic cleanup
- **Streaming Processing**: Memory-efficient processing of large document collections

### Installation Options
- **Core Installation**: `pip install eless` (minimal dependencies)
- **Full Installation**: `pip install eless[full]` (all optional features)
- **Targeted Installation**: Install specific feature sets (embeddings, databases, parsers)

### Documentation
- **Comprehensive README**: Complete setup and usage instructions
- **Storage Configuration Guide**: Detailed documentation for data location control
- **User Configurability Analysis**: Full breakdown of customizable vs. fixed components
- **Architecture Documentation**: Technical details and extension points

### Platform Support
- **Python**: 3.8, 3.9, 3.10, 3.11, 3.12
- **Operating Systems**: Linux, macOS, Windows
- **Architectures**: x86_64, ARM64 (Apple Silicon)

### Database Compatibility
- **ChromaDB**: Local vector database for easy setup
- **FAISS**: High-performance similarity search and clustering
- **Qdrant**: Cloud-ready vector database with HTTP API
- **PostgreSQL**: Traditional SQL database with vector extensions
- **Cassandra**: Distributed NoSQL for high-scale deployments

## [Unreleased]

### Planned Features
- **Plugin Architecture**: Extensible system for custom parsers, chunkers, and embedders
- **Multiple Embedding Providers**: OpenAI, Cohere, Azure OpenAI integration
- **Semantic Chunking**: Advanced text splitting strategies
- **Event-Driven Architecture**: Hooks and notifications for custom workflows
- **Hot Configuration Reload**: Runtime configuration updates without restart
- **Web-based Management Interface**: Browser-based monitoring and control
- **Distributed Processing**: Multi-node processing support
- **Advanced Caching Backends**: Redis, S3, and database-backed caching

### Known Issues
- **GPU Detection**: Limited GPU auto-detection and configuration
- **Large File Memory Usage**: Full file loading for very large documents
- **Plugin System**: No current support for user-defined plugins
- **Real-time Updates**: Configuration changes require pipeline restart

## Development

### Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and contribution guidelines.

### License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.