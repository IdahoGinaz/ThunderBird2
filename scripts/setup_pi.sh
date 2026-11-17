#!/bin/bash
# Install dependencies for ThunderBird2 on Raspberry Pi

set -e

echo "================================"
echo "ThunderBird2 — Pi Setup Script"
echo "================================"
echo ""

# Check if running on Pi
if ! grep -q "Raspberry" /proc/device-tree/model 2>/dev/null; then
    echo "WARNING: This doesn't appear to be a Raspberry Pi"
    echo "Continuing anyway..."
fi

echo "1. Updating package lists..."
sudo apt-get update

echo ""
echo "2. Installing system dependencies..."
# Install core packages first
sudo apt-get install -y \
    python3-dev \
    python3-venv \
    python3-opencv \
    python3-gi \
    libopencv-dev \
    v4l-utils

# Then install GStreamer components
echo "   Installing GStreamer..."
sudo apt-get install -y \
    gstreamer1.0-tools \
    libgstreamer1.0-0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav

# Finally install introspection libraries
echo "   Installing GStreamer introspection libraries..."
sudo apt-get install -y \
    gir1.2-gstreamer-1.0 \
    gir1.2-gst-rtsp-server-1.0

echo ""
echo "3. Creating Python virtual environment..."
if [ -d ~/thunderbird2/.venv ]; then
    echo "   Virtual environment already exists, skipping..."
else
    python3 -m venv ~/thunderbird2/.venv
    source ~/thunderbird2/.venv/bin/activate
    pip install --upgrade pip setuptools wheel
fi

echo ""
echo "4. Installing Python dependencies..."
source ~/thunderbird2/.venv/bin/activate
cd ~/thunderbird2
pip install -e . || echo "Note: Some dependencies may already be installed"

echo ""
echo "✓ Setup complete!"
echo ""
echo "To run the application:"
echo "  cd ~/thunderbird2"
echo "  source .venv/bin/activate"
echo "  python3 src/main.py"
echo ""

