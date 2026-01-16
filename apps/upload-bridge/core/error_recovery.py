"""
Error recovery utilities for robust upload operations.

Provides mechanisms for:
- Partial upload resume capability
- Recovery from transient failures
- Graceful degradation
- User notification of recovery status
"""

import logging
import os
import time
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class UploadCheckpoint:
    """Represents a checkpoint during upload for resume capability"""
    file_path: str
    device_ip: str
    total_size: int
    bytes_uploaded: int
    timestamp: float
    chunk_size: int
    checksum: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'file_path': self.file_path,
            'device_ip': self.device_ip,
            'total_size': self.total_size,
            'bytes_uploaded': self.bytes_uploaded,
            'timestamp': self.timestamp,
            'chunk_size': self.chunk_size,
            'checksum': self.checksum,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UploadCheckpoint':
        """Create from dictionary"""
        return cls(**data)


class UploadRecoveryManager:
    """Manages upload recovery and resume capabilities"""
    
    def __init__(self, checkpoint_dir: Optional[Path] = None):
        """
        Initialize recovery manager.
        
        Args:
            checkpoint_dir: Directory to store checkpoint files
        """
        if checkpoint_dir is None:
            checkpoint_dir = Path.home() / '.uploadbridge' / 'checkpoints'
        
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
    
    def save_checkpoint(self, checkpoint: UploadCheckpoint) -> bool:
        """
        Save an upload checkpoint.
        
        Args:
            checkpoint: UploadCheckpoint instance
        
        Returns:
            True if saved successfully
        """
        try:
            import json
            
            # Create filename from device IP and file hash
            file_hash = hash(checkpoint.file_path) % (2**32)
            filename = f"{checkpoint.device_ip.replace('.', '_')}_{file_hash}.json"
            filepath = self.checkpoint_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(checkpoint.to_dict(), f, indent=2)
            
            logger.info(f"Checkpoint saved: {filename}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
            return False
    
    def load_checkpoint(self, file_path: str, device_ip: str) -> Optional[UploadCheckpoint]:
        """
        Load an upload checkpoint.
        
        Args:
            file_path: Original file path
            device_ip: Device IP address
        
        Returns:
            UploadCheckpoint if found, None otherwise
        """
        try:
            import json
            
            # Find checkpoint file
            file_hash = hash(file_path) % (2**32)
            filename = f"{device_ip.replace('.', '_')}_{file_hash}.json"
            filepath = self.checkpoint_dir / filename
            
            if not filepath.exists():
                return None
            
            # Check if checkpoint is still valid (not older than 24 hours)
            age_seconds = time.time() - filepath.stat().st_mtime
            if age_seconds > 24 * 3600:
                logger.warning(f"Checkpoint expired: {filename}")
                filepath.unlink()
                return None
            
            # Load checkpoint
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            checkpoint = UploadCheckpoint.from_dict(data)
            logger.info(f"Checkpoint loaded: {filename} ({checkpoint.bytes_uploaded}/{checkpoint.total_size} bytes)")
            return checkpoint
        
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None
    
    def delete_checkpoint(self, file_path: str, device_ip: str) -> bool:
        """
        Delete an upload checkpoint (after successful completion).
        
        Args:
            file_path: Original file path
            device_ip: Device IP address
        
        Returns:
            True if deleted successfully
        """
        try:
            file_hash = hash(file_path) % (2**32)
            filename = f"{device_ip.replace('.', '_')}_{file_hash}.json"
            filepath = self.checkpoint_dir / filename
            
            if filepath.exists():
                filepath.unlink()
                logger.info(f"Checkpoint deleted: {filename}")
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete checkpoint: {e}")
            return False
    
    def cleanup_expired_checkpoints(self, max_age_hours: int = 24) -> int:
        """
        Remove expired checkpoints.
        
        Args:
            max_age_hours: Age in hours after which to delete
        
        Returns:
            Number of checkpoints deleted
        """
        deleted = 0
        max_age_seconds = max_age_hours * 3600
        current_time = time.time()
        
        for checkpoint_file in self.checkpoint_dir.glob('*.json'):
            try:
                age = current_time - checkpoint_file.stat().st_mtime
                if age > max_age_seconds:
                    checkpoint_file.unlink()
                    deleted += 1
            except OSError:
                pass
        
        if deleted > 0:
            logger.info(f"Cleaned up {deleted} expired checkpoints")
        
        return deleted
    
    def get_checkpoint_status(self) -> Dict[str, Any]:
        """
        Get status of all checkpoints.
        
        Returns:
            Dictionary with checkpoint information
        """
        checkpoints = []
        total_size = 0
        
        for checkpoint_file in self.checkpoint_dir.glob('*.json'):
            try:
                import json
                with open(checkpoint_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                checkpoints.append({
                    'filename': checkpoint_file.name,
                    'file_path': data.get('file_path'),
                    'device_ip': data.get('device_ip'),
                    'progress': f"{data.get('bytes_uploaded')}/{data.get('total_size')}",
                })
                total_size += checkpoint_file.stat().st_size
            except Exception as e:
                logger.warning(f"Could not read checkpoint {checkpoint_file.name}: {e}")
        
        return {
            'total_checkpoints': len(checkpoints),
            'checkpoints': checkpoints,
            'total_size_mb': total_size / (1024 * 1024),
        }


class RecoveryNotifier:
    """Notifies user of recovery attempts and status"""
    
    @staticmethod
    def notify_recovery_started(file_name: str, bytes_to_recover: int) -> None:
        """
        Notify that recovery is starting.
        
        Args:
            file_name: Name of file being recovered
            bytes_to_recover: Number of bytes to recover
        """
        logger.info(
            f"Resuming upload for {file_name}: "
            f"recovering {bytes_to_recover / 1024:.1f} KB"
        )
    
    @staticmethod
    def notify_recovery_progress(current: int, total: int) -> None:
        """
        Notify of recovery progress.
        
        Args:
            current: Current bytes uploaded
            total: Total bytes to upload
        """
        percent = (current / total * 100) if total > 0 else 0
        logger.debug(f"Recovery progress: {percent:.1f}% ({current}/{total} bytes)")
    
    @staticmethod
    def notify_recovery_complete(file_name: str, duration: float) -> None:
        """
        Notify that recovery completed successfully.
        
        Args:
            file_name: Name of recovered file
            duration: Time taken for recovery
        """
        logger.info(f"Recovery completed for {file_name} in {duration:.2f} seconds")
    
    @staticmethod
    def notify_recovery_failed(file_name: str, reason: str) -> None:
        """
        Notify that recovery failed.
        
        Args:
            file_name: Name of file that failed recovery
            reason: Reason for failure
        """
        logger.error(f"Recovery failed for {file_name}: {reason}")
    
    @staticmethod
    def get_recovery_suggestion(error_type: str) -> str:
        """
        Get suggestion for recovery based on error type.
        
        Args:
            error_type: Type of error that occurred
        
        Returns:
            Recovery suggestion string
        """
        suggestions = {
            'timeout': 'Connection timed out. The device may be out of range or powered off. Try moving closer.',
            'connection_refused': 'Device refused connection. Ensure device is powered on and accepting connections.',
            'device_busy': 'Device is busy. Wait a moment and try again.',
            'partial_upload': 'Upload was interrupted. Resuming from where it left off.',
            'checksum_mismatch': 'File integrity check failed. Retrying upload from scratch.',
            'insufficient_space': 'Device has insufficient storage. Free up space and try again.',
        }
        
        return suggestions.get(error_type, 'Upload failed. Please try again.')


class FailureRecoveryStrategy:
    """Strategies for recovering from different types of failures"""
    
    @staticmethod
    def should_retry(error_type: str, attempt_count: int) -> bool:
        """
        Determine if an operation should be retried.
        
        Args:
            error_type: Type of error
            attempt_count: Number of attempts made
        
        Returns:
            True if should retry
        """
        # Retryable errors
        retryable = {
            'timeout': True,
            'connection_refused': True,
            'connection_reset': True,
            'temporary_failure': True,
            'device_busy': True,
        }
        
        # Non-retryable errors
        non_retryable = {
            'invalid_file': False,
            'insufficient_space': False,  # Until space is freed
            'authentication_failed': False,
            'permission_denied': False,
        }
        
        is_retryable = retryable.get(error_type, False)
        max_attempts = 3
        
        return is_retryable and attempt_count < max_attempts
    
    @staticmethod
    def should_resume(error_type: str, bytes_uploaded: int, total_size: int) -> bool:
        """
        Determine if an upload should be resumed vs restarted.
        
        Args:
            error_type: Type of error
            bytes_uploaded: Bytes already uploaded
            total_size: Total file size
        
        Returns:
            True if should resume, False to restart
        """
        # Only resume for connection-type errors after significant progress
        progress_threshold = 0.1  # 10%
        progress = bytes_uploaded / total_size if total_size > 0 else 0
        
        connection_errors = {'timeout', 'connection_reset', 'connection_refused'}
        
        should_resume = (
            error_type in connection_errors and 
            progress >= progress_threshold
        )
        
        return should_resume
    
    @staticmethod
    def get_backoff_delay(attempt_count: int) -> float:
        """
        Get delay before next recovery attempt.
        
        Args:
            attempt_count: Number of attempts made
        
        Returns:
            Delay in seconds
        """
        # Exponential backoff: 1s, 2s, 4s, etc.
        base_delay = 1.0
        max_delay = 30.0
        
        delay = min(base_delay * (2 ** attempt_count), max_delay)
        return delay


# Global recovery manager instance
_recovery_manager: Optional[UploadRecoveryManager] = None


def get_recovery_manager() -> UploadRecoveryManager:
    """Get the global recovery manager instance"""
    global _recovery_manager
    if _recovery_manager is None:
        _recovery_manager = UploadRecoveryManager()
    return _recovery_manager
