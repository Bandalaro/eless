import logging
import traceback
from typing import Dict, Any, Optional, Callable, Type, Union
from enum import Enum
from contextlib import contextmanager
import time

logger = logging.getLogger("ELESS.ErrorHandler")


class ErrorSeverity(Enum):
    """Error severity levels for graceful degradation"""

    LOW = "low"  # Non-critical, can continue processing
    MEDIUM = "medium"  # Some functionality lost, but core features work
    HIGH = "high"  # Major functionality compromised
    CRITICAL = "critical"  # Cannot continue processing


class ComponentStatus(Enum):
    """Component availability status"""

    AVAILABLE = "available"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class ElessError(Exception):
    """Base exception class for ELESS-specific errors"""

    def __init__(
        self,
        message: str,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        suggestions: Optional[list] = None,
        component: Optional[str] = None,
    ):
        super().__init__(message)
        self.severity = severity
        self.suggestions = suggestions or []
        self.component = component
        self.timestamp = time.time()


class DependencyError(ElessError):
    """Raised when optional dependencies are missing"""

    def __init__(self, dependency: str, feature: str, install_command: str):
        message = f"Optional dependency '{dependency}' required for {feature} is not available"
        suggestions = [
            f"Install with: {install_command}",
            f"Or disable {feature} in configuration",
        ]
        super().__init__(message, ErrorSeverity.MEDIUM, suggestions, dependency)
        self.dependency = dependency
        self.feature = feature
        self.install_command = install_command


class ConfigurationError(ElessError):
    """Raised when configuration is invalid"""

    def __init__(self, message: str, config_key: str = None, suggestions: list = None):
        super().__init__(message, ErrorSeverity.HIGH, suggestions, "configuration")
        self.config_key = config_key


class ProcessingError(ElessError):
    """Raised when document processing fails"""

    def __init__(self, message: str, file_path: str = None, suggestions: list = None):
        super().__init__(message, ErrorSeverity.MEDIUM, suggestions, "processing")
        self.file_path = file_path


class ErrorHandler:
    """
    Centralized error handling and graceful degradation system for ELESS.
    Provides consistent error reporting, dependency checking, and fallback strategies.
    """

    def __init__(self, config: Dict[str, Any], state_manager=None):
        self.config = config
        self.state_manager = state_manager
        self.component_status: Dict[str, ComponentStatus] = {}
        self.error_counts: Dict[str, int] = {}
        self.failed_components: set = set()

        # Check optional dependencies at startup
        self._check_dependencies()

    def _check_dependencies(self):
        """Check availability of optional dependencies"""
        dependencies = {
            # Embedding models
            "sentence-transformers": {
                "feature": "embedding models",
                "install": "pip install sentence-transformers",
                "test": lambda: __import__("sentence_transformers"),
            },
            "torch": {
                "feature": "PyTorch backend for embeddings",
                "install": "pip install torch",
                "test": lambda: __import__("torch"),
            },
            # Database connectors
            "chromadb": {
                "feature": "ChromaDB vector database",
                "install": "pip install chromadb langchain-community",
                "test": lambda: __import__("chromadb"),
            },
            "qdrant_client": {
                "feature": "Qdrant vector database",
                "install": "pip install qdrant-client",
                "test": lambda: __import__("qdrant_client"),
            },
            "faiss": {
                "feature": "FAISS similarity search",
                "install": "pip install faiss-cpu",
                "test": lambda: __import__("faiss"),
            },
            "psycopg2": {
                "feature": "PostgreSQL database connector",
                "install": "pip install psycopg2-binary",
                "test": lambda: __import__("psycopg2"),
            },
            "cassandra": {
                "feature": "Cassandra database connector",
                "install": "pip install cassandra-driver",
                "test": lambda: __import__("cassandra"),
            },
            # Document parsers
            "pypdf": {
                "feature": "PDF document parsing",
                "install": "pip install pypdf",
                "test": lambda: __import__("pypdf"),
            },
            "docx": {
                "feature": "DOCX document parsing",
                "install": "pip install python-docx",
                "test": lambda: __import__("docx"),
            },
            "openpyxl": {
                "feature": "Excel document parsing",
                "install": "pip install openpyxl",
                "test": lambda: __import__("openpyxl"),
            },
            "pandas": {
                "feature": "CSV and data file parsing",
                "install": "pip install pandas",
                "test": lambda: __import__("pandas"),
            },
            "bs4": {
                "feature": "HTML document parsing",
                "install": "pip install beautifulsoup4 lxml",
                "test": lambda: __import__("bs4"),
            },
        }

        for dep_name, dep_info in dependencies.items():
            try:
                dep_info["test"]()
                self.component_status[dep_name] = ComponentStatus.AVAILABLE
                logger.debug(f"Dependency {dep_name} is available")
            except ImportError:
                self.component_status[dep_name] = ComponentStatus.UNAVAILABLE
                logger.warning(
                    f"Optional dependency {dep_name} is not available - {dep_info['feature']} will be disabled"
                )
                self.failed_components.add(dep_name)

    def handle_dependency_error(
        self,
        dependency: str,
        feature: str,
        install_command: str,
        critical: bool = False,
    ) -> bool:
        """
        Handle missing dependency with appropriate fallback or error reporting.

        Returns:
            bool: True if processing can continue, False if it should stop
        """
        error = DependencyError(dependency, feature, install_command)

        if critical:
            error.severity = ErrorSeverity.CRITICAL
            self.log_error(error)
            return False
        else:
            # Non-critical dependency, log warning and continue
            error.severity = ErrorSeverity.LOW
            self.log_error(error)
            self.component_status[dependency] = ComponentStatus.UNAVAILABLE
            return True

    def is_component_available(self, component: str) -> bool:
        """Check if a component is available for use"""
        status = self.component_status.get(component, ComponentStatus.UNAVAILABLE)
        return status == ComponentStatus.AVAILABLE

    def get_component_status(self, component: str) -> ComponentStatus:
        """Get the current status of a component"""
        return self.component_status.get(component, ComponentStatus.UNAVAILABLE)

    def log_error(
        self,
        error: Union[ElessError, Exception],
        context: Optional[Dict[str, Any]] = None,
    ):
        """Log an error with appropriate level and suggestions"""
        if isinstance(error, ElessError):
            # Custom ELESS error with metadata
            level_map = {
                ErrorSeverity.LOW: logging.WARNING,
                ErrorSeverity.MEDIUM: logging.ERROR,
                ErrorSeverity.HIGH: logging.ERROR,
                ErrorSeverity.CRITICAL: logging.CRITICAL,
            }

            log_level = level_map.get(error.severity, logging.ERROR)
            logger.log(log_level, f"{error.component or 'Unknown'}: {error}")

            if error.suggestions:
                logger.info("Suggestions to resolve this issue:")
                for suggestion in error.suggestions:
                    logger.info(f"  • {suggestion}")

            if context:
                logger.debug(f"Error context: {context}")
        else:
            # Standard Python exception
            logger.error(f"Unexpected error: {error}", exc_info=True)

    @contextmanager
    def error_context(self, component: str, operation: str):
        """Context manager for consistent error handling"""
        try:
            logger.debug(f"Starting {operation} in {component}")
            yield
            logger.debug(f"Completed {operation} in {component}")
        except ElessError as e:
            e.component = component
            self.log_error(e, {"operation": operation})
            raise
        except Exception as e:
            # Convert standard exception to ElessError
            eless_error = ElessError(
                f"Unexpected error in {operation}: {str(e)}",
                ErrorSeverity.MEDIUM,
                ["Check logs for more details", "Report this issue if it persists"],
                component,
            )
            self.log_error(eless_error, {"operation": operation})
            raise eless_error from e

    def with_fallback(
        self,
        primary_func: Callable,
        fallback_func: Callable,
        component: str,
        operation: str,
    ):
        """Execute function with fallback on failure"""
        try:
            return primary_func()
        except Exception as e:
            logger.warning(f"{component} {operation} failed, trying fallback: {e}")
            self.component_status[component] = ComponentStatus.DEGRADED

            try:
                result = fallback_func()
                logger.info(f"Fallback successful for {component} {operation}")
                return result
            except Exception as fallback_error:
                logger.error(
                    f"Fallback also failed for {component} {operation}: {fallback_error}"
                )
                self.component_status[component] = ComponentStatus.UNAVAILABLE
                raise ProcessingError(
                    f"Both primary and fallback methods failed for {operation}",
                    suggestions=[
                        "Check component dependencies",
                        "Review configuration settings",
                        "Check system resources",
                    ],
                )

    def require_component(self, component: str, feature: str) -> bool:
        """Check if a required component is available, raise error if not"""
        if not self.is_component_available(component):
            raise DependencyError(component, feature, f"pip install {component}")
        return True

    def get_available_parsers(self) -> Dict[str, bool]:
        """Get list of available document parsers"""
        return {
            "pdf": self.is_component_available("pypdf"),
            "docx": self.is_component_available("docx"),
            "xlsx": self.is_component_available("openpyxl"),
            "csv": self.is_component_available("pandas"),
            "html": self.is_component_available("bs4"),
        }

    def get_available_databases(self) -> Dict[str, bool]:
        """Get list of available database connectors"""
        return {
            "chroma": self.is_component_available("chromadb"),
            "qdrant": self.is_component_available("qdrant_client"),
            "faiss": self.is_component_available("faiss"),
            "postgresql": self.is_component_available("psycopg2"),
            "cassandra": self.is_component_available("cassandra"),
        }

    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status"""
        total_components = len(self.component_status)
        available_count = sum(
            1
            for status in self.component_status.values()
            if status == ComponentStatus.AVAILABLE
        )
        degraded_count = sum(
            1
            for status in self.component_status.values()
            if status == ComponentStatus.DEGRADED
        )

        health_score = (
            (available_count + degraded_count * 0.5) / total_components
            if total_components > 0
            else 1.0
        )

        if health_score >= 0.8:
            health_status = "healthy"
        elif health_score >= 0.6:
            health_status = "degraded"
        else:
            health_status = "unhealthy"

        return {
            "status": health_status,
            "health_score": health_score,
            "total_components": total_components,
            "available": available_count,
            "degraded": degraded_count,
            "unavailable": total_components - available_count - degraded_count,
            "failed_components": list(self.failed_components),
            "available_parsers": self.get_available_parsers(),
            "available_databases": self.get_available_databases(),
        }

    def get_error_log(self, file_hash: str) -> Optional[str]:
        """Get the last error message for a file hash"""
        if self.state_manager:
            file_info = self.state_manager.manifest.get(file_hash, {})
            return file_info.get("last_error")
        return None


# Decorator for automatic error handling
def handle_errors(
    component: str = "Unknown", fallback_return: Any = None, reraise: bool = True
):
    """Decorator for automatic error handling with optional fallback"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except ElessError as e:
                if e.component is None:
                    e.component = component
                logger.error(f"Error in {func.__name__}: {e}")
                if reraise:
                    raise
                return fallback_return
            except Exception as e:
                error = ElessError(
                    f"Unexpected error in {func.__name__}: {str(e)}",
                    ErrorSeverity.MEDIUM,
                    component=component,
                )
                logger.error(f"Error in {func.__name__}: {error}", exc_info=True)
                if reraise:
                    raise error from e
                return fallback_return

        return wrapper

    return decorator
