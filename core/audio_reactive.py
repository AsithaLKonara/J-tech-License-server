"""
Audio-Reactive Effects - Generate LED patterns from audio input
"""

import logging
from typing import List, Tuple, Optional, Callable, Dict, Any

try:
    import numpy as np
    import scipy.fft
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

from dataclasses import dataclass

from .pattern import Pattern, Frame, PatternMetadata

logger = logging.getLogger(__name__)

try:
    import pyaudio
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False
    logger.warning("Audio libraries not available. Install pyaudio and scipy for audio-reactive effects.")


@dataclass
class AudioConfig:
    """Audio capture configuration"""
    sample_rate: int = 44100
    chunk_size: int = 1024
    channels: int = 1
    format: int = None  # pyaudio format
    device_index: Optional[int] = None


class AudioReactiveGenerator:
    """
    Generate LED patterns from audio input using FFT analysis
    
    Features:
    - Real-time audio capture
    - FFT frequency analysis
    - Multiple visualization modes
    - Pattern generation
    """
    
    def __init__(self, led_count: int, width: int, height: int):
        """
        Initialize audio-reactive generator
        
        Args:
            led_count: Number of LEDs
            width: Matrix width
            height: Matrix height
        """
        if not AUDIO_AVAILABLE:
            raise ImportError("Audio libraries not available. Install pyaudio for audio-reactive effects.")
        if not NUMPY_AVAILABLE:
            raise ImportError("NumPy/Scipy not available. Install numpy and scipy for audio-reactive effects.")
        
        self.led_count = led_count
        self.width = width
        self.height = height
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.config = AudioConfig()
        self.is_capturing = False
        
        # FFT analysis
        self.fft_size = self.config.chunk_size
        self.freq_bins = self.fft_size // 2
        
        # Frequency bands for LED mapping
        self.freq_bands = self._calculate_freq_bands()
    
    def _calculate_freq_bands(self) -> List[Tuple[int, int]]:
        """
        Calculate frequency bands for LED mapping
        
        Returns:
            List of (start_freq, end_freq) tuples
        """
        nyquist = self.config.sample_rate / 2
        bands = []
        
        # Divide frequency spectrum into LED count bands
        for i in range(self.led_count):
            start_freq = (i / self.led_count) * nyquist
            end_freq = ((i + 1) / self.led_count) * nyquist
            bands.append((int(start_freq), int(end_freq)))
        
        return bands
    
    def list_audio_devices(self) -> List[Tuple[int, str]]:
        """
        List available audio input devices
        
        Returns:
            List of (device_index, device_name) tuples
        """
        devices = []
        for i in range(self.audio.get_device_count()):
            info = self.audio.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                devices.append((i, info['name']))
        return devices
    
    def start_capture(self, device_index: Optional[int] = None,
                     callback: Optional[Callable] = None):
        """
        Start audio capture
        
        Args:
            device_index: Audio device index (None for default)
            callback: Optional callback(frame_data) for each audio chunk
        """
        if self.is_capturing:
            self.stop_capture()
        
        self.config.device_index = device_index
        
        # Open audio stream
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=self.config.channels,
            rate=self.config.sample_rate,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=self.config.chunk_size,
            stream_callback=callback
        )
        
        self.stream.start_stream()
        self.is_capturing = True
        logger.info("Audio capture started")
    
    def stop_capture(self):
        """Stop audio capture"""
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        self.is_capturing = False
        logger.info("Audio capture stopped")
    
    def read_audio_chunk(self) -> Optional[np.ndarray]:
        """
        Read one chunk of audio data
        
        Returns:
            NumPy array of audio samples or None if not capturing
        """
        if not self.is_capturing or not self.stream:
            return None
        
        try:
            data = self.stream.read(self.config.chunk_size, exception_on_overflow=False)
            audio_data = np.frombuffer(data, dtype=np.int16)
            return audio_data.astype(np.float32) / 32768.0  # Normalize to [-1, 1]
        except Exception as e:
            logger.error(f"Error reading audio: {e}")
            return None
    
    def analyze_audio(self, audio_data: np.ndarray) -> Dict[str, Any]:
        """
        Analyze audio data using FFT
        
        Args:
            audio_data: Audio samples array
            
        Returns:
            Dictionary with frequency analysis results
        """
        # Apply window function to reduce spectral leakage
        window = np.hanning(len(audio_data))
        windowed = audio_data * window
        
        # Perform FFT
        fft_data = scipy.fft.fft(windowed, n=self.fft_size)
        fft_magnitude = np.abs(fft_data[:self.freq_bins])
        
        # Calculate frequency values
        freqs = np.fft.fftfreq(self.fft_size, 1.0 / self.config.sample_rate)[:self.freq_bins]
        
        # Calculate overall volume
        volume = np.sqrt(np.mean(audio_data ** 2))
        
        # Map frequencies to LED bands
        led_values = self._map_frequencies_to_leds(fft_magnitude, freqs)
        
        return {
            'fft_magnitude': fft_magnitude,
            'frequencies': freqs,
            'volume': volume,
            'led_values': led_values,
            'peak_frequency': freqs[np.argmax(fft_magnitude)] if len(fft_magnitude) > 0 else 0
        }
    
    def _map_frequencies_to_leds(self, fft_magnitude: np.ndarray, 
                                 freqs: np.ndarray) -> List[float]:
        """
        Map frequency spectrum to LED values
        
        Args:
            fft_magnitude: FFT magnitude array
            freqs: Frequency array
            
        Returns:
            List of LED intensity values (0.0-1.0)
        """
        led_values = []
        
        for start_freq, end_freq in self.freq_bands:
            # Find frequency indices in this band
            mask = (freqs >= start_freq) & (freqs < end_freq)
            if np.any(mask):
                # Average magnitude in this band
                band_magnitude = np.mean(fft_magnitude[mask])
                # Normalize to 0-1 range
                normalized = min(1.0, band_magnitude / 100.0)  # Adjust scaling as needed
                led_values.append(normalized)
            else:
                led_values.append(0.0)
        
        return led_values
    
    def generate_pattern_from_audio(self, duration_seconds: float = 10.0,
                                   fps: float = 30.0,
                                   visualization_mode: str = "frequency_bars") -> Pattern:
        """
        Generate pattern from audio input
        
        Args:
            duration_seconds: Duration to capture
            fps: Frames per second
            visualization_mode: Visualization mode
                - "frequency_bars": Vertical bars per frequency band
                - "spectrum": Full spectrum visualization
                - "volume_wave": Volume-based wave
                - "peak_tracker": Track frequency peaks
        
        Returns:
            Pattern object
        """
        frames = []
        frame_duration_ms = int(1000.0 / fps)
        total_frames = int(duration_seconds * fps)
        
        logger.info(f"Generating pattern from {duration_seconds}s of audio ({total_frames} frames)...")
        
        # Start capture
        self.start_capture()
        
        try:
            for frame_idx in range(total_frames):
                # Read audio chunk
                audio_data = self.read_audio_chunk()
                
                if audio_data is None:
                    # Generate empty frame if no audio
                    frame = Frame(
                        pixels=[(0, 0, 0)] * self.led_count,
                        duration_ms=frame_duration_ms
                    )
                    frames.append(frame)
                    continue
                
                # Analyze audio
                analysis = self.analyze_audio(audio_data)
                
                # Generate frame based on visualization mode
                pixels = self._generate_frame_pixels(analysis, visualization_mode)
                
                frame = Frame(
                    pixels=pixels,
                    duration_ms=frame_duration_ms
                )
                frames.append(frame)
                
                # Progress logging
                if (frame_idx + 1) % 30 == 0:
                    logger.info(f"Generated {frame_idx + 1}/{total_frames} frames...")
        
        finally:
            self.stop_capture()
        
        # Create pattern
        metadata = PatternMetadata(
            width=self.width,
            height=self.height,
            fps=fps
        )
        
        pattern = Pattern(
            name="Audio-Reactive Pattern",
            metadata=metadata,
            frames=frames
        )
        
        logger.info(f"Generated pattern: {len(frames)} frames")
        return pattern
    
    def _generate_frame_pixels(self, analysis: Dict, mode: str) -> List[Tuple[int, int, int]]:
        """
        Generate pixel colors from audio analysis
        
        Args:
            analysis: Audio analysis dictionary
            mode: Visualization mode
            
        Returns:
            List of (R, G, B) tuples
        """
        led_values = analysis['led_values']
        volume = analysis['volume']
        peak_freq = analysis['peak_frequency']
        
        pixels = []
        
        if mode == "frequency_bars":
            # Vertical bars: each LED represents a frequency band
            for i, intensity in enumerate(led_values):
                # Color based on frequency (hue) and intensity (brightness)
                hue = int((i / len(led_values)) * 360) % 360
                brightness = int(intensity * 255)
                
                # Convert HSV to RGB
                rgb = self._hsv_to_rgb(hue, 1.0, intensity)
                pixels.append(rgb)
        
        elif mode == "spectrum":
            # Full spectrum: map all LEDs to frequency spectrum
            fft_mag = analysis['fft_magnitude']
            for i in range(self.led_count):
                # Map LED index to frequency bin
                bin_idx = int((i / self.led_count) * len(fft_mag))
                if bin_idx < len(fft_mag):
                    intensity = min(1.0, fft_mag[bin_idx] / 100.0)
                    hue = int((i / self.led_count) * 360) % 360
                    rgb = self._hsv_to_rgb(hue, 1.0, intensity)
                    pixels.append(rgb)
                else:
                    pixels.append((0, 0, 0))
        
        elif mode == "volume_wave":
            # Volume-based wave: volume controls overall brightness
            base_color = (255, 100, 0)  # Orange
            volume_scale = min(1.0, volume * 10.0)  # Scale volume
        
            for i in range(self.led_count):
                # Create wave pattern
                wave_pos = (i / self.led_count) * 2 * np.pi
                wave_intensity = (np.sin(wave_pos) + 1) / 2
                brightness = int(wave_intensity * volume_scale * 255)
                
                r = int(base_color[0] * brightness / 255)
                g = int(base_color[1] * brightness / 255)
                b = int(base_color[2] * brightness / 255)
                pixels.append((r, g, b))
        
        elif mode == "peak_tracker":
            # Track frequency peaks
            peak_bin = int((peak_freq / (self.config.sample_rate / 2)) * len(led_values))
            peak_bin = max(0, min(len(led_values) - 1, peak_bin))
            
            for i in range(self.led_count):
                distance = abs(i - peak_bin)
                intensity = max(0.0, 1.0 - (distance / (self.led_count / 2)))
                hue = int((peak_bin / len(led_values)) * 360) % 360
                rgb = self._hsv_to_rgb(hue, 1.0, intensity)
                pixels.append(rgb)
        
        else:
            # Default: simple intensity mapping
            for intensity in led_values:
                brightness = int(intensity * 255)
                pixels.append((brightness, brightness, brightness))
        
        return pixels
    
    def _hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[int, int, int]:
        """
        Convert HSV to RGB
        
        Args:
            h: Hue (0-360)
            s: Saturation (0-1)
            v: Value/Brightness (0-1)
            
        Returns:
            (R, G, B) tuple
        """
        h = h / 360.0
        c = v * s
        x = c * (1 - abs((h * 6) % 2 - 1))
        m = v - c
        
        if h < 1/6:
            r, g, b = c, x, 0
        elif h < 2/6:
            r, g, b = x, c, 0
        elif h < 3/6:
            r, g, b = 0, c, x
        elif h < 4/6:
            r, g, b = 0, x, c
        elif h < 5/6:
            r, g, b = x, 0, c
        else:
            r, g, b = c, 0, x
        
        r = int((r + m) * 255)
        g = int((g + m) * 255)
        b = int((b + m) * 255)
        
        return (r, g, b)
    
    def cleanup(self):
        """Cleanup resources"""
        self.stop_capture()
        if self.audio:
            self.audio.terminate()

