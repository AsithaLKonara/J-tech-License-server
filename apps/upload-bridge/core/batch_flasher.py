"""
Batch Flasher - Multi-device concurrent flashing
Complete implementation with threading and progress tracking
"""

import threading
import queue
import time
from dataclasses import dataclass
from typing import List, Callable, Optional
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.pattern import Pattern
from uploaders.base import UploaderBase, UploadResult
from uploaders.uploader_registry import get_uploader


@dataclass
class FlashJob:
    """Single flash job for one device"""
    job_id: str
    port: str
    chip_id: str
    firmware_path: str
    gpio_pin: int = 2


@dataclass
class FlashJobResult:
    """Result of a flash job"""
    job_id: str
    port: str
    success: bool
    duration_seconds: float
    bytes_written: int
    error_message: Optional[str] = None


class BatchFlasher:
    """
    Manages flashing multiple devices concurrently or sequentially
    
    Features:
    - Queue-based job management
    - Configurable concurrency (1-N devices at once)
    - Progress tracking per device
    - Error handling and retry
    - Results aggregation
    """
    
    def __init__(self, max_concurrent: int = 1):
        """
        Initialize batch flasher
        
        Args:
            max_concurrent: Maximum devices to flash simultaneously (default: 1 for safety)
        """
        self.max_concurrent = max_concurrent
        self.job_queue = queue.Queue()
        self.results: List[FlashJobResult] = []
        self.progress_callback: Optional[Callable] = None
        self.active_jobs = 0
        self.total_jobs = 0
        self.lock = threading.Lock()
    
    def add_job(self, job: FlashJob):
        """
        Add flash job to queue
        
        Args:
            job: FlashJob with device and firmware info
        """
        self.job_queue.put(job)
        self.total_jobs += 1
    
    def clear_jobs(self):
        """Clear all pending jobs"""
        while not self.job_queue.empty():
            try:
                self.job_queue.get_nowait()
                self.job_queue.task_done()
            except queue.Empty:
                break
        
        self.total_jobs = 0
        self.results.clear()
    
    def flash_all(self) -> List[FlashJobResult]:
        """
        Execute all queued jobs
        
        Returns:
            List of FlashJobResult for all jobs
        """
        if self.total_jobs == 0:
            return []
        
        # Create worker threads
        workers = []
        
        for i in range(min(self.max_concurrent, self.total_jobs)):
            worker = threading.Thread(
                target=self._worker,
                name=f"FlashWorker-{i}",
                daemon=True
            )
            worker.start()
            workers.append(worker)
        
        # Wait for all workers to complete
        for worker in workers:
            worker.join()
        
        # Wait for queue to be fully processed
        self.job_queue.join()
        
        return self.results
    
    def _worker(self):
        """Worker thread that processes flash jobs"""
        while True:
            try:
                # Get next job (with timeout)
                job = self.job_queue.get(timeout=1)
            except queue.Empty:
                # No more jobs
                break
            
            # Execute job
            try:
                with self.lock:
                    self.active_jobs += 1
                
                result = self._flash_device(job)
                
                with self.lock:
                    self.results.append(result)
                    self.active_jobs -= 1
                
                # Report progress
                if self.progress_callback:
                    completed = len(self.results)
                    remaining = self.job_queue.qsize()
                    self.progress_callback(completed, remaining, result)
            
            except Exception as e:
                # Job failed critically
                result = FlashJobResult(
                    job_id=job.job_id,
                    port=job.port,
                    success=False,
                    duration_seconds=0,
                    bytes_written=0,
                    error_message=str(e)
                )
                
                with self.lock:
                    self.results.append(result)
                    self.active_jobs -= 1
                
                if self.progress_callback:
                    completed = len(self.results)
                    remaining = self.job_queue.qsize()
                    self.progress_callback(completed, remaining, result)
            
            finally:
                self.job_queue.task_done()
    
    def _flash_device(self, job: FlashJob) -> FlashJobResult:
        """
        Flash single device
        
        Args:
            job: FlashJob to execute
        
        Returns:
            FlashJobResult with outcome
        """
        start_time = time.time()
        
        try:
            # Get uploader
            uploader = get_uploader(job.chip_id)
            
            if not uploader:
                raise Exception(f"No uploader for {job.chip_id}")
            
            # Upload firmware
            upload_result = uploader.upload(job.firmware_path, {
                'port': job.port,
                'gpio': job.gpio_pin
            })
            
            duration = time.time() - start_time
            
            return FlashJobResult(
                job_id=job.job_id,
                port=job.port,
                success=upload_result.success,
                duration_seconds=duration,
                bytes_written=upload_result.bytes_written,
                error_message=upload_result.error_message
            )
        
        except Exception as e:
            duration = time.time() - start_time
            
            return FlashJobResult(
                job_id=job.job_id,
                port=job.port,
                success=False,
                duration_seconds=duration,
                bytes_written=0,
                error_message=str(e)
            )
    
    def set_progress_callback(self, callback: Callable[[int, int, FlashJobResult], None]):
        """
        Set callback for progress updates
        
        Args:
            callback: Function(completed, remaining, last_result)
        """
        self.progress_callback = callback
    
    def get_summary(self) -> dict:
        """
        Get summary of batch flash results
        
        Returns:
            Dictionary with success/failure counts and details
        """
        success_count = sum(1 for r in self.results if r.success)
        failure_count = sum(1 for r in self.results if not r.success)
        
        total_time = sum(r.duration_seconds for r in self.results)
        total_bytes = sum(r.bytes_written for r in self.results)
        
        return {
            "total_jobs": len(self.results),
            "successful": success_count,
            "failed": failure_count,
            "success_rate": success_count / len(self.results) if self.results else 0,
            "total_duration_seconds": total_time,
            "total_bytes_written": total_bytes,
            "average_time_per_device": total_time / len(self.results) if self.results else 0,
            "failed_ports": [r.port for r in self.results if not r.success],
            "errors": [r.error_message for r in self.results if r.error_message]
        }


# Convenience function
def batch_flash_devices(
    pattern: Pattern,
    chip_id: str,
    ports: List[str],
    gpio_pin: int = 2,
    max_concurrent: int = 1,
    progress_callback: Optional[Callable] = None
) -> List[FlashJobResult]:
    """
    Flash pattern to multiple devices
    
    Args:
        pattern: Pattern to flash
        chip_id: Target chip type
        ports: List of serial ports
        gpio_pin: Data pin for LEDs
        max_concurrent: How many to flash at once
        progress_callback: Optional callback for progress
    
    Returns:
        List of FlashJobResult
    """
    from firmware.builder import FirmwareBuilder
    
    # Build firmware once
    builder = FirmwareBuilder()
    build_result = builder.build(pattern, chip_id, {'gpio_pin': gpio_pin})
    
    if not build_result.success:
        raise Exception(f"Build failed: {build_result.error_message}")
    
    # Create batch flasher
    flasher = BatchFlasher(max_concurrent=max_concurrent)
    
    if progress_callback:
        flasher.set_progress_callback(progress_callback)
    
    # Add jobs
    for i, port in enumerate(ports):
        job = FlashJob(
            job_id=f"job_{i}",
            port=port,
            chip_id=chip_id,
            firmware_path=build_result.firmware_path,
            gpio_pin=gpio_pin
        )
        flasher.add_job(job)
    
    # Execute all
    return flasher.flash_all()

