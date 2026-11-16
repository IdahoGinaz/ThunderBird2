# Setup

## Dev machine
```
python -m venv .venv
.venv\Scripts\activate
pip install -e .
```

**Windows SSH keys**: Already set up with ED25519 key at `~/.ssh/id_ed25519`

## Raspberry Pi

### SSH Access
- **Username**: `wolfpack`
- **IP**: 192.168.178.103
- **Auth**: Public key at `~/.ssh/id_ed25519.pub` (configure manually or run `scripts/setup_ssh.ps1`)

### OS & Interfaces
- **OS**: Raspberry Pi OS Bookworm
- **Enable SPI**: For RS485 CAN HAT communication
- **Enable I2C**: For future sensor integration
- **Enable UART**: For debugging (optional)

### Python Environment
```bash
ssh wolfpack@192.168.178.103

# On Pi:
python3 -m venv ~/thunderbird2/.venv
source ~/thunderbird2/.venv/bin/activate
pip install -e ~/thunderbird2

# Install system dependencies:
sudo apt update
sudo apt install -y \
    python3-dev \
    python3-opencv \
    libopencv-dev \
    v4l-utils \
    gstreamer1.0 \
    libgstreamer1.0-0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav

# Optional (for CAN/OBDII):
pip install python-can
```

### Systemd Service
Not yet implemented. Planned for Phase 3.

**Service file** will be created at:
```
/etc/systemd/system/thunderbird2-camera.service
```

**Usage**:
```bash
sudo systemctl start thunderbird2-camera
sudo systemctl stop thunderbird2-camera
sudo systemctl enable thunderbird2-camera  # Auto-start on boot
sudo journalctl -fu thunderbird2-camera    # View logs
```

## Raspberry Pi Hardware Setup

### RS485 CAN HAT (TODO)
- Wiring: TBD — verify pinout on HAT
- Bus speed: 500 kbps (config.py)
- Nissan Atlas CAN IDs: TBD

### Octocoupler (GPIO inputs) (TODO)
- 8 GPIO pins to be assigned in config.py
- Currently marked as NOT YET WIRED
- Once wired, test with: `python src/view_logic.py` (GPIO reader test)

### USB Hub & Cameras
- **Hub**: Sabrent HB-BU10 (self-powered, mounted in tray above head unit)
- **Cameras**: 2x Arducam 1080P + 1x Logitech 720p on USB
- **Test camera detection**: `python src/camera_detection.py --verbose`

## ESP32 (Optional Future)
- Not currently used; reserved for future sensor integration

## Home Assistant / MQTT / TAK (Optional Future)
- Currently using local systemd service model
- MQTT integration planned for status/telemetry (see .env.example)

## Testing Commands

```bash
# On dev machine (Windows):
python src/config.py                      # Print configuration summary
python src/camera_detection.py --verbose  # Detect cameras & capabilities

# Deploy to Pi:
.\scripts\deploy.ps1 192.168.178.103      # (Once created)

# On Pi:
python src/camera_detection.py            # Verify cameras on Pi
python src/camera_manager.py              # Test camera manager (stub)
python src/view_logic.py                  # Test view logic (stub)
python src/output_manager.py              # Test output manager (stub)
```

