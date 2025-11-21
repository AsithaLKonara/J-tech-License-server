# Chip Integration Guide

## Overview

This guide explains how to integrate new chip uploaders using the UploaderAdapter interface.

## UploaderAdapter Interface

All chip uploaders must implement the `UploaderAdapter` ABC from `uploaders.adapter_interface`.

### Required Methods

```python
class UploaderAdapter(ABC):
    @property
    @abstractmethod
    def chip_id(self) -> str:
        """Chip identifier (e.g., 'ESP32', 'STM32F407')"""
        pass
    
    @property
    @abstractmethod
    def chip_variant(self) -> Optional[str]:
        """Chip variant if applicable"""
        pass
    
    @abstractmethod
    def detect_device(self, port: Optional[str] = None) -> Optional[DeviceInfo]:
        """Detect connected device"""
        pass
    
    @abstractmethod
    def build_firmware(
        self,
        pattern: Pattern,
        output_path: Path,
        options: Optional[Dict[str, Any]] = None
    ) -> BuildResult:
        """Build firmware from pattern"""
        pass
    
    @abstractmethod
    def flash_firmware(
        self,
        firmware_path: Path,
        device_info: DeviceInfo,
        options: Optional[FlashOptions] = None
    ) -> FlashResult:
        """Flash firmware to device"""
        pass
    
    @abstractmethod
    def verify_firmware(
        self,
        firmware_path: Path,
        device_info: DeviceInfo,
        expected_hash: Optional[str] = None
    ) -> VerifyResult:
        """Verify flashed firmware"""
        pass
    
    @abstractmethod
    def get_device_profile(self) -> Dict[str, Any]:
        """Get device profile (JSON-serializable)"""
        pass
```

## Implementation Steps

### 1. Create Uploader Class

```python
from uploaders.adapter_interface import (
    UploaderAdapter,
    DeviceInfo,
    FlashResult,
    VerifyResult,
    FlashOptions,
    BuildResult,
)
from uploaders.adapter_registry import register_adapter

class MyChipUploader(UploaderAdapter):
    # Implement all required methods
    pass

# Register adapter
register_adapter(MyChipUploader)
```

### 2. Create Device Profile

Create a JSON profile in `uploaders/profiles/mychip.json`:

```json
{
  "chip_id": "MyChip",
  "chip_variant": null,
  "chip_name": "My Chip",
  "manufacturer": "Manufacturer",
  "architecture": "Architecture",
  "flash_size_bytes": 1048576,
  "ram_size_bytes": 32768,
  "cpu_frequency_mhz": 80,
  "supported_formats": ["bin", "hex"],
  "toolchain": {
    "compiler": "gcc",
    "flasher": "tool",
    "version_required": "1.0.0"
  },
  "flash_options": {
    "default_baud_rate": 115200
  },
  "capabilities": ["flash", "verify"]
}
```

### 3. Implement Detection

```python
def detect_device(self, port: Optional[str] = None) -> Optional[DeviceInfo]:
    """Detect connected device"""
    try:
        # Use chip-specific detection method
        cmd = ["tool", "detect"]
        if port:
            cmd.extend(["--port", port])
        
        result = subprocess.run(cmd, capture_output=True, timeout=5)
        
        if result.returncode == 0:
            return DeviceInfo(
                chip_id=self.chip_id,
                chip_variant=self.chip_variant,
                port=port or "auto",
                capabilities=["flash", "verify"]
            )
    except Exception:
        pass
    return None
```

### 4. Implement Firmware Building

```python
def build_firmware(
    self,
    pattern: Pattern,
    output_path: Path,
    options: Optional[Dict[str, Any]] = None
) -> BuildResult:
    """Build firmware from pattern"""
    try:
        # Generate firmware binary
        firmware_bytes = self._generate_firmware(pattern, options)
        
        # Write firmware
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(firmware_bytes)
        
        # Compute hash
        import hashlib
        artifact_hash = hashlib.sha256(firmware_bytes).hexdigest()
        
        return BuildResult(
            success=True,
            firmware_path=output_path,
            artifact_hash=artifact_hash
        )
    except Exception as e:
        return BuildResult(
            success=False,
            error_message=str(e)
        )
```

### 5. Implement Flashing

```python
def flash_firmware(
    self,
    firmware_path: Path,
    device_info: DeviceInfo,
    options: Optional[FlashOptions] = None
) -> FlashResult:
    """Flash firmware to device"""
    if options is None:
        options = FlashOptions()
    
    try:
        cmd = [
            "flasher-tool",
            "--port", device_info.port,
            "--baud", str(options.baud_rate),
            "flash", str(firmware_path)
        ]
        
        if options.verify:
            cmd.append("--verify")
        
        result = subprocess.run(cmd, timeout=60)
        
        if result.returncode == 0:
            if options.verify:
                verify_result = self.verify_firmware(
                    firmware_path,
                    device_info,
                    None
                )
                if verify_result != VerifyResult.SUCCESS:
                    return FlashResult.VERIFICATION_FAILED
            return FlashResult.SUCCESS
        return FlashResult.FAILURE
    except subprocess.TimeoutExpired:
        return FlashResult.TIMEOUT
    except Exception:
        return FlashResult.FAILURE
```

### 6. Implement Verification

```python
def verify_firmware(
    self,
    firmware_path: Path,
    device_info: DeviceInfo,
    expected_hash: Optional[str] = None
) -> VerifyResult:
    """Verify flashed firmware"""
    try:
        if expected_hash and firmware_path.exists():
            import hashlib
            with open(firmware_path, "rb") as f:
                firmware_bytes = f.read()
            actual_hash = hashlib.sha256(firmware_bytes).hexdigest()
            
            if actual_hash != expected_hash:
                return VerifyResult.HASH_MISMATCH
        
        # Use tool verification
        cmd = ["flasher-tool", "verify", str(firmware_path)]
        result = subprocess.run(cmd, timeout=30)
        
        if result.returncode == 0:
            return VerifyResult.SUCCESS
        return VerifyResult.FAILURE
    except Exception:
        return VerifyResult.FAILURE
```

### 7. Load Device Profile

```python
def get_device_profile(self) -> Dict[str, Any]:
    """Get device profile"""
    profile_path = Path(__file__).parent / "profiles" / "mychip.json"
    if profile_path.exists():
        import json
        with open(profile_path, "r") as f:
            return json.load(f)
    
    # Return default profile
    return {
        "chip_id": self.chip_id,
        # ... default values
    }
```

## Registration

Adapters are automatically registered when imported. Add to `uploaders/adapter_init.py`:

```python
from uploaders.mychip_uploader import MyChipUploader
```

## Testing

Create tests in `tests/integration/test_mychip_uploader.py`:

```python
def test_detect_device(mychip_uploader):
    device = mychip_uploader.detect_device()
    assert device is not None
    assert device.chip_id == "MyChip"

def test_build_firmware(mychip_uploader, test_pattern):
    result = mychip_uploader.build_firmware(
        test_pattern,
        Path("build/test.bin")
    )
    assert result.success
    assert result.firmware_path.exists()
```

## CI/CD Integration

Add chip to build matrix in `.github/workflows/build.yml`:

```yaml
matrix:
  chip:
    - mychip
```

Create Dockerfile in `docker/mychip/Dockerfile` for reproducible builds.

## Verification

Implement hash verification using `uploaders/verification/verifier.py`:

```python
from uploaders.verification import verify_firmware_hash

result, actual_hash = verify_firmware_hash(
    firmware_path=Path("build/firmware.bin"),
    device_info=device_info,
    adapter=uploader,
    expected_hash=expected_hash
)
```

