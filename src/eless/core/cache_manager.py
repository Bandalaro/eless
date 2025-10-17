import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import OrderedDict
import shutil

logger = logging.getLogger("ELESS.CacheManager")


class SmartCacheManager:
    """
    Advanced cache manager for low-end systems with size limits, LRU eviction,
    and corruption recovery.
    """

    def __init__(self, config: Dict):
        self.cache_dir = Path(config["cache"]["directory"])
        self.max_size_mb = config["cache"].get("max_size_mb", 1024)  # Default 1GB
        self.max_files = config["cache"].get("max_files", 10000)  # Default 10k files

        # Access tracking for LRU
        self.access_log_path = self.cache_dir / "access_log.json"
        self.access_times: OrderedDict[str, float] = OrderedDict()

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Load existing access log
        self._load_access_log()

        logger.info(
            f"SmartCacheManager initialized: max_size={self.max_size_mb}MB, max_files={self.max_files}"
        )

    def _load_access_log(self):
        """Load access times from disk for LRU tracking."""
        if self.access_log_path.exists():
            try:
                with open(self.access_log_path, "r") as f:
                    access_data = json.load(f)
                    # Convert to OrderedDict and sort by access time
                    sorted_items = sorted(access_data.items(), key=lambda x: x[1])
                    self.access_times = OrderedDict(sorted_items)
                logger.debug(f"Loaded {len(self.access_times)} access time entries")
            except (json.JSONDecodeError, OSError) as e:
                logger.warning(f"Failed to load access log: {e}. Starting fresh.")
                self.access_times = OrderedDict()

    def _save_access_log(self):
        """Save access times to disk."""
        try:
            with open(self.access_log_path, "w") as f:
                json.dump(dict(self.access_times), f)
        except OSError as e:
            logger.error(f"Failed to save access log: {e}")

    def record_access(self, file_hash: str):
        """Record file access for LRU tracking."""
        current_time = time.time()
        # Remove if already exists (to move to end)
        if file_hash in self.access_times:
            del self.access_times[file_hash]
        # Add to end (most recent)
        self.access_times[file_hash] = current_time

    def get_cache_size_mb(self) -> float:
        """Calculate current cache size in MB."""
        total_size = 0
        try:
            for file_path in self.cache_dir.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except OSError as e:
            logger.warning(f"Error calculating cache size: {e}")
        return total_size / (1024 * 1024)

    def get_cache_file_count(self) -> int:
        """Count cache files."""
        try:
            return len(list(self.cache_dir.rglob("*")))
        except OSError as e:
            logger.warning(f"Error counting cache files: {e}")
            return 0

    def should_evict(self) -> bool:
        """Check if cache eviction is needed."""
        current_size = self.get_cache_size_mb()
        current_files = self.get_cache_file_count()

        size_exceeded = current_size > self.max_size_mb
        files_exceeded = current_files > self.max_files

        if size_exceeded or files_exceeded:
            logger.info(
                f"Cache limits exceeded - Size: {current_size:.1f}MB/{self.max_size_mb}MB, "
                f"Files: {current_files}/{self.max_files}"
            )
            return True
        return False

    def evict_lru_items(self, target_size_mb: Optional[float] = None) -> List[str]:
        """
        Evict least recently used items to free space.

        Args:
            target_size_mb: Target size after eviction (default: 80% of max_size_mb)

        Returns:
            List of evicted file hashes
        """
        if target_size_mb is None:
            target_size_mb = self.max_size_mb * 0.8  # Free up to 80% of limit

        evicted = []
        current_size = self.get_cache_size_mb()

        if current_size <= target_size_mb:
            return evicted

        logger.info(
            f"Starting LRU eviction: {current_size:.1f}MB -> {target_size_mb:.1f}MB"
        )

        # Sort by access time (oldest first)
        for file_hash, access_time in list(self.access_times.items()):
            if current_size <= target_size_mb:
                break

            # Remove cache files for this hash
            files_removed = self._remove_cached_files(file_hash)
            if files_removed:
                evicted.append(file_hash)
                del self.access_times[file_hash]
                # Recalculate size after removal
                current_size = self.get_cache_size_mb()
                logger.debug(f"Evicted {file_hash[:8]}, new size: {current_size:.1f}MB")

        self._save_access_log()
        logger.info(
            f"LRU eviction complete: evicted {len(evicted)} items, new size: {current_size:.1f}MB"
        )
        return evicted

    def _remove_cached_files(self, file_hash: str) -> bool:
        """Remove all cached files for a given hash."""
        removed = False
        patterns = [f"{file_hash}.chunks.pkl", f"{file_hash}.vectors.npy"]

        for pattern in patterns:
            file_path = self.cache_dir / pattern
            if file_path.exists():
                try:
                    file_path.unlink()
                    removed = True
                    logger.debug(f"Removed cache file: {file_path.name}")
                except OSError as e:
                    logger.error(f"Failed to remove {file_path}: {e}")

        return removed

    def cleanup_corrupted_files(self) -> List[str]:
        """Remove corrupted cache files and return their hashes."""
        corrupted = []

        # Check pickle files
        for pickle_file in self.cache_dir.glob("*.chunks.pkl"):
            try:
                import pickle

                with open(pickle_file, "rb") as f:
                    pickle.load(f)
            except (pickle.PickleError, EOFError, OSError) as e:
                logger.warning(f"Corrupted pickle file detected: {pickle_file.name}")
                file_hash = pickle_file.stem.replace(".chunks", "")
                corrupted.append(file_hash)
                self._remove_cached_files(file_hash)

        # Check numpy files
        for npy_file in self.cache_dir.glob("*.vectors.npy"):
            try:
                import numpy as np

                np.load(npy_file)
            except (OSError, ValueError) as e:
                logger.warning(f"Corrupted numpy file detected: {npy_file.name}")
                file_hash = npy_file.stem.replace(".vectors", "")
                if file_hash not in corrupted:
                    corrupted.append(file_hash)
                self._remove_cached_files(file_hash)

        if corrupted:
            logger.info(f"Cleaned up {len(corrupted)} corrupted cache entries")

        return corrupted

    def get_cache_stats(self) -> Dict:
        """Get comprehensive cache statistics."""
        return {
            "size_mb": self.get_cache_size_mb(),
            "max_size_mb": self.max_size_mb,
            "file_count": self.get_cache_file_count(),
            "max_files": self.max_files,
            "tracked_accesses": len(self.access_times),
            "utilization_percent": (self.get_cache_size_mb() / self.max_size_mb) * 100,
        }

    def clear_cache(self) -> bool:
        """Clear all cache files and access log."""
        try:
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            self.access_times.clear()
            logger.info("Cache cleared successfully")
            return True
        except OSError as e:
            logger.error(f"Failed to clear cache: {e}")
            return False

    def auto_maintain(self):
        """Perform automatic cache maintenance."""
        logger.debug("Starting automatic cache maintenance")

        # 1. Clean up corrupted files
        corrupted = self.cleanup_corrupted_files()

        # 2. Evict old files if needed
        if self.should_evict():
            evicted = self.evict_lru_items()
            logger.info(
                f"Auto-maintenance complete: cleaned {len(corrupted)} corrupted, "
                f"evicted {len(evicted)} LRU items"
            )
        else:
            logger.debug("No cache eviction needed")

        # 3. Update access log
        self._save_access_log()
