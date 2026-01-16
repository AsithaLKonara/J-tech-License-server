#!/usr/bin/env python3
"""
ESP8266 Pattern Flasher with WiFi Upload - Launcher Script
Quick launcher for the enhanced version with WiFi capabilities
"""

import sys
import os
import logging

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from main_wifi import main
    
    if __name__ == "__main__":
        logger = logging.getLogger(__name__)
        logger.info("ESP8266 Pattern Flasher with WiFi Upload")
        logger.info("Starting enhanced GUI application with WiFi features")
        
        main()
        
except ImportError as e:
    logging.getLogger(__name__).error("Import Error: %s", e)
    logging.getLogger(__name__).error("Please install required dependencies: pip install -r requirements.txt")
    logging.getLogger(__name__).info("Or run the original version: python main.py")
    
except Exception as e:
    logging.getLogger(__name__).error("Error: %s", e)
    logging.getLogger(__name__).info("Falling back to original version...")
    try:
        from main import main as original_main
        original_main()
    except Exception as e2:
        logging.getLogger(__name__).error("Fallback failed: %s", e2)

