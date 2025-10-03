import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger('ELESS.StateManager')

# Define the file processing states
class FileStatus:
    PENDING = "PENDING"          # File is known but processing hasn't started.
    SCANNED = "SCANNED"          # File hash is generated, ready for processing.
    CHUNKED = "CHUNKED"          # Text extracted and chunked, chunks are saved to disk.
    EMBEDDED = "EMBEDDED"        # Vectors generated, vectors are saved to disk.
    LOADED = "LOADED"            # Vectors successfully loaded into ALL target databases.
    ERROR = "ERROR"              # An error occurred during processing.

class StateManager:
    """
    Manages the manifest.json file, tracking the state of all processed files
    to enable checkpointing and resumption.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initializes the StateManager based on configuration settings.
        Creates the cache directory if it doesn't exist.
        """
        self.config = config
        self.cache_dir = Path(config['cache']['directory'])
        self.manifest_path = self.cache_dir / config['cache']['manifest_file']
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.manifest: Dict[str, Dict[str, Any]] = self._load_or_init_manifest()
        logger.info(f"StateManager initialized. Manifest loaded from {self.manifest_path}")

    def _load_or_init_manifest(self) -> Dict[str, Dict[str, Any]]:
        """Loads the manifest file or creates an empty one if it doesn't exist."""
        if self.manifest_path.exists():
            try:
                with open(self.manifest_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.warning("Manifest file is corrupted. Initializing new manifest.")
                return {}
        return {}

    def _save_manifest(self):
        """Writes the current state of the manifest back to disk."""
        with open(self.manifest_path, 'w') as f:
            json.dump(self.manifest, f, indent=4)

    def get_status(self, file_hash: str) -> str:
        """Returns the current status of a file using its hash."""
        return self.manifest.get(file_hash, {}).get('status', FileStatus.PENDING)

    def is_file_known(self, file_hash: str) -> bool:
        """Checks if a file (hash) is tracked in the manifest."""
        return file_hash in self.manifest

    def add_or_update_file(self, file_hash: str, file_path: str, status: str, metadata: Optional[Dict] = None):
        """Adds a new file or updates the status and metadata of an existing one."""
        try:
            if file_hash not in self.manifest:
                self.manifest[file_hash] = {
                    'path': file_path,
                    'timestamp': self._get_current_timestamp(),
                    'status': FileStatus.PENDING,
                    'metadata': {},
                    'hash': file_hash,  # Store hash consistently
                    'error_count': 0,
                    'last_error': None
                }
            
            # Update status and timestamp
            old_status = self.manifest[file_hash]['status']
            self.manifest[file_hash]['status'] = status
            self.manifest[file_hash]['timestamp'] = self._get_current_timestamp()
            
            # Update path if provided (handle path changes)
            if file_path and file_path != 'N/A':
                self.manifest[file_hash]['path'] = file_path
            
            # Handle error status specially
            if status == FileStatus.ERROR:
                self.manifest[file_hash]['error_count'] += 1
                self.manifest[file_hash]['last_error'] = self._get_current_timestamp()
            elif status in [FileStatus.LOADED, FileStatus.EMBEDDED]:
                # Reset error count on successful status
                self.manifest[file_hash]['error_count'] = 0
                self.manifest[file_hash]['last_error'] = None
            
            if metadata:
                self.manifest[file_hash]['metadata'].update(metadata)
            
            # Save manifest immediately after a state change for robust checkpointing
            self._save_manifest()
            
            if old_status != status:
                logger.debug(f"File {file_hash[:8]} status changed: {old_status} → {status}")
            
        except Exception as e:
            logger.error(f"Failed to update file {file_hash[:8]} status to {status}: {e}")
            raise

    def get_all_loaded_files(self) -> List[str]:
        """Returns a list of file paths that are fully LOADED."""
        return [
            item['path'] for item in self.manifest.values() 
            if item['status'] == FileStatus.LOADED
        ]

    def get_all_hashes(self) -> List[str]:
        """Returns all file hashes currently tracked."""
        return list(self.manifest.keys())

    def _get_current_timestamp(self) -> str:
        """Utility function to get a simple timestamp for tracking."""
        import datetime
        return datetime.datetime.now().isoformat()
    
    def cleanup_orphaned_states(self, archiver) -> int:
        """
        Clean up manifest entries for files that no longer have cached data.
        
        Args:
            archiver: Archiver instance to check for cached files
            
        Returns:
            Number of orphaned entries removed
        """
        orphaned_hashes = []
        
        for file_hash, file_info in self.manifest.items():
            # Check if cache files exist for this hash
            has_chunks = archiver.load_chunks(file_hash) is not None
            has_vectors = archiver.load_vectors(file_hash) is not None
            
            # If no cache data and status indicates it should exist, mark as orphaned
            if file_info['status'] in [FileStatus.CHUNKED, FileStatus.EMBEDDED, FileStatus.LOADED]:
                if not has_chunks and not has_vectors:
                    orphaned_hashes.append(file_hash)
                    logger.warning(f"Orphaned manifest entry found: {file_hash[:8]} - no cache data exists")
        
        # Remove orphaned entries
        for file_hash in orphaned_hashes:
            del self.manifest[file_hash]
        
        if orphaned_hashes:
            self._save_manifest()
            logger.info(f"Cleaned up {len(orphaned_hashes)} orphaned manifest entries")
        
        return len(orphaned_hashes)
    
    def get_error_files(self, min_error_count: int = 3) -> List[str]:
        """
        Get files that have failed multiple times.
        
        Args:
            min_error_count: Minimum error count to consider a file problematic
            
        Returns:
            List of file hashes with high error counts
        """
        error_files = []
        for file_hash, file_info in self.manifest.items():
            if file_info.get('error_count', 0) >= min_error_count:
                error_files.append(file_hash)
        
        return error_files
    
    def reset_file_status(self, file_hash: str) -> bool:
        """
        Reset a file's status to PENDING and clear error counts.
        Useful for retrying failed files.
        
        Args:
            file_hash: Hash of the file to reset
            
        Returns:
            True if file was reset, False if file not found
        """
        if file_hash in self.manifest:
            self.manifest[file_hash]['status'] = FileStatus.PENDING
            self.manifest[file_hash]['error_count'] = 0
            self.manifest[file_hash]['last_error'] = None
            self.manifest[file_hash]['timestamp'] = self._get_current_timestamp()
            self._save_manifest()
            logger.info(f"Reset status for file {file_hash[:8]} to PENDING")
            return True
        return False
    
    def get_file_info(self, file_hash: str) -> Optional[Dict[str, Any]]:
        """
        Get complete information about a file.
        
        Args:
            file_hash: Hash of the file
            
        Returns:
            File information dictionary or None if not found
        """
        return self.manifest.get(file_hash)
    
    def get_files_by_status(self, status: str) -> List[str]:
        """
        Get all file hashes with a specific status.
        
        Args:
            status: Status to filter by (e.g., FileStatus.ERROR)
            
        Returns:
            List of file hashes with the specified status
        """
        return [
            file_hash for file_hash, file_info in self.manifest.items()
            if file_info['status'] == status
        ]
    
    def get_manifest_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the current manifest.
        
        Returns:
            Dictionary with manifest statistics
        """
        status_counts = {}
        total_errors = 0
        files_with_errors = 0
        
        for file_info in self.manifest.values():
            status = file_info['status']
            status_counts[status] = status_counts.get(status, 0) + 1
            
            error_count = file_info.get('error_count', 0)
            total_errors += error_count
            if error_count > 0:
                files_with_errors += 1
        
        return {
            'total_files': len(self.manifest),
            'status_counts': status_counts,
            'total_errors': total_errors,
            'files_with_errors': files_with_errors,
            'manifest_size_kb': len(str(self.manifest)) / 1024
        }
