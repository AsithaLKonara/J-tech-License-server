#!/usr/bin/env python3
"""
Create Professional GUI Installer for Upload Bridge
Includes requirements installation, progress bars, and auto-launch
"""

import os
import shutil
import zipfile
import subprocess
import sys
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time

class UploadBridgeInstaller:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("J Tech Pixel Upload Bridge - Installer")
        self.root.geometry("800x600")
        self.root.resizable(False, False)
        
        # Center the window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (800 // 2)
        y = (self.root.winfo_screenheight() // 2) - (600 // 2)
        self.root.geometry(f"800x600+{x}+{y}")
        
        # Set icon (if available)
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass
        
        self.setup_ui()
        self.installation_path = None
        self.installation_complete = False
        
    def setup_ui(self):
        """Setup the installer GUI"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        title_label = ttk.Label(header_frame, text="J Tech Pixel Upload Bridge", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        subtitle_label = ttk.Label(header_frame, text="Universal LED Matrix Firmware Uploader", 
                                  font=("Arial", 10))
        subtitle_label.grid(row=1, column=0, sticky=tk.W)
        
        # Installation path selection
        path_frame = ttk.LabelFrame(main_frame, text="Installation Directory", padding="10")
        path_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        self.path_var = tk.StringVar(value=r"C:\Program Files\J Tech Pixel Upload Bridge")
        path_entry = ttk.Entry(path_frame, textvariable=self.path_var, width=50)
        path_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        browse_btn = ttk.Button(path_frame, text="Browse...", command=self.browse_directory)
        browse_btn.grid(row=0, column=1)
        
        # Features selection
        features_frame = ttk.LabelFrame(main_frame, text="Installation Features", padding="10")
        features_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        self.install_python_var = tk.BooleanVar(value=True)
        self.install_esp_tools_var = tk.BooleanVar(value=True)
        self.install_avr_tools_var = tk.BooleanVar(value=True)
        self.install_stm32_tools_var = tk.BooleanVar(value=True)
        self.create_desktop_shortcut_var = tk.BooleanVar(value=True)
        self.auto_launch_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(features_frame, text="Install Python dependencies", 
                       variable=self.install_python_var).grid(row=0, column=0, sticky=tk.W)
        ttk.Checkbutton(features_frame, text="Install ESP chip tools (Arduino CLI + esptool)", 
                       variable=self.install_esp_tools_var).grid(row=1, column=0, sticky=tk.W)
        ttk.Checkbutton(features_frame, text="Install AVR chip tools (AVR-GCC + avrdude)", 
                       variable=self.install_avr_tools_var).grid(row=2, column=0, sticky=tk.W)
        ttk.Checkbutton(features_frame, text="Install STM32 chip tools (ARM GCC + stm32flash)", 
                       variable=self.install_stm32_tools_var).grid(row=3, column=0, sticky=tk.W)
        ttk.Checkbutton(features_frame, text="Create desktop shortcut", 
                       variable=self.create_desktop_shortcut_var).grid(row=4, column=0, sticky=tk.W)
        ttk.Checkbutton(features_frame, text="Launch application after installation", 
                       variable=self.auto_launch_var).grid(row=5, column=0, sticky=tk.W)
        
        # Progress section
        progress_frame = ttk.LabelFrame(main_frame, text="Installation Progress", padding="10")
        progress_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, 
                                          maximum=100, length=400)
        self.progress_bar.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_var = tk.StringVar(value="Ready to install")
        self.status_label = ttk.Label(progress_frame, textvariable=self.status_var)
        self.status_label.grid(row=1, column=0, sticky=tk.W)
        
        # Log area
        log_frame = ttk.LabelFrame(main_frame, text="Installation Log", padding="10")
        log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 20))
        
        self.log_text = tk.Text(log_frame, height=8, width=70, wrap=tk.WORD)
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        self.install_btn = ttk.Button(button_frame, text="Install", command=self.start_installation)
        self.install_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.root.quit)
        self.cancel_btn.grid(row=0, column=1)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(4, weight=1)
        path_frame.columnconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
    def browse_directory(self):
        """Browse for installation directory"""
        directory = filedialog.askdirectory(
            title="Select Installation Directory",
            initialdir="C:\\Program Files"
        )
        if directory:
            self.path_var.set(os.path.join(directory, "J Tech Pixel Upload Bridge"))
    
    def log_message(self, message):
        """Add message to log"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def update_progress(self, value, status=""):
        """Update progress bar and status"""
        self.progress_var.set(value)
        if status:
            self.status_var.set(status)
        self.root.update()
    
    def start_installation(self):
        """Start installation in separate thread"""
        self.installation_path = self.path_var.get()
        
        # Disable install button
        self.install_btn.config(state="disabled")
        self.cancel_btn.config(text="Close", command=self.root.quit)
        
        # Start installation thread
        thread = threading.Thread(target=self.run_installation)
        thread.daemon = True
        thread.start()
    
    def run_installation(self):
        """Run the actual installation"""
        try:
            self.log_message("🚀 Starting J Tech Pixel Upload Bridge Installation")
            self.log_message("=" * 60)
            
            # Step 1: Create installation directory
            self.update_progress(5, "Creating installation directory...")
            self.log_message("📁 Creating installation directory...")
            install_dir = Path(self.installation_path)
            install_dir.mkdir(parents=True, exist_ok=True)
            self.log_message(f"   ✅ Directory created: {install_dir}")
            
            # Step 2: Copy application files
            self.update_progress(15, "Copying application files...")
            self.log_message("📦 Copying application files...")
            self.copy_application_files(install_dir)
            
            # Step 3: Install Python dependencies
            if self.install_python_var.get():
                self.update_progress(25, "Installing Python dependencies...")
                self.log_message("🐍 Installing Python dependencies...")
                self.install_python_dependencies(install_dir)
            
            # Step 4: Install ESP tools
            if self.install_esp_tools_var.get():
                self.update_progress(40, "Installing ESP chip tools...")
                self.log_message("🔧 Installing ESP chip tools...")
                self.install_esp_tools(install_dir)
            
            # Step 5: Install AVR tools
            if self.install_avr_tools_var.get():
                self.update_progress(55, "Installing AVR chip tools...")
                self.log_message("🔧 Installing AVR chip tools...")
                self.install_avr_tools(install_dir)
            
            # Step 6: Install STM32 tools
            if self.install_stm32_tools_var.get():
                self.update_progress(70, "Installing STM32 chip tools...")
                self.log_message("🔧 Installing STM32 chip tools...")
                self.install_stm32_tools(install_dir)
            
            # Step 7: Create desktop shortcut
            if self.create_desktop_shortcut_var.get():
                self.update_progress(85, "Creating desktop shortcut...")
                self.log_message("🔗 Creating desktop shortcut...")
                self.create_desktop_shortcut(install_dir)
            
            # Step 8: Finalize installation
            self.update_progress(95, "Finalizing installation...")
            self.log_message("✨ Finalizing installation...")
            self.finalize_installation(install_dir)
            
            # Step 9: Complete
            self.update_progress(100, "Installation complete!")
            self.log_message("🎉 Installation completed successfully!")
            self.log_message("=" * 60)
            self.log_message("J Tech Pixel Upload Bridge is ready to use!")
            
            self.installation_complete = True
            
            # Auto-launch if requested
            if self.auto_launch_var.get():
                self.log_message("🚀 Launching application...")
                self.launch_application(install_dir)
            
            # Show completion message
            messagebox.showinfo("Installation Complete", 
                              "J Tech Pixel Upload Bridge has been successfully installed!\n\n"
                              f"Installation directory: {install_dir}\n\n"
                              "The application is ready to use.")
            
        except Exception as e:
            self.log_message(f"❌ Installation failed: {str(e)}")
            self.update_progress(0, "Installation failed")
            messagebox.showerror("Installation Failed", f"Installation failed:\n{str(e)}")
    
    def copy_application_files(self, install_dir):
        """Copy all application files to installation directory"""
        source_dir = Path(__file__).parent
        
        # Files and directories to copy
        items_to_copy = [
            "main.py", "requirements.txt", "README.md", "setup.py",
            "ui/", "core/", "uploaders/", "parsers/", "firmware/", "config/", "build/"
        ]
        
        for item in items_to_copy:
            source_path = source_dir / item
            if source_path.exists():
                dest_path = install_dir / item
                if source_path.is_file():
                    shutil.copy2(source_path, dest_path)
                    self.log_message(f"   ✅ Copied: {item}")
                elif source_path.is_dir():
                    shutil.copytree(source_path, dest_path, dirs_exist_ok=True)
                    self.log_message(f"   ✅ Copied: {item}/")
    
    def install_python_dependencies(self, install_dir):
        """Install Python dependencies"""
        try:
            # Change to installation directory
            os.chdir(install_dir)
            
            # Install requirements
            result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                                 capture_output=True, text=True, cwd=install_dir)
            
            if result.returncode == 0:
                self.log_message("   ✅ Python dependencies installed successfully")
            else:
                self.log_message(f"   ⚠️  Python dependencies installation had warnings: {result.stderr}")
                
        except Exception as e:
            self.log_message(f"   ❌ Failed to install Python dependencies: {e}")
    
    def install_esp_tools(self, install_dir):
        """Install ESP chip tools"""
        try:
            # Install esptool
            result = subprocess.run([sys.executable, "-m", "pip", "install", "esptool"], 
                                 capture_output=True, text=True)
            if result.returncode == 0:
                self.log_message("   ✅ esptool installed")
            else:
                self.log_message("   ⚠️  esptool installation failed")
            
            # Download Arduino CLI
            self.log_message("   📥 Downloading Arduino CLI...")
            try:
                import urllib.request
                urllib.request.urlretrieve(
                    "https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_Windows_64bit.zip",
                    install_dir / "arduino-cli.zip"
                )
                
                # Extract Arduino CLI
                import zipfile
                with zipfile.ZipFile(install_dir / "arduino-cli.zip", 'r') as zip_ref:
                    zip_ref.extractall(install_dir / "arduino-cli")
                
                self.log_message("   ✅ Arduino CLI downloaded and extracted")
                
                # Install ESP cores
                arduino_cli = install_dir / "arduino-cli" / "arduino-cli.exe"
                if arduino_cli.exists():
                    subprocess.run([str(arduino_cli), "core", "install", "esp8266:esp8266"], 
                                 capture_output=True)
                    subprocess.run([str(arduino_cli), "core", "install", "esp32:esp32"], 
                                 capture_output=True)
                    self.log_message("   ✅ ESP cores installed")
                
            except Exception as e:
                self.log_message(f"   ⚠️  Arduino CLI installation failed: {e}")
                
        except Exception as e:
            self.log_message(f"   ❌ ESP tools installation failed: {e}")
    
    def install_avr_tools(self, install_dir):
        """Install AVR chip tools"""
        try:
            # Download AVR-GCC
            self.log_message("   📥 Downloading AVR-GCC...")
            try:
                import urllib.request
                urllib.request.urlretrieve(
                    "https://github.com/ZakKemble/AVR-GCC/releases/download/v13.2.0/avr-gcc-13.2.0-x64-windows.zip",
                    install_dir / "avr-gcc.zip"
                )
                
                # Extract AVR-GCC
                import zipfile
                with zipfile.ZipFile(install_dir / "avr-gcc.zip", 'r') as zip_ref:
                    zip_ref.extractall(install_dir / "avr-gcc")
                
                self.log_message("   ✅ AVR-GCC downloaded and extracted")
                
            except Exception as e:
                self.log_message(f"   ⚠️  AVR-GCC download failed: {e}")
                
        except Exception as e:
            self.log_message(f"   ❌ AVR tools installation failed: {e}")
    
    def install_stm32_tools(self, install_dir):
        """Install STM32 chip tools"""
        try:
            # Install stm32flash
            result = subprocess.run([sys.executable, "-m", "pip", "install", "stm32flash"], 
                                 capture_output=True, text=True)
            if result.returncode == 0:
                self.log_message("   ✅ stm32flash installed")
            else:
                self.log_message("   ⚠️  stm32flash installation failed")
            
            # Download ARM GCC
            self.log_message("   📥 Downloading ARM GCC...")
            try:
                import urllib.request
                urllib.request.urlretrieve(
                    "https://developer.arm.com/-/media/Files/downloads/gnu-rm/10.3-2021.10/gcc-arm-none-eabi-10.3-2021.10-win32.zip",
                    install_dir / "arm-gcc.zip"
                )
                
                # Extract ARM GCC
                import zipfile
                with zipfile.ZipFile(install_dir / "arm-gcc.zip", 'r') as zip_ref:
                    zip_ref.extractall(install_dir / "arm-gcc")
                
                self.log_message("   ✅ ARM GCC downloaded and extracted")
                
            except Exception as e:
                self.log_message(f"   ⚠️  ARM GCC download failed: {e}")
                
        except Exception as e:
            self.log_message(f"   ❌ STM32 tools installation failed: {e}")
    
    def create_desktop_shortcut(self, install_dir):
        """Create desktop shortcut"""
        try:
            desktop = Path.home() / "Desktop"
            shortcut_path = desktop / "J Tech Pixel Upload Bridge.url"
            
            with open(shortcut_path, 'w') as f:
                f.write("[InternetShortcut]\n")
                f.write(f"URL=file:///{install_dir / 'main.py'}\n")
                f.write(f"IconFile={install_dir / 'main.py'}\n")
                f.write("IconIndex=0\n")
            
            self.log_message(f"   ✅ Desktop shortcut created: {shortcut_path}")
            
        except Exception as e:
            self.log_message(f"   ❌ Failed to create desktop shortcut: {e}")
    
    def finalize_installation(self, install_dir):
        """Finalize installation"""
        # Create launcher script
        launcher_path = install_dir / "Launch Upload Bridge.bat"
        with open(launcher_path, 'w') as f:
            f.write(f"""@echo off
title J Tech Pixel Upload Bridge
cd /d "{install_dir}"
python main.py
pause
""")
        
        self.log_message(f"   ✅ Launcher script created: {launcher_path}")
    
    def launch_application(self, install_dir):
        """Launch the application"""
        try:
            launcher_path = install_dir / "Launch Upload Bridge.bat"
            subprocess.Popen([str(launcher_path)], cwd=install_dir)
            self.log_message("   ✅ Application launched successfully")
        except Exception as e:
            self.log_message(f"   ❌ Failed to launch application: {e}")
    
    def run(self):
        """Run the installer"""
        self.root.mainloop()

def create_installer():
    """Create the installer application"""
    installer = UploadBridgeInstaller()
    installer.run()

if __name__ == "__main__":
    create_installer()











