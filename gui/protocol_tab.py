"""
Protocol Analysis Tab for RS232 Spoofer
Displays parsed protocol information and statistics
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import Dict, List
import json
from datetime import datetime

from core.protocol_parser import ProtocolType, ParsedMessage, ProtocolStatistics

class ProtocolTab:
    def __init__(self, parent_notebook, serial_manager, logger):
        self.serial_manager = serial_manager
        self.logger = logger
        self.statistics = ProtocolStatistics()
        
        # Create the tab frame
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="Protocol Analysis")
        
        self.setup_ui()
        self.update_display()
    
    def setup_ui(self):
        """Setup the protocol analysis UI"""
        # Main container with paned window
        main_paned = ttk.PanedWindow(self.frame, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Protocol selection and statistics
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=1)
        
        # Right panel - Message details
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=2)
        
        self.setup_left_panel(left_frame)
        self.setup_right_panel(right_frame)
    
    def setup_left_panel(self, parent):
        """Setup left panel with protocol controls and statistics"""
        # Protocol Selection
        protocol_frame = ttk.LabelFrame(parent, text="Protocol Settings")
        protocol_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(protocol_frame, text="Auto-detect Protocol:").pack(anchor=tk.W, padx=5, pady=2)
        self.auto_detect_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(protocol_frame, text="Enable auto-detection", 
                       variable=self.auto_detect_var,
                       command=self.on_auto_detect_changed).pack(anchor=tk.W, padx=5)
        
        ttk.Label(protocol_frame, text="Force Protocol:").pack(anchor=tk.W, padx=5, pady=(10,2))
        self.protocol_var = tk.StringVar(value=ProtocolType.RAW.value)
        protocol_combo = ttk.Combobox(protocol_frame, textvariable=self.protocol_var,
                                     values=[p.value for p in ProtocolType],
                                     state="readonly")
        protocol_combo.pack(fill=tk.X, padx=5, pady=2)
        protocol_combo.bind('<<ComboboxSelected>>', self.on_protocol_changed)
        
        # Statistics
        stats_frame = ttk.LabelFrame(parent, text="Protocol Statistics")
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Statistics tree
        self.stats_tree = ttk.Treeview(stats_frame, columns=('Messages', 'Bytes', 'Errors'), 
                                      show='tree headings', height=8)
        self.stats_tree.heading('#0', text='Protocol')
        self.stats_tree.heading('Messages', text='Messages')
        self.stats_tree.heading('Bytes', text='Bytes')
        self.stats_tree.heading('Errors', text='Errors')
        
        self.stats_tree.column('#0', width=120)
        self.stats_tree.column('Messages', width=80)
        self.stats_tree.column('Bytes', width=80)
        self.stats_tree.column('Errors', width=60)
        
        stats_scrollbar = ttk.Scrollbar(stats_frame, orient=tk.VERTICAL, command=self.stats_tree.yview)
        self.stats_tree.configure(yscrollcommand=stats_scrollbar.set)
        
        self.stats_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        stats_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Control buttons
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Reset Statistics", 
                  command=self.reset_statistics).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Export Stats", 
                  command=self.export_statistics).pack(side=tk.LEFT, padx=2)
    
    def setup_right_panel(self, parent):
        """Setup right panel with message details"""
        # Message list
        list_frame = ttk.LabelFrame(parent, text="Recent Messages")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Message tree
        self.message_tree = ttk.Treeview(list_frame, 
                                        columns=('Time', 'Direction', 'Protocol', 'Description', 'Valid'),
                                        show='headings', height=10)
        
        self.message_tree.heading('Time', text='Time')
        self.message_tree.heading('Direction', text='Dir')
        self.message_tree.heading('Protocol', text='Protocol')
        self.message_tree.heading('Description', text='Description')
        self.message_tree.heading('Valid', text='Valid')
        
        self.message_tree.column('Time', width=80)
        self.message_tree.column('Direction', width=40)
        self.message_tree.column('Protocol', width=100)
        self.message_tree.column('Description', width=200)
        self.message_tree.column('Valid', width=50)
        
        msg_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.message_tree.yview)
        self.message_tree.configure(yscrollcommand=msg_scrollbar.set)
        
        self.message_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        msg_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.message_tree.bind('<<TreeviewSelect>>', self.on_message_selected)
        
        # Message details
        details_frame = ttk.LabelFrame(parent, text="Message Details")
        details_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create notebook for different views
        details_notebook = ttk.Notebook(details_frame)
        details_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Parsed data tab
        parsed_frame = ttk.Frame(details_notebook)
        details_notebook.add(parsed_frame, text="Parsed Data")
        
        self.parsed_text = scrolledtext.ScrolledText(parsed_frame, height=8, wrap=tk.WORD)
        self.parsed_text.pack(fill=tk.BOTH, expand=True)
        
        # Raw data tab
        raw_frame = ttk.Frame(details_notebook)
        details_notebook.add(raw_frame, text="Raw Data")
        
        self.raw_text = scrolledtext.ScrolledText(raw_frame, height=8, wrap=tk.WORD, font=('Courier', 9))
        self.raw_text.pack(fill=tk.BOTH, expand=True)
        
        # Store recent messages
        self.recent_messages: List[ParsedMessage] = []
        self.max_recent_messages = 1000
    
    def on_auto_detect_changed(self):
        """Handle auto-detect checkbox change"""
        if self.auto_detect_var.get():
            # Enable auto-detection
            pass
        else:
            # Use forced protocol
            pass
    
    def on_protocol_changed(self, event=None):
        """Handle protocol selection change"""
        if not self.auto_detect_var.get():
            # Re-parse recent messages with new protocol
            self.reparse_messages()
    
    def on_message_selected(self, event):
        """Handle message selection in tree"""
        selection = self.message_tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        try:
            index = int(self.message_tree.item(item_id)['values'][0])  # Hidden index
            if 0 <= index < len(self.recent_messages):
                self.display_message_details(self.recent_messages[index])
        except (ValueError, IndexError):
            pass
    
    def add_message(self, message: ParsedMessage, direction: str):
        """Add a new parsed message to the display"""
        # Add to recent messages
        self.recent_messages.append(message)
        if len(self.recent_messages) > self.max_recent_messages:
            self.recent_messages.pop(0)
        
        # Update statistics
        self.statistics.update(message)
        
        # Add to tree
        time_str = message.timestamp.strftime("%H:%M:%S")
        valid_str = "✓" if message.is_valid else "✗"
        
        # Color coding
        if message.is_valid:
            tags = ('valid',)
        else:
            tags = ('invalid',)
        
        self.message_tree.insert('', 0, values=(
            len(self.recent_messages) - 1,  # Hidden index
            time_str,
            direction,
            message.protocol.value,
            message.description,
            valid_str
        ), tags=tags)
        
        # Configure tags
        self.message_tree.tag_configure('valid', foreground='green')
        self.message_tree.tag_configure('invalid', foreground='red')
        
        # Limit tree items
        children = self.message_tree.get_children()
        if len(children) > self.max_recent_messages:
            self.message_tree.delete(children[-1])
        
        # Update statistics display
        self.update_statistics_display()
    
    def display_message_details(self, message: ParsedMessage):
        """Display detailed information about a message"""
        # Clear previous content
        self.parsed_text.delete(1.0, tk.END)
        self.raw_text.delete(1.0, tk.END)
        
        # Display parsed data
        parsed_info = f"Protocol: {message.protocol.value}\n"
        parsed_info += f"Timestamp: {message.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]}\n"
        parsed_info += f"Valid: {'Yes' if message.is_valid else 'No'}\n"
        
        if message.error_message:
            parsed_info += f"Error: {message.error_message}\n"
        
        parsed_info += f"Description: {message.description}\n\n"
        
        if message.parsed_data:
            parsed_info += "Parsed Fields:\n"
            for key, value in message.parsed_data.items():
                parsed_info += f"  {key}: {value}\n"
        
        self.parsed_text.insert(tk.END, parsed_info)
        
        # Display raw data
        raw_info = f"Length: {len(message.raw_data)} bytes\n\n"
        raw_info += "Hexadecimal:\n"
        
        # Format hex dump
        hex_data = message.raw_data
        for i in range(0, len(hex_data), 16):
            chunk = hex_data[i:i+16]
            hex_str = ' '.join(f'{b:02X}' for b in chunk)
            ascii_str = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
            raw_info += f"{i:04X}: {hex_str:<48} |{ascii_str}|\n"
        
        raw_info += "\nASCII (if printable):\n"
        try:
            ascii_text = message.raw_data.decode('ascii', errors='replace')
            raw_info += ascii_text
        except:
            raw_info += "(Not valid ASCII)"
        
        self.raw_text.insert(tk.END, raw_info)
    
    def update_statistics_display(self):
        """Update the statistics tree display"""
        # Clear existing items
        for item in self.stats_tree.get_children():
            self.stats_tree.delete(item)
        
        # Add protocol statistics
        for protocol in ProtocolType:
            messages = self.statistics.message_counts[protocol]
            bytes_count = self.statistics.byte_counts[protocol]
            errors = self.statistics.error_counts[protocol]
            
            if messages > 0:  # Only show protocols with activity
                self.stats_tree.insert('', tk.END, text=protocol.value,
                                     values=(messages, bytes_count, errors))
        
        # Add totals
        summary = self.statistics.get_summary()
        self.stats_tree.insert('', tk.END, text="TOTAL",
                             values=(summary['total_messages'], 
                                   summary['total_bytes'],
                                   summary['total_errors']))
    
    def reset_statistics(self):
        """Reset all statistics"""
        if messagebox.askyesno("Reset Statistics", "Are you sure you want to reset all statistics?"):
            self.statistics.reset()
            self.recent_messages.clear()
            
            # Clear displays
            for item in self.stats_tree.get_children():
                self.stats_tree.delete(item)
            for item in self.message_tree.get_children():
                self.message_tree.delete(item)
            
            self.parsed_text.delete(1.0, tk.END)
            self.raw_text.delete(1.0, tk.END)
    
    def export_statistics(self):
        """Export statistics to JSON file"""
        try:
            from tkinter import filedialog
            
            filename = filedialog.asksaveasfilename(
                title="Export Protocol Statistics",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                summary = self.statistics.get_summary()
                
                # Add detailed breakdown
                export_data = {
                    'export_time': datetime.now().isoformat(),
                    'summary': summary,
                    'protocol_details': {}
                }
                
                for protocol in ProtocolType:
                    export_data['protocol_details'][protocol.value] = {
                        'messages': self.statistics.message_counts[protocol],
                        'bytes': self.statistics.byte_counts[protocol],
                        'errors': self.statistics.error_counts[protocol]
                    }
                
                with open(filename, 'w') as f:
                    json.dump(export_data, f, indent=2)
                
                messagebox.showinfo("Export Complete", f"Statistics exported to {filename}")
        
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export statistics: {str(e)}")
    
    def reparse_messages(self):
        """Re-parse recent messages with current protocol settings"""
        # This would re-parse messages if protocol is changed
        # Implementation depends on how messages are stored
        pass
    
    def update_display(self):
        """Update the display (called periodically)"""
        # This method can be called periodically to refresh the display
        pass
    
    def get_current_protocol(self) -> ProtocolType:
        """Get the currently selected protocol"""
        if self.auto_detect_var.get():
            return None  # Auto-detect
        else:
            protocol_name = self.protocol_var.get()
            for protocol in ProtocolType:
                if protocol.value == protocol_name:
                    return protocol
            return ProtocolType.RAW
