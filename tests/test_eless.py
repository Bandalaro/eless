#!/usr/bin/env python3
"""
Full test script for ELESS package.
Tests all major functions: processing, embedding, database storage, search, status checks.
Uses sample documents and logs progress.
"""

import logging
import os
import sys
from pathlib import Path
import time
import yaml

# Import ELESS components
from eless import ElessPipeline, StateManager, ConfigLoader
from eless.core.default_config import get_default_config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_eless.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("ELESS_TEST")

def print_progress(message: str):
    """Print progress with timestamp."""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] PROGRESS: {message}")
    logger.info(message)

def create_sample_documents(test_dir: Path):
    """Create sample documents for testing."""
    print_progress("Creating sample documents...")

    # Copy existing sample
    sample_src = Path("tests/fixtures/sample.txt")
    if sample_src.exists():
        (test_dir / "sample.txt").write_text(sample_src.read_text())
    else:
        (test_dir / "sample.txt").write_text("This is a sample text document for testing ELESS.\nIt contains multiple lines.\n")

    # Create a markdown file
    (test_dir / "readme.md").write_text("""# Sample Markdown

This is a sample markdown document.

## Features

- Lists
- **Bold text**
- Code blocks

```python
print("Hello, world!")
```
""")

    # Create a simple HTML file
    (test_dir / "index.html").write_text("""<!DOCTYPE html>
<html>
<head><title>Sample HTML</title></head>
<body>
<h1>Sample HTML Document</h1>
<p>This is a sample HTML document for testing.</p>
<ul>
<li>Item 1</li>
<li>Item 2</li>
</ul>
</body>
</html>""")

    print_progress(f"Created sample documents in {test_dir}")

def main():
    print_progress("Starting ELESS full test...")

    # Create test directory
    test_dir = Path("test_documents")
    test_dir.mkdir(exist_ok=True)

    # Create sample documents
    create_sample_documents(test_dir)

    # Load configuration
    print_progress("Loading configuration...")
    config = get_default_config()

    # Override for testing: use in-memory or local paths
    config["cache"]["directory"] = "test_cache"
    config["logging"]["directory"] = "test_logs"
    config["embedding"]["model_path"] = "./models"  # Fix for model_path
    config["databases"]["targets"] = ["chroma"]  # Use only Chroma for simplicity
    config["databases"]["connections"]["chroma"]["path"] = "test_chroma"

    # Save config for reference
    with open("test_config.yaml", "w") as f:
        yaml.dump(config, f)

    print_progress("Configuration loaded and saved.")

    # Initialize pipeline
    print_progress("Initializing ELESS pipeline...")
    pipeline = ElessPipeline(config)
    print_progress("Pipeline initialized.")

    # Process documents
    print_progress("Starting document processing...")
    start_time = time.time()
    pipeline.run_process(str(test_dir))
    end_time = time.time()
    print_progress(f"Processing completed in {end_time - start_time:.2f} seconds.")

    # Check status
    print_progress("Checking processing status...")
    state_manager = StateManager(config)
    all_files = state_manager.get_all_files()
    print(f"Total files processed: {len(all_files)}")
    for file_info in all_files:
        print(f"  - {file_info['path']}: {file_info['status']}")

    # Test search (if databases are loaded)
    print_progress("Testing search functionality...")
    try:
        db_loader = pipeline.db_loader
        if db_loader and db_loader.active_connectors:
            query = "sample text"
            results = db_loader.search(query, limit=5)
            if results:
                print(f"Search results for '{query}': {len(results)} found")
                for i, result in enumerate(results):
                    if isinstance(result, dict):
                        score = result['score'] if 'score' in result else 0
                        content = result['content'] if 'content' in result else ''
                        print(f"  {i+1}. Score: {score:.4f}, Content: {content[:100]}...")
                    else:
                        print(f"  {i+1}. Invalid result format")
            else:
                print(f"No search results for '{query}'")
        else:
            print_progress("No active database connectors for search.")
    except Exception as e:
        logger.error(f"Search test failed: {e}")

    # Test resume functionality
    print_progress("Testing resume functionality...")
    try:
        pipeline.run_resume()
        print_progress("Resume test completed.")
    except Exception as e:
        logger.error(f"Resume test failed: {e}")

    # Test status command
    print_progress("Testing status checks...")
    all_hashes = state_manager.get_all_hashes()
    print(f"Total hashes tracked: {len(all_hashes)}")
    for hash_id in all_hashes[:3]:  # Show first 3
        status = state_manager.get_status(hash_id)
        info = state_manager.get_file_info(hash_id)
        print(f"  Hash {hash_id[:12]}...: Status: {status}, Path: {info.get('path', 'N/A')}")

    # Cleanup
    print_progress("Cleaning up test files...")
    import shutil
    shutil.rmtree(test_dir, ignore_errors=True)
    shutil.rmtree("test_cache", ignore_errors=True)
    shutil.rmtree("test_logs", ignore_errors=True)
    shutil.rmtree("test_chroma", ignore_errors=True)
    os.remove("test_config.yaml")

    print_progress("ELESS full test completed successfully!")

if __name__ == "__main__":
    main()