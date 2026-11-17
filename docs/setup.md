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
- **Username**: `thunderbird2`
- **Hostname**: thunderbird2.local (recommended over IP)
- **Auth**: Public key (ED25519) — passwordless SSH configured ✓

**Connect**:
```bash
ssh thunderbird2@thunderbird2.local
```

### OS & Interfaces
- **OS**: Raspberry Pi OS Bookworm
- **Enable SPI**: For RS485 CAN HAT communication
- **Enable I2C**: For future sensor integration
- **Enable UART**: For debugging (optional)

### Python Dependencies (System)

First, enable passwordless sudo for the `thunderbird2` user. As `root` or via `sudo visudo`:

```bash
# Add to /etc/sudoers:
thunderbird2 ALL=(ALL) NOPASSWD: ALL
```

Then install system packages:

```bash
ssh thunderbird2@thunderbird2.local

# On Pi:
sudo apt update
sudo apt install -y \
    python3-dev \
    python3-opencv \
    python3-gi \
    libopencv-dev \
    v4l-utils \
    gstreamer1.0 \
    gstreamer1.0-tools \
    libgstreamer1.0-0 \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    gir1.2-gstreamer-1.0 \
    gir1.2-gst-rtsp-server-1.0

# Optional (for CAN/OBDII):
pip install python-can
```

### Python Environment
```bash
# On Pi:
python3 -m venv ~/thunderbird2/.venv
source ~/thunderbird2/.venv/bin/activate
pip install -e ~/thunderbird2
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

# On Pi (after SSH):
python3 src/camera_detection.py           # Verify cameras
python3 src/main.py --config              # Print config
python3 src/main.py --test                # Run self-tests
python3 src/main.py                       # Run application
```

