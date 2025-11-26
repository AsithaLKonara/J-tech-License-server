"""
AI Pattern Generation Dialog - UI for prompt-based pattern generation using Cloudie CLI
"""

from __future__ import annotations

import logging
from typing import Optional, Tuple
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTextEdit,
    QPushButton,
    QSpinBox,
    QComboBox,
    QGroupBox,
    QFormLayout,
    QMessageBox,
    QProgressBar,
    QCheckBox,
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer

from core.pattern import Pattern
from core.ai_pattern_generator import (
    AIGenerationConfig,
    CloudieCLIInterface,
    FallbackAIGenerator,
)

logger = logging.getLogger(__name__)


class AIGenerationWorker(QThread):
    """Worker thread for AI pattern generation"""
    
    progress_updated = Signal(int, str)  # progress (0-100), status message
    generation_complete = Signal(Pattern)  # Generated pattern
    generation_failed = Signal(str)  # Error message
    
    def __init__(self, config: AIGenerationConfig, use_cli: bool = True):
        super().__init__()
        self.config = config
        self.use_cli = use_cli
        self._cancelled = False
    
    def run(self):
        """Execute AI generation"""
        try:
            self.progress_updated.emit(10, "Initializing AI generator...")
            
            if self.use_cli:
                try:
                    # Try Cloudie CLI
                    cli = CloudieCLIInterface()
                    self.progress_updated.emit(30, "Generating pattern with Cloudie CLI...")
                    
                    ai_output = cli.generate_pattern(self.config)
                    self.progress_updated.emit(70, "Converting to pattern format...")
                    
                    pattern = cli.convert_to_pattern(ai_output)
                    self.progress_updated.emit(100, "Generation complete!")
                    
                    self.generation_complete.emit(pattern)
                    return
                
                except RuntimeError as e:
                    logger.warning(f"Cloudie CLI failed: {e}, falling back to rule-based generator")
                    # Fall through to fallback generator
            
            # Fallback: rule-based generator
            self.progress_updated.emit(50, "Generating pattern (rule-based)...")
            pattern = FallbackAIGenerator.generate_from_prompt(self.config)
            self.progress_updated.emit(100, "Generation complete!")
            
            self.generation_complete.emit(pattern)
        
        except Exception as e:
            logger.error(f"AI generation failed: {e}", exc_info=True)
            self.generation_failed.emit(str(e))
    
    def cancel(self):
        """Cancel generation"""
        self._cancelled = True


class AIGenerateDialog(QDialog):
    """Dialog for AI-powered pattern generation"""
    
    pattern_generated = Signal(Pattern)  # Emitted when pattern is generated
    
    def __init__(self, parent=None, current_width: int = 16, current_height: int = 16):
        super().__init__(parent)
        self.setWindowTitle("AI Pattern Generator")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        self.current_width = current_width
        self.current_height = current_height
        self.worker: Optional[AIGenerationWorker] = None
        
        self._setup_ui()
        self._check_cli_availability()
    
    def _setup_ui(self):
        """Setup UI components"""
        layout = QVBoxLayout(self)
        
        # Prompt input
        prompt_group = QGroupBox("Prompt")
        prompt_layout = QVBoxLayout()
        
        self.prompt_edit = QTextEdit()
        self.prompt_edit.setPlaceholderText(
            "Describe the pattern you want to create...\n\n"
            "Examples:\n"
            "- Scrolling text: 'Hello World'\n"
            "- Bouncing ball animation\n"
            "- Fire effect\n"
            "- Rain animation\n"
            "- Gradient wave"
        )
        self.prompt_edit.setMaximumHeight(120)
        prompt_layout.addWidget(self.prompt_edit)
        
        prompt_group.setLayout(prompt_layout)
        layout.addWidget(prompt_group)
        
        # Configuration
        config_group = QGroupBox("Configuration")
        config_layout = QFormLayout()
        
        # Matrix size
        size_layout = QHBoxLayout()
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 256)
        self.width_spin.setValue(self.current_width)
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 256)
        self.height_spin.setValue(self.current_height)
        size_layout.addWidget(QLabel("Width:"))
        size_layout.addWidget(self.width_spin)
        size_layout.addWidget(QLabel("Height:"))
        size_layout.addWidget(self.height_spin)
        size_layout.addStretch()
        config_layout.addRow("Matrix Size:", size_layout)
        
        # Frames
        self.frames_spin = QSpinBox()
        self.frames_spin.setRange(1, 1000)
        self.frames_spin.setValue(10)
        config_layout.addRow("Frames:", self.frames_spin)
        
        # Style
        self.style_combo = QComboBox()
        self.style_combo.addItems(["animated", "static", "scrolling", "effect"])
        config_layout.addRow("Style:", self.style_combo)
        
        # Duration
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(10, 10000)
        self.duration_spin.setValue(100)
        self.duration_spin.setSuffix(" ms")
        config_layout.addRow("Frame Duration:", self.duration_spin)
        
        # Use CLI checkbox
        self.use_cli_checkbox = QCheckBox("Use Cloudie CLI (if available)")
        self.use_cli_checkbox.setChecked(True)
        config_layout.addRow("", self.use_cli_checkbox)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Status and progress
        status_group = QGroupBox("Status")
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("Ready to generate")
        status_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        status_layout.addWidget(self.progress_bar)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("Generate Pattern")
        self.generate_btn.clicked.connect(self._on_generate)
        button_layout.addWidget(self.generate_btn)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self._on_cancel)
        self.cancel_btn.setEnabled(False)
        button_layout.addWidget(self.cancel_btn)
        
        button_layout.addStretch()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
    
    def _check_cli_availability(self):
        """Check if Cloudie CLI is available"""
        try:
            cli = CloudieCLIInterface()
            self.status_label.setText("✓ Cloudie CLI detected and ready")
            self.use_cli_checkbox.setEnabled(True)
        except RuntimeError:
            self.status_label.setText("⚠ Cloudie CLI not found - will use rule-based generator")
            self.use_cli_checkbox.setChecked(False)
            self.use_cli_checkbox.setEnabled(False)
    
    def _on_generate(self):
        """Start pattern generation"""
        prompt = self.prompt_edit.toPlainText().strip()
        if not prompt:
            QMessageBox.warning(self, "No Prompt", "Please enter a prompt describing the pattern you want to create.")
            return
        
        # Create config
        config = AIGenerationConfig(
            prompt=prompt,
            width=self.width_spin.value(),
            height=self.height_spin.value(),
            frames=self.frames_spin.value(),
            style=self.style_combo.currentText(),
            duration_ms=self.duration_spin.value(),
        )
        
        # Disable controls
        self.generate_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.prompt_edit.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_label.setText("Generating pattern...")
        
        # Start worker
        self.worker = AIGenerationWorker(
            config,
            use_cli=self.use_cli_checkbox.isChecked()
        )
        self.worker.progress_updated.connect(self._on_progress_updated)
        self.worker.generation_complete.connect(self._on_generation_complete)
        self.worker.generation_failed.connect(self._on_generation_failed)
        self.worker.start()
    
    def _on_cancel(self):
        """Cancel generation"""
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait()
            self.status_label.setText("Generation cancelled")
            self._reset_ui()
    
    def _on_progress_updated(self, progress: int, message: str):
        """Update progress"""
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)
    
    def _on_generation_complete(self, pattern: Pattern):
        """Handle successful generation"""
        self.status_label.setText("✓ Pattern generated successfully!")
        self.progress_bar.setValue(100)
        
        # Emit signal
        self.pattern_generated.emit(pattern)
        
        # Show success message
        QMessageBox.information(
            self,
            "Generation Complete",
            f"Pattern generated successfully!\n\n"
            f"Name: {pattern.name}\n"
            f"Size: {pattern.metadata.width}×{pattern.metadata.height}\n"
            f"Frames: {len(pattern.frames)}"
        )
        
        self._reset_ui()
        self.accept()  # Close dialog
    
    def _on_generation_failed(self, error: str):
        """Handle generation failure"""
        self.status_label.setText(f"✗ Generation failed: {error}")
        self.progress_bar.setValue(0)
        
        QMessageBox.critical(
            self,
            "Generation Failed",
            f"Failed to generate pattern:\n\n{error}"
        )
        
        self._reset_ui()
    
    def _reset_ui(self):
        """Reset UI to initial state"""
        self.generate_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.prompt_edit.setEnabled(True)
        self.worker = None

