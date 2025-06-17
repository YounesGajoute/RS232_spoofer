"""
Protocol parsing module for RS232 Spoofer
Supports Modbus RTU/ASCII, NMEA, and custom protocols
"""

import struct
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

class ProtocolType(Enum):
    RAW = "Raw"
    MODBUS_RTU = "Modbus RTU"
    MODBUS_ASCII = "Modbus ASCII"
    NMEA = "NMEA 0183"
    ASCII_DELIMITED = "ASCII Delimited"
    CUSTOM_BINARY = "Custom Binary"

class ParsedMessage:
    def __init__(self, protocol: ProtocolType, raw_data: bytes, timestamp: datetime = None):
        self.protocol = protocol
        self.raw_data = raw_data
        self.timestamp = timestamp or datetime.now()
        self.parsed_data = {}
        self.is_valid = False
        self.error_message = ""
        self.description = ""

class ProtocolParser:
    def __init__(self):
        self.parsers = {
            ProtocolType.MODBUS_RTU: self._parse_modbus_rtu,
            ProtocolType.MODBUS_ASCII: self._parse_modbus_ascii,
            ProtocolType.NMEA: self._parse_nmea,
            ProtocolType.ASCII_DELIMITED: self._parse_ascii_delimited,
            ProtocolType.CUSTOM_BINARY: self._parse_custom_binary,
            ProtocolType.RAW: self._parse_raw
        }
        
        # Protocol detection patterns
        self.detection_patterns = {
            ProtocolType.MODBUS_ASCII: re.compile(rb'^:[0-9A-Fa-f]+\r\n$'),
            ProtocolType.NMEA: re.compile(rb'^\$[A-Z]{2}[A-Z0-9]{3},[^*]*\*[0-9A-Fa-f]{2}\r\n$'),
        }

    def auto_detect_protocol(self, data: bytes) -> ProtocolType:
        """Auto-detect protocol based on data patterns"""
        # Check ASCII-based protocols first
        for protocol, pattern in self.detection_patterns.items():
            if pattern.match(data):
                return protocol
        
        # Check Modbus RTU (binary, minimum 4 bytes)
        if len(data) >= 4 and self._is_likely_modbus_rtu(data):
            return ProtocolType.MODBUS_RTU
        
        # Check if it's printable ASCII
        try:
            data.decode('ascii')
            if b',' in data or b';' in data or b'|' in data:
                return ProtocolType.ASCII_DELIMITED
        except UnicodeDecodeError:
            pass
        
        # Default to raw
        return ProtocolType.RAW

    def parse_message(self, data: bytes, protocol: ProtocolType = None) -> ParsedMessage:
        """Parse message according to specified or auto-detected protocol"""
        if protocol is None:
            protocol = self.auto_detect_protocol(data)
        
        message = ParsedMessage(protocol, data)
        
        try:
            parser = self.parsers.get(protocol, self._parse_raw)
            parser(message)
        except Exception as e:
            message.error_message = str(e)
            message.is_valid = False
        
        return message

    def _is_likely_modbus_rtu(self, data: bytes) -> bool:
        """Check if data looks like Modbus RTU"""
        if len(data) < 4:
            return False
        
        # Check if first byte is valid slave address (1-247)
        slave_addr = data[0]
        if slave_addr == 0 or slave_addr > 247:
            return False
        
        # Check if second byte is valid function code
        func_code = data[1]
        valid_func_codes = [1, 2, 3, 4, 5, 6, 15, 16, 23]
        if func_code not in valid_func_codes:
            return False
        
        return True

    def _parse_modbus_rtu(self, message: ParsedMessage):
        """Parse Modbus RTU message"""
        data = message.raw_data
        if len(data) < 4:
            message.error_message = "Message too short for Modbus RTU"
            return
        
        slave_addr = data[0]
        func_code = data[1]
        
        # Calculate and verify CRC
        msg_data = data[:-2]
        received_crc = struct.unpack('<H', data[-2:])[0]
        calculated_crc = self._calculate_modbus_crc(msg_data)
        
        message.is_valid = (received_crc == calculated_crc)
        
        message.parsed_data = {
            'slave_address': slave_addr,
            'function_code': func_code,
            'function_name': self._get_modbus_function_name(func_code),
            'data_length': len(data) - 4,
            'crc_received': f"0x{received_crc:04X}",
            'crc_calculated': f"0x{calculated_crc:04X}",
            'crc_valid': message.is_valid
        }
        
        # Parse function-specific data
        if func_code in [3, 4]:  # Read Holding/Input Registers
            if len(data) >= 6:
                start_addr = struct.unpack('>H', data[2:4])[0]
                num_regs = struct.unpack('>H', data[4:6])[0]
                message.parsed_data.update({
                    'start_address': start_addr,
                    'register_count': num_regs
                })
        elif func_code in [1, 2]:  # Read Coils/Discrete Inputs
            if len(data) >= 6:
                start_addr = struct.unpack('>H', data[2:4])[0]
                num_coils = struct.unpack('>H', data[4:6])[0]
                message.parsed_data.update({
                    'start_address': start_addr,
                    'coil_count': num_coils
                })
        
        message.description = f"Modbus RTU - Slave {slave_addr}, {message.parsed_data['function_name']}"

    def _parse_modbus_ascii(self, message: ParsedMessage):
        """Parse Modbus ASCII message"""
        data = message.raw_data
        
        try:
            # Remove start/end characters and convert from ASCII hex
            if not (data.startswith(b':') and data.endswith(b'\r\n')):
                message.error_message = "Invalid Modbus ASCII frame"
                return
            
            hex_data = data[1:-2].decode('ascii')
            if len(hex_data) % 2 != 0:
                message.error_message = "Invalid hex data length"
                return
            
            # Convert hex string to bytes
            binary_data = bytes.fromhex(hex_data)
            
            if len(binary_data) < 3:
                message.error_message = "Message too short"
                return
            
            slave_addr = binary_data[0]
            func_code = binary_data[1]
            lrc_received = binary_data[-1]
            msg_data = binary_data[:-1]
            
            # Calculate and verify LRC
            calculated_lrc = self._calculate_modbus_lrc(msg_data)
            message.is_valid = (lrc_received == calculated_lrc)
            
            message.parsed_data = {
                'slave_address': slave_addr,
                'function_code': func_code,
                'function_name': self._get_modbus_function_name(func_code),
                'lrc_received': f"0x{lrc_received:02X}",
                'lrc_calculated': f"0x{calculated_lrc:02X}",
                'lrc_valid': message.is_valid,
                'hex_data': hex_data
            }
            
            message.description = f"Modbus ASCII - Slave {slave_addr}, {message.parsed_data['function_name']}"
            
        except Exception as e:
            message.error_message = f"ASCII parsing error: {str(e)}"

    def _parse_nmea(self, message: ParsedMessage):
        """Parse NMEA 0183 message"""
        data = message.raw_data
        
        try:
            # Convert to string and remove line endings
            nmea_str = data.decode('ascii').strip()
            
            if not nmea_str.startswith('$'):
                message.error_message = "Invalid NMEA sentence start"
                return
            
            # Split sentence and checksum
            if '*' in nmea_str:
                sentence, checksum_str = nmea_str.rsplit('*', 1)
                received_checksum = int(checksum_str, 16)
                
                # Calculate checksum
                calculated_checksum = 0
                for char in sentence[1:]:  # Skip the '$'
                    calculated_checksum ^= ord(char)
                
                message.is_valid = (received_checksum == calculated_checksum)
            else:
                sentence = nmea_str
                received_checksum = None
                calculated_checksum = None
                message.is_valid = True  # No checksum to verify
            
            # Parse sentence components
            parts = sentence.split(',')
            talker_id = parts[0][1:3] if len(parts[0]) >= 3 else ""
            sentence_id = parts[0][3:] if len(parts[0]) > 3 else ""
            
            message.parsed_data = {
                'talker_id': talker_id,
                'sentence_id': sentence_id,
                'sentence_type': parts[0][1:],
                'fields': parts[1:] if len(parts) > 1 else [],
                'field_count': len(parts) - 1,
                'checksum_received': f"0x{received_checksum:02X}" if received_checksum is not None else "None",
                'checksum_calculated': f"0x{calculated_checksum:02X}" if calculated_checksum is not None else "None",
                'checksum_valid': message.is_valid
            }
            
            message.description = f"NMEA - {talker_id} {sentence_id}"
            
        except Exception as e:
            message.error_message = f"NMEA parsing error: {str(e)}"

    def _parse_ascii_delimited(self, message: ParsedMessage):
        """Parse ASCII delimited message"""
        try:
            text = message.raw_data.decode('ascii').strip()
            
            # Detect delimiter
            delimiters = [',', ';', '|', '\t']
            delimiter = None
            for delim in delimiters:
                if delim in text:
                    delimiter = delim
                    break
            
            if delimiter:
                fields = text.split(delimiter)
            else:
                fields = [text]
            
            message.parsed_data = {
                'delimiter': delimiter or "None",
                'field_count': len(fields),
                'fields': fields,
                'text': text
            }
            
            message.is_valid = True
            message.description = f"ASCII - {len(fields)} fields"
            
        except UnicodeDecodeError:
            message.error_message = "Not valid ASCII text"

    def _parse_custom_binary(self, message: ParsedMessage):
        """Parse custom binary protocol"""
        data = message.raw_data
        
        message.parsed_data = {
            'length': len(data),
            'hex_dump': ' '.join(f'{b:02X}' for b in data),
            'ascii_repr': ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data)
        }
        
        message.is_valid = True
        message.description = f"Binary - {len(data)} bytes"

    def _parse_raw(self, message: ParsedMessage):
        """Parse raw data (no specific protocol)"""
        data = message.raw_data
        
        # Try to decode as ASCII
        try:
            ascii_text = data.decode('ascii')
            is_ascii = True
        except UnicodeDecodeError:
            ascii_text = ""
            is_ascii = False
        
        message.parsed_data = {
            'length': len(data),
            'is_ascii': is_ascii,
            'ascii_text': ascii_text if is_ascii else "",
            'hex_dump': ' '.join(f'{b:02X}' for b in data),
            'binary_repr': ''.join(f'{b:08b} ' for b in data).strip()
        }
        
        message.is_valid = True
        message.description = f"Raw - {len(data)} bytes"

    def _calculate_modbus_crc(self, data: bytes) -> int:
        """Calculate Modbus RTU CRC16"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 1:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc >>= 1
        return crc

    def _calculate_modbus_lrc(self, data: bytes) -> int:
        """Calculate Modbus ASCII LRC"""
        lrc = 0
        for byte in data:
            lrc += byte
        return (-lrc) & 0xFF

    def _get_modbus_function_name(self, func_code: int) -> str:
        """Get Modbus function name from code"""
        function_names = {
            1: "Read Coils",
            2: "Read Discrete Inputs",
            3: "Read Holding Registers",
            4: "Read Input Registers",
            5: "Write Single Coil",
            6: "Write Single Register",
            15: "Write Multiple Coils",
            16: "Write Multiple Registers",
            23: "Read/Write Multiple Registers"
        }
        return function_names.get(func_code, f"Unknown (0x{func_code:02X})")

class ProtocolStatistics:
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.message_counts = {protocol: 0 for protocol in ProtocolType}
        self.error_counts = {protocol: 0 for protocol in ProtocolType}
        self.byte_counts = {protocol: 0 for protocol in ProtocolType}
        self.start_time = datetime.now()
    
    def update(self, message: ParsedMessage):
        self.message_counts[message.protocol] += 1
        self.byte_counts[message.protocol] += len(message.raw_data)
        if not message.is_valid:
            self.error_counts[message.protocol] += 1
    
    def get_summary(self) -> Dict[str, Any]:
        total_messages = sum(self.message_counts.values())
        total_bytes = sum(self.byte_counts.values())
        total_errors = sum(self.error_counts.values())
        
        runtime = datetime.now() - self.start_time
        
        return {
            'total_messages': total_messages,
            'total_bytes': total_bytes,
            'total_errors': total_errors,
            'runtime_seconds': runtime.total_seconds(),
            'messages_per_second': total_messages / max(runtime.total_seconds(), 1),
            'bytes_per_second': total_bytes / max(runtime.total_seconds(), 1),
            'error_rate': (total_errors / max(total_messages, 1)) * 100,
            'protocol_breakdown': dict(self.message_counts)
        }
