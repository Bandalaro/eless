# ELESS - Evolving Low-resource Embedding and Storage System

A resilient RAG data processing pipeline with comprehensive logging, multi-database support, and CLI interface.

## ✨ Recent Improvements

### 🎯 Database Selection CLI
- **Multi-database support**: Choose from ChromaDB, Qdrant, FAISS, PostgreSQL, and Cassandra
- **CLI database selection**: `--databases chroma --databases qdrant`
- **Runtime database targeting**: Override configuration on-the-fly

### 📊 Comprehensive Logging System
- **Structured logging**: Detailed logs with timestamps, log levels, and module names
- **File-based logging**: Automatic log files with rotation (configurable size and retention)
- **Multiple log streams**: Separate error logs and general logs
- **Performance tracking**: Execution time logging for all major operations
- **Log management**: Built-in log cleanup and file management

### 🔧 Enhanced CLI Interface
- **Global log level control**: `--log-level DEBUG`
- **Custom log directories**: `--log-dir /path/to/logs`
- **Configuration inspection**: `eless config-info`
- **System testing**: `eless test`
- **Log management**: `eless logs`
- **Comprehensive status**: `eless status --all`

### 🛠 Improved Architecture
- **Graceful dependency handling**: Missing dependencies don't crash the system
- **Performance decorators**: Automatic execution time tracking
- **Consistent error handling**: Structured exception handling throughout
- **Modular configuration**: Database-specific configuration sections

## 🚀 Quick Start

### 1. Installation
```bash
# Clone and setup
cd eless
python3 -m venv venv
source venv/bin/activate

# Install core dependencies
pip install click PyYAML numpy

# Install optional dependencies as needed
pip install sentence-transformers  # For embedding model
pip install chromadb langchain-community  # For ChromaDB support
pip install qdrant-client  # For Qdrant support
# ... see requirements.txt for complete list
```

### 2. Configuration
The system uses `config/default_config.yaml` for configuration. Key sections:

```yaml
# Logging configuration
logging:
  directory: .eless_logs
  level: INFO
  enable_console: true

# Database selection
databases:
  targets:
    - chroma
    - qdrant  # Add multiple databases
  connections:
    chroma:
      type: chroma
      path: .eless_chroma
```

### 3. Usage Examples

#### Basic Processing
```bash
# Process documents with default settings
eless process /path/to/documents

# Process with specific database
eless process /path/to/documents --databases chroma

# Process with multiple databases
eless process /path/to/documents --databases chroma --databases qdrant

# Process with custom settings
eless process /path/to/documents --chunk-size 1000 --log-level DEBUG
```

#### System Management
```bash
# Check configuration
eless config-info

# Test system components
eless test

# Test specific database
eless test --test-db chroma

# Check processing status
eless status
eless status --all

# Manage logs
eless logs
eless logs --days 7  # Clean logs older than 7 days
```

#### Advanced Usage
```bash
# Resume interrupted processing
eless process /path/to/documents --resume

# Custom configuration file
eless process /path/to/documents --config my_config.yaml

# Debug with verbose logging
eless --log-level DEBUG process /path/to/documents
```

## 🏗 Architecture Overview

### Core Components

1. **CLI Layer** (`src/cli.py`)
   - Command-line interface with database selection
   - Global logging and configuration options
   - Comprehensive help and examples

2. **Logging System** (`src/core/logging_config.py`)
   - Centralized logging configuration
   - File rotation and cleanup
   - Performance tracking decorators

3. **Configuration Management** (`src/core/config_loader.py`)
   - Hierarchical configuration merging
   - CLI override support
   - Environment-specific settings

4. **Processing Pipeline**
   - **File Scanner** (`src/processing/file_scanner.py`): Content-based file hashing
   - **Dispatcher** (`src/processing/dispatcher.py`): Parser routing and chunking coordination
   - **Text Chunker** (`src/processing/parsers/text_chunker.py`): Intelligent text segmentation

5. **Database Layer** (`src/database/`)
   - **Database Loader** (`db_loader.py`): Multi-database coordination
   - **Connector Base** (`db_connector_base.py`): Abstract connector interface
   - **Specific Connectors**: ChromaDB, Qdrant, FAISS, PostgreSQL, Cassandra

### Key Features

#### Graceful Dependency Handling
The system continues to function even with missing optional dependencies:
- Missing parsers only affect specific file types
- Missing databases are reported but don't crash the system
- Clear error messages guide users to required installations

#### Performance Monitoring
All major operations are instrumented with performance logging:
```python
@log_performance('ELESS.ComponentName')
def important_operation(self):
    # Execution time automatically logged
    pass
```

#### Comprehensive Error Handling
- Structured exception handling with context
- Graceful degradation for missing components
- Detailed error reporting with suggestions

## 📋 Commands Reference

### `eless process`
Main processing command for documents.

**Options:**
- `--databases/-db`: Select databases (repeatable)
- `--config`: Custom configuration file
- `--resume`: Resume interrupted processing
- `--chunk-size`: Override chunk size
- `--batch-size`: Override batch size

### `eless status`
Check processing status and file tracking.

**Options:**
- `--all`: Show all tracked files
- `file_id`: Show specific file details

### `eless test`
System health checks and component testing.

**Options:**
- `--test-db`: Test specific database connection

### `eless config-info`
Display current configuration and available options.

### `eless logs`
Log file management and cleanup.

**Options:**
- `--days`: Clean logs older than N days

## 🎛 Configuration Options

### Logging Configuration
```yaml
logging:
  directory: .eless_logs          # Log file location
  level: INFO                     # DEBUG|INFO|WARNING|ERROR|CRITICAL
  enable_console: true            # Console output
  max_file_size_mb: 10           # Log rotation size
  backup_count: 5                # Number of backup files
```

### Database Configuration
```yaml
databases:
  targets:                       # Active databases
    - chroma
  connections:                   # Database-specific settings
    chroma:
      type: chroma
      path: .eless_chroma
    qdrant:
      type: qdrant
      host: localhost
      port: 6333
```

## 🔍 Logging and Debugging

### Log Files
- `eless.log`: All application logs
- `eless_errors.log`: Warnings and errors only

### Log Format
```
2024-01-01 12:00:00 | INFO     | ELESS.ComponentName | function_name:123 | Message
```

### Debug Mode
Enable detailed logging for troubleshooting:
```bash
eless --log-level DEBUG process documents/
```

## 🎯 Database Support

| Database | Status | Installation |
|----------|--------|-------------|
| ChromaDB | ✅ Ready | `pip install chromadb langchain-community` |
| Qdrant | ✅ Ready | `pip install qdrant-client` |
| FAISS | ✅ Ready | `pip install faiss-cpu` |
| PostgreSQL | ✅ Ready | `pip install psycopg2-binary` |
| Cassandra | ✅ Ready | `pip install cassandra-driver` |

## 🚨 Error Messages and Solutions

### "SentenceTransformers library not available"
```bash
pip install sentence-transformers
```

### "ChromaDB connector not available"
```bash
pip install chromadb langchain-community
```

### "No active database connections"
- Check configuration targets match available connectors
- Ensure database dependencies are installed
- Use `eless test --test-db <database>` to diagnose

## 🔄 Migration and Resumption

The system supports resumable processing:
1. **File Tracking**: SHA-256 content hashing for reliable identification
2. **State Management**: Processing status tracking (PENDING → CHUNKED → EMBEDDED → LOADED)
3. **Resume Support**: `--resume` flag to continue interrupted processing

## 🧪 Testing

Test the installation:
```bash
# Create a test document
echo "This is a test document for ELESS processing." > test.txt

# Test with basic processing (will show missing dependencies)
eless test

# Check available parsers and databases
eless config-info
```

## 📈 Performance

### Streaming Processing for Low-End Systems
ELESS now supports memory-efficient streaming for large text files, avoiding loading entire files into RAM.

Key capabilities:
- Stream files in small buffers with smart breakpoints to preserve sentence/paragraph boundaries
- Automatic decision to use streaming based on estimated memory usage vs. configured limits
- Adaptive batch processing for embeddings based on real-time memory pressure

Configuration (defaults shown):
```yaml
resource_limits:
  max_memory_mb: 512                # Memory budget used to decide streaming
  enable_adaptive_batching: true

streaming:
  buffer_size: 8192                 # 8KB read buffer
  max_file_size_mb: 100             # Hard cap for processing
  auto_streaming_threshold: 0.7     # Stream if estimate exceeds 70% of budget
```

Usage:
```bash
# Standard processing automatically streams when beneficial
eless process /path/to/documents

# Demo script to visualize streaming behavior
python demo_streaming.py
```

Notes:
- Streaming currently applies to plain text/markdown. Other formats are parsed normally first, then chunked.
- You can tune buffer_size and batch sizes to fit very low-end machines.

- **Batch Processing**: Configurable batch sizes for optimal throughput
- **Memory Management**: Streaming processing for large datasets
- **Parallel Processing**: Multi-database concurrent loading
- **Performance Monitoring**: Execution time tracking for all operations

The enhanced ELESS system provides a robust, observable, and flexible RAG data processing pipeline with comprehensive database support and professional-grade logging.