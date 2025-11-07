"""
Intel HEX Parser - Parses Intel HEX format
Real implementation
"""

from typing import Optional
import sys
sys.path.insert(0, str(__file__ + "/../../.."))

from core.pattern import Pattern, Frame, PatternMetadata
from .base_parser import ParserBase


class IntelHexParser(ParserBase):
    """
    Parser for Intel HEX format
    
    Format:
    -------
    ASCII text format with records like:
    :10010000214601360121470136007EFE09D2190140
    
    Record format:
    :LLAAAATTHHHH...HHCC
    
    LL = Byte count
    AAAA = Address
    TT = Record type
    HH...HH = Data
    CC = Checksum
    """
    
    def get_format_name(self) -> str:
        return "Intel HEX Format"
    
    def get_format_description(self) -> str:
        return "Intel HEX file format (.hex) - ASCII text-based"
    
    def detect(self, data: bytes, filename: str = "",
               suggested_leds: Optional[int] = None,
               suggested_frames: Optional[int] = None) -> bool:
        """Detect if data is Intel HEX format"""
        
        try:
            # Try to decode as ASCII
            text = data.decode('ascii', errors='ignore')
            lines = text.split('\n')
            
            # Must have multiple lines
            if len(lines) < 2:
                return False
            
            # First line should start with ':'
            first_line = lines[0].strip()
            if not first_line.startswith(':'):
                return False
            
            # Check if looks like hex records
            hex_char_count = sum(1 for c in first_line[1:] if c in '0123456789ABCDEFabcdef')
            if hex_char_count < 10:
                return False
            
            # Check filename
            if filename.lower().endswith('.hex'):
                return True
            
            # Check multiple lines start with ':'
            colon_lines = sum(1 for line in lines[:10] if line.strip().startswith(':'))
            if colon_lines >= 3:
                return True
        
        except:
            pass
        
        return False
    
    def get_confidence(self, data: bytes) -> float:
        """Calculate confidence for HEX detection"""
        if not self.detect(data, ""):
            return 0.0
        
        try:
            text = data.decode('ascii', errors='ignore')
            lines = text.split('\n')
            
            # Check how many lines are valid HEX records
            valid_lines = 0
            total_lines = min(len(lines), 20)
            
            for line in lines[:total_lines]:
                line = line.strip()
                if line and line.startswith(':') and len(line) >= 11:
                    # Check if all hex characters after ':'
                    hex_part = line[1:]
                    if all(c in '0123456789ABCDEFabcdef' for c in hex_part):
                        valid_lines += 1
            
            # Higher proportion of valid lines = higher confidence
            if valid_lines >= 10:
                return 0.9
            elif valid_lines >= 5:
                return 0.7
            elif valid_lines >= 2:
                return 0.5
            else:
                return 0.3
        
        except:
            return 0.0
    
    def parse(self, data: bytes,
              suggested_leds: Optional[int] = None,
              suggested_frames: Optional[int] = None) -> Pattern:
        """Parse Intel HEX into Pattern"""
        
        try:
            text = data.decode('ascii')
        except:
            raise ValueError("File is not valid ASCII text")
        
        lines = text.split('\n')
        
        # Parse HEX records and extract binary data
        binary_data = bytearray()
        
        for line in lines:
            line = line.strip()
            if not line or not line.startswith(':'):
                continue
            
            try:
                # Parse record
                record = line[1:]  # Remove ':'
                
                byte_count = int(record[0:2], 16)
                address = int(record[2:6], 16)
                record_type = int(record[6:8], 16)
                
                # Type 00 = Data record
                if record_type == 0x00:
                    # Extract data bytes
                    for i in range(byte_count):
                        byte_offset = 8 + i * 2
                        byte_value = int(record[byte_offset:byte_offset+2], 16)
                        binary_data.append(byte_value)
                
                # Type 01 = End of file
                elif record_type == 0x01:
                    break
            
            except:
                # Skip malformed lines
                continue
        
        if not binary_data:
            raise ValueError("No valid data found in HEX file")
        
        # Now parse the binary data
        # Try standard format first
        if len(binary_data) >= 4:
            try:
                # Import here to avoid circular dependency
                from .standard_format_parser import StandardFormatParser
                
                parser = StandardFormatParser()
                if parser.detect(bytes(binary_data), ""):
                    return parser.parse(bytes(binary_data))
            except:
                pass
        
        # Fall back to raw RGB
        from .raw_rgb_parser import RawRgbParser
        
        parser = RawRgbParser()
        return parser.parse(bytes(binary_data), suggested_leds, suggested_frames)

