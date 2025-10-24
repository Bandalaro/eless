# ELESS Error Documentation

This document lists possible errors that users may encounter when using ELESS, along with their causes and solutions.

## Installation Errors

### Error: "No module named 'sentence_transformers'"

**Cause:** The sentence-transformers library is not installed.

**Solution:** Install the embeddings extra:
```bash
pip install -e ".[embeddings]"
```

### Error: "ChromaDB connector not available"

**Cause:** ChromaDB or langchain-community is not installed.

**Solution:** Install the databases extra:
```bash
pip install -e ".[databases]"
```

### Error: "PDF parser not available"

**Cause:** pypdf is not installed.

**Solution:** Install the parsers extra:
```bash
pip install -e ".[parsers]"
```

## Configuration Errors

### Error: "Configuration file not found"

**Cause:** The specified config file does not exist.

**Solution:** Ensure the config file path is correct or use the default config.

### Error: "Invalid configuration value"

**Cause:** A configuration value is invalid (e.g., negative batch size).

**Solution:** Check the configuration schema in API_REFERENCE.md and fix the values.

## Processing Errors

### Error: "File not found"

**Cause:** The specified file or directory does not exist.

**Solution:** Verify the path and ensure the file/directory exists.

### Error: "Failed to parse file"

**Cause:** The file format is not supported or corrupted.

**Solution:** Check if the file type is supported. For PDFs, ensure pypdf is installed.

### Error: "Out of memory"

**Cause:** Insufficient memory for the batch size or model.

**Solution:** Reduce batch_size in config or enable adaptive batching.

### Error: "Database connection failed"

**Cause:** Database is not running or config is wrong.

**Solution:** Check database settings and ensure the database is accessible.

## Runtime Errors

### Error: "Model not loaded"

**Cause:** Embedding model failed to load.

**Solution:** Ensure sentence-transformers is installed and the model name is correct.

### Error: "Unknown database type"

**Cause:** Database type not supported or dependencies missing.

**Solution:** Install the required database extra or use a supported database.

### Error: "Processing interrupted"

**Cause:** Process was stopped or crashed.

**Solution:** Use --resume to continue from the last checkpoint.

## CLI Errors

### Error: "Command not found"

**Cause:** ELESS not installed or not in PATH.

**Solution:** Ensure ELESS is installed and the virtual environment is activated.

### Error: "Invalid option"

**Cause:** Incorrect CLI option.

**Solution:** Check the CLI reference in QUICK_START.md.

## General Troubleshooting

- Check logs in .eless_logs/ for detailed error messages.
- Run `eless doctor` if available for system checks.
- Ensure all optional dependencies are installed for full functionality.
- For more help, see the troubleshooting section in QUICK_START.md.