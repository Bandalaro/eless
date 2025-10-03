"""
Default configuration for ELESS.
This file contains the default configuration as a Python dictionary to ensure
it's always available regardless of how the package is installed.
"""

DEFAULT_CONFIG = {
    # The cache directory for storing processed files and their states.
    'cache': {
        'directory': '.eless_cache',
        'manifest_file': 'manifest.json',
        'max_size_mb': 1024,  # Maximum cache size in MB (1GB)
        'max_files': 10000,   # Maximum number of cache files
        'auto_cleanup': True  # Enable automatic cache maintenance
    },

    # Logging configuration
    'logging': {
        'directory': '.eless_logs',
        'level': 'INFO',
        'enable_console': True,
        'max_file_size_mb': 10,
        'backup_count': 5
    },

    # Settings for the low-resource embedding model.
    'embedding': {
        'model_name': 'sentence-transformers/all-MiniLM-L6-v2',
        'dimensions': 384,
        'device': 'cpu',
        'batch_size': 32
    },

    # Resource monitoring and limits for low-end systems
    'resource_limits': {
        'memory_warning_percent': 80,   # Start reducing batch size
        'memory_critical_percent': 90,  # Aggressive batch size reduction
        'cpu_high_percent': 85,         # High CPU usage threshold
        'min_memory_mb': 256,           # Minimum available memory required
        'max_memory_mb': 512,           # Maximum memory to use (for streaming decisions)
        'enable_adaptive_batching': True # Enable automatic batch size adjustment
    },
    
    # Streaming processing settings for memory efficiency
    'streaming': {
        'buffer_size': 8192,            # Buffer size for streaming (8KB)
        'max_file_size_mb': 100,        # Maximum file size for processing (100MB)
        'enable_memory_mapping': True,   # Use memory mapping for large files
        'auto_streaming_threshold': 0.7  # Use streaming if estimated memory > 70% of available
    },

    # Parameters for splitting documents into smaller chunks.
    'chunking': {
        'chunk_size': 500,
        'chunk_overlap': 50
    },

    # Parallel processing configuration
    'parallel_processing': {
        # Worker configuration
        'max_workers': None,                    # Auto-detect if None
        'mode': 'auto',                        # 'thread', 'process', 'auto'
        
        # Enable/disable parallel processing for different stages
        'enable_parallel_files': True,         # Process multiple files in parallel
        'enable_parallel_chunks': True,        # Process chunks in parallel
        'enable_parallel_embedding': True,     # Generate embeddings in parallel
        'enable_parallel_database': True,      # Write to multiple databases in parallel
        
        # Batch sizes for parallel processing
        'chunk_batch_size': 100,               # Chunks per parallel batch
        'file_batch_size': 10,                 # Files per parallel batch
        
        # Resource management
        'resource_monitoring': True,           # Enable resource-aware processing
        'adaptive_workers': True,              # Dynamically adjust worker count
        'memory_threshold_percent': 80,        # Reduce workers above this memory usage
        'cpu_threshold_percent': 85,           # Reduce workers above this CPU usage
        
        # Performance tuning
        'queue_size': 100,                     # Task queue size
        'timeout_seconds': 300,                # Task timeout
        'enable_progress_tracking': True       # Track and display progress
    },

    # Database configurations.
    'databases': {
        'batch_size': 64,
        'default': {
            'drop_existing': False
        },

        # List of databases to use.
        'targets': [
            'chroma'
        ],

        # Individual database connection settings.
        'connections': {
            # ChromaDB settings
            'chroma': {
                'type': 'chroma',
                'path': '.eless_chroma'
            },

            # FAISS settings
            'faiss': {
                'type': 'faiss',
                'index_path': '.eless_faiss/index.faiss',
                'metadata_path': '.eless_faiss/metadata.json'
            },

            # Qdrant settings
            'qdrant': {
                'type': 'qdrant',
                'host': 'localhost',
                'port': 6333,
                'api_key': None,
                'collection_name': 'eless_embeddings',
                'timeout': 30
            },

            # PostgreSQL/CockroachDB settings
            'postgresql': {
                'type': 'postgresql',
                'host': 'localhost',
                'port': 5432,
                'user': 'your_user',
                'password': 'your_password',
                'database': 'your_db',
                'table_name': 'eless_embeddings',
                'connection_timeout': 30
            },

            # Cassandra settings
            'cassandra': {
                'type': 'cassandra',
                'hosts': ['localhost'],
                'port': 9042,
                'keyspace': 'eless_keyspace',
                'table_name': 'eless_embeddings',
                'replication_factor': 1
            }
        }
    }
}


def get_default_config():
    """Return a copy of the default configuration."""
    import copy
    return copy.deepcopy(DEFAULT_CONFIG)