"""
ThunderBird2 Configuration Module

Centralized location for all hardware pinouts, camera settings, CAN configuration,
and system parameters. Never scatter magic numbers in code — reference them here.

Author: Copilot
Updated: 2026-11-17
"""

import os
from typing import Dict, List, Tuple

# ============================================================================
# SYSTEM PATHS & LOGGING
# ============================================================================

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
CAMERA_LOG_PATH = os.path.join(LOG_DIR, "camera_detection.log")

# Log level: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL = "INFO"

# ============================================================================
# RASPBERRY PI GPIO PINS
# ============================================================================

# Octocoupler (8-channel relay inputs) — maps truck signals to GPIO
# Status: NOT YET WIRED — GPIO pins TBD
# Once wired, fill in the GPIO numbers (physical pin or BCM)
OCTOCOUPLER_PINS: Dict[str, int] = {
    "LEFT_INDICATOR": -1,      # GPIO pin for left turn signal
    "RIGHT_INDICATOR": -1,     # GPIO pin for right turn signal
    "REVERSE": -1,             # GPIO pin for reverse (backup camera)
    "BRAKE": -1,               # GPIO pin for brake lights
    "RESERVED_4": -1,          # Spare octocoupler channels
    "RESERVED_5": -1,
    "RESERVED_6": -1,
    "RESERVED_7": -1,
}

# Pi I2C/SPI interfaces
I2C_BUS = 1  # Default I2C bus on Pi 4
SPI_BUS = 0  # Default SPI bus

# CAN bus (RS485 HAT)
CAN_BAUDRATE = 500000  # 500kbps typical for automotive
CAN_TIMEOUT = 1.0  # seconds

# ============================================================================
# CAMERAS
# ============================================================================

# USB camera configuration
# Arducam 1080P Low Light cameras
CAMERA_ARDUCAM_VENDOR_ID = "0c45"
CAMERA_ARDUCAM_PRODUCT_ID = "0261"
CAMERA_ARDUCAM_MAX_CAMERAS = 2  # Expect up to 2 Arducams

# Logitech C270 / similar
CAMERA_LOGITECH_VENDOR_ID = "046d"  # Update if different model
CAMERA_LOGITECH_MAX_CAMERAS = 1

# Video device enumeration
VIDEO_DEVICE_PATH = "/dev/video*"  # Linux pattern
VIDEO_DEVICE_TIMEOUT = 5  # seconds to detect all cameras

# Camera capabilities
CAMERA_FORMATS = {
    "1080P": {"width": 1920, "height": 1080, "fps": 30},
    "720P": {"width": 1280, "height": 720, "fps": 30},
    "480P": {"width": 640, "height": 480, "fps": 30},
}

# Default camera resolution (can be overridden via setup menu)
DEFAULT_RESOLUTION = "1080P"
DEFAULT_FPS = 30

# ============================================================================
# VIDEO OUTPUT PIPELINE
# ============================================================================

# Multi-output configuration: priority order and fallback
# 1. RTSP stream (network camera feed)
# 2. RCA composite video (via USB adapter)
# 3. USB DVR mode (Android head unit direct USB input)

# RTSP output
RTSP_ENABLED = True
RTSP_HOST = "0.0.0.0"
RTSP_PORT = 8554
RTSP_PATH = "/camera"
RTSP_BITRATE = "4M"  # 4 Mbps
RTSP_CODEC = "h264"  # or "h265" for newer systems

# RCA composite video (requires USB adapter)
RCA_ENABLED = True
RCA_DEVICE = "/dev/video10"  # Loopback device (may vary)
RCA_FORMAT = "NTSC"  # or "PAL" (TV standard)

# USB DVR mode (Android head unit)
# Pi acts as USB camera device; Android sees it in DVR app
USB_DVR_ENABLED = True
USB_DVR_BITRATE = "2M"  # Lower for USB compatibility

# Encoder selection
VIDEO_ENCODER = "libx264"  # h.264 (best compatibility)
# VIDEO_ENCODER = "libx265"  # HEVC (better compression, needs support)

# ============================================================================
# VIEW SWITCHING LOGIC
# ============================================================================

# Camera view modes (what the driver sees)
VIEW_MODES = {
    "NORMAL": "Front view + side mirrors optional",
    "LEFT_INDICATOR": "Show left side camera when turning left",
    "RIGHT_INDICATOR": "Show right side camera when turning right",
    "REVERSE": "Show rear camera when in reverse",
    "PARKED": "Show all cameras in quad view or carousel",
    "MANUAL": "Driver selects view via BT keyboard",
}

# Default view on startup
DEFAULT_VIEW = "NORMAL"

# Keyboard input (for manual testing and final UI)
KEYBOARD_ENABLED = True  # Keep in final model for manual override
KEYBOARD_HELP = {
    "1": "Front camera",
    "2": "Left camera", 
    "3": "Right camera",
    "r": "Reverse camera",
    "l": "Left indicator (turn)",
    "k": "Right indicator (turn)",
    "n": "Normal view",
    "q": "Quit",
}

# Minimum turn signal duration to trigger camera switch (ms)
INDICATOR_DEBOUNCE_MS = 200

# ============================================================================
# CAN BUS (Nissan Atlas 2007)
# ============================================================================

# CAN bus messages for turn signals, reverse, brake
# Reference: Nissan Atlas 2007 service manual / forum posts
CAN_MESSAGES = {
    "TURN_LEFT": {"CAN_ID": 0x000, "BYTE": 0, "BIT": 0},     # TBD - actual CAN IDs
    "TURN_RIGHT": {"CAN_ID": 0x000, "BYTE": 0, "BIT": 1},
    "REVERSE": {"CAN_ID": 0x000, "BYTE": 0, "BIT": 2},
    "BRAKE": {"CAN_ID": 0x000, "BYTE": 0, "BIT": 3},
}

CAN_FALLBACK_TIMEOUT = 5.0  # Switch to GPIO if CAN silent for 5s

# ============================================================================
# ANDROID HEAD UNIT
# ============================================================================

# Android "B200 Core 8" specifications
ANDROID_RESOLUTION = (1280, 720)
ANDROID_NATIVE_FPS = 30
ANDROID_SUPPORTED_CODECS = ["h264", "h265"]  # Check device capabilities

# Network discovery (optional)
ANDROID_HOSTNAME = "tb2-headunit"
ANDROID_IP = None  # Will be detected via DHCP / mDNS

# ============================================================================
# SYSTEM SERVICES
# ============================================================================

# Systemd service configuration
SERVICE_NAME = "thunderbird2-camera"
SERVICE_RESTART_ON_FAILURE = True
SERVICE_AUTO_START = True

# Process priorities
CPU_PRIORITY = 0  # -20 (high) to 19 (low)
PROCESS_NICE = -5  # Slightly elevated priority for real-time performance

# Health check heartbeat
HEARTBEAT_INTERVAL = 5  # seconds

# ============================================================================
# PERFORMANCE & TUNING
# ============================================================================

# Buffer sizes for video streaming
FRAME_BUFFER_SIZE = 30  # frames
ENCODER_THREADS = 4

# Timeout for camera initialization
CAMERA_INIT_TIMEOUT = 10  # seconds

# Graceful shutdown timeout
SHUTDOWN_TIMEOUT = 5  # seconds

# ============================================================================
# BLUETOOTH PERIPHERALS
# ============================================================================

# Bluetooth keyboard for manual control
BT_KEYBOARD_ENABLED = True
BT_KEYBOARD_DEVICE_NAME = "Mini Keyboard"  # Will scan for this

# OBDII reader (future use)
BT_OBDII_ENABLED = False
BT_OBDII_DEVICE_NAME = "OBDII-Reader"

# ============================================================================
# ENVIRONMENT & STARTUP
# ============================================================================

# Load from .env file
def load_env_overrides():
    """Load environment-specific overrides from .env file (not in git)."""
    env_path = os.path.join(PROJECT_ROOT, ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()

# Call on module import
load_env_overrides()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_camera_info() -> Dict:
    """Return summary of camera configuration."""
    return {
        "arducam_expected": CAMERA_ARDUCAM_MAX_CAMERAS,
        "logitech_expected": CAMERA_LOGITECH_MAX_CAMERAS,
        "total_expected": CAMERA_ARDUCAM_MAX_CAMERAS + CAMERA_LOGITECH_MAX_CAMERAS,
        "default_resolution": DEFAULT_RESOLUTION,
        "formats_supported": list(CAMERA_FORMATS.keys()),
    }

def get_output_pipeline() -> List[str]:
    """Return list of enabled video outputs in priority order."""
    outputs = []
    if RTSP_ENABLED:
        outputs.append(f"RTSP://{RTSP_HOST}:{RTSP_PORT}{RTSP_PATH}")
    if RCA_ENABLED:
        outputs.append(f"RCA Composite ({RCA_FORMAT})")
    if USB_DVR_ENABLED:
        outputs.append("USB DVR (Android direct)")
    return outputs

def validate_config() -> Tuple[bool, List[str]]:
    """
    Validate configuration for common issues.
    Returns: (is_valid, list_of_warnings_or_errors)
    """
    issues = []
    
    # Check GPIO pins are assigned
    for pin_name, pin_num in OCTOCOUPLER_PINS.items():
        if pin_num == -1:
            issues.append(f"WARNING: Octocoupler pin '{pin_name}' not yet configured")
    
    # Check CAN messages are configured
    for msg_name, msg_config in CAN_MESSAGES.items():
        if msg_config["CAN_ID"] == 0x000:
            issues.append(f"WARNING: CAN message '{msg_name}' CAN_ID not configured (Nissan Atlas specific)")
    
    # Check output pipeline has at least one enabled
    if not (RTSP_ENABLED or RCA_ENABLED or USB_DVR_ENABLED):
        issues.append("ERROR: No video output enabled!")
        return False, issues
    
    return len(issues) == 0, issues

if __name__ == "__main__":
    print("=" * 70)
    print("ThunderBird2 Configuration Summary")
    print("=" * 70)
    print()
    print("Camera Configuration:")
    for key, val in get_camera_info().items():
        print(f"  {key}: {val}")
    print()
    print("Video Output Pipeline (priority order):")
    for i, output in enumerate(get_output_pipeline(), 1):
        print(f"  {i}. {output}")
    print()
    print("Configuration Status:")
    is_valid, issues = validate_config()
    if is_valid:
        print("  ✓ Configuration valid")
    else:
        for issue in issues:
            print(f"  ! {issue}")
    print()
    print("=" * 70)
