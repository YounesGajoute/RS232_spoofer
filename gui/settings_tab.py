"""
Settings tab for RS232 Spoofer
Manages application configuration
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os

class SettingsTab:
    def __init__(self, parent_notebook, config_manager, config_callback):
        self.config_manager = config_manager
        self.config_callback = config_callback
        
        # Create the tab frame
        self.frame = ttk.Frame(parent_notebook)
        parent_notebook.add(self.frame, text="Settings")
        
        # Current configuration
        self.config = {}
        
        self.setup_ui()

    def setup_ui(self):
        """Setup the settings UI"""
        # Create notebook for different setting categories
        self.settings_notebook = ttk.Notebook(self.frame)
        self.settings_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create setting tabs
        self.setup_serial_settings()
        self.setup_logging_settings()
        self.setup_protocol_settings()
        self.setup_gui_settings()
        self.setup_advanced_settings()
        
        # Control buttons
        button_frame = ttk.Frame(self.frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(button_frame, text="Apply Settings", command=self.apply_settings).pack(side=tk.RIGHT, padx=2)
        ttk.Button(button_frame, text="Reset to Defaults", command=self.reset_to_defaults).pack(side=tk.RIGHT, padx=2)
        ttk.Button(button_frame, text="Import Config", command=self.import_config).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="Export Config", command=self.export_config).pack(side=tk.LEFT, padx=2)

    def setup_serial_settings(self):
        """Setup serial port settings"""
        serial_frame = ttk.Frame(self.settings_notebook)
        self.settings_notebook.add(serial_frame, text="Serial Ports")
        
        # Port configuration
        ports_frame = ttk.LabelFrame(serial_frame, text="Port Configuration")
        ports_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Port A
        ttk.Label(ports_frame, text="Port A:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.port_a_var = tk.StringVar()
        port_a_combo = ttk.Combobox(ports_frame, textvariable=self.port_a_var, width=20)
        port_a_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Port B
        ttk.Label(ports_frame, text="Port B:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.port_b_var = tk.StringVar()
        port_b_combo = ttk.Combobox(ports_frame, textvariable=self.port_b_var, width=20)
        port_b_combo.grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Populate port lists
        self.populate_port_lists([port_a_combo, port_b_combo])
        
        # Refresh button
        ttk.Button(ports_frame, text="Refresh Ports", 
                  command=lambda: self.populate_port_lists([port_a_combo, port_b_combo])).grid(row=0, column=2, padx=10, pady=2)
        
        # Communication parameters
        comm_frame = ttk.LabelFrame(serial_frame, text="Communication Parameters")
        comm_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Baud rate
        ttk.Label(comm_frame, text="Baud Rate:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.baud_rate_var = tk.StringVar()
        baud_combo = ttk.Combobox(comm_frame, textvariable=self.baud_rate_var, 
                                 values=['300', '600', '1200', '2400', '4800', '9600', '19200', '38400', '57600', '115200'],
                                 state="readonly", width=10)
        baud_combo.grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Data bits
        ttk.Label(comm_frame, text="Data Bits:").grid(row=0, column=2, sticky=tk.W, padx=20, pady=2)
        self.data_bits_var = tk.StringVar()
        ttk.Combobox(comm_frame, textvariable=self.data_bits_var, 
                    values=['5', '6', '7', '8'], state="readonly", width=5).grid(row=0, column=3, sticky=tk.W, padx=5, pady=2)
        
        # Parity
        ttk.Label(comm_frame, text="Parity:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.parity_var = tk.StringVar()
        ttk.Combobox(comm_frame, textvariable=self.parity_var, 
                    values=['none', 'even', 'odd', 'mark', 'space'], state="readonly", width=10).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Stop bits
        ttk.Label(comm_frame, text="Stop Bits:").grid(row=1, column=2, sticky=tk.W, padx=20, pady=2)
        self.stop_bits_var = tk.StringVar()
        ttk.Combobox(comm_frame, textvariable=self.stop_bits_var, 
                    values=['1', '1.5', '2'], state="readonly", width=5).grid(row=1, column=3, sticky=tk.W, padx=5, pady=2)
        
        # Flow control
        ttk.Label(comm_frame, text="Flow Control:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.flow_control_var = tk.StringVar()
        ttk.Combobox(comm_frame, textvariable=self.flow_control_var, 
                    values=['none', 'xonxoff', 'rtscts', 'dsrdtr'], state="readonly", width=10).grid(row=2, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Timeout
        ttk.Label(comm_frame, text="Timeout (s):").grid(row=2, column=2, sticky=tk.W, padx=20, pady=2)
        self.timeout_var = tk.StringVar()
        ttk.Entry(comm_frame, textvariable=self.timeout_var, width=8).grid(row=2, column=3, sticky=tk.W, padx=5, pady=2)

    def setup_logging_settings(self):
        """Setup logging settings"""
        logging_frame = ttk.Frame(self.settings_notebook)
        self.settings_notebook.add(logging_frame, text="Logging")
        
        # Log folder
        folder_frame = ttk.LabelFrame(logging_frame, text="Log Storage")
        folder_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(folder_frame, text="Log Folder:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.log_folder_var = tk.StringVar()
        ttk.Entry(folder_frame, textvariable=self.log_folder_var, width=40).grid(row=0, column=1, sticky=tk.EW, padx=5, pady=2)
        ttk.Button(folder_frame, text="Browse", command=self.browse_log_folder).grid(row=0, column=2, padx=5, pady=2)
        
        folder_frame.columnconfigure(1, weight=1)
        
        # Log format
        format_frame = ttk.LabelFrame(logging_frame, text="Log Format")
        format_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.log_format_var = tk.StringVar()
        ttk.Radiobutton(format_frame, text="ASCII only", variable=self.log_format_var, value="ascii").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Radiobutton(format_frame, text="HEX only", variable=self.log_format_var, value="hex").pack(anchor=tk.W, padx=5, pady=2)
        ttk.Radiobutton(format_frame, text="Both ASCII and HEX", variable=self.log_format_var, value="both").pack(anchor=tk.W, padx=5, pady=2)
        
        # Log retention
        retention_frame = ttk.LabelFrame(logging_frame, text="Log Retention")
        retention_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(retention_frame, text="Max Log Files:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.max_log_files_var = tk.StringVar()
        ttk.Entry(retention_frame, textvariable=self.max_log_files_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(retention_frame, text="Log Level:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.log_level_var = tk.StringVar()
        ttk.Combobox(retention_frame, textvariable=self.log_level_var, 
                    values=['DEBUG', 'INFO', 'WARNING', 'ERROR'], state="readonly", width=10).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)

    def setup_protocol_settings(self):
        """Setup protocol settings"""
        protocol_frame = ttk.Frame(self.settings_notebook)
        self.settings_notebook.add(protocol_frame, text="Protocol")
        
        # Auto-detection
        detection_frame = ttk.LabelFrame(protocol_frame, text="Protocol Detection")
        detection_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.auto_detect_var = tk.BooleanVar()
        ttk.Checkbutton(detection_frame, text="Enable automatic protocol detection", 
                       variable=self.auto_detect_var).pack(anchor=tk.W, padx=5, pady=2)
        
        ttk.Label(detection_frame, text="Default Protocol:").pack(anchor=tk.W, padx=5, pady=2)
        self.default_protocol_var = tk.StringVar()
        ttk.Combobox(detection_frame, textvariable=self.default_protocol_var, 
                    values=['Raw', 'Modbus RTU', 'Modbus ASCII', 'NMEA', 'ASCII Delimited'], 
                    state="readonly", width=20).pack(anchor=tk.W, padx=5, pady=2)
        
        # Timeouts
        timeout_frame = ttk.LabelFrame(protocol_frame, text="Protocol Timeouts")
        timeout_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(timeout_frame, text="Protocol Detection Timeout (s):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.protocol_timeout_var = tk.StringVar()
        ttk.Entry(timeout_frame, textvariable=self.protocol_timeout_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(timeout_frame, text="Message Timeout (s):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.message_timeout_var = tk.StringVar()
        ttk.Entry(timeout_frame, textvariable=self.message_timeout_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)

    def setup_gui_settings(self):
        """Setup GUI settings"""
        gui_frame = ttk.Frame(self.settings_notebook)
        self.settings_notebook.add(gui_frame, text="Interface")
        
        # Appearance
        appearance_frame = ttk.LabelFrame(gui_frame, text="Appearance")
        appearance_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(appearance_frame, text="Theme:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.theme_var = tk.StringVar()
        ttk.Combobox(appearance_frame, textvariable=self.theme_var, 
                    values=['light', 'dark'], state="readonly", width=10).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(appearance_frame, text="Window Size:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.window_geometry_var = tk.StringVar()
        ttk.Entry(appearance_frame, textvariable=self.window_geometry_var, width=15).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Behavior
        behavior_frame = ttk.LabelFrame(gui_frame, text="Behavior")
        behavior_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.auto_start_var = tk.BooleanVar()
        ttk.Checkbutton(behavior_frame, text="Auto-start monitoring on connection", 
                       variable=self.auto_start_var).pack(anchor=tk.W, padx=5, pady=2)
        
        ttk.Label(behavior_frame, text="Update Interval (ms):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.update_interval_var = tk.StringVar()
        ttk.Entry(behavior_frame, textvariable=self.update_interval_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)

    def setup_advanced_settings(self):
        """Setup advanced settings"""
        advanced_frame = ttk.Frame(self.settings_notebook)
        self.settings_notebook.add(advanced_frame, text="Advanced")
        
        # Buffer settings
        buffer_frame = ttk.LabelFrame(advanced_frame, text="Buffer Settings")
        buffer_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(buffer_frame, text="Buffer Size (bytes):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=2)
        self.buffer_size_var = tk.StringVar()
        ttk.Entry(buffer_frame, textvariable=self.buffer_size_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=5, pady=2)
        
        ttk.Label(buffer_frame, text="Max Message Size (bytes):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=2)
        self.max_message_size_var = tk.StringVar()
        ttk.Entry(buffer_frame, textvariable=self.max_message_size_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=5, pady=2)
        
        # Performance
        performance_frame = ttk.LabelFrame(advanced_frame, text="Performance")
        performance_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(performance_frame, text="These settings affect performance and should only be changed by advanced users.").pack(anchor=tk.W, padx=5, pady=2)
        
        # Reset button
        ttk.Button(advanced_frame, text="Reset Advanced Settings", 
                  command=self.reset_advanced_settings).pack(pady=10)

    def populate_port_lists(self, combo_boxes):
        """Populate serial port combo boxes"""
        try:
            import serial.tools.list_ports
            ports = [port.device for port in serial.tools.list_ports.comports()]
            
            # Add common Linux/Unix ports
            common_ports = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyUSB2', '/dev/ttyUSB3',
                           '/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyS0', '/dev/ttyS1']
            
            for port in common_ports:
                if port not in ports and os.path.exists(port):
                    ports.append(port)
            
            # Update combo boxes
            for combo in combo_boxes:
                combo['values'] = ports
                
        except ImportError:
            # Fallback if pyserial tools not available
            common_ports = ['/dev/ttyUSB0', '/dev/ttyUSB1', '/dev/ttyUSB2', '/dev/ttyUSB3',
                           '/dev/ttyACM0', '/dev/ttyACM1', '/dev/ttyS0', '/dev/ttyS1']
            for combo in combo_boxes:
                combo['values'] = common_ports

    def browse_log_folder(self):
        """Browse for log folder"""
        folder = filedialog.askdirectory(title="Select Log Folder")
        if folder:
            self.log_folder_var.set(folder)

    def load_config(self, config):
        """Load configuration into UI"""
        self.config = config
        
        # Serial settings
        self.port_a_var.set(config.get('port_a', '/dev/ttyUSB0'))
        self.port_b_var.set(config.get('port_b', '/dev/ttyUSB1'))
        self.baud_rate_var.set(str(config.get('baud_rate', 9600)))
        self.data_bits_var.set(str(config.get('data_bits', 8)))
        self.parity_var.set(config.get('parity', 'none'))
        self.stop_bits_var.set(str(config.get('stop_bits', 1)))
        self.flow_control_var.set(config.get('flow_control', 'none'))
        self.timeout_var.set(str(config.get('timeout', 1.0)))
        
        # Logging settings
        self.log_folder_var.set(config.get('log_folder', './logs'))
        self.log_format_var.set(config.get('log_format', 'both'))
        self.max_log_files_var.set(str(config.get('max_log_files', 30)))
        self.log_level_var.set(config.get('log_level', 'INFO'))
        
        # Protocol settings
        self.auto_detect_var.set(config.get('auto_detect_protocol', True))
        self.default_protocol_var.set(config.get('default_protocol', 'Raw'))
        self.protocol_timeout_var.set(str(config.get('protocol_timeout', 5.0)))
        self.message_timeout_var.set(str(config.get('message_timeout', 1.0)))
        
        # GUI settings
        self.theme_var.set(config.get('theme', 'light'))
        self.window_geometry_var.set(config.get('window_geometry', '1200x800'))
        self.auto_start_var.set(config.get('auto_start', False))
        self.update_interval_var.set(str(config.get('update_interval', 1000)))
        
        # Advanced settings
        self.buffer_size_var.set(str(config.get('buffer_size', 4096)))
        self.max_message_size_var.set(str(config.get('max_message_size', 1024)))

    def apply_settings(self):
        """Apply current settings"""
        try:
            # Collect all settings
            new_config = {
                # Serial settings
                'port_a': self.port_a_var.get(),
                'port_b': self.port_b_var.get(),
                'baud_rate': int(self.baud_rate_var.get()),
                'data_bits': int(self.data_bits_var.get()),
                'parity': self.parity_var.get(),
                'stop_bits': float(self.stop_bits_var.get()),
                'flow_control': self.flow_control_var.get(),
                'timeout': float(self.timeout_var.get()),
                
                # Logging settings
                'log_folder': self.log_folder_var.get(),
                'log_format': self.log_format_var.get(),
                'max_log_files': int(self.max_log_files_var.get()),
                'log_level': self.log_level_var.get(),
                
                # Protocol settings
                'auto_detect_protocol': self.auto_detect_var.get(),
                'default_protocol': self.default_protocol_var.get(),
                'protocol_timeout': float(self.protocol_timeout_var.get()),
                'message_timeout': float(self.message_timeout_var.get()),
                
                # GUI settings
                'theme': self.theme_var.get(),
                'window_geometry': self.window_geometry_var.get(),
                'auto_start': self.auto_start_var.get(),
                'update_interval': int(self.update_interval_var.get()),
                
                # Advanced settings
                'buffer_size': int(self.buffer_size_var.get()),
                'max_message_size': int(self.max_message_size_var.get()),
                
                # Preserve existing settings
                'spoofing_enabled': self.config.get('spoofing_enabled', True),
                'spoofing_rules': self.config.get('spoofing_rules', [])
            }
            
            # Validate configuration
            validated_config = self.config_manager.validate_config(new_config)
            
            # Apply configuration
            if self.config_callback:
                self.config_callback(validated_config)
            
            messagebox.showinfo("Success", "Settings applied successfully.")
            
        except ValueError as e:
            messagebox.showerror("Validation Error", f"Invalid setting value: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to apply settings: {str(e)}")

    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        if messagebox.askyesno("Reset Settings", "Are you sure you want to reset all settings to defaults?"):
            default_config = self.config_manager.default_config.copy()
            self.load_config(default_config)
            messagebox.showinfo("Reset Complete", "All settings have been reset to defaults.")

    def reset_advanced_settings(self):
        """Reset only advanced settings"""
        if messagebox.askyesno("Reset Advanced", "Reset advanced settings to defaults?"):
            self.buffer_size_var.set(str(self.config_manager.default_config['buffer_size']))
            self.max_message_size_var.set(str(self.config_manager.default_config['max_message_size']))

    def import_config(self):
        """Import configuration from file"""
        filename = filedialog.askopenfilename(
            title="Import Configuration",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            imported_config = self.config_manager.import_config(filename)
            if imported_config:
                self.load_config(imported_config)
                messagebox.showinfo("Import Complete", "Configuration imported successfully.")
            else:
                messagebox.showerror("Import Error", "Failed to import configuration.")

    def export_config(self):
        """Export current configuration to file"""
        filename = filedialog.asksaveasfilename(
            title="Export Configuration",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            if self.config_manager.export_config(filename, self.config):
                messagebox.showinfo("Export Complete", f"Configuration exported to {filename}")
            else:
                messagebox.showerror("Export Error", "Failed to export configuration.")
