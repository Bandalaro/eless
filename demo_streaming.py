#!/usr/bin/env python3
"""
Demonstration script for ELESS streaming processing capabilities.
This script shows how the streaming processor handles large files efficiently.
"""

import logging
from pathlib import Path
import tempfile
import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.core.default_config import get_default_config
from src.processing.streaming_processor import StreamingDocumentProcessor, BatchProcessor
from src.core.resource_monitor import ResourceMonitor


def create_test_file(size_mb: float, content_pattern: str = "This is test content. ") -> Path:
    """
    Create a test file of specified size.
    
    Args:
        size_mb: Size of file to create in MB
        content_pattern: Pattern to repeat to fill the file
        
    Returns:
        Path to the created test file
    """
    target_size = int(size_mb * 1024 * 1024)  # Convert to bytes
    
    test_file = Path(tempfile.mktemp(suffix='.txt'))
    
    with open(test_file, 'w') as f:
        written = 0
        while written < target_size:
            f.write(content_pattern)
            written += len(content_pattern)
    
    actual_size = test_file.stat().st_size / (1024 * 1024)
    print(f"Created test file: {test_file} ({actual_size:.1f}MB)")
    return test_file


def dummy_chunker(raw_text: str, file_hash: str, chunk_size: int, chunk_overlap: int) -> list:
    """
    Simple dummy chunker for demonstration.
    
    Args:
        raw_text: Text to chunk
        file_hash: File identifier
        chunk_size: Size of each chunk
        chunk_overlap: Overlap between chunks
        
    Returns:
        List of chunk dictionaries
    """
    chunks = []
    start = 0
    chunk_index = 0
    
    while start < len(raw_text):
        end = min(start + chunk_size, len(raw_text))
        chunk_text = raw_text[start:end]
        
        chunks.append({
            'text': chunk_text,
            'metadata': {
                'file_id': file_hash,
                'chunk_index': chunk_index,
                'chunk_id': f"{file_hash[:8]}-{chunk_index:04d}",
                'start_pos': start,
                'end_pos': end
            }
        })
        
        chunk_index += 1
        start = end - chunk_overlap
        
        if start >= end:
            break
    
    return chunks


def demonstrate_streaming():
    """Demonstrate streaming processing with different file sizes."""
    
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger('StreamingDemo')
    
    print("=== ELESS Streaming Processing Demonstration ===\n")
    
    # Get default configuration
    config = get_default_config()
    
    # Override some settings for demonstration
    config['streaming']['max_file_size_mb'] = 50  # Allow files up to 50MB
    config['resource_limits']['max_memory_mb'] = 128  # Simulate low-end system
    config['chunking']['chunk_size'] = 500
    config['chunking']['chunk_overlap'] = 50
    
    # Initialize components
    resource_monitor = ResourceMonitor(config)
    streaming_processor = StreamingDocumentProcessor(config)
    batch_processor = BatchProcessor(config, resource_monitor)
    
    print(f"System Configuration:")
    print(f"  Max memory limit: {config['resource_limits']['max_memory_mb']}MB")
    print(f"  Chunk size: {config['chunking']['chunk_size']} chars")
    print(f"  Streaming buffer: {config['streaming']['buffer_size']} bytes")
    print()
    
    # Test different file sizes
    test_sizes = [1, 5, 10, 25]  # MB
    
    for size_mb in test_sizes:
        print(f"--- Testing {size_mb}MB file ---")
        
        # Create test file
        test_file = create_test_file(size_mb)
        file_hash = f"test_{size_mb}mb"
        
        try:
            # Check if streaming should be used
            should_stream = streaming_processor.should_use_streaming(test_file)
            estimated_memory = streaming_processor.estimate_memory_usage(test_file)
            
            print(f"Estimated memory usage: {estimated_memory:.1f}MB")
            print(f"Should use streaming: {should_stream}")
            
            if should_stream:
                print("Processing with streaming...")
                chunk_count = 0
                
                # Process using streaming
                for chunk in streaming_processor.process_large_text_file(
                    file_path=test_file,
                    file_hash=file_hash,
                    chunker_func=dummy_chunker
                ):
                    chunk_count += 1
                    if chunk_count % 100 == 0:
                        print(f"  Processed {chunk_count} chunks...")
                
                print(f"  Total chunks processed: {chunk_count}")
            else:
                print("Processing with regular method (small file)...")
                # Traditional processing
                with open(test_file, 'r') as f:
                    content = f.read()
                
                chunks = dummy_chunker(content, file_hash, 
                                     config['chunking']['chunk_size'],
                                     config['chunking']['chunk_overlap'])
                print(f"  Total chunks created: {len(chunks)}")
            
            # Show current memory usage
            memory_info = resource_monitor.get_memory_info()
            print(f"  Current memory usage: {memory_info['percent']:.1f}%")
            print()
            
        except Exception as e:
            logger.error(f"Error processing {size_mb}MB file: {e}")
        
        finally:
            # Clean up test file
            if test_file.exists():
                test_file.unlink()
    
    print("=== Batch Processing Demonstration ===\n")
    
    # Demonstrate adaptive batch processing
    test_items = list(range(1000))  # 1000 items to process
    
    def dummy_processor(batch):
        """Dummy processor that just returns the batch size."""
        return [f"processed_{item}" for item in batch]
    
    print(f"Processing {len(test_items)} items with adaptive batching...")
    
    processed_count = 0
    for batch_result in batch_processor.process_in_batches(test_items, dummy_processor):
        processed_count += len(batch_result)
        if processed_count % 200 == 0:
            print(f"  Processed {processed_count} items...")
    
    print(f"  Total items processed: {processed_count}")
    
    # Show memory pressure adaptation
    pressure_level = resource_monitor.get_memory_pressure_level()
    optimal_batch_size = batch_processor.get_optimal_batch_size(100)
    print(f"  Current memory pressure: {pressure_level}")
    print(f"  Optimal batch size for 100 items: {optimal_batch_size}")
    
    print("\n=== Demonstration Complete ===")


if __name__ == "__main__":
    demonstrate_streaming()