#!/usr/bin/env python3
"""
Capture Hardware Output - Captures output from connected hardware

This script is used by CI/CD workflows to capture hardware output for verification.
"""

import argparse
import sys
import serial
import time
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description='Capture hardware output')
    parser.add_argument('--chip', required=True, help='Chip identifier')
    parser.add_argument('--port', required=True, help='Serial port')
    parser.add_argument('--output', required=True, type=Path, help='Output log file')
    parser.add_argument('--duration', type=int, default=5, help='Capture duration in seconds')
    
    args = parser.parse_args()
    
    try:
        # Open serial port
        ser = serial.Serial(args.port, 115200, timeout=1)
        
        # Capture output
        output_lines = []
        start_time = time.time()
        
        print(f"Capturing output from {args.port} for {args.duration} seconds...")
        
        while time.time() - start_time < args.duration:
            if ser.in_waiting:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    output_lines.append(line)
                    print(line)
            time.sleep(0.1)
        
        ser.close()
        
        # Write output
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, 'w') as f:
            f.write('\n'.join(output_lines))
        
        print(f"SUCCESS: Captured {len(output_lines)} lines to {args.output}")
        sys.exit(0)
        
    except serial.SerialException as e:
        print(f"ERROR: Serial port error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

