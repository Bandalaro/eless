import psutil
import time
import logging
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger("ELESS.ResourceMonitor")


@dataclass
class ResourceMetrics:
    """System resource metrics snapshot."""

    cpu_percent: float
    memory_percent: float
    available_memory_mb: float
    disk_usage_percent: float
    timestamp: float


class ResourceMonitor:
    """
    System resource monitor for adaptive processing on low-end systems.
    Provides memory, CPU, and disk monitoring with adaptive batch size suggestions.
    """

    def __init__(self, config: Dict):
        self.config = config

        # Resource thresholds for adaptive processing
        self.memory_warning_threshold = config.get("resource_limits", {}).get(
            "memory_warning_percent", 80
        )
        self.memory_critical_threshold = config.get("resource_limits", {}).get(
            "memory_critical_percent", 90
        )
        self.cpu_high_threshold = config.get("resource_limits", {}).get(
            "cpu_high_percent", 85
        )

        # Minimum system requirements
        self.min_available_memory_mb = config.get("resource_limits", {}).get(
            "min_memory_mb", 256
        )
        self.max_batch_size = config["embedding"]["batch_size"]
        self.min_batch_size = max(
            1, self.max_batch_size // 8
        )  # Never go below 1/8 of max

        # Monitoring history for trends
        self.history_size = 10
        self.metrics_history = []

        logger.info(
            f"ResourceMonitor initialized - Memory thresholds: {self.memory_warning_threshold}%/{self.memory_critical_threshold}%, "
            f"CPU threshold: {self.cpu_high_threshold}%, Min memory: {self.min_available_memory_mb}MB"
        )

    def get_current_metrics(self) -> ResourceMetrics:
        """Get current system resource metrics."""
        try:
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            available_memory_mb = memory.available / (1024 * 1024)

            # CPU metrics (1-second average)
            cpu_percent = psutil.cpu_percent(interval=1)

            # Disk metrics for cache directory
            cache_dir = self.config["cache"]["directory"]
            disk_usage = psutil.disk_usage(cache_dir)
            disk_usage_percent = (disk_usage.used / disk_usage.total) * 100

            metrics = ResourceMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                available_memory_mb=available_memory_mb,
                disk_usage_percent=disk_usage_percent,
                timestamp=time.time(),
            )

            # Update history
            self._update_history(metrics)

            return metrics

        except Exception as e:
            logger.error(f"Failed to get system metrics: {e}")
            # Return conservative estimates on error
            return ResourceMetrics(
                cpu_percent=50.0,
                memory_percent=75.0,
                available_memory_mb=512.0,
                disk_usage_percent=50.0,
                timestamp=time.time(),
            )

    def _update_history(self, metrics: ResourceMetrics):
        """Update metrics history for trend analysis."""
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.history_size:
            self.metrics_history.pop(0)

    def should_throttle_processing(self) -> Tuple[bool, str]:
        """
        Check if processing should be throttled due to resource constraints.

        Returns:
            Tuple of (should_throttle, reason)
        """
        metrics = self.get_current_metrics()

        # Check critical memory threshold
        if metrics.memory_percent >= self.memory_critical_threshold:
            return True, f"Critical memory usage: {metrics.memory_percent:.1f}%"

        # Check minimum available memory
        if metrics.available_memory_mb < self.min_available_memory_mb:
            return True, f"Low available memory: {metrics.available_memory_mb:.1f}MB"

        # Check high CPU usage combined with high memory
        if (
            metrics.cpu_percent > self.cpu_high_threshold
            and metrics.memory_percent > self.memory_warning_threshold
        ):
            return (
                True,
                f"High CPU ({metrics.cpu_percent:.1f}%) + Memory ({metrics.memory_percent:.1f}%)",
            )

        return False, ""

    def get_adaptive_batch_size(self, current_batch_size: int) -> Tuple[int, str]:
        """
        Get adaptive batch size based on current system resources.

        Args:
            current_batch_size: Current batch size being used

        Returns:
            Tuple of (recommended_batch_size, reason)
        """
        metrics = self.get_current_metrics()

        # Start with current batch size
        recommended_size = current_batch_size
        reason = "No change needed"

        # Reduce batch size if memory is high
        if metrics.memory_percent >= self.memory_critical_threshold:
            recommended_size = max(self.min_batch_size, current_batch_size // 4)
            reason = f"Critical memory usage ({metrics.memory_percent:.1f}%): reduced to {recommended_size}"

        elif metrics.memory_percent >= self.memory_warning_threshold:
            recommended_size = max(self.min_batch_size, current_batch_size // 2)
            reason = f"High memory usage ({metrics.memory_percent:.1f}%): reduced to {recommended_size}"

        # Further reduce if available memory is very low
        elif metrics.available_memory_mb < self.min_available_memory_mb:
            recommended_size = self.min_batch_size
            reason = f"Low available memory ({metrics.available_memory_mb:.1f}MB): set to minimum"

        # Increase batch size if resources are abundant (but be conservative)
        elif (
            metrics.memory_percent < 50
            and metrics.available_memory_mb > self.min_available_memory_mb * 2
            and current_batch_size < self.max_batch_size
        ):
            recommended_size = min(self.max_batch_size, int(current_batch_size * 1.5))
            reason = f"Abundant resources: increased to {recommended_size}"

        return recommended_size, reason

    def get_memory_pressure_level(self) -> str:
        """Get current memory pressure level as a string."""
        metrics = self.get_current_metrics()

        if metrics.memory_percent >= self.memory_critical_threshold:
            return "CRITICAL"
        elif metrics.memory_percent >= self.memory_warning_threshold:
            return "HIGH"
        elif metrics.memory_percent >= 50:
            return "MODERATE"
        else:
            return "LOW"

    def wait_for_resources(self, max_wait_seconds: int = 30) -> bool:
        """
        Wait for system resources to become available.

        Args:
            max_wait_seconds: Maximum time to wait

        Returns:
            True if resources became available, False if timed out
        """
        start_time = time.time()

        while time.time() - start_time < max_wait_seconds:
            should_throttle, reason = self.should_throttle_processing()
            if not should_throttle:
                return True

            logger.info(f"Waiting for resources: {reason}")
            time.sleep(2)  # Check every 2 seconds

        logger.warning(f"Timed out waiting for resources after {max_wait_seconds}s")
        return False

    def get_system_summary(self) -> Dict:
        """Get comprehensive system resource summary."""
        metrics = self.get_current_metrics()

        # Calculate trends if we have history
        memory_trend = "stable"
        cpu_trend = "stable"

        if len(self.metrics_history) >= 3:
            recent_memory = [m.memory_percent for m in self.metrics_history[-3:]]
            recent_cpu = [m.cpu_percent for m in self.metrics_history[-3:]]

            if recent_memory[-1] > recent_memory[0] + 5:
                memory_trend = "increasing"
            elif recent_memory[-1] < recent_memory[0] - 5:
                memory_trend = "decreasing"

            if recent_cpu[-1] > recent_cpu[0] + 10:
                cpu_trend = "increasing"
            elif recent_cpu[-1] < recent_cpu[0] - 10:
                cpu_trend = "decreasing"

        return {
            "memory_percent": metrics.memory_percent,
            "memory_available_mb": metrics.available_memory_mb,
            "memory_pressure": self.get_memory_pressure_level(),
            "memory_trend": memory_trend,
            "cpu_percent": metrics.cpu_percent,
            "cpu_trend": cpu_trend,
            "disk_usage_percent": metrics.disk_usage_percent,
            "should_throttle": self.should_throttle_processing()[0],
            "recommended_batch_size": self.get_adaptive_batch_size(self.max_batch_size)[
                0
            ],
            "timestamp": metrics.timestamp,
        }

    def log_system_status(self):
        """Log current system status for monitoring."""
        summary = self.get_system_summary()

        logger.info(
            f"System Status - Memory: {summary['memory_percent']:.1f}% ({summary['memory_pressure']}), "
            f"CPU: {summary['cpu_percent']:.1f}%, "
            f"Available RAM: {summary['memory_available_mb']:.0f}MB, "
            f"Recommended batch: {summary['recommended_batch_size']}"
        )
