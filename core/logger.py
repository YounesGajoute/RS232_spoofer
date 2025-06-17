"""
Data logging system for RS232 Spoofer
Handles CSV logging, data formatting, and log management
"""

import csv
import os
from datetime import datetime, date
from typing import Optional, List, Dict, Any
import logging
import threading

class DataLogger:
    def __init__(self):
        self.log_folder = "./logs"
        self.log_format = "both"  # ascii, hex, both
        self.max_log_files = 30
        
        self.current_log_file = None
        self.current_date = None
        self.csv_writer = None
        self.log_file_handle = None
        
        self.logger = logging.getLogger(__name__)
        self.lock = threading.Lock()
        
        # Statistics
        self.stats = {
            'total_messages': 0,
            'total_bytes': 0,
            'spoofed_messages': 0,
            'start_time': datetime.now()
        }

    def configure(self, log_folder: str, log_format: str, max_log_files: int = 30):
        """Configure logger settings"""
        self.log_folder = log_folder
        self.log_format = log_format
        self.max_log_files = max_log_files
        
        # Create log folder if it doesn't exist
        os.makedirs(self.log_folder, exist_ok=True)
        
        # Clean up old log files
        self._cleanup_old_logs()

    def log_data(self, data: bytes, direction: str, timestamp: datetime, 
                 modified_data: Optional[bytes] = None, spoofed: bool = False):
        """Log communication data"""
        with self.lock:
            try:
                # Check if we need a new log file (new day)
                current_date = timestamp.date()
                if current_date != self.current_date:
                    self._create_new_log_file(current_date)
                
                # Prepare log entry
                log_entry = self._prepare_log_entry(data, direction, timestamp, modified_data, spoofed)
                
                # Write to CSV
                if self.csv_writer:
                    self.csv_writer.writerow(log_entry)
                    self.log_file_handle.flush()
                
                # Update statistics
                self.stats['total_messages'] += 1
                self.stats['total_bytes'] += len(data)
                if spoofed:
                    self.stats['spoofed_messages'] += 1
                
            except Exception as e:
                self.logger.error(f"Error logging data: {e}")

    def _create_new_log_file(self, log_date: date):
        """Create a new log file for the given date"""
        try:
            # Close current file if open
            if self.log_file_handle:
                self.log_file_handle.close()
            
            # Create new file
            filename = f"rs232_log_{log_date.strftime('%Y%m%d')}.csv"
            filepath = os.path.join(self.log_folder, filename)
            
            self.log_file_handle = open(filepath, 'a', newline='', encoding='utf-8')
            self.csv_writer = csv.writer(self.log_file_handle)
            
            # Write header if file is new
            if os.path.getsize(filepath) == 0:
                self._write_csv_header()
            
            self.current_log_file = filepath
            self.current_date = log_date
            
            self.logger.info(f"Created new log file: {filepath}")
            
        except Exception as e:
            self.logger.error(f"Error creating log file: {e}")

    def _write_csv_header(self):
        """Write CSV header row"""
        header = ['Timestamp', 'Direction', 'Length', 'Spoofed']
        
        if self.log_format in ['ascii', 'both']:
            header.extend(['Original_ASCII', 'Modified_ASCII'])
        
        if self.log_format in ['hex', 'both']:
            header.extend(['Original_HEX', 'Modified_HEX'])
        
        header.extend(['Protocol', 'Valid', 'Description', 'Error'])
        
        self.csv_writer.writerow(header)

    def _prepare_log_entry(self, data: bytes, direction: str, timestamp: datetime,
                          modified_data: Optional[bytes], spoofed: bool) -> List[str]:
        """Prepare a log entry for CSV writing"""
        entry = [
            timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            direction,
            str(len(data)),
            'Yes' if spoofed else 'No'
        ]
        
        # Add ASCII data if requested
        if self.log_format in ['ascii', 'both']:
            original_ascii = self._bytes_to_ascii(data)
            modified_ascii = self._bytes_to_ascii(modified_data) if modified_data else original_ascii
            entry.extend([original_ascii, modified_ascii])
        
        # Add HEX data if requested
        if self.log_format in ['hex', 'both']:
            original_hex = self._bytes_to_hex(data)
            modified_hex = self._bytes_to_hex(modified_data) if modified_data else original_hex
            entry.extend([original_hex, modified_hex])
        
        # Add protocol information (placeholders for now)
        entry.extend(['', '', '', ''])  # Protocol, Valid, Description, Error
        
        return entry

    def _bytes_to_ascii(self, data: bytes) -> str:
        """Convert bytes to ASCII representation"""
        if not data:
            return ""
        
        try:
            # Try to decode as ASCII, replace non-printable characters
            return ''.join(chr(b) if 32 <= b <= 126 else f'\\x{b:02x}' for b in data)
        except:
            return f"<decode_error:{len(data)}_bytes>"

    def _bytes_to_hex(self, data: bytes) -> str:
        """Convert bytes to hexadecimal representation"""
        if not data:
            return ""
        return ' '.join(f'{b:02X}' for b in data)

    def _cleanup_old_logs(self):
        """Remove old log files beyond the retention limit"""
        try:
            if not os.path.exists(self.log_folder):
                return
            
            # Get all log files
            log_files = []
            for filename in os.listdir(self.log_folder):
                if filename.startswith('rs232_log_') and filename.endswith('.csv'):
                    filepath = os.path.join(self.log_folder, filename)
                    mtime = os.path.getmtime(filepath)
                    log_files.append((filepath, mtime))
            
            # Sort by modification time (newest first)
            log_files.sort(key=lambda x: x[1], reverse=True)
            
            # Remove old files
            for filepath, _ in log_files[self.max_log_files:]:
                try:
                    os.remove(filepath)
                    self.logger.info(f"Removed old log file: {filepath}")
                except Exception as e:
                    self.logger.warning(f"Could not remove old log file {filepath}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error cleaning up old logs: {e}")

    def export_logs(self, filename: str, start_date: Optional[date] = None, 
                   end_date: Optional[date] = None) -> bool:
        """Export logs to a single file"""
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as outfile:
                writer = csv.writer(outfile)
                
                # Write header
                self._write_export_header(writer)
                
                # Get log files in date range
                log_files = self._get_log_files_in_range(start_date, end_date)
                
                # Copy data from each log file
                for log_file in log_files:
                    try:
                        with open(log_file, 'r', encoding='utf-8') as infile:
                            reader = csv.reader(infile)
                            next(reader, None)  # Skip header
                            for row in reader:
                                writer.writerow(row)
                    except Exception as e:
                        self.logger.warning(f"Error reading log file {log_file}: {e}")
            
            self.logger.info(f"Logs exported to {filename}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting logs: {e}")
            return False

    def _write_export_header(self, writer):
        """Write header for exported logs"""
        header = ['Timestamp', 'Direction', 'Length', 'Spoofed']
        
        if self.log_format in ['ascii', 'both']:
            header.extend(['Original_ASCII', 'Modified_ASCII'])
        
        if self.log_format in ['hex', 'both']:
            header.extend(['Original_HEX', 'Modified_HEX'])
        
        header.extend(['Protocol', 'Valid', 'Description', 'Error'])
        writer.writerow(header)

    def _get_log_files_in_range(self, start_date: Optional[date], 
                               end_date: Optional[date]) -> List[str]:
        """Get log files within the specified date range"""
        log_files = []
        
        if not os.path.exists(self.log_folder):
            return log_files
        
        for filename in os.listdir(self.log_folder):
            if filename.startswith('rs232_log_') and filename.endswith('.csv'):
                try:
                    # Extract date from filename
                    date_str = filename[10:18]  # rs232_log_YYYYMMDD.csv
                    file_date = datetime.strptime(date_str, '%Y%m%d').date()
                    
                    # Check if in range
                    if start_date and file_date < start_date:
                        continue
                    if end_date and file_date > end_date:
                        continue
                    
                    log_files.append(os.path.join(self.log_folder, filename))
                    
                except ValueError:
                    # Invalid date format, skip
                    continue
        
        return sorted(log_files)

    def get_statistics(self) -> Dict[str, Any]:
        """Get logging statistics"""
        runtime = datetime.now() - self.stats['start_time']
        
        return {
            'total_messages': self.stats['total_messages'],
            'total_bytes': self.stats['total_bytes'],
            'spoofed_messages': self.stats['spoofed_messages'],
            'spoofed_percentage': (self.stats['spoofed_messages'] / max(self.stats['total_messages'], 1)) * 100,
            'runtime_seconds': runtime.total_seconds(),
            'messages_per_second': self.stats['total_messages'] / max(runtime.total_seconds(), 1),
            'bytes_per_second': self.stats['total_bytes'] / max(runtime.total_seconds(), 1),
            'current_log_file': self.current_log_file
        }

    def reset_statistics(self):
        """Reset logging statistics"""
        self.stats = {
            'total_messages': 0,
            'total_bytes': 0,
            'spoofed_messages': 0,
            'start_time': datetime.now()
        }

    def close(self):
        """Close the logger and any open files"""
        with self.lock:
            if self.log_file_handle:
                self.log_file_handle.close()
                self.log_file_handle = None
                self.csv_writer = None
