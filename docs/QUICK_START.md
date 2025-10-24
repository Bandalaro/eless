# ELESS Quick Start Guide

Get started with ELESS in 5 minutes!

## What is ELESS?

ELESS (Evolving Low-resource Embedding and Storage System) is a powerful yet lightweight RAG (Retrieval-Augmented Generation) data processing pipeline that:

- Processes various document types (PDF, DOCX, TXT, MD, HTML)
- Generates embeddings using state-of-the-art models
- Stores vectors in multiple databases (ChromaDB, Qdrant, FAISS, PostgreSQL, Cassandra)
- Supports resumable processing for large datasets
- Provides comprehensive logging and monitoring
- Works efficiently on low-resource systems

---

## Installation

### Step 1: Install ELESS

```bash
# Clone the repository
git clone https://github.com/Bandalaro/eless.git
cd eless

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install with core dependencies
pip install -e .

# Or install with all features
pip install -e ".[full]"
```

### Step 2: Install Optional Dependencies

Choose the features you need:

```bash
# For embedding generation
pip install -e ".[embeddings]"

# For vector databases
pip install -e ".[databases]"

# For document parsing
pip install -e ".[parsers]"

# For everything
pip install -e ".[full]"
```

---

## 5-Minute Tutorial

### 1. Verify Installation

```bash
eless --version
```

### 2. Check Configuration

```bash
eless config-info
```

This shows your current configuration, available parsers, and database connectors.

### 3. Create Test Documents

```bash
# Create a test directory
mkdir test_docs

# Create sample documents
echo "This is a test document about artificial intelligence and machine learning." > test_docs/sample1.txt
echo "ELESS is a powerful RAG data processing pipeline for embeddings." > test_docs/sample2.txt
echo "Vector databases enable semantic search and similarity matching." > test_docs/sample3.txt
```

### 4. Process Documents

```bash
# Process with default settings (ChromaDB)
eless process test_docs

# Process with specific database
eless process test_docs --databases chroma

# Process with multiple databases
eless process test_docs --databases chroma --databases qdrant
```

### 5. Check Status

```bash
# View processing status
eless status

# View all processed files
eless status --all
```

### 6. View Logs

```bash
# View logs
eless logs

# Clean old logs
eless logs --days 7
```

---

## Common Use Cases

### Use Case 1: Processing Local Documents

```bash
# Process all documents in a directory
eless process /path/to/documents

# Process with custom chunk size
eless process /path/to/documents --chunk-size 1000

# Process with debug logging
eless --log-level DEBUG process /path/to/documents
```

### Use Case 2: Multiple Databases

```bash
# Store in multiple databases for redundancy
eless process documents/ \
  --databases chroma \
  --databases qdrant \
  --databases faiss
```

### Use Case 3: Large Dataset Processing

```bash
# Process large dataset with resumable support
eless process large_dataset/

# If interrupted, resume processing
eless process large_dataset/ --resume
```

### Use Case 4: Custom Configuration

Create `my_config.yaml`:

```yaml
logging:
  level: INFO
  directory: ./logs

embedding:
  model_name: all-MiniLM-L6-v2
  batch_size: 32

databases:
  targets:
    - chroma
  connections:
    chroma:
      type: chroma
      path: ./my_vectors
```

Use it:

```bash
eless process documents/ --config my_config.yaml
```

---

## Configuration Guide

### Default Configuration Location

ELESS uses `config/default_config.yaml` by default.

### Key Configuration Sections

#### 1. Logging

```yaml
logging:
  directory: .eless_logs    # Log file location
  level: INFO               # DEBUG, INFO, WARNING, ERROR
  enable_console: true      # Show logs in console
```

#### 2. Embedding

```yaml
embedding:
  model_name: all-MiniLM-L6-v2  # Embedding model
  device: cpu                    # cpu or cuda
  batch_size: 32                 # Batch size for processing
```

#### 3. Chunking

```yaml
chunking:
  chunk_size: 500    # Characters per chunk
  overlap: 50        # Overlap between chunks
  strategy: semantic # Chunking strategy
```

#### 4. Databases

```yaml
databases:
  targets:
    - chroma         # Active database
  connections:
    chroma:
      type: chroma
      path: .eless_chroma
      collection_name: eless_vectors
```

#### 5. Resource Limits

```yaml
resource_limits:
  max_memory_mb: 512              # Memory budget
  enable_adaptive_batching: true  # Adjust batch size automatically
```

---

## Troubleshooting

### Problem: "No module named 'sentence_transformers'"

**Solution:**
```bash
pip install sentence-transformers
```

### Problem: "ChromaDB connector not available"

**Solution:**
```bash
pip install chromadb langchain-community
```

### Problem: "Failed to parse PDF file"

**Solution:**
```bash
pip install pypdf  # or PyPDF2
```

### Problem: "Out of memory error"

**Solution:** Reduce batch size and enable streaming:

```yaml
embedding:
  batch_size: 8

resource_limits:
  max_memory_mb: 256

streaming:
  auto_streaming_threshold: 0.5
```

### Problem: "Processing is slow"

**Solution:** Increase batch size and workers:

```yaml
embedding:
  batch_size: 64

parallel:
  enable: true
  max_workers: 4
```

---

## CLI Command Reference

### Main Commands

```bash
# Process documents
eless process <path> [OPTIONS]

# Check status
eless status [OPTIONS]

# View configuration
eless config-info

# Test system
eless test [OPTIONS]

# Manage logs
eless logs [OPTIONS]
```

### Common Options

```bash
--databases, -db <name>    # Select database (repeatable)
--config <path>            # Custom config file
--resume                   # Resume interrupted processing
--chunk-size <size>        # Override chunk size
--batch-size <size>        # Override batch size
--log-level <level>        # Set log level (DEBUG, INFO, WARNING, ERROR)
--log-dir <path>           # Custom log directory
```

### Examples

```bash
# Process with ChromaDB
eless process docs/ --databases chroma

# Process with custom config
eless process docs/ --config my_config.yaml

# Process with debug logging
eless --log-level DEBUG process docs/

# Resume interrupted processing
eless process docs/ --resume

# Check specific file status
eless status abc123def

# Clean old logs
eless logs --days 30
```

---

## Performance Tips

### For Low-End Systems

```yaml
# Minimal resource usage
resource_limits:
  max_memory_mb: 256
  enable_adaptive_batching: true

embedding:
  batch_size: 8

streaming:
  auto_streaming_threshold: 0.5
```

```bash
eless process docs/ --batch-size 8
```

### For High-End Systems

```yaml
# Maximum performance
resource_limits:
  max_memory_mb: 4096

embedding:
  batch_size: 128
  device: cuda  # If GPU available

parallel:
  enable: true
  max_workers: 8
```

```bash
eless process docs/ --batch-size 128
```

---

## Next Steps

### 1. Read the Full Documentation

- **README.md** - Complete user guide
- **API_REFERENCE.md** - Detailed API documentation
- **DEVELOPER_GUIDE.md** - For contributors and advanced users

### 2. Explore Advanced Features

- **Streaming Processing** - For large files
- **Parallel Processing** - For faster execution
- **Custom Parsers** - Add support for new file types
- **Custom Databases** - Integrate new vector databases

### 3. Integrate with Your Application

```python
from src.eless_pipeline import ElessPipeline
import yaml

# Load configuration
with open("config/default_config.yaml") as f:
    config = yaml.safe_load(f)

# Create pipeline
pipeline = ElessPipeline(config)

# Process documents
pipeline.run_process("/path/to/documents")

# Check status
files = pipeline.state_manager.get_all_files()
for file in files:
    print(f"{file['path']}: {file['status']}")
```

### 4. Join the Community

- **GitHub Issues:** Report bugs or request features
- **GitHub Discussions:** Ask questions, share ideas
- **Contributing:** See CONTRIBUTING.md

---

## Example Workflows

### Workflow 1: Research Paper Processing

```bash
# Process research papers
eless process papers/ \
  --databases chroma \
  --chunk-size 1000 \
  --log-level INFO

# Check results
eless status --all

# Query your vector database (using your RAG application)
python query_rag.py "machine learning techniques"
```

### Workflow 2: Documentation Indexing

```bash
# Process documentation
eless process docs/ \
  --databases qdrant \
  --databases faiss \
  --chunk-size 500

# Build search index
python build_search.py

# Search documentation
python search.py "how to configure databases"
```

### Workflow 3: Batch Processing

```bash
# Process multiple directories
for dir in dataset1 dataset2 dataset3; do
  eless process "$dir" --databases chroma
done

# Check overall status
eless status --all | grep LOADED
```

---

## Best Practices

### 1. Start Small

Begin with a small dataset to test your configuration:

```bash
eless process sample_docs/ --databases chroma
```

### 2. Monitor Resources

Check resource usage during processing:

```bash
# Run with debug logging to see resource metrics
eless --log-level DEBUG process docs/
```

### 3. Use Resumable Processing

For large datasets, enable resumable processing:

```yaml
cache:
  enable_resume: true
```

```bash
eless process large_dataset/ --resume
```

### 4. Regular Maintenance

Clean old logs and check cache size:

```bash
# Clean logs older than 30 days
eless logs --days 30

# Check cache size
du -sh .eless_cache/
```

### 5. Backup Important Data

Regularly backup your manifest and vectors:

```bash
# Backup manifest
cp .eless_cache/cache_manifest.json backups/

# Backup vector database
cp -r .eless_chroma/ backups/
```

---

## FAQ

### Q: What file types are supported?

**A:** Text (.txt, .md), PDF (.pdf), Word (.docx), HTML (.html), and more with optional dependencies.

### Q: Can I use my own embedding model?

**A:** Yes, configure it in the YAML file:

```yaml
embedding:
  model_name: your-model-name
  model_path: /path/to/model
```

### Q: How do I add a new database?

**A:** See the Developer Guide for adding custom database connectors.

### Q: Is GPU supported?

**A:** Yes, set `device: cuda` in the configuration (requires PyTorch with CUDA).

### Q: Can I process remote files?

**A:** Currently, ELESS processes local files. You can download remote files first.

### Q: How much disk space do I need?

**A:** Plan for ~2-3x the size of your input documents (for cache and vectors).

### Q: Can I run multiple instances?

**A:** Use separate cache directories for each instance:

```bash
eless process docs1/ --config config1.yaml
eless process docs2/ --config config2.yaml
```

### Q: How do I update ELESS?

**A:**
```bash
git pull
pip install -e ".[full]"
```

---

## Support

- **Documentation:** Check README.md and docs/ folder
- **Issues:** https://github.com/Bandalaro/eless/issues
- **Discussions:** https://github.com/Bandalaro/eless/discussions

---

## License

MIT License - See LICENSE file for details.

---

**Ready to process your documents? Start with:**

```bash
eless process your_documents/ --databases chroma
```

Happy processing!
