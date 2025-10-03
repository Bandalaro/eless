# ELESS Storage Configuration Guide

## 📁 Storage Location Control

ELESS provides comprehensive control over where your embedded data, cache files, logs, and database files are stored. This is especially important for users with limited disk space or specific directory requirements.

## 🎯 Quick Storage Setup

### Option 1: Use a Single Data Directory (Recommended)
```bash
# All ELESS data goes under /path/to/my/data
eless --data-dir /path/to/my/data process documents/

# This creates:
# /path/to/my/data/.eless_cache/     (processed files & vectors)
# /path/to/my/data/.eless_logs/      (log files)
# /path/to/my/data/.eless_chroma/    (ChromaDB database)
# /path/to/my/data/.eless_faiss/     (FAISS index files)
```

### Option 2: Fine-Grained Control
```bash
# Specify each directory individually
eless --cache-dir /fast/ssd/cache \
      --log-dir /var/log/eless \
      process documents/
```

### Option 3: Configuration File
Create a custom config file:
```yaml
# my_config.yaml
cache:
  directory: /path/to/cache
  max_size_mb: 2048  # 2GB limit
  max_files: 50000

logging:
  directory: /path/to/logs

databases:
  connections:
    chroma:
      type: chroma
      path: /path/to/chroma_db
    faiss:
      type: faiss
      index_path: /path/to/faiss/index.faiss
      metadata_path: /path/to/faiss/metadata.json
```

Then use it:
```bash
eless --config my_config.yaml process documents/
```

## 🗄️ What Gets Stored Where

### Cache Directory (`.eless_cache`)
- **Chunked Text Files**: `{file_hash}.chunks.pkl`
- **Vector Embeddings**: `{file_hash}.vectors.npy` 
- **Processing State**: `manifest.json`
- **Access Log**: `access_log.json` (for LRU cache management)

**Size**: Varies by document volume. Expect ~1-5MB per document.

### Log Directory (`.eless_logs`)
- **Main Logs**: `eless.log`
- **Error Logs**: `eless_errors.log`

**Size**: ~10-50MB with rotation enabled.

### Database Directories

#### ChromaDB (`.eless_chroma`)
- Vector database files
- **Size**: ~2-10x the size of your cache directory

#### FAISS (`.eless_faiss`)
- `index.faiss`: Vector index file
- `metadata.json`: Document metadata
- **Size**: Similar to ChromaDB

#### Qdrant/PostgreSQL/Cassandra
- Configurable remote hosts
- No local storage required

## 🔧 Cache Management for Low-End Systems

### Built-in Cache Limits
```yaml
cache:
  max_size_mb: 1024    # 1GB cache limit
  max_files: 10000     # Max 10k cached files
  auto_cleanup: true   # Automatic maintenance
```

### Cache Commands
```bash
# Check cache status
eless cache --stats

# Clean corrupted files
eless cache --cleanup

# Force cleanup old files
eless cache --evict

# Clear entire cache (WARNING: destructive)
eless cache --clear
```

### Smart Cache Features
- **LRU Eviction**: Automatically removes least recently used files
- **Corruption Detection**: Finds and removes corrupted cache files
- **Size Monitoring**: Tracks cache growth and warns when limits approached

## 💾 Storage Requirements by System Type

### Minimal System (2GB RAM, 32GB storage)
```bash
eless --data-dir /home/user/eless_data \
      process documents/ \
      --chunk-size 300 \
      --batch-size 8
```
**Config:**
```yaml
cache:
  max_size_mb: 512     # 512MB cache
  max_files: 5000
resource_limits:
  memory_warning_percent: 70
  memory_critical_percent: 85
embedding:
  batch_size: 8        # Small batches
```

### Standard System (8GB RAM, 256GB storage)
```bash
eless --data-dir /data/eless process documents/
```
**Config (default):**
```yaml
cache:
  max_size_mb: 1024    # 1GB cache
  max_files: 10000
resource_limits:
  memory_warning_percent: 80
  memory_critical_percent: 90
embedding:
  batch_size: 32
```

### High-End System (16GB+ RAM, 1TB+ storage)
```bash
eless --data-dir /data/eless process documents/
```
**Config:**
```yaml
cache:
  max_size_mb: 4096    # 4GB cache
  max_files: 50000
resource_limits:
  memory_warning_percent: 85
  memory_critical_percent: 95
embedding:
  batch_size: 64       # Larger batches
```

## 🔄 Moving Storage Locations

### Migrating Existing Data
```bash
# 1. Stop any running ELESS processes

# 2. Copy existing data
cp -r .eless_cache /new/location/eless_cache
cp -r .eless_logs /new/location/eless_logs
cp -r .eless_chroma /new/location/eless_chroma

# 3. Use new locations
eless --data-dir /new/location process documents/
```

### Backup Important Data
```bash
# Backup cache and manifest (contains all processing state)
tar -czf eless_backup.tar.gz .eless_cache .eless_logs

# Restore
tar -xzf eless_backup.tar.gz -C /new/location/
```

## ⚡ Performance Tips

### SSD vs HDD Placement
- **Cache on SSD**: Fastest access to processed data
- **Logs on HDD**: Less critical, sequential writes
- **Databases on SSD**: Better query performance

### Network Storage Considerations
- Avoid network drives for cache (frequent small file access)
- Network databases (Qdrant, PostgreSQL) are fine
- Logs can go on network storage

### Example Multi-Drive Setup
```bash
eless --cache-dir /fast/ssd/eless_cache \
      --log-dir /storage/hdd/eless_logs \
      --databases chroma qdrant \
      process documents/
```

## 🛡️ Security and Permissions

### Directory Permissions
```bash
# Create secure storage directory
mkdir -p /secure/eless_data
chmod 700 /secure/eless_data

# Use with restricted permissions
eless --data-dir /secure/eless_data process sensitive_docs/
```

### Cleanup Sensitive Data
```bash
# Securely clear cache containing sensitive embeddings
eless cache --clear

# Or remove specific cached files
rm /path/to/cache/{file_hash}.*
```

## 📊 Monitoring Storage Usage

### Built-in Monitoring
```bash
# Check all storage locations
eless cache --stats
eless logs --days 0  # Show current log size

# System resource monitoring
eless --data-dir /my/data process documents/
# Automatically monitors memory and adjusts batch sizes
```

### External Monitoring
```bash
# Monitor cache directory size
du -sh /path/to/eless_cache

# Monitor database growth
du -sh /path/to/eless_chroma

# Watch real-time cache changes
watch -n 5 'du -sh /path/to/cache && ls /path/to/cache | wc -l'
```

This comprehensive storage system ensures that ELESS can adapt to any system configuration, from minimal embedded devices to high-end servers, while providing users complete control over where their data is stored.