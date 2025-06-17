"""
Configuration management for RS232 Spoofer
Handles loading, saving, and validation of application settings
"""

import json
import os
from typing import Dict, Any, Optional
import logging

class ConfigManager:
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.logger = logging.getLogger(__name__)
        
        # Default configuration
        self.default_config = {
            "port_a": "/dev/ttyUSB0",
            "port_b": "/dev/ttyUSB1",
            "baud_rate": 9600,
            "data_bits": 8,
            "parity": "none",
            "stop_bits": 1,
            "timeout": 1.0,
            "flow_control": "none",
            
            # Logging settings
            "log_folder": "./logs",
            "log_format": "both",  # ascii, hex, both
            "max_log_files": 30,
            "log_level": "INFO",
            
            # GUI settings
            "theme": "light",
            "window_geometry": "1200x800",
            "auto_start": False,
            "update_interval": 1000,
            
            # Protocol settings
            "auto_detect_protocol": True,
            "default_protocol": "Raw",
            "protocol_timeout": 5.0,
            
            # Spoofing settings
            "spoofing_enabled": True,
            "spoofing_rules": [],
            
            # Advanced settings
            "buffer_size": 4096,
            "max_message_size": 1024,
            "message_timeout": 1.0
        }

    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                
                # Merge with defaults to ensure all keys exist
                merged_config = self.default_config.copy()
                merged_config.update(config)
                
                self.logger.info(f"Configuration loaded from {self.config_file}")
                return merged_config
            else:
                self.logger.info("No config file found, using defaults")
                return self.default_config.copy()
                
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return self.default_config.copy()

    def save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to file"""
        try:
            # Validate configuration
            validated_config = self.validate_config(config)
            
            with open(self.config_file, 'w') as f:
                json.dump(validated_config, f, indent=2)
            
            self.logger.info(f"Configuration saved to {self.config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")
            return False

    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize configuration values"""
        validated = config.copy()
        
        # Validate baud rate
        valid_baud_rates = [300, 600, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]
        if validated.get('baud_rate') not in valid_baud_rates:
            validated['baud_rate'] = 9600
        
        # Validate data bits
        if validated.get('data_bits') not in [5, 6, 7, 8]:
            validated['data_bits'] = 8
        
        # Validate parity
        if validated.get('parity') not in ['none', 'even', 'odd', 'mark', 'space']:
            validated['parity'] = 'none'
        
        # Validate stop bits
        if validated.get('stop_bits') not in [1, 1.5, 2]:
            validated['stop_bits'] = 1
        
        # Validate timeout
        timeout = validated.get('timeout', 1.0)
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            validated['timeout'] = 1.0
        
        # Validate log format
        if validated.get('log_format') not in ['ascii', 'hex', 'both']:
            validated['log_format'] = 'both'
        
        # Validate theme
        if validated.get('theme') not in ['light', 'dark']:
            validated['theme'] = 'light'
        
        # Ensure spoofing_rules is a list
        if not isinstance(validated.get('spoofing_rules'), list):
            validated['spoofing_rules'] = []
        
        return validated

    def get_serial_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Extract serial port configuration"""
        return {
            'port_a': config.get('port_a', '/dev/ttyUSB0'),
            'port_b': config.get('port_b', '/dev/ttyUSB1'),
            'baudrate': config.get('baud_rate', 9600),
            'bytesize': config.get('data_bits', 8),
            'parity': self._get_parity_constant(config.get('parity', 'none')),
            'stopbits': config.get('stop_bits', 1),
            'timeout': config.get('timeout', 1.0),
            'xonxoff': config.get('flow_control') == 'xonxoff',
            'rtscts': config.get('flow_control') == 'rtscts',
            'dsrdtr': config.get('flow_control') == 'dsrdtr'
        }

    def _get_parity_constant(self, parity_str: str):
        """Convert parity string to pyserial constant"""
        import serial
        parity_map = {
            'none': serial.PARITY_NONE,
            'even': serial.PARITY_EVEN,
            'odd': serial.PARITY_ODD,
            'mark': serial.PARITY_MARK,
            'space': serial.PARITY_SPACE
        }
        return parity_map.get(parity_str, serial.PARITY_NONE)

    def export_config(self, filename: str, config: Dict[str, Any]) -> bool:
        """Export configuration to specified file"""
        try:
            with open(filename, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            self.logger.error(f"Error exporting config: {e}")
            return False

    def import_config(self, filename: str) -> Optional[Dict[str, Any]]:
        """Import configuration from specified file"""
        try:
            with open(filename, 'r') as f:
                config = json.load(f)
            return self.validate_config(config)
        except Exception as e:
            self.logger.error(f"Error importing config: {e}")
            return None
