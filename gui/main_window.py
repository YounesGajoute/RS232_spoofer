"""
Enhanced Main Window with Protocol Analysis Support
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime

from core.serial_manager import SerialManager
from core.logger import DataLogger
from core.config import ConfigManager
from core.protocol_parser import ParsedMessage

from .dashboard_tab import DashboardTab
from .rules_tab import RulesTab
from .injection_tab import InjectionTab
from .settings_tab import SettingsTab
from .protocol_tab import ProtocolTab

class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("RS232 Protocol Spoofer/Emulator v2.0")
        self.root.geometry("1200x800")
        
        # Initialize core components
        self.serial_manager = SerialManager()
        self.logger = DataLogger()
        self.config_manager = ConfigManager()
        
        # Load configuration
        self.config = self.config_manager.load_config()
        self.apply_config()
        
        # Setup callbacks
        self.serial_manager.set_data_callback(self.on_data_received)
        self.serial_manager.set_status_callback(self.on_status_changed)
        self.serial_manager.set_protocol_callback(self.on_protocol_message)
        
        # Create GUI
        self.setup_ui()
        
        # Start update timer
        self.update_timer()
        
        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_ui(self):
        """Setup the main user interface"""
        # Create main menu
        self.create_menu()
        
        # Create status bar
        self.create_status_bar()
        
        # Create main notebook
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        self.dashboard_tab = DashboardTab(self.notebook, self.serial_manager, self.logger)
        self.protocol_tab = ProtocolTab(self.notebook, self.serial_manager, self.logger)
        self.rules_tab = RulesTab(self.notebook, self.serial_manager)
        self.injection_tab = InjectionTab(self.notebook, self.serial_manager)
        self.settings_tab = SettingsTab(self.notebook, self.config_manager, self.on_config_changed)

    def create_menu(self):
        """Create the main menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export Logs...", command=self.export_logs)
        file_menu.add_command(label="Export Protocol Stats...", command=self.export_protocol_stats)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Connection menu
        conn_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Connection", menu=conn_menu)
        conn_menu.add_command(label="Connect", command=self.connect_ports)
        conn_menu.add_command(label="Disconnect", command=self.disconnect_ports)
        conn_menu.add_separator()
        conn_menu.add_command(label="Start Monitoring", command=self.start_monitoring)
        conn_menu.add_command(label="Stop Monitoring", command=self.stop_monitoring)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Reset Statistics", command=self.reset_statistics)
        tools_menu.add_command(label="Clear Logs", command=self.clear_logs)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def create_status_bar(self):
        """Create the status bar"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = ttk.Label(self.status_frame, text="Ready")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Connection status
        self.connection_label = ttk.Label(self.status_frame, text="Disconnected", foreground="red")
        self.connection_label.pack(side=tk.RIGHT, padx=5)

    def apply_config(self):
        """Apply loaded configuration"""
        self.serial_manager.configure_ports(
            self.config.get('port_a', '/dev/ttyUSB0'),
            self.config.get('port_b', '/dev/ttyUSB1'),
            self.config.get('baud_rate', 9600),
            self.config.get('timeout', 1.0)
        )
        
        self.logger.configure(
            self.config.get('log_folder', './logs'),
            self.config.get('log_format', 'both')
        )
        
        # Apply spoofing rules
        rules = self.config.get('spoofing_rules', [])
        self.serial_manager.set_spoofing_rules(rules)

    def on_config_changed(self, config):
        """Handle configuration changes"""
        self.config = config
        self.apply_config()
        self.config_manager.save_config(config)

    def on_data_received(self, data, direction, timestamp, modified_data=None, spoofed=False):
        """Handle received data"""
        # Log the data
        self.logger.log_data(data, direction, timestamp, modified_data, spoofed)
        
        # Update dashboard
        if hasattr(self, 'dashboard_tab'):
            self.dashboard_tab.add_log_entry(data, direction, timestamp, modified_data, spoofed)

    def on_protocol_message(self, message: ParsedMessage, direction: str):
        """Handle parsed protocol message"""
        if hasattr(self, 'protocol_tab'):
            self.protocol_tab.add_message(message, direction)

    def on_status_changed(self, status):
        """Handle status changes"""
        self.status_label.config(text=status)
        
        # Update connection status
        if self.serial_manager.is_connected:
            self.connection_label.config(text="Connected", foreground="green")
        else:
            self.connection_label.config(text="Disconnected", foreground="red")

    def connect_ports(self):
        """Connect to serial ports"""
        if self.serial_manager.connect():
            messagebox.showinfo("Connection", "Successfully connected to both ports")
        else:
            messagebox.showerror("Connection Error", "Failed to connect to ports")

    def disconnect_ports(self):
        """Disconnect from serial ports"""
        self.serial_manager.disconnect()

    def start_monitoring(self):
        """Start monitoring ports"""
        if not self.serial_manager.is_connected:
            messagebox.showwarning("Not Connected", "Please connect to ports first")
            return
        
        if self.serial_manager.start_monitoring():
            messagebox.showinfo("Monitoring", "Monitoring started")

    def stop_monitoring(self):
        """Stop monitoring ports"""
        self.serial_manager.stop_monitoring_ports()

    def reset_statistics(self):
        """Reset all statistics"""
        if messagebox.askyesno("Reset Statistics", "Reset all statistics and protocol data?"):
            self.serial_manager.reset_statistics()
            if hasattr(self, 'protocol_tab'):
                self.protocol_tab.reset_statistics()
            if hasattr(self, 'dashboard_tab'):
                self.dashboard_tab.reset_statistics()

    def clear_logs(self):
        """Clear log displays"""
        if messagebox.askyesno("Clear Logs", "Clear all log displays?"):
            if hasattr(self, 'dashboard_tab'):
                self.dashboard_tab.clear_logs()

    def export_logs(self):
        """Export logs to file"""
        try:
            from tkinter import filedialog
            filename = filedialog.asksaveasfilename(
                title="Export Logs",
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
            )
            if filename:
                self.logger.export_logs(filename)
                messagebox.showinfo("Export Complete", f"Logs exported to {filename}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export logs: {str(e)}")

    def export_protocol_stats(self):
        """Export protocol statistics"""
        if hasattr(self, 'protocol_tab'):
            self.protocol_tab.export_statistics()

    def show_about(self):
        """Show about dialog"""
        about_text = """RS232 Protocol Spoofer/Emulator v2.0

A comprehensive tool for intercepting, analyzing, and modifying
RS232 serial communication with protocol-specific parsing.

Features:
• Bidirectional RS232 communication
• Protocol parsing (Modbus RTU/ASCII, NMEA, ASCII)
• Real-time spoofing and modification
• Comprehensive logging and statistics
• Manual packet injection

Developed for Raspberry Pi 5
Python 3 with Tkinter GUI"""
        
        messagebox.showinfo("About", about_text)

    def update_timer(self):
        """Update timer for periodic tasks"""
        # Update displays
        if hasattr(self, 'dashboard_tab'):
            self.dashboard_tab.update_display()
        if hasattr(self, 'protocol_tab'):
            self.protocol_tab.update_display()
        
        # Schedule next update
        self.root.after(1000, self.update_timer)

    def on_closing(self):
        """Handle application closing"""
        if self.serial_manager.is_monitoring:
            if messagebox.askyesno("Exit", "Monitoring is active. Stop monitoring and exit?"):
                self.serial_manager.stop_monitoring_ports()
                self.serial_manager.disconnect()
                self.root.destroy()
        else:
            self.serial_manager.disconnect()
            self.root.destroy()

    def run(self):
        """Run the application"""
        self.root.mainloop()

def main():
    app = MainWindow()
    app.run()

if __name__ == "__main__":
    main()
