import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional, Dict, Any
import sys


class ElessLogger:
    """
    Centralized logging configuration for ELESS pipeline.
    Provides structured logging with file output, console output, and rotating file handlers.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.log_dir = Path(config.get("logging", {}).get("directory", ".eless_logs"))
        self.log_level = config.get("logging", {}).get("level", "INFO").upper()
        self.max_file_size = (
            config.get("logging", {}).get("max_file_size_mb", 10) * 1024 * 1024
        )
        self.backup_count = config.get("logging", {}).get("backup_count", 5)
        self.enable_console = config.get("logging", {}).get("enable_console", True)

        # Create log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self._setup_logging()

    def _setup_logging(self):
        """Configure logging handlers and formatters"""
        # Create main log file path
        main_log_file = self.log_dir / "eless.log"
        error_log_file = self.log_dir / "eless_errors.log"

        # Create formatter
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)-20s | %(funcName)-15s:%(lineno)-3d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # Create console formatter (simpler)
        console_formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s",
            datefmt="%H:%M:%S",
        )

        # Get root logger and set level
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.log_level, logging.INFO))

        # Clear any existing handlers
        root_logger.handlers = []

        # Create and configure file handler (all logs)
        file_handler = logging.handlers.RotatingFileHandler(
            main_log_file,
            maxBytes=self.max_file_size,
            backupCount=self.backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        # Create and configure error file handler (errors and warnings only)
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=self.max_file_size,
            backupCount=self.backup_count,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.WARNING)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)

        # Create and configure console handler
        if self.enable_console and "pytest" not in sys.modules:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, self.log_level, logging.INFO))
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)

        # Log the initialization
        logger = logging.getLogger("ELESS.Logger")
        logger.info(
            f"Logging initialized - Level: {self.log_level}, Directory: {self.log_dir}"
        )
        logger.info(f"Log files: {main_log_file.name}, {error_log_file.name}")

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger with the specified name"""
        return logging.getLogger(name)

    def set_level(self, level: str):
        """Dynamically change logging level"""
        new_level = getattr(logging, level.upper(), logging.INFO)
        logging.getLogger().setLevel(new_level)

        # Update console handler level if it exists
        for handler in logging.getLogger().handlers:
            if (
                isinstance(handler, logging.StreamHandler)
                and handler.stream == sys.stdout
            ):
                handler.setLevel(new_level)
                break

        logger = logging.getLogger("ELESS.Logger")
        logger.info(f"Logging level changed to: {level.upper()}")

    def get_log_files(self):
        """Return list of current log files"""
        return list(self.log_dir.glob("*.log*"))

    def cleanup_old_logs(self, days_old: int = 30):
        """Clean up log files older than specified days"""
        import time

        current_time = time.time()
        cutoff_time = current_time - (days_old * 24 * 60 * 60)

        removed_files = []
        for log_file in self.log_dir.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff_time:
                try:
                    log_file.unlink()
                    removed_files.append(str(log_file))
                except OSError as e:
                    logger = logging.getLogger("ELESS.Logger")
                    logger.warning(f"Could not remove old log file {log_file}: {e}")

        if removed_files:
            logger = logging.getLogger("ELESS.Logger")
            logger.info(f"Cleaned up {len(removed_files)} old log files")

        return removed_files


def setup_logging(config: Dict[str, Any]) -> ElessLogger:
    """
    Setup logging for the entire ELESS application.
    Should be called early in the application startup.
    """
    return ElessLogger(config)


# Context manager for temporary log level changes
class TemporaryLogLevel:
    """Context manager to temporarily change log level"""

    def __init__(self, level: str, logger_name: Optional[str] = None):
        self.new_level = getattr(logging, level.upper(), logging.INFO)
        self.logger = (
            logging.getLogger(logger_name) if logger_name else logging.getLogger()
        )
        self.old_level = None

    def __enter__(self):
        self.old_level = self.logger.level
        self.logger.setLevel(self.new_level)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.setLevel(self.old_level)


# Performance logging decorator
def log_performance(logger_name: Optional[str] = None):
    """Decorator to log function execution time"""
    import time
    from functools import wraps

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(logger_name or f"ELESS.{func.__module__}")
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                logger.debug(f"{func.__name__} executed in {execution_time:.3f}s")
                return result
            except Exception as e:
                execution_time = time.time() - start_time
                logger.error(f"{func.__name__} failed after {execution_time:.3f}s: {e}")
                raise

        return wrapper

    return decorator
