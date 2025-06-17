"""
Dashboard tab for RS232 Spoofer
Displays real-time communication logs and statistics
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime
from typing import List, Dict, Any
import threading

class DashboardTab:
    def __init__(self, parent_notebook, serial_manager, logger):
        self.serial_manager = serial_manager
        self.logger = logger
        
        # Create the tab frame
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="Dashboard")
        
        # Data storage
        self.log_entries = []
        self.max_log_entries = 1000
        self.filter_direction = "All"
        self.filter_protocol = "All"
        
        # Threading lock for GUI updates
        self.update_lock = threading.Lock()
        
        self.setup_ui()

    def setup_ui(self):
        """Setup the dashboard user interface"""
        # Create main paned window
        main_paned = ttk.PanedWindow(self.frame, orient=tk.VERTICAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Top section - Statistics and controls
        top_frame = ttk.Frame(main_paned)
        main_paned.add(top_frame, weight=1)
        
        # Bottom section - Log display
        bottom_frame = ttk.Frame(main_paned)
        main_paned.add(bottom_frame, weight=3)
        
        self.setup_statistics_section(top_frame)
        self.setup_log_section(bottom_frame)

    def setup_statistics_section(self, parent):
        """Setup statistics and control section"""
        # Connection status frame
        status_frame = ttk.LabelFrame(parent, text="Connection Status")
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        status_grid = ttk.Frame(status_frame)
        status_grid.pack(fill=tk.X, padx=5, pady=5)
        
        # Port A status
        ttk.Label(status_grid, text="Port A:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.port_a_status = ttk.Label(status_grid, text="Disconnected", foreground="red")
        self.port_a_status.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Port B status
        ttk.Label(status_grid, text="Port B:").grid(row=0, column=2, sticky=tk.W, padx=20)
        self.port_b_status = ttk.Label(status_grid, text="Disconnected", foreground="red")
        self.port_b_status.grid(row=0, column=3, sticky=tk.W, padx=5)
        
        # Monitoring status
        ttk.Label(status_grid, text="Monitoring:").grid(row=0, column=4, sticky=tk.W, padx=20)
        self.monitoring_status = ttk.Label(status_grid, text="Stopped", foreground="red")
        self.monitoring_status.grid(row=0, column=5, sticky=tk.W, padx=5)
        
        # Statistics frame
        stats_frame = ttk.LabelFrame(parent, text="Communication Statistics")
        stats_frame.pack(fill=tk.X, padx=5, pady=5)
        
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill=tk.X, padx=5, pady=5)
        
        # Configure grid columns
        for i in range(8):
            stats_grid.columnconfigure(i, weight=1)
        
        # Statistics labels
        ttk.Label(stats_grid, text="A→B Messages:").grid(row=0, column=0, sticky=tk.W)
        self.stats_a_to_b = ttk.Label(stats_grid, text="0")
        self.stats_a_to_b.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(stats_grid, text="B→A Messages:").grid(row=0, column=2, sticky=tk.W, padx=10)
        self.stats_b_to_a = ttk.Label(stats_grid, text="0")
        self.stats_b_to_a.grid(row=0, column=3, sticky=tk.W, padx=5)
        
        ttk.Label(stats_grid, text="Total Bytes:").grid(row=0, column=4, sticky=tk.W, padx=10)
        self.stats_total_bytes = ttk.Label(stats_grid, text="0")
        self.stats_total_bytes.grid(row=0, column=5, sticky=tk.W, padx=5)
        
        ttk.Label(stats_grid, text="Spoofed:").grid(row=0, column=6, sticky=tk.W, padx=10)
        self.stats_spoofed = ttk.Label(stats_grid, text="0")
        self.stats_spoofed.grid(row=0, column=7, sticky=tk.W, padx=5)
        
        # Second row of statistics
        ttk.Label(stats_grid, text="Messages/sec:").grid(row=1, column=0, sticky=tk.W)
        self.stats_msg_per_sec = ttk.Label(stats_grid, text="0.0")
        self.stats_msg_per_sec.grid(row=1, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(stats_grid, text="Bytes/sec:").grid(row=1, column=2, sticky=tk.W, padx=10)
        self.stats_bytes_per_sec = ttk.Label(stats_grid, text="0.0")
        self.stats_bytes_per_sec.grid(row=1, column=3, sticky=tk.W, padx=5)
        
        ttk.Label(stats_grid, text="Runtime:").grid(row=1, column=4, sticky=tk.W, padx=10)
        self.stats_runtime = ttk.Label(stats_grid, text="00:00:00")
        self.stats_runtime.grid(row=1, column=5, sticky=tk.W, padx=5)
        
        ttk.Label(stats_grid, text="Error Rate:").grid(row=1, column=6, sticky=tk.W, padx=10)
        self.stats_error_rate = ttk.Label(stats_grid, text="0.0%")
        self.stats_error_rate.grid(row=1, column=7, sticky=tk.W, padx=5)

    def setup_log_section(self, parent):
        """Setup log display section"""
        # Control frame
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Filters
        ttk.Label(control_frame, text="Filter Direction:").pack(side=tk.LEFT, padx=5)
        self.direction_filter = ttk.Combobox(control_frame, values=["All", "A→B", "B→A", "INJECT→A", "INJECT→B"],
                                           state="readonly", width=10)
        self.direction_filter.set("All")
        self.direction_filter.pack(side=tk.LEFT, padx=5)
        self.direction_filter.bind('<<ComboboxSelected>>', self.on_filter_changed)
        
        ttk.Label(control_frame, text="Show Format:").pack(side=tk.LEFT, padx=(20, 5))
        self.format_var = tk.StringVar(value="both")
        format_frame = ttk.Frame(control_frame)
        format_frame.pack(side=tk.LEFT, padx=5)
        
        ttk.Radiobutton(format_frame, text="ASCII", variable=self.format_var, 
                       value="ascii", command=self.refresh_log_display).pack(side=tk.LEFT)
        ttk.Radiobutton(format_frame, text="HEX", variable=self.format_var, 
                       value="hex", command=self.refresh_log_display).pack(side=tk.LEFT)
        ttk.Radiobutton(format_frame, text="Both", variable=self.format_var, 
                       value="both", command=self.refresh_log_display).pack(side=tk.LEFT)
        
        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(side=tk.RIGHT, padx=5)
        
        ttk.Button(button_frame, text="Clear Logs", command=self.clear_logs).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Pause", command=self.toggle_pause).pack(side=tk.LEFT, padx=2)
        
        self.paused = False
        
        # Log display
        log_frame = ttk.LabelFrame(parent, text="Communication Log")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create text widget with scrollbar
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            wrap=tk.WORD, 
            font=('Courier', 9),
            state=tk.DISABLED
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure text tags for color coding
        self.log_text.tag_configure("a_to_b", foreground="blue")
        self.log_text.tag_configure("b_to_a", foreground="green")
        self.log_text.tag_configure("inject", foreground="purple")
        self.log_text.tag_configure("spoofed", foreground="red", font=('Courier', 9, 'bold'))
        self.log_text.tag_configure("timestamp", foreground="gray")
        self.log_text.tag_configure("direction", font=('Courier', 9, 'bold'))

    def add_log_entry(self, data: bytes, direction: str, timestamp: datetime, 
                     modified_data: bytes = None, spoofed: bool = False):
        """Add a new log entry"""
        if self.paused:
            return
        
        with self.update_lock:
            # Create log entry
            entry = {
                'data': data,
                'direction': direction,
                'timestamp': timestamp,
                'modified_data': modified_data,
                'spoofed': spoofed
            }
            
            # Add to storage
            self.log_entries.append(entry)
            
            # Limit entries
            if len(self.log_entries) > self.max_log_entries:
                self.log_entries.pop(0)
            
            # Update display
            self.add_log_line(entry)

    def add_log_line(self, entry: Dict):
        """Add a single log line to the display"""
        if not self.should_show_entry(entry):
            return
        
        self.log_text.config(state=tk.NORMAL)
        
        # Format timestamp
        time_str = entry['timestamp'].strftime("%H:%M:%S.%f")[:-3]
        
        # Add timestamp
        self.log_text.insert(tk.END, f"[{time_str}] ", "timestamp")
        
        # Add direction with color
        direction = entry['direction']
        if direction == "A→B":
            tag = "a_to_b"
        elif direction == "B→A":
            tag = "b_to_a"
        elif "INJECT" in direction:
            tag = "inject"
        else:
            tag = "direction"
        
        self.log_text.insert(tk.END, f"{direction:10} ", tag)
        
        # Add spoofed indicator
        if entry['spoofed']:
            self.log_text.insert(tk.END, "[SPOOFED] ", "spoofed")
        
        # Add data based on format selection
        format_type = self.format_var.get()
        data_str = self.format_data(entry['data'], format_type)
        
        if entry['spoofed'] and entry['modified_data']:
            modified_str = self.format_data(entry['modified_data'], format_type)
            self.log_text.insert(tk.END, f"Original: {data_str}\n")
            self.log_text.insert(tk.END, f"          Modified: {modified_str}\n", "spoofed")
        else:
            self.log_text.insert(tk.END, f"{data_str}\n")
        
        self.log_text.config(state=tk.DISABLED)
        
        # Auto-scroll to bottom
        self.log_text.see(tk.END)

    def format_data(self, data: bytes, format_type: str) -> str:
        """Format data according to the specified format"""
        if not data:
            return ""
        
        if format_type == "ascii":
            return ''.join(chr(b) if 32 <= b <= 126 else f'\\x{b:02x}' for b in data)
        elif format_type == "hex":
            return ' '.join(f'{b:02X}' for b in data)
        else:  # both
            ascii_str = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data)
            hex_str = ' '.join(f'{b:02X}' for b in data)
            return f"ASCII: {ascii_str} | HEX: {hex_str}"

    def should_show_entry(self, entry: Dict) -> bool:
        """Check if entry should be displayed based on filters"""
        direction_filter = self.direction_filter.get()
        if direction_filter != "All" and entry['direction'] != direction_filter:
            return False
        
        return True

    def on_filter_changed(self, event=None):
        """Handle filter changes"""
        self.refresh_log_display()

    def refresh_log_display(self):
        """Refresh the entire log display"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        
        for entry in self.log_entries:
            self.add_log_line(entry)
        
        self.log_text.config(state=tk.DISABLED)

    def clear_logs(self):
        """Clear all log entries"""
        with self.update_lock:
            self.log_entries.clear()
            self.log_text.config(state=tk.NORMAL)
            self.log_text.delete(1.0, tk.END)
            self.log_text.config(state=tk.DISABLED)

    def toggle_pause(self):
        """Toggle pause state"""
        self.paused = not self.paused
        # Update button text would go here if we had a reference to it

    def update_display(self):
        """Update statistics display"""
        # Update connection status
        if self.serial_manager.is_connected:
            self.port_a_status.config(text="Connected", foreground="green")
            self.port_b_status.config(text="Connected", foreground="green")
        else:
            self.port_a_status.config(text="Disconnected", foreground="red")
            self.port_b_status.config(text="Disconnected", foreground="red")
        
        if self.serial_manager.is_monitoring:
            self.monitoring_status.config(text="Active", foreground="green")
        else:
            self.monitoring_status.config(text="Stopped", foreground="red")
        
        # Update statistics
        stats = self.serial_manager.get_statistics()
        
        self.stats_a_to_b.config(text=str(stats.get('messages_a_to_b', 0)))
        self.stats_b_to_a.config(text=str(stats.get('messages_b_to_a', 0)))
        
        total_bytes = stats.get('bytes_a_to_b', 0) + stats.get('bytes_b_to_a', 0)
        self.stats_total_bytes.config(text=str(total_bytes))
        
        # Get logger statistics for spoofed count
        logger_stats = self.logger.get_statistics()
        self.stats_spoofed.config(text=str(logger_stats.get('spoofed_messages', 0)))
        
        # Calculate rates
        runtime = stats.get('runtime_seconds', 0)
        if runtime > 0:
            msg_per_sec = (stats.get('messages_a_to_b', 0) + stats.get('messages_b_to_a', 0)) / runtime
            bytes_per_sec = total_bytes / runtime
            self.stats_msg_per_sec.config(text=f"{msg_per_sec:.1f}")
            self.stats_bytes_per_sec.config(text=f"{bytes_per_sec:.1f}")
        
        # Format runtime
        if runtime > 0:
            hours = int(runtime // 3600)
            minutes = int((runtime % 3600) // 60)
            seconds = int(runtime % 60)
            self.stats_runtime.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    def reset_statistics(self):
        """Reset statistics display"""
        self.stats_a_to_b.config(text="0")
        self.stats_b_to_a.config(text="0")
        self.stats_total_bytes.config(text="0")
        self.stats_spoofed.config(text="0")
        self.stats_msg_per_sec.config(text="0.0")
        self.stats_bytes_per_sec.config(text="0.0")
        self.stats_runtime.config(text="00:00:00")
        self.stats_error_rate.config(text="0.0%")
