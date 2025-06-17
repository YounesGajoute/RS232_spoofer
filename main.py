#!/usr/bin/env python3
"""
RS232 Protocol Spoofer/Emulator v2.0
Main application entry point

A comprehensive tool for intercepting, analyzing, and modifying
RS232 serial communication with protocol-specific parsing.

Author: RS232 Spoofer Team
License: MIT
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import logging

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from gui.main_window import MainWindow
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all required modules are installed:")
    print("pip3 install pyserial")
    sys.exit(1)

def setup_logging():
    """Setup application logging"""
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_dir, 'application.log')),
            logging.StreamHandler()
        ]
    )

def check_permissions():
    """Check if user has permissions for serial ports"""
    import grp
    import pwd
    
    try:
        # Check if user is in dialout group
        user = pwd.getpwuid(os.getuid()).pw_name
        dialout_group = grp.getgrnam('dialout')
        
        if user not in dialout_group.gr_mem:
            messagebox.showwarning(
                "Permission Warning",
                f"User '{user}' is not in the 'dialout' group.\n\n"
                "You may not have permission to access serial ports.\n\n"
                "To fix this, run:\n"
                "sudo usermod -a -G dialout $USER\n\n"
                "Then log out and back in."
            )
    except (KeyError, OSError):
        # Group doesn't exist or other error - continue anyway
        pass

def main():
    """Main application entry point"""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting RS232 Protocol Spoofer/Emulator v2.0")
    
    try:
        # Check permissions
        check_permissions()
        
        # Create and run the main application
        app = MainWindow()
        app.run()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        messagebox.showerror("Application Error", f"An unexpected error occurred:\n{str(e)}")
    finally:
        logger.info("Application shutdown")

if __name__ == "__main__":
    main()
