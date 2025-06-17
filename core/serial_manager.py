"""
Enhanced Serial Manager with Protocol Parsing Support
"""

import serial
import threading
import time
from datetime import datetime
from typing import Callable, Optional, List, Dict, Any
from queue import Queue, Empty

from .protocol_parser import ProtocolParser, ProtocolType, ParsedMessage

class SerialManager:
    def __init__(self):
        self.port_a = None
        self.port_b = None
        self.port_a_name = "/dev/ttyUSB0"
        self.port_b_name = "/dev/ttyUSB1"
        self.baud_rate = 9600
        self.timeout = 1.0
        
        self.is_connected = False
        self.is_monitoring = False
        
        self.data_callback = None
        self.status_callback = None
        
        self.monitor_thread_a = None
        self.monitor_thread_b = None
        self.stop_monitoring = False
        
        # Protocol parsing
        self.protocol_parser = ProtocolParser()
        self.protocol_callback = None  # Callback for parsed messages
        
        # Statistics
        self.stats = {
            'port_a_rx': 0,
            'port_a_tx': 0,
            'port_b_rx': 0,
            'port_b_tx': 0,
            'messages_a_to_b': 0,
            'messages_b_to_a': 0,
            'bytes_a_to_b': 0,
            'bytes_b_to_a': 0,
            'start_time': None
        }
        
        # Spoofing rules
        self.spoofing_rules = []
        self.spoofing_enabled = True
        
        # Message queues for injection
        self.inject_queue_a = Queue()
        self.inject_queue_b = Queue()

    def set_protocol_callback(self, callback: Callable[[ParsedMessage, str], None]):
        """Set callback for parsed protocol messages"""
        self.protocol_callback = callback

    def connect(self) -> bool:
        """Connect to both serial ports"""
        try:
            # Connect to Port A
            self.port_a = serial.Serial(
                port=self.port_a_name,
                baudrate=self.baud_rate,
                timeout=self.timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            # Connect to Port B
            self.port_b = serial.Serial(
                port=self.port_b_name,
                baudrate=self.baud_rate,
                timeout=self.timeout,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE
            )
            
            self.is_connected = True
            self.stats['start_time'] = datetime.now()
            
            if self.status_callback:
                self.status_callback("Connected to both ports")
            
            return True
            
        except Exception as e:
            self.disconnect()
            if self.status_callback:
                self.status_callback(f"Connection failed: {str(e)}")
            return False

    def disconnect(self):
        """Disconnect from serial ports"""
        self.stop_monitoring_ports()
        
        if self.port_a and self.port_a.is_open:
            self.port_a.close()
        if self.port_b and self.port_b.is_open:
            self.port_b.close()
        
        self.port_a = None
        self.port_b = None
        self.is_connected = False
        
        if self.status_callback:
            self.status_callback("Disconnected")

    def start_monitoring(self) -> bool:
        """Start monitoring both ports"""
        if not self.is_connected:
            return False
        
        self.stop_monitoring = False
        self.is_monitoring = True
        
        # Start monitoring threads
        self.monitor_thread_a = threading.Thread(target=self._monitor_port_a, daemon=True)
        self.monitor_thread_b = threading.Thread(target=self._monitor_port_b, daemon=True)
        
        self.monitor_thread_a.start()
        self.monitor_thread_b.start()
        
        if self.status_callback:
            self.status_callback("Monitoring started")
        
        return True

    def stop_monitoring_ports(self):
        """Stop monitoring ports"""
        self.stop_monitoring = True
        self.is_monitoring = False
        
        # Wait for threads to finish
        if self.monitor_thread_a and self.monitor_thread_a.is_alive():
            self.monitor_thread_a.join(timeout=2.0)
        if self.monitor_thread_b and self.monitor_thread_b.is_alive():
            self.monitor_thread_b.join(timeout=2.0)
        
        if self.status_callback:
            self.status_callback("Monitoring stopped")

    def _monitor_port_a(self):
        """Monitor Port A and forward to Port B"""
        buffer = b''
        
        while not self.stop_monitoring and self.is_connected:
            try:
                # Check for manual injection
                try:
                    inject_data = self.inject_queue_a.get_nowait()
                    self.port_a.write(inject_data)
                    self.stats['port_a_tx'] += len(inject_data)
                    
                    if self.data_callback:
                        self.data_callback(inject_data, "INJECT→A", datetime.now())
                except Empty:
                    pass
                
                # Read from Port A
                if self.port_a.in_waiting > 0:
                    data = self.port_a.read(self.port_a.in_waiting)
                    if data:
                        buffer += data
                        
                        # Try to extract complete messages
                        messages = self._extract_messages(buffer)
                        for message_data in messages:
                            buffer = buffer[len(message_data):]
                            self._process_message(message_data, "A→B")
                
                time.sleep(0.001)  # Small delay to prevent CPU spinning
                
            except Exception as e:
                if self.status_callback:
                    self.status_callback(f"Port A error: {str(e)}")
                break

    def _monitor_port_b(self):
        """Monitor Port B and forward to Port A"""
        buffer = b''
        
        while not self.stop_monitoring and self.is_connected:
            try:
                # Check for manual injection
                try:
                    inject_data = self.inject_queue_b.get_nowait()
                    self.port_b.write(inject_data)
                    self.stats['port_b_tx'] += len(inject_data)
                    
                    if self.data_callback:
                        self.data_callback(inject_data, "INJECT→B", datetime.now())
                except Empty:
                    pass
                
                # Read from Port B
                if self.port_b.in_waiting > 0:
                    data = self.port_b.read(self.port_b.in_waiting)
                    if data:
                        buffer += data
                        
                        # Try to extract complete messages
                        messages = self._extract_messages(buffer)
                        for message_data in messages:
                            buffer = buffer[len(message_data):]
                            self._process_message(message_data, "B→A")
                
                time.sleep(0.001)  # Small delay to prevent CPU spinning
                
            except Exception as e:
                if self.status_callback:
                    self.status_callback(f"Port B error: {str(e)}")
                break

    def _extract_messages(self, buffer: bytes) -> List[bytes]:
        """Extract complete messages from buffer based on protocol patterns"""
        messages = []
        
        if len(buffer) == 0:
            return messages
        
        # Try different message extraction strategies
        
        # 1. NMEA messages (start with $ and end with \r\n)
        if buffer.startswith(b'$'):
            end_pos = buffer.find(b'\r\n')
            if end_pos != -1:
                messages.append(buffer[:end_pos + 2])
                return messages
        
        # 2. Modbus ASCII (start with : and end with \r\n)
        if buffer.startswith(b':'):
            end_pos = buffer.find(b'\r\n')
            if end_pos != -1:
                messages.append(buffer[:end_pos + 2])
                return messages
        
        # 3. Modbus RTU (try to detect complete frame)
        if len(buffer) >= 4:
            # Simple heuristic: if we have at least 4 bytes and no new data for a while
            # This is a simplified approach - in practice, you'd need more sophisticated timing
            messages.append(buffer)
            return messages
        
        # 4. Line-based ASCII protocols
        if b'\n' in buffer:
            lines = buffer.split(b'\n')
            for i, line in enumerate(lines[:-1]):  # All but the last (potentially incomplete) line
                if line.endswith(b'\r'):
                    messages.append(line + b'\n')
                else:
                    messages.append(line + b'\n')
            return messages
        
        # 5. If buffer is getting large, treat as single message
        if len(buffer) > 1024:
            messages.append(buffer)
            return messages
        
        # 6. For very short messages or unknown protocols, wait for more data
        # This is a timeout-based approach that would need refinement
        return messages

    def _process_message(self, data: bytes, direction: str):
        """Process a complete message with protocol parsing and spoofing"""
        original_data = data
        modified_data = data
        spoofed = False
        
        # Apply spoofing rules
        if self.spoofing_enabled:
            modified_data, spoofed = self._apply_spoofing_rules(data)
        
        # Parse the message
        parsed_message = self.protocol_parser.parse_message(original_data)
        
        # Forward the (possibly modified) data
        try:
            if direction == "A→B" and self.port_b:
                self.port_b.write(modified_data)
                self.stats['port_a_rx'] += len(original_data)
                self.stats['port_b_tx'] += len(modified_data)
                self.stats['messages_a_to_b'] += 1
                self.stats['bytes_a_to_b'] += len(modified_data)
            elif direction == "B→A" and self.port_a:
                self.port_a.write(modified_data)
                self.stats['port_b_rx'] += len(original_data)
                self.stats['port_a_tx'] += len(modified_data)
                self.stats['messages_b_to_a'] += 1
                self.stats['bytes_b_to_a'] += len(modified_data)
        except Exception as e:
            if self.status_callback:
                self.status_callback(f"Forward error: {str(e)}")
        
        # Notify callbacks
        if self.data_callback:
            self.data_callback(original_data, direction, datetime.now(), 
                             modified_data if spoofed else None, spoofed)
        
        if self.protocol_callback:
            self.protocol_callback(parsed_message, direction)

    def _apply_spoofing_rules(self, data: bytes) -> tuple[bytes, bool]:
        """Apply spoofing rules to data"""
        modified_data = data
        spoofed = False
        
        for rule in self.spoofing_rules:
            if not rule.get('enabled', True):
                continue
            
            try:
                if rule['type'] == 'ascii':
                    pattern = rule['pattern'].encode('ascii')
                    replacement = rule['replacement'].encode('ascii')
                elif rule['type'] == 'hex':
                    pattern = bytes.fromhex(rule['pattern'].replace(' ', ''))
                    replacement = bytes.fromhex(rule['replacement'].replace(' ', ''))
                else:
                    continue
                
                if pattern in modified_data:
                    modified_data = modified_data.replace(pattern, replacement)
                    spoofed = True
                    
            except Exception as e:
                # Skip invalid rules
                continue
        
        return modified_data, spoofed

    def inject_data(self, data: bytes, target_port: str):
        """Inject data into specified port"""
        try:
            if target_port.upper() == 'A':
                self.inject_queue_a.put(data)
            elif target_port.upper() == 'B':
                self.inject_queue_b.put(data)
        except Exception as e:
            if self.status_callback:
                self.status_callback(f"Injection error: {str(e)}")

    def get_statistics(self) -> Dict[str, Any]:
        """Get current statistics"""
        stats = self.stats.copy()
        if stats['start_time']:
            runtime = datetime.now() - stats['start_time']
            stats['runtime_seconds'] = runtime.total_seconds()
            stats['messages_per_second'] = (stats['messages_a_to_b'] + stats['messages_b_to_a']) / max(runtime.total_seconds(), 1)
        return stats

    def reset_statistics(self):
        """Reset all statistics"""
        self.stats = {
            'port_a_rx': 0,
            'port_a_tx': 0,
            'port_b_rx': 0,
            'port_b_tx': 0,
            'messages_a_to_b': 0,
            'messages_b_to_a': 0,
            'bytes_a_to_b': 0,
            'bytes_b_to_a': 0,
            'start_time': datetime.now() if self.is_connected else None
        }

    def set_spoofing_rules(self, rules: List[Dict]):
        """Set spoofing rules"""
        self.spoofing_rules = rules

    def set_spoofing_enabled(self, enabled: bool):
        """Enable or disable spoofing"""
        self.spoofing_enabled = enabled

    def configure_ports(self, port_a: str, port_b: str, baud_rate: int, timeout: float):
        """Configure port settings"""
        self.port_a_name = port_a
        self.port_b_name = port_b
        self.baud_rate = baud_rate
        self.timeout = timeout

    def set_data_callback(self, callback: Callable):
        """Set callback for data events"""
        self.data_callback = callback

    def set_status_callback(self, callback: Callable):
        """Set callback for status events"""
        self.status_callback = callback
