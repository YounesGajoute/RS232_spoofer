#!/bin/bash

# RS232 Protocol Spoofer/Emulator Installation Script
# For Raspberry Pi OS and Debian-based systems

echo "Installing RS232 Protocol Spoofer/Emulator v2.0..."

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo "Please do not run this script as root"
    exit 1
fi

# Update package list
echo "Updating package list..."
sudo apt update

# Install Python3 and pip if not already installed
echo "Installing Python3 and pip..."
sudo apt install -y python3 python3-pip python3-venv python3-tk

# Install system dependencies
echo "Installing system dependencies..."
sudo apt install -y git

# Create application directory
APP_DIR="$HOME/rs232-spoofer"
echo "Creating application directory: $APP_DIR"
mkdir -p "$APP_DIR"

# Copy application files (assuming they're in current directory)
echo "Copying application files..."
cp -r . "$APP_DIR/"

# Create virtual environment
echo "Creating Python virtual environment..."
cd "$APP_DIR"
python3 -m venv venv

# Activate virtual environment and install dependencies
echo "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install pyserial

# Add user to dialout group for serial port access
echo "Adding user to dialout group..."
sudo usermod -a -G dialout $USER

# Create logs directory
echo "Creating logs directory..."
mkdir -p "$APP_DIR/logs"

# Create desktop entry
echo "Creating desktop entry..."
DESKTOP_FILE="$HOME/.local/share/applications/rs232-spoofer.desktop"
mkdir -p "$(dirname "$DESKTOP_FILE")"

cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=RS232 Protocol Spoofer
Comment=RS232 serial communication interceptor and analyzer
Exec=$APP_DIR/venv/bin/python $APP_DIR/main.py
Icon=$APP_DIR/icon.png
Terminal=false
Type=Application
Categories=Development;Electronics;
StartupNotify=true
EOF

# Make desktop file executable
chmod +x "$DESKTOP_FILE"

# Create launcher script
echo "Creating launcher script..."
cat > "$APP_DIR/run.sh" << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python main.py
EOF

chmod +x "$APP_DIR/run.sh"

# Create systemd service (optional)
echo "Creating systemd service..."
SERVICE_FILE="$HOME/.config/systemd/user/rs232-spoofer.service"
mkdir -p "$(dirname "$SERVICE_FILE")"

cat > "$SERVICE_FILE" << EOF
[Unit]
Description=RS232 Protocol Spoofer
After=graphical-session.target

[Service]
Type=simple
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/main.py
WorkingDirectory=$APP_DIR
Restart=on-failure
Environment=DISPLAY=:0

[Install]
WantedBy=default.target
EOF

# Enable systemd service for user
systemctl --user daemon-reload
systemctl --user enable rs232-spoofer.service

# Set permissions for serial ports (temporary)
echo "Setting temporary permissions for serial ports..."
sudo chmod 666 /dev/ttyUSB* 2>/dev/null || true
sudo chmod 666 /dev/ttyACM* 2>/dev/null || true

# Create udev rules for persistent permissions
echo "Creating udev rules for serial port permissions..."
sudo tee /etc/udev/rules.d/99-rs232-spoofer.rules > /dev/null << 'EOF'
# RS232 Spoofer - USB Serial devices
SUBSYSTEM=="tty", ATTRS{idVendor}=="*", ATTRS{idProduct}=="*", MODE="0666", GROUP="dialout"
KERNEL=="ttyUSB[0-9]*", MODE="0666", GROUP="dialout"
KERNEL=="ttyACM[0-9]*", MODE="0666", GROUP="dialout"
EOF

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger

echo ""
echo "Installation completed successfully!"
echo ""
echo "IMPORTANT: You need to log out and back in for group permissions to take effect."
echo ""
echo "To run the application:"
echo "1. From desktop: Look for 'RS232 Protocol Spoofer' in applications menu"
echo "2. From terminal: cd $APP_DIR && ./run.sh"
echo "3. From file manager: Double-click run.sh in $APP_DIR"
echo ""
echo "Application installed in: $APP_DIR"
echo "Logs will be stored in: $APP_DIR/logs"
echo ""
echo "For auto-start on boot:"
echo "systemctl --user start rs232-spoofer.service"
echo ""
echo "Troubleshooting:"
echo "- If you get permission errors, make sure you're in the dialout group"
echo "- Check available serial ports with: ls -la /dev/ttyUSB* /dev/ttyACM*"
echo "- View logs with: tail -f $APP_DIR/logs/application.log"
