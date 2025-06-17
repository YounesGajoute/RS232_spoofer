# RS232 Protocol Spoofer/Emulator v2.0

A comprehensive tool for intercepting, analyzing, and modifying RS232 serial communication with advanced protocol-specific parsing capabilities. Designed specifically for Raspberry Pi 5 with a professional Tkinter GUI.

## 🚀 Features

### 📡 **Bidirectional RS232 Communication**
- Full-duplex real-time communication between two serial ports
- Configurable baud rates (300-115200), data bits, parity, stop bits
- Hardware and software flow control support
- Thread-based architecture for non-blocking operation

### 🔍 **Advanced Protocol Analysis**
- **Modbus RTU**: Binary format with CRC16 validation
- **Modbus ASCII**: ASCII format with LRC validation  
- **NMEA 0183**: GPS/marine data with checksum verification
- **ASCII Delimited**: CSV, semicolon, pipe-separated data
- **Custom Binary**: Hex dump analysis with pattern recognition
- **Auto-detection** based on data patterns and structure

### 🎯 **Intelligent Spoofing System**
- Pattern-based message replacement (ASCII and HEX formats)
- Real-time rule application with enable/disable toggles
- Protocol-aware spoofing with validation
- Rule import/export functionality
- Test mode for rule validation

### 📊 **Comprehensive Logging & Analysis**
- Daily CSV log files with timestamps
- Multiple display formats (ASCII, HEX, both)
- Protocol-specific log entries with parsed fields
- Real-time filtering and search capabilities
- Export functionality for external analysis
- Statistics tracking and performance metrics

### 🖥️ **Professional GUI Interface**
- **Dashboard Tab**: Live monitoring with color-coded logs and statistics
- **Protocol Analysis Tab**: Real-time message parsing with detailed breakdown
- **Spoofing Rules Tab**: Visual rule editor with validation and testing
- **Manual Injection Tab**: Packet injection with format selection and history
- **Settings Tab**: Complete configuration management with import/export

### ⚡ **Performance & Reliability**
- Multi-threaded design prevents GUI freezing
- Efficient data handling for high-speed streams (up to 115200 baud)
- Smart buffer management for incomplete messages
- Error handling and automatic recovery
- Memory-efficient circular buffers

## 📋 Requirements

### Hardware
- Raspberry Pi 5 (recommended) or Raspberry Pi 4
- Two USB-to-Serial adapters (FTDI, CH340, CP2102, etc.)
- Serial devices or equipment to monitor

### Software
- Raspberry Pi OS (64-bit recommended)
- Python 3.8 or higher
- Tkinter (included with Python)
- pyserial library

## 🔧 Installation

### Automatic Installation (Recommended)

```bash
# Clone or download the application
git clone https://github.com/your-repo/rs232-spoofer.git
cd rs232-spoofer

# Run the installation script
chmod +x install.sh
./install.sh
