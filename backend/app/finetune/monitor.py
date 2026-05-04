"""Training monitoring and metrics tracking."""
import asyncio
import json
import logging
from pathlib import Path
from typing import Optional, AsyncIterator
from datetime import datetime
from collections import deque
from dataclasses import dataclass, asdict
import uuid

logger = logging.getLogger(__name__)


@dataclass
class TrainingMetrics:
    """Training metrics snapshot."""
    timestamp: str
    step: int
    epoch: int
    loss: float
    learning_rate: float
    gpu_memory_used: int
    gpu_utilization: float
    samples_per_second: float
    steps_per_second: float
    best_loss: float
    progress_pct: float


@dataclass
class SystemMetrics:
    """System resource metrics."""
    timestamp: str
    gpu_count: int
    gpu_memory_total: int
    gpu_memory_used: int
    gpu_utilization: float
    cpu_percent: float
    memory_used: int
    memory_total: int
    disk_used: int
    disk_total: int


class MetricsCollector:
    """Collects and stores training metrics."""
    
    def __init__(self, max_history: int = 10000):
        self.max_history = max_history
        self._metrics: deque = deque(maxlen=max_history)
        self._loss_history: deque = deque(maxlen=max_history)
        self._lr_history: deque = deque(maxlen=max_history)
        
        # Running statistics
        self.total_steps = 0
        self.total_loss = 0.0
        self.loss_count = 0
    
    def add_metrics(self, metrics: TrainingMetrics) -> None:
        """Add training metrics."""
        self._metrics.append(metrics)
        self._loss_history.append((metrics.step, metrics.loss))
        self._lr_history.append((metrics.step, metrics.learning_rate))
        
        self.total_steps = metrics.step
        self.total_loss += metrics.loss
        self.loss_count += 1
    
    def get_recent_metrics(self, count: int = 100) -> list[TrainingMetrics]:
        """Get recent metrics."""
        return list(self._metrics)[-count:]
    
    def get_loss_curve_data(self) -> dict:
        """Get loss curve data for charting."""
        steps = [m.step for m in self._metrics]
        losses = [m.loss for m in self._metrics]
        return {
            "steps": steps,
            "losses": losses,
        }
    
    def get_average_loss(self, window: int = 100) -> float:
        """Get average loss over recent window."""
        if not self._metrics:
            return 0.0
        
        recent = list(self._metrics)[-window:]
        return sum(m.loss for m in recent) / len(recent)
    
    def get_smoothed_loss(self, window: int = 10) -> list[float]:
        """Get smoothed loss curve using moving average."""
        if len(self._loss_history) < window:
            return [l for _, l in self._loss_history]
        
        smoothed = []
        for i in range(len(self._loss_history)):
            start = max(0, i - window + 1)
            window_losses = [l for _, l in list(self._loss_history)[start:i+1]]
            smoothed.append(sum(window_losses) / len(window_losses))
        
        return smoothed
    
    def get_statistics(self) -> dict:
        """Get overall statistics."""
        if not self._metrics:
            return {}
        
        losses = [m.loss for m in self._metrics]
        
        return {
            "total_steps": self.total_steps,
            "average_loss": self.total_loss / self.loss_count if self.loss_count > 0 else 0,
            "min_loss": min(losses) if losses else 0,
            "max_loss": max(losses) if losses else 0,
            "final_loss": losses[-1] if losses else 0,
            "metrics_count": len(self._metrics),
        }


class SystemMonitor:
    """Monitors system resources during training."""
    
    def __init__(self, interval: float = 5.0):
        self.interval = interval
        self._is_running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._system_metrics: deque = deque(maxlen=1000)
    
    async def start(self) -> None:
        """Start monitoring."""
        if self._is_running:
            return
        
        self._is_running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("System monitoring started")
    
    async def stop(self) -> None:
        """Stop monitoring."""
        self._is_running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("System monitoring stopped")
    
    async def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self._is_running:
            try:
                metrics = await self._collect_metrics()
                self._system_metrics.append(metrics)
                await asyncio.sleep(self.interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
    
    async def _collect_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        # In production, use psutil and nvidia-ml-py3
        # This is a simplified simulation
        return SystemMetrics(
            timestamp=datetime.utcnow().isoformat(),
            gpu_count=1,
            gpu_memory_total=24576 * 1024 * 1024,  # 24GB
            gpu_memory_used=8192 * 1024 * 1024,  # 8GB
            gpu_utilization=85.0,
            cpu_percent=45.0,
            memory_used=16 * 1024 * 1024 * 1024,  # 16GB
            memory_total=32 * 1024 * 1024 * 1024,  # 32GB
            disk_used=500 * 1024 * 1024 * 1024,  # 500GB
            disk_total=1000 * 1024 * 1024 * 1024,  # 1TB
        )
    
    async def get_current_metrics(self) -> Optional[SystemMetrics]:
        """Get most recent metrics."""
        return self._system_metrics[-1] if self._system_metrics else None
    
    def get_gpu_utilization_history(self) -> list[tuple[str, float]]:
        """Get GPU utilization history."""
        return [(m.timestamp, m.gpu_utilization) for m in self._system_metrics]
    
    def get_memory_history(self) -> list[dict]:
        """Get memory usage history."""
        return [
            {
                "timestamp": m.timestamp,
                "gpu_memory_used": m.gpu_memory_used,
                "gpu_memory_total": m.gpu_memory_total,
                "memory_used": m.memory_used,
                "memory_total": m.memory_total,
            }
            for m in self._system_metrics
        ]


class TrainingMonitor:
    """
    Unified training monitor combining metrics and system monitoring.
    """
    
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.metrics_collector = MetricsCollector()
        self.system_monitor = SystemMonitor(interval=5.0)
        self._is_running = False
        self._subscribers: dict[str, asyncio.Queue] = {}
    
    async def start(self) -> None:
        """Start monitoring."""
        self._is_running = True
        await self.system_monitor.start()
        logger.info(f"Training monitor started for job {self.job_id}")
    
    async def stop(self) -> None:
        """Stop monitoring."""
        self._is_running = False
        await self.system_monitor.stop()
        logger.info(f"Training monitor stopped for job {self.job_id}")
    
    async def record_metrics(self, metrics: TrainingMetrics) -> None:
        """Record training metrics and broadcast to subscribers."""
        self.metrics_collector.add_metrics(metrics)
        
        # Broadcast to subscribers
        for queue in self._subscribers.values():
            await queue.put({
                "type": "metrics",
                "data": asdict(metrics),
            })
    
    def subscribe(self) -> tuple[str, asyncio.Queue]:
        """Subscribe to monitoring updates. Returns subscription ID and queue."""
        sub_id = str(uuid.uuid4())
        queue = asyncio.Queue(maxsize=100)
        self._subscribers[sub_id] = queue
        return sub_id, queue
    
    def unsubscribe(self, sub_id: str) -> None:
        """Unsubscribe from monitoring updates."""
        self._subscribers.pop(sub_id, None)
    
    async def stream_updates(self, sub_id: str) -> AsyncIterator[dict]:
        """Stream monitoring updates to subscriber."""
        if sub_id not in self._subscribers:
            return
        
        queue = self._subscribers[sub_id]
        
        while self._is_running:
            try:
                update = await asyncio.wait_for(queue.get(), timeout=30.0)
                yield update
            except asyncio.TimeoutError:
                # Send heartbeat
                yield {"type": "heartbeat", "timestamp": datetime.utcnow().isoformat()}
    
    def get_loss_curve(self) -> dict:
        """Get loss curve data for charting."""
        return self.metrics_collector.get_loss_curve_data()
    
    def get_smoothed_loss_curve(self) -> dict:
        """Get smoothed loss curve."""
        data = self.metrics_collector.get_loss_curve_data()
        smoothed = self.metrics_collector.get_smoothed_loss()
        data["smoothed_losses"] = smoothed
        return data
    
    async def get_current_status(self) -> dict:
        """Get current monitoring status."""
        metrics = await self.system_monitor.get_current_metrics()
        
        return {
            "job_id": self.job_id,
            "is_running": self._is_running,
            "metrics": self.metrics_collector.get_statistics(),
            "system": asdict(metrics) if metrics else None,
            "loss_curve": self.get_loss_curve(),
        }


# Global monitor registry
_monitors: dict[str, TrainingMonitor] = {}


def get_training_monitor(job_id: str) -> Optional[TrainingMonitor]:
    """Get existing training monitor."""
    return _monitors.get(job_id)


def create_training_monitor(job_id: str) -> TrainingMonitor:
    """Create new training monitor."""
    monitor = TrainingMonitor(job_id)
    _monitors[job_id] = monitor
    return monitor


def remove_training_monitor(job_id: str) -> None:
    """Remove training monitor."""
    monitor = _monitors.pop(job_id, None)
    if monitor:
        asyncio.create_task(monitor.stop())
