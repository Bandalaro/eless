# Error Handling and Prevention

This document describes all the errors that ELESS catches and prevents, along with their handling strategies.

## Table of Contents

- [File Access Errors](#file-access-errors)
- [Configuration Errors](#configuration-errors)
- [Model Loading Errors](#model-loading-errors)
- [Database Connection Errors](#database-connection-errors)
- [Processing Errors](#processing-errors)
- [Resource Management Errors](#resource-management-errors)
- [Cache and State Errors](#cache-and-state-errors)

## File Access Errors

### Permission Denied

**Description**: Occurs when the application lacks permission to read a file.

**Handling Strategy**:
- File status is set to ERROR
- Error is logged with file hash
- Processing continues with other files
- User can fix permissions and re-process

**Test Coverage**: `test_file_access_error`, `test_parallel_processing_errors`

### Invalid File Format

**Description**: Occurs when a file format is not supported or is corrupted.

**Handling Strategy**:
- File status is set to ERROR
- Error is logged at ERROR level
- File is skipped and processing continues
- Supported formats: .txt, .md, .pdf, .docx, .html, .bin

**Test Coverage**: `test_invalid_file_format`

## Configuration Errors

### Invalid YAML Syntax

**Description**: Configuration file contains malformed YAML.

**Handling Strategy**:
- `yaml.YAMLError` is raised
- Application exits with error message
- User must fix YAML syntax before proceeding

**Test Coverage**: `test_config_loader_invalid_yaml`

### Invalid Configuration Values

**Description**: Configuration values are out of valid ranges or incorrect types.

**Handled Validations**:

1. **Chunk Size**
   - Must be integer
   - Must be greater than 0
   - Must be less than or equal to 10000
   - Raises: `ValueError` or `TypeError`

2. **Embedding Batch Size**
   - Must be integer
   - Must be greater than 0
   - Required field (raises `KeyError` if missing)
   - Raises: `ValueError` or `TypeError`

3. **Parallel Processing Workers**
   - Must be integer
   - Must be between 1 and 64
   - Raises: `ValueError` or `TypeError`

4. **Memory Limits**
   - Must be numeric (int or float)
   - Memory warning percent must be between 0 and 100
   - Min memory cannot be negative
   - Raises: `ValueError` or `TypeError`

5. **Cache Configuration**
   - Parent directory must exist
   - Retention days must be greater than 0
   - Raises: `ValueError`

6. **Database Targets**
   - Must be supported type: sqlite, postgresql, chroma, faiss, qdrant, cassandra
   - Raises: `ValueError` for unsupported types

7. **Chunk/Batch Size Relationship**
   - Chunk size must be greater than or equal to batch size
   - Raises: `ValueError`

**Test Coverage**: `test_config_validation_errors`, `test_invalid_*` tests in test_config_validation.py

## Model Loading Errors

### Missing Dependencies

**Description**: Required library (sentence-transformers, torch) is not installed.

**Handling Strategy**:
- `SENTENCE_TRANSFORMERS_AVAILABLE` flag is set to False
- Error logged at ERROR level
- Model returns None
- Default embedding dimension (384) is used
- Application continues but cannot generate embeddings

**Test Coverage**: `test_model_loader_import_error`

### Model Loading Failure

**Description**: Model fails to load from Hugging Face or local path.

**Handling Strategy**:
- Exception caught and logged at CRITICAL level
- Returns None instead of raising
- Allows graceful degradation
- User notified to check model name and dependencies

**Test Coverage**: `test_model_loader_import_error`

## Database Connection Errors

### Qdrant Connection Failure

**Description**: Cannot connect to Qdrant server.

**Handling Strategy**:
- `ConnectionError` is raised during connect()
- Error logged with host and port information
- Application can continue with other databases if configured
- User notified to check if Qdrant server is running

**Test Coverage**: `test_qdrant_connection_error`, `test_qdrant_server_not_running`

### PostgreSQL Connection Failure

**Description**: Cannot connect to PostgreSQL server.

**Handling Strategy**:
- `ConnectionError` is raised during connect()
- Error logged with connection details
- Application can continue with other databases if configured
- User notified to check PostgreSQL credentials and server status

**Test Coverage**: `test_postgresql_connection_error`, `test_postgresql_server_not_running`

### Database Not Initialized

**Description**: Attempting operations before database connection is established.

**Handling Strategy**:
- `ConnectionError` raised when attempting upsert without client
- Clear error message indicating database not connected
- User must call connect() before operations

**Test Coverage**: `test_qdrant_upsert_batch_no_client`, `test_postgresql_upsert_batch_no_connection`

### Database Initialization Failure

**Description**: Database connector initialization fails during pipeline setup.

**Handling Strategy**:
- Exception caught during `_initialize_connectors()`
- Error logged at ERROR level
- Pipeline continues with available databases
- If no databases available, user is notified

**Test Coverage**: `test_database_error_recovery`

### Missing Database Dependencies

**Description**: Required database client library is not installed.

**Handling Strategy**:
- Availability flag (e.g., `QDRANT_AVAILABLE`) set to False
- Warning logged about missing library
- Connector class set to None
- Application continues without that database
- No connectors added for unavailable databases

**Test Coverage**: `test_database_loader_import_error`

## Processing Errors

### Interrupted Processing

**Description**: Processing is interrupted due to exception during chunking or embedding.

**Handling Strategy**:
- Exception caught internally
- File status set to ERROR
- Error recorded in state manager
- User can reset status and retry
- Processing continues with remaining files

**Test Coverage**: `test_interrupted_processing`

### Memory Error

**Description**: Out of memory during processing of large files.

**Handling Strategy**:
- `MemoryError` caught during processing
- File status set to ERROR
- Streaming processor activated for large files
- User can reduce batch size or chunk size in config
- Status can be reset for retry with adjusted settings

**Test Coverage**: `test_memory_error_recovery`

### Database Error During Recovery

**Description**: Database operation fails during resume/recovery process.

**Handling Strategy**:
- Error logged at ERROR level
- Pipeline attempts retry on next run
- Files with EMBEDDED status can be reloaded
- State preserved for recovery

**Test Coverage**: `test_database_error_recovery`

## Resource Management Errors

### Resource Limit Violations

**Description**: File size or memory usage exceeds configured limits.

**Handling Strategy**:
- Warning logged when approaching limits
- Streaming processor activated automatically
- Adaptive batching reduces batch size
- Processing continues with adjustments
- File still successfully processed

**Test Coverage**: `test_resource_limit_handling`

### Parallel Processing Errors

**Description**: Errors occur during parallel file processing.

**Handling Strategy**:
- Each file processed independently
- Error in one file doesn't affect others
- Individual file statuses tracked
- Failed files marked as ERROR
- Successful files marked as LOADED
- Summary shows which files failed

**Test Coverage**: `test_parallel_processing_errors`

## Cache and State Errors

### Corrupted Cache

**Description**: Cached data is corrupted or unreadable.

**Handling Strategy**:
- Corruption detected during cache loading
- File status reset to allow re-processing
- New cache generated from source file
- Old corrupted cache overwritten
- Validation ensures new cache is valid

**Test Coverage**: `test_corrupted_cache_recovery`

### Invalid Status Update

**Description**: Attempt to set file status to invalid value.

**Handling Strategy**:
- `TypeError` raised if status is not a string
- `ValueError` raised if status is not a valid FileStatus
- Valid statuses: PENDING, SCANNED, CHUNKED, EMBEDDED, LOADED, ERROR
- Error logged with details
- Operation aborted, state remains unchanged

**Test Coverage**: `test_state_manager_invalid_status_update`

### Manifest File Corruption

**Description**: State manifest JSON file is corrupted.

**Handling Strategy**:
- `json.JSONDecodeError` caught during load
- Warning logged about corrupted manifest
- New empty manifest initialized
- Previous state lost but application continues
- Backup manifest (.bak) preserved when possible

**Test Coverage**: Implicit in StateManager initialization

## Error Recovery Mechanisms

### Automatic Recovery

1. **Streaming Fallback**: Automatically switches to streaming for large files
2. **Adaptive Batching**: Reduces batch size when memory pressure detected
3. **Graceful Degradation**: Continues with available resources/databases
4. **State Preservation**: All states saved for recovery

### Manual Recovery

1. **Status Reset**: `reset_file_status(hash)` allows re-processing
2. **Resume Processing**: `run_resume()` continues from last checkpoint
3. **Configuration Adjustment**: Modify settings and retry
4. **Selective Reprocessing**: Target specific failed files

## Best Practices

### For Users

1. **Check Health First**: Run `eless doctor` before processing
2. **Start Small**: Test with small files before batch processing
3. **Monitor Logs**: Check logs for warnings and errors
4. **Configure Appropriately**: Set chunk and batch sizes based on resources
5. **Use Resume**: After fixing errors, use `--resume` to continue

### For Developers

1. **Validate Early**: Check inputs at entry points
2. **Fail Gracefully**: Return None or default values instead of crashing
3. **Log Appropriately**: ERROR for failures, WARNING for issues, INFO for status
4. **Preserve State**: Save state before and after critical operations
5. **Test Error Paths**: Ensure all error handlers are tested

## Error Code Reference

### Exit Codes

- 0: Success
- 1: General error
- 2: Configuration error
- 3: Database connection error
- 4: File processing error
- 5: Resource limit error

### Status Codes

- PENDING: File known, not processed
- SCANNED: File hash generated
- CHUNKED: Text extracted and chunked
- EMBEDDED: Vectors generated
- LOADED: Vectors in database
- ERROR: Processing failed

## Logging Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: Normal operation status
- **WARNING**: Issues that don't prevent operation
- **ERROR**: Errors that affect specific operations
- **CRITICAL**: System-level failures

## Related Documentation

- [Developer Guide](DEVELOPER_GUIDE.md) - Implementation details
- [API Reference](API_REFERENCE.md) - Function signatures and parameters
- [Quick Start](QUICK_START.md) - Getting started guide
