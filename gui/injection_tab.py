"""
Manual Injection tab for RS232 Spoofer
Allows manual sending of data to either port
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from datetime import datetime
import threading

class InjectionTab:
    def __init__(self, parent_notebook, serial_manager):
        self.serial_manager = serial_manager
        
        # Create the tab frame
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="Manual Injection")
        
        # History storage
        self.injection_history = []
        self.max_history = 100
        
        self.setup_ui()

    def setup_ui(self):
        """Setup the injection UI"""
        # Create main paned window
        main_paned = ttk.PanedWindow(self.frame, orient=tk.VERTICAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Top section - Injection controls
        top_frame = ttk.Frame(main_paned)
        main_paned.add(top_frame, weight=2)
        
        # Bottom section - History
        bottom_frame = ttk.Frame(main_paned)
        main_paned.add(bottom_frame, weight=1)
        
        self.setup_injection_controls(top_frame)
        self.setup_history_section(bottom_frame)

    def setup_injection_controls(self, parent):
        """Setup injection control section"""
        # Target selection
        target_frame = ttk.LabelFrame(parent, text="Target Port")
        target_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.target_port = tk.StringVar(value="A")
        port_frame = ttk.Frame(target_frame)
        port_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Radiobutton(port_frame, text="Port A", variable=self.target_port, value="A").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(port_frame, text="Port B", variable=self.target_port, value="B").pack(side=tk.LEFT, padx=10)
        
        # Format selection
        format_frame = ttk.LabelFrame(parent, text="Data Format")
        format_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.data_format = tk.StringVar(value="ascii")
        format_controls = ttk.Frame(format_frame)
        format_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Radiobutton(format_controls, text="ASCII", variable=self.data_format, 
                       value="ascii", command=self.on_format_changed).pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(format_controls, text="HEX", variable=self.data_format, 
                       value="hex", command=self.on_format_changed).pack(side=tk.LEFT, padx=10)
        
        # Data input
        input_frame = ttk.LabelFrame(parent, text="Data to Send")
        input_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Input text area
        self.data_input = scrolledtext.ScrolledText(input_frame, height=8, wrap=tk.WORD)
        self.data_input.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Help text
        self.help_label = ttk.Label(input_frame, text="ASCII mode: Enter text directly")
        self.help_label.pack(anchor=tk.W, padx=5, pady=2)
        
        # Control buttons
        button_frame = ttk.Frame(input_frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Send Data", command=self.send_data).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Clear", command=self.clear_input).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Load from History", command=self.load_from_history).pack(side=tk.LEFT, padx=10)
        
        # Quick send buttons
        quick_frame = ttk.LabelFrame(parent, text="Quick Send")
        quick_frame.pack(fill=tk.X, padx=5, pady=5)
        
        quick_buttons = ttk.Frame(quick_frame)
        quick_buttons.pack(fill=tk.X, padx=5, pady=5)
        
        # Common commands
        ttk.Button(quick_buttons, text="CR", command=lambda: self.quick_send('\r')).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_buttons, text="LF", command=lambda: self.quick_send('\n')).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_buttons, text="CR+LF", command=lambda: self.quick_send('\r\n')).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_buttons, text="NULL", command=lambda: self.quick_send('\x00')).pack(side=tk.LEFT, padx=2)
        ttk.Button(quick_buttons, text="ESC", command=lambda: self.quick_send('\x1b')).pack(side=tk.LEFT, padx=2)

    def setup_history_section(self, parent):
        """Setup injection history section"""
        history_frame = ttk.LabelFrame(parent, text="Injection History")
        history_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # History list
        self.history_tree = ttk.Treeview(history_frame, 
                                        columns=('Time', 'Port', 'Format', 'Data', 'Status'),
                                        show='headings', height=6)
        
        self.history_tree.heading('Time', text='Time')
        self.history_tree.heading('Port', text='Port')
        self.history_tree.heading('Format', text='Format')
        self.history_tree.heading('Data', text='Data')
        self.history_tree.heading('Status', text='Status')
        
        self.history_tree.column('Time', width=80)
        self.history_tree.column('Port', width=40)
        self.history_tree.column('Format', width=60)
        self.history_tree.column('Data', width=200)
        self.history_tree.column('Status', width=60)
        
        history_scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=history_scrollbar.set)
        
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.history_tree.bind('<Double-1>', self.on_history_double_click)
        
        # History controls
        history_controls = ttk.Frame(parent)
        history_controls.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(history_controls, text="Clear History", command=self.clear_history).pack(side=tk.LEFT, padx=2)
        ttk.Button(history_controls, text="Export History", command=self.export_history).pack(side=tk.LEFT, padx=2)

    def on_format_changed(self):
        """Handle format change"""
        format_type = self.data_format.get()
        if format_type == "ascii":
            self.help_label.config(text="ASCII mode: Enter text directly")
        else:
            self.help_label.config(text="HEX mode: Enter hex bytes separated by spaces (e.g., 41 42 43)")

    def send_data(self):
        """Send data to the selected port"""
        if not self.serial_manager.is_connected:
            messagebox.showwarning("Not Connected", "Please connect to ports first.")
            return
        
        # Get input data
        input_text = self.data_input.get(1.0, tk.END).strip()
        if not input_text:
            messagebox.showwarning("No Data", "Please enter data to send.")
            return
        
        target = self.target_port.get()
        format_type = self.data_format.get()
        
        try:
            # Convert data based on format
            if format_type == "ascii":
                data = input_text.encode('utf-8')
            else:  # hex
                # Remove spaces and convert hex to bytes
                hex_string = input_text.replace(' ', '').replace('\n', '').replace('\t', '')
                if len(hex_string) % 2 != 0:
                    raise ValueError("Hex string must have even number of characters")
                data = bytes.fromhex(hex_string)
            
            # Send data
            self.serial_manager.inject_data(data, target)
            
            # Add to history
            self.add_to_history(target, format_type, input_text, "Sent")
            
            # Show success message
            messagebox.showinfo("Success", f"Data sent to Port {target}")
            
        except ValueError as e:
            messagebox.showerror("Format Error", f"Invalid data format: {str(e)}")
        except Exception as e:
            messagebox.showerror("Send Error", f"Failed to send data: {str(e)}")
            self.add_to_history(target, format_type, input_text, "Failed")

    def quick_send(self, data: str):
        """Quick send common control characters"""
        if not self.serial_manager.is_connected:
            messagebox.showwarning("Not Connected", "Please connect to ports first.")
            return
        
        target = self.target_port.get()
        
        try:
            data_bytes = data.encode('utf-8')
            self.serial_manager.inject_data(data_bytes, target)
            
            # Add to history
            display_data = repr(data)[1:-1]  # Remove quotes from repr
            self.add_to_history(target, "ascii", display_data, "Sent")
            
        except Exception as e:
            messagebox.showerror("Send Error", f"Failed to send data: {str(e)}")

    def clear_input(self):
        """Clear the input area"""
        self.data_input.delete(1.0, tk.END)

    def load_from_history(self):
        """Load selected history item into input"""
        selection = self.history_tree.selection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a history item to load.")
            return
        
        item_id = selection[0]
        values = self.history_tree.item(item_id)['values']
        
        if len(values) >= 4:
            port = values[1]
            format_type = values[2]
            data = values[3]
            
            # Set format and port
            self.target_port.set(port)
            self.data_format.set(format_type.lower())
            self.on_format_changed()
            
            # Load data
            self.data_input.delete(1.0, tk.END)
            self.data_input.insert(1.0, data)

    def on_history_double_click(self, event):
        """Handle double-click on history item"""
        self.load_from_history()

    def add_to_history(self, port: str, format_type: str, data: str, status: str):
        """Add entry to injection history"""
        timestamp = datetime.now()
        
        # Create history entry
        entry = {
            'timestamp': timestamp,
            'port': port,
            'format': format_type,
            'data': data,
            'status': status
        }
        
        # Add to storage
        self.injection_history.append(entry)
        
        # Limit history size
        if len(self.injection_history) > self.max_history:
            self.injection_history.pop(0)
        
        # Add to tree
        time_str = timestamp.strftime("%H:%M:%S")
        data_preview = data[:50] + "..." if len(data) > 50 else data
        
        # Color coding
        if status == "Sent":
            tags = ('success',)
        else:
            tags = ('error',)
        
        self.history_tree.insert('', 0, values=(
            time_str, port, format_type.upper(), data_preview, status
        ), tags=tags)
        
        # Configure tags
        self.history_tree.tag_configure('success', foreground='green')
        self.history_tree.tag_configure('error', foreground='red')
        
        # Limit tree items
        children = self.history_tree.get_children()
        if len(children) > self.max_history:
            self.history_tree.delete(children[-1])

    def clear_history(self):
        """Clear injection history"""
        if messagebox.askyesno("Clear History", "Are you sure you want to clear the injection history?"):
            self.injection_history.clear()
            
            # Clear tree
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)

    def export_history(self):
        """Export injection history"""
        if not self.injection_history:
            messagebox.showinfo("No History", "No injection history to export.")
            return
        
        try:
            from tkinter import filedialog
            import csv
            
            filename = filedialog.asksaveasfilename(
                title="Export Injection History",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    
                    # Write header
                    writer.writerow(['Timestamp', 'Port', 'Format', 'Data', 'Status'])
                    
                    # Write data
                    for entry in self.injection_history:
                        writer.writerow([
                            entry['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
                            entry['port'],
                            entry['format'],
                            entry['data'],
                            entry['status']
                        ])
                
                messagebox.showinfo("Export Complete", f"History exported to {filename}")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export history: {str(e)}")
