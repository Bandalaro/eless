# ELESS Examples and Usage Guide

**Version**: 1.0.0  
**Audience**: Users, Integrators, Application Developers

---

## Table of Contents

1. [Quick Start Examples](#quick-start-examples)
2. [CLI Usage Examples](#cli-usage-examples)
3. [Python API Examples](#python-api-examples)
4. [Configuration Examples](#configuration-examples)
5. [Integration Examples](#integration-examples)
6. [Advanced Usage](#advanced-usage)
7. [Common Patterns](#common-patterns)
8. [Real-World Scenarios](#real-world-scenarios)

---

## Quick Start Examples

### Example 1: Process Documents (Simplest)

```bash
# Process a directory with auto-configuration
eless go /path/to/documents
```

This uses automatic configuration and the lightest database (FAISS).

### Example 2: Process with Specific Database

```bash
# Process with ChromaDB
eless process /docs --databases chroma
```

### Example 3: Interactive Processing

```bash
# Interactive mode with prompts
eless process -i
```

The CLI will ask you:
- Which directory to process?
- Which databases to use?
- What chunk size?
- And more...

---

## CLI Usage Examples

### Basic Processing

#### Process a Single File

```bash
eless process /path/to/document.pdf
```

#### Process a Directory

```bash
eless process /path/to/documents/
```

#### Process with Custom Settings

```bash
eless process /docs \
  --databases chroma,faiss \
  --chunk-size 1000 \
  --log-level DEBUG
```

### Database Selection

#### Single Database

```bash
# Use ChromaDB only
eless process /docs --databases chroma

# Use FAISS only
eless process /docs --databases faiss
```

#### Multiple Databases

```bash
# Store in multiple databases simultaneously
eless process /docs --databases chroma,qdrant,faiss
```

### Configuration

#### Use Custom Config File

```bash
eless process /docs --config my_config.yaml
```

#### Override Config Settings

```bash
# Override cache directory
eless process /docs --cache-dir /custom/cache

# Override log directory
eless process /docs --log-dir /var/log/eless

# Override data directory (parent for cache/logs)
eless process /docs --data-dir /data/eless
```

### Resume Processing

#### Resume After Interruption

```bash
# Start processing
eless process /large/dataset

# If interrupted (Ctrl+C or error), resume with:
eless process /large/dataset --resume
```

### Status and Monitoring

#### Check Processing Status

```bash
# Show all files
eless status --all

# Show only loaded files
eless status --status LOADED

# Show files with errors
eless status --status ERROR
```

#### Monitor Resources

```bash
# Real-time resource monitoring
eless monitor
```

#### System Information

```bash
# View system information
eless sysinfo
```

### Testing and Diagnostics

#### Health Check

```bash
# Comprehensive health check
eless health
```

Output:
```
ELESS Health Check
============================================================

Python version     : ✓ Python 3.10.12 ✓
Core dependencies  : ✓ All core dependencies installed ✓
Embedding model    : ✓ sentence-transformers available ✓
ChromaDB          : ✓ chromadb installed ✓
Qdrant            : ✓ qdrant installed ✓
FAISS             : ✓ faiss installed ✓
Disk space        : ✓ 25.3GB available ✓
Memory            : ✓ 8.2GB / 16.0GB available ✓
Configuration     : ✓ Configuration valid ✓

✓ Overall health: Good
  ELESS is ready to use!
```

#### Test System Components

```bash
# Test all components
eless test

# Test specific database
eless test --test-db chroma
```

#### Diagnose Issues

```bash
# Run doctor for diagnostics
eless doctor
```

### Configuration Management

#### List Templates

```bash
eless template list
```

Output:
```
Available configuration templates:

  lightweight    - Low resource usage (FAISS, small model)
  balanced       - Good performance (ChromaDB, standard model)
  production     - High performance (multi-DB, large model)
  development    - Testing setup (debug logs, multi-DB)
```

#### Create Config from Template

```bash
# Create config from template
eless template create balanced --output my_config.yaml

# Use the created config
eless process /docs --config my_config.yaml
```

#### Run Configuration Wizard

```bash
# Interactive setup
eless init
```

### Demo and Tutorial

#### Try Demo Data

```bash
# Process sample documents
eless demo
```

#### Interactive Tutorial

```bash
# Learn ELESS interactively
eless tutorial
```

---

## Python API Examples

### Example 1: Basic Pipeline

```python
import yaml
from eless import ElessPipeline

# Load configuration
with open("config.yaml") as f:
    config = yaml.safe_load(f)

# Create pipeline
pipeline = ElessPipeline(config)

# Process documents
pipeline.run_process("/path/to/documents")
```

### Example 2: Custom Configuration

```python
from eless import ElessPipeline, ConfigLoader

# Load config with overrides
config_loader = ConfigLoader()
config = config_loader.get_final_config(
    logging={"level": "DEBUG"},
    chunking={"chunk_size": 1000},
    databases={"targets": ["chroma", "faiss"]}
)

# Create and run pipeline
pipeline = ElessPipeline(config)
pipeline.run_process("/documents")
```

### Example 3: State Management

```python
from eless import StateManager, FileStatus, ConfigLoader

# Setup
config_loader = ConfigLoader()
config = config_loader.get_final_config()
state_manager = StateManager(config)

# Get all files
all_files = state_manager.get_all_files()
for file_info in all_files:
    print(f"{file_info['path']}: {file_info['status']}")

# Get files by status
loaded_files = state_manager.get_all_files(status=FileStatus.LOADED)
print(f"Loaded: {len(loaded_files)} files")

# Get specific file info
file_info = state_manager.get_file_info("file_hash_here")
if file_info:
    print(f"Status: {file_info['status']}")
    print(f"Path: {file_info['path']}")
```

### Example 4: Resume Processing

```python
from eless import ElessPipeline

# Create pipeline
pipeline = ElessPipeline(config)

# Resume from cached vectors
pipeline.run_resume()
```

### Example 5: Component Access

```python
from eless import ElessPipeline

pipeline = ElessPipeline(config)

# Access state manager
state_manager = pipeline.state_manager
files = state_manager.get_all_files()

# Access embedder
embedder = pipeline.embedder
texts = ["Hello world", "ELESS example"]
vectors = embedder.encode(texts)
print(f"Vector shape: {vectors.shape}")

# Access database loader
db_loader = pipeline.db_loader
# Query databases via their connectors
```

### Example 6: File Scanner

```python
from eless.processing.file_scanner import FileScanner

scanner = FileScanner(config)

# Scan directory
for file_data in scanner.scan_input("/documents"):
    print(f"Found: {file_data['path']}")
    print(f"Hash: {file_data['hash'][:8]}...")
    print(f"Extension: {file_data['extension']}")
```

### Example 7: Direct Embedding

```python
from eless.embedding.model_loader import ModelLoader
from eless.embedding.embedder import Embedder
from eless.core.state_manager import StateManager
from eless.core.archiver import Archiver

# Setup
state_manager = StateManager(config)
archiver = Archiver(config)
model_loader = ModelLoader(config)

# Create embedder
embedder = Embedder(config, state_manager, archiver, model_loader)

# Encode texts
texts = [
    "ELESS is a RAG pipeline",
    "Vector databases store embeddings",
    "Document processing made easy"
]

vectors = embedder.encode(texts)
print(f"Generated {len(vectors)} vectors")
print(f"Dimension: {len(vectors[0])}")
```

### Example 8: Custom Processing Loop

```python
from eless import ElessPipeline
from eless.core.state_manager import FileStatus

pipeline = ElessPipeline(config)

# Custom processing with progress tracking
scanner = pipeline.scanner
dispatcher = pipeline.dispatcher
embedder = pipeline.embedder

file_count = 0
chunk_count = 0

for file_data in scanner.scan_input("/documents"):
    file_count += 1
    file_hash = file_data['hash']
    
    # Check if already processed
    status = pipeline.state_manager.get_status(file_hash)
    if status == FileStatus.LOADED:
        print(f"Skipping {file_data['path']} (already loaded)")
        continue
    
    # Process file
    chunks = list(dispatcher.process_document(file_data))
    chunk_count += len(chunks)
    
    # Embed
    embedded_chunks = embedder.embed_file_chunks(file_hash, chunks)
    
    print(f"Processed: {file_data['path']} ({len(chunks)} chunks)")

print(f"Total: {file_count} files, {chunk_count} chunks")
```

---

## Configuration Examples

### Example 1: Minimal Configuration

```yaml
# minimal_config.yaml
cache:
  directory: ".eless_cache"

chunking:
  chunk_size: 512

embedding:
  model_name: "all-MiniLM-L6-v2"

databases:
  targets:
    - faiss
  connections:
    faiss:
      index_path: ".eless_data/faiss_index"
```

### Example 2: Production Configuration

```yaml
# production_config.yaml
cache:
  directory: "/var/eless/cache"
  manifest_file: "manifest.json"

chunking:
  chunk_size: 512
  chunk_overlap: 50
  method: "recursive"

embedding:
  model_name: "sentence-transformers/all-mpnet-base-v2"
  batch_size: 64
  device: "cuda"  # Use GPU if available
  cache_dir: "/var/eless/models"

databases:
  targets:
    - chroma
    - qdrant
    - faiss
  connections:
    chroma:
      host: "chroma.example.com"
      port: 8000
      collection_name: "production_docs"
    qdrant:
      host: "qdrant.example.com"
      port: 6333
      collection_name: "production_docs"
    faiss:
      index_path: "/var/eless/faiss/index"

logging:
  level: "INFO"
  directory: "/var/log/eless"
  max_file_size_mb: 50
  backup_count: 10
  enable_console: true

processing:
  parallel_workers: 4
  batch_size: 100
```

### Example 3: Development Configuration

```yaml
# dev_config.yaml
cache:
  directory: ".dev_cache"
  manifest_file: "dev_manifest.json"

chunking:
  chunk_size: 256  # Smaller for faster testing

embedding:
  model_name: "all-MiniLM-L6-v2"  # Fast model
  batch_size: 16
  device: "cpu"

databases:
  targets:
    - chroma  # Easy setup
  connections:
    chroma:
      host: "localhost"
      port: 8000
      collection_name: "dev_test"

logging:
  level: "DEBUG"  # Verbose logging
  directory: ".dev_logs"
  enable_console: true
```

### Example 4: Multi-Database Configuration

```yaml
# multi_db_config.yaml
databases:
  targets:
    - chroma
    - qdrant
    - faiss
    - postgresql
  
  connections:
    chroma:
      host: "localhost"
      port: 8000
      collection_name: "eless_vectors"
    
    qdrant:
      host: "localhost"
      port: 6333
      collection_name: "eless_vectors"
      # Optional: API key for remote Qdrant
      # api_key: "your_api_key"
    
    faiss:
      index_path: ".eless_data/faiss_index"
      index_type: "IndexFlatIP"  # Inner product
    
    postgresql:
      host: "localhost"
      port: 5432
      database: "vectordb"
      user: "eless_user"
      password: "secure_password"
      table_name: "embeddings"
```

---

## Integration Examples

### Example 1: FastAPI Integration

```python
from fastapi import FastAPI, UploadFile
from eless import ElessPipeline
import yaml
import tempfile
import os

app = FastAPI()

# Load ELESS configuration
with open("config.yaml") as f:
    config = yaml.safe_load(f)

pipeline = ElessPipeline(config)

@app.post("/upload")
async def upload_document(file: UploadFile):
    """Upload and process a document."""
    # Save uploaded file
    with tempfile.NamedTemporaryFile(delete=False, suffix=file.filename) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # Process with ELESS
        pipeline.run_process(tmp_path)
        return {"status": "success", "filename": file.filename}
    finally:
        # Cleanup
        os.unlink(tmp_path)

@app.get("/status")
def get_status():
    """Get processing status."""
    files = pipeline.state_manager.get_all_files()
    return {
        "total": len(files),
        "loaded": len([f for f in files if f['status'] == 'LOADED']),
        "pending": len([f for f in files if f['status'] == 'PENDING']),
        "error": len([f for f in files if f['status'] == 'ERROR'])
    }
```

### Example 2: Flask Integration

```python
from flask import Flask, request, jsonify
from eless import ElessPipeline, ConfigLoader
from pathlib import Path

app = Flask(__name__)

# Initialize ELESS
config_loader = ConfigLoader()
config = config_loader.get_final_config()
pipeline = ElessPipeline(config)

@app.route('/process', methods=['POST'])
def process_documents():
    """Process documents from a directory."""
    data = request.json
    source_path = data.get('source_path')
    
    if not source_path or not Path(source_path).exists():
        return jsonify({"error": "Invalid source path"}), 400
    
    try:
        pipeline.run_process(source_path)
        return jsonify({"status": "completed"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/files', methods=['GET'])
def list_files():
    """List all processed files."""
    status_filter = request.args.get('status')
    files = pipeline.state_manager.get_all_files(status=status_filter)
    
    return jsonify({
        "count": len(files),
        "files": [
            {
                "path": f['path'],
                "status": f['status'],
                "hash": f['hash'][:8]
            }
            for f in files
        ]
    })

if __name__ == '__main__':
    app.run(debug=True)
```

### Example 3: Streamlit Dashboard

```python
import streamlit as st
from eless import ElessPipeline, ConfigLoader, FileStatus
import pandas as pd

st.title("ELESS Document Processing Dashboard")

# Initialize ELESS
@st.cache_resource
def get_pipeline():
    config_loader = ConfigLoader()
    config = config_loader.get_final_config()
    return ElessPipeline(config)

pipeline = get_pipeline()

# Sidebar
st.sidebar.header("Actions")

# Upload and process
uploaded_file = st.sidebar.file_uploader("Upload Document")
if uploaded_file and st.sidebar.button("Process"):
    # Save and process file
    with open(f"/tmp/{uploaded_file.name}", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    with st.spinner("Processing..."):
        pipeline.run_process(f"/tmp/{uploaded_file.name}")
    
    st.success("Processing complete!")

# Main area - Status dashboard
st.header("Processing Status")

files = pipeline.state_manager.get_all_files()

# Statistics
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Files", len(files))
col2.metric("Loaded", len([f for f in files if f['status'] == FileStatus.LOADED]))
col3.metric("Processing", len([f for f in files if f['status'] in [FileStatus.CHUNKED, FileStatus.EMBEDDED]]))
col4.metric("Errors", len([f for f in files if f['status'] == FileStatus.ERROR]))

# Files table
if files:
    df = pd.DataFrame([
        {
            "File": f['path'],
            "Status": f['status'],
            "Hash": f['hash'][:8],
            "Timestamp": f['timestamp']
        }
        for f in files
    ])
    
    st.dataframe(df, use_container_width=True)
```

### Example 4: Django Integration

```python
# views.py
from django.http import JsonResponse
from django.views import View
from eless import ElessPipeline, ConfigLoader
import yaml

# Initialize ELESS once
config_loader = ConfigLoader()
config = config_loader.get_final_config()
pipeline = ElessPipeline(config)

class ProcessDocumentsView(View):
    def post(self, request):
        source_path = request.POST.get('source_path')
        
        try:
            pipeline.run_process(source_path)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

class StatusView(View):
    def get(self, request):
        files = pipeline.state_manager.get_all_files()
        
        return JsonResponse({
            'total': len(files),
            'files': [
                {
                    'path': f['path'],
                    'status': f['status'],
                    'timestamp': f['timestamp']
                }
                for f in files
            ]
        })
```

---

## Advanced Usage

### Example 1: Batch Processing with Progress

```python
from eless import ElessPipeline
from pathlib import Path
from tqdm import tqdm

pipeline = ElessPipeline(config)

# Get all PDF files
pdf_files = list(Path("/documents").rglob("*.pdf"))

print(f"Found {len(pdf_files)} PDF files")

# Process with progress bar
for pdf_path in tqdm(pdf_files, desc="Processing PDFs"):
    try:
        pipeline.run_process(str(pdf_path))
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")

print("Batch processing complete!")
```

### Example 2: Parallel Processing Multiple Directories

```python
from eless import ElessPipeline
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

def process_directory(dir_path, config):
    """Process a single directory."""
    pipeline = ElessPipeline(config)
    pipeline.run_process(str(dir_path))
    return dir_path

# List of directories to process
directories = [
    "/data/docs1",
    "/data/docs2",
    "/data/docs3",
    "/data/docs4"
]

# Process in parallel
with ProcessPoolExecutor(max_workers=4) as executor:
    futures = [
        executor.submit(process_directory, dir_path, config)
        for dir_path in directories
    ]
    
    for future in futures:
        completed_dir = future.result()
        print(f"Completed: {completed_dir}")
```

### Example 3: Custom Error Handling

```python
from eless import ElessPipeline, FileStatus
import logging

logger = logging.getLogger(__name__)

pipeline = ElessPipeline(config)

def process_with_retry(source_path, max_retries=3):
    """Process with automatic retry on failure."""
    for attempt in range(max_retries):
        try:
            pipeline.run_process(source_path)
            return True
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                logger.error(f"Failed after {max_retries} attempts")
                return False
    return False

# Use it
success = process_with_retry("/documents")
if success:
    print("Processing completed successfully")
else:
    print("Processing failed after retries")
```

### Example 4: Custom Metadata Enrichment

```python
from eless import ElessPipeline
from eless.core.state_manager import FileStatus
from pathlib import Path
import os

pipeline = ElessPipeline(config)

# Process files
pipeline.run_process("/documents")

# Enrich metadata
files = pipeline.state_manager.get_all_files(status=FileStatus.LOADED)

for file_info in files:
    file_hash = file_info['hash']
    file_path = Path(file_info['path'])
    
    # Add custom metadata
    custom_metadata = {
        'file_size': os.path.getsize(file_path),
        'owner': file_path.owner(),
        'department': 'Engineering',  # Custom field
        'project': 'Project X'        # Custom field
    }
    
    pipeline.state_manager.add_or_update_file(
        file_hash,
        FileStatus.LOADED,
        metadata=custom_metadata
    )

print("Metadata enrichment complete")
```

---

## Common Patterns

### Pattern 1: Check Before Process

```python
from eless import ElessPipeline, FileStatus

pipeline = ElessPipeline(config)

def safe_process(file_path):
    """Only process if not already loaded."""
    # Get file hash
    import hashlib
    with open(file_path, 'rb') as f:
        file_hash = hashlib.sha256(f.read()).hexdigest()
    
    # Check status
    status = pipeline.state_manager.get_status(file_hash)
    
    if status == FileStatus.LOADED:
        print(f"Skipping {file_path} (already loaded)")
        return
    
    # Process
    pipeline.run_process(file_path)
```

### Pattern 2: Incremental Updates

```python
from eless import ElessPipeline
from pathlib import Path
import time

pipeline = ElessPipeline(config)
watch_dir = Path("/documents")
processed = set()

print("Watching for new files...")

while True:
    # Find new files
    current_files = set(watch_dir.rglob("*.pdf"))
    new_files = current_files - processed
    
    # Process new files
    for file_path in new_files:
        print(f"Processing new file: {file_path}")
        pipeline.run_process(str(file_path))
        processed.add(file_path)
    
    # Wait before next check
    time.sleep(60)
```

### Pattern 3: Cleanup Old Cache

```python
from eless import StateManager, ConfigLoader, FileStatus
from pathlib import Path
import time

config_loader = ConfigLoader()
config = config_loader.get_final_config()
state_manager = StateManager(config)
cache_dir = Path(config['cache']['directory'])

# Remove cache for files older than 30 days
cutoff_time = time.time() - (30 * 24 * 60 * 60)

for file_info in state_manager.get_all_files():
    file_time = file_info.get('timestamp', 0)
    
    if file_time < cutoff_time:
        file_hash = file_info['hash']
        
        # Remove cache files
        chunks_file = cache_dir / f"{file_hash}.chunks.pkl"
        vectors_file = cache_dir / f"{file_hash}.vectors.npy"
        
        if chunks_file.exists():
            chunks_file.unlink()
        if vectors_file.exists():
            vectors_file.unlink()
        
        print(f"Removed cache for {file_info['path']}")
```

---

## Real-World Scenarios

### Scenario 1: Company Knowledge Base

```bash
# Initial setup
eless init

# Configure for production
# Edit config to use ChromaDB + Qdrant

# Process company documents
eless process /company/docs \
  --databases chroma,qdrant \
  --chunk-size 512

# Monitor progress
eless status --all

# Verify everything loaded
eless test --test-db chroma
eless test --test-db qdrant
```

### Scenario 2: Research Paper Archive

```python
from eless import ElessPipeline, ConfigLoader

# Custom config for research papers
config_loader = ConfigLoader()
config = config_loader.get_final_config(
    chunking={
        "chunk_size": 1024,  # Larger chunks for academic content
        "chunk_overlap": 100
    },
    embedding={
        "model_name": "allenai/scibert_scivocab_uncased"  # Scientific model
    },
    databases={
        "targets": ["qdrant"]  # Scalable for large archives
    }
)

pipeline = ElessPipeline(config)

# Process papers by year
for year in range(2020, 2025):
    papers_dir = f"/research/papers/{year}"
    print(f"Processing papers from {year}...")
    pipeline.run_process(papers_dir)

print("Research archive processing complete!")
```

### Scenario 3: Legal Document Processing

```yaml
# legal_config.yaml
chunking:
  chunk_size: 2048  # Larger for legal documents
  chunk_overlap: 200  # More overlap for context
  method: "recursive"

embedding:
  model_name: "nlpaueb/legal-bert-base-uncased"
  batch_size: 16  # Conservative for large chunks

databases:
  targets:
    - postgresql  # SQL for compliance
  connections:
    postgresql:
      host: "legal-db.company.com"
      database: "legal_docs"
      table_name: "document_embeddings"

logging:
  level: "INFO"
  directory: "/var/log/legal_processing"
  # Comprehensive logging for audit trail
```

### Scenario 4: Multi-Tenant SaaS

```python
from eless import ElessPipeline, ConfigLoader
from pathlib import Path

class TenantProcessor:
    """Process documents for multiple tenants."""
    
    def __init__(self):
        self.pipelines = {}
    
    def get_tenant_pipeline(self, tenant_id):
        """Get or create pipeline for tenant."""
        if tenant_id not in self.pipelines:
            # Tenant-specific configuration
            config_loader = ConfigLoader()
            config = config_loader.get_final_config(
                cache={"directory": f".cache/{tenant_id}"},
                databases={
                    "targets": ["chroma"],
                    "connections": {
                        "chroma": {
                            "collection_name": f"tenant_{tenant_id}"
                        }
                    }
                }
            )
            
            self.pipelines[tenant_id] = ElessPipeline(config)
        
        return self.pipelines[tenant_id]
    
    def process_tenant_documents(self, tenant_id, docs_path):
        """Process documents for a specific tenant."""
        pipeline = self.get_tenant_pipeline(tenant_id)
        pipeline.run_process(docs_path)

# Usage
processor = TenantProcessor()

# Process for different tenants
processor.process_tenant_documents("acme_corp", "/uploads/acme_corp/")
processor.process_tenant_documents("widgets_inc", "/uploads/widgets_inc/")
```

---

**More examples at**: [GitHub Repository](https://github.com/Bandalaro/eless)

---

**Guide Version**: 1.0  
**Last Updated**: 2025-10-25
