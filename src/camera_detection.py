#!/usr/bin/env python3
"""
ThunderBird2 — Camera Detection Script

Enumerates connected USB cameras, retrieves their capabilities, vendor/product IDs,
and resolution/format support. Used for initial setup and auto-detection of camera changes.

Usage:
    python src/camera_detection.py         # List all cameras
    python src/camera_detection.py --save  # Save to log file

Author: Copilot
Updated: 2026-11-17
"""

import os
import sys
import json
import subprocess
import argparse
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

# Try to import dependencies
try:
    import cv2
except ImportError:
    cv2 = None

# Import configuration
sys.path.insert(0, os.path.dirname(__file__))
from config import CAMERA_LOG_PATH, LOG_LEVEL

# ============================================================================
# LOGGING
# ============================================================================

def setup_logging(save_to_file: bool = False) -> logging.Logger:
    """Configure logging for camera detection."""
    logger = logging.getLogger("ThunderBird2.CameraDetection")
    logger.setLevel(LOG_LEVEL)
    
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console output
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File output (optional)
    if save_to_file:
        log_dir = os.path.dirname(CAMERA_LOG_PATH)
        os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(CAMERA_LOG_PATH)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.info(f"Logging to {CAMERA_LOG_PATH}")
    
    return logger

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class CameraCapability:
    """Single camera capability (resolution + format)."""
    width: int
    height: int
    fps: int
    format: str  # e.g., "YUYV", "MJPEG", "H.264"

@dataclass
class CameraInfo:
    """Complete information about one detected camera."""
    device: str              # e.g., "/dev/video0"
    index: int              # OpenCV camera index
    name: str               # Human-readable name
    vendor_id: str          # USB vendor ID (hex)
    product_id: str         # USB product ID (hex)
    vendor_name: Optional[str] = None
    product_name: Optional[str] = None
    capabilities: List[CameraCapability] = None
    resolution: Optional[str] = None  # e.g., "1920x1080"
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = []

# ============================================================================
# CAMERA DETECTION (Linux v4l2-ctl)
# ============================================================================

def get_usb_camera_devices() -> Dict[str, Dict[str, str]]:
    """
    Enumerate USB cameras using lsusb and v4l2-ctl.
    Returns dict mapping /dev/videoX to {vendor_id, product_id, name}.
    """
    cameras = {}
    
    try:
        # Get list of video devices
        result = subprocess.run(
            ["ls", "-1", "/dev/video*"],
            shell=True,
            capture_output=True,
            text=True,
            timeout=5
        )
        video_devices = result.stdout.strip().split("\n")
        video_devices = [d for d in video_devices if d]  # Filter empty strings
        
    except Exception as e:
        logging.warning(f"Could not enumerate /dev/video* devices: {e}")
        return cameras
    
    # For each video device, try to get USB info
    for device in video_devices:
        if not os.path.exists(device):
            continue
        
        try:
            # Use v4l2-ctl to get device info
            result = subprocess.run(
                ["v4l2-ctl", "-d", device, "--info"],
                capture_output=True,
                text=True,
                timeout=2
            )
            
            if result.returncode == 0:
                info_text = result.stdout
                
                # Try to extract USB vendor:product from sysfs
                try:
                    # Get device bus info
                    result_bus = subprocess.run(
                        ["v4l2-ctl", "-d", device, "-D"],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    bus_info = result_bus.stdout
                    
                    # Fallback: try udevadm
                    result_udev = subprocess.run(
                        ["udevadm", "info", "--query=all", "-n", device],
                        capture_output=True,
                        text=True,
                        timeout=2
                    )
                    udev_info = result_udev.stdout
                    
                    # Extract vendor/product from udev
                    vendor_id = "0000"
                    product_id = "0000"
                    
                    for line in udev_info.split("\n"):
                        if "ID_VENDOR_ID=" in line:
                            vendor_id = line.split("=")[1].strip()
                        if "ID_MODEL_ID=" in line:
                            product_id = line.split("=")[1].strip()
                    
                    cameras[device] = {
                        "vendor_id": vendor_id,
                        "product_id": product_id,
                        "name": "USB Camera",  # Will be refined later
                    }
                except Exception:
                    pass
        
        except subprocess.TimeoutExpired:
            logging.warning(f"Timeout querying {device}")
        except Exception as e:
            logging.warning(f"Error querying {device}: {e}")
    
    return cameras

# ============================================================================
# CAMERA CAPABILITIES (OpenCV)
# ============================================================================

def get_camera_capabilities_opencv(camera_index: int) -> List[CameraCapability]:
    """
    Query camera capabilities using OpenCV.
    Returns list of supported resolutions and frame rates.
    """
    if cv2 is None:
        return []
    
    capabilities = []
    
    try:
        cap = cv2.VideoCapture(camera_index)
        
        if not cap.isOpened():
            return []
        
        # Try common resolutions
        common_resolutions = [
            (640, 480),
            (800, 600),
            (1024, 768),
            (1280, 720),
            (1920, 1080),
            (2560, 1440),
        ]
        
        for width, height in common_resolutions:
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            cap.set(cv2.CAP_PROP_FPS, 30)
            
            actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(cap.get(cv2.CAP_PROP_FPS))
            
            if actual_width == width and actual_height == height:
                capabilities.append(CameraCapability(
                    width=width,
                    height=height,
                    fps=actual_fps,
                    format="OpenCV"
                ))
        
        cap.release()
    
    except Exception as e:
        logging.warning(f"Error getting OpenCV capabilities: {e}")
    
    return capabilities

def get_camera_capabilities_v4l2(device: str) -> List[CameraCapability]:
    """
    Query camera capabilities using v4l2-ctl.
    Returns list of supported formats and resolutions.
    """
    capabilities = []
    
    try:
        result = subprocess.run(
            ["v4l2-ctl", "-d", device, "--list-formats-ext"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            # Parse v4l2-ctl output for resolutions
            current_format = None
            for line in result.stdout.split("\n"):
                line = line.strip()
                
                # Look for format lines: "[1]: 'YUYV' (YUYV)"
                if "[" in line and "]:" in line:
                    parts = line.split("'")
                    if len(parts) >= 2:
                        current_format = parts[1]
                
                # Look for resolution lines: "Size: Discrete 640x480"
                if "Size: Discrete" in line:
                    try:
                        size_part = line.split("Discrete")[1].strip()
                        width, height = map(int, size_part.split("x"))
                        
                        capabilities.append(CameraCapability(
                            width=width,
                            height=height,
                            fps=30,  # Default assumption
                            format=current_format or "Unknown"
                        ))
                    except ValueError:
                        pass
    
    except subprocess.TimeoutExpired:
        logging.warning(f"Timeout getting v4l2-ctl capabilities for {device}")
    except FileNotFoundError:
        logging.warning("v4l2-ctl not found; install with: sudo apt install v4l-utils")
    except Exception as e:
        logging.warning(f"Error getting v4l2 capabilities: {e}")
    
    return capabilities

# ============================================================================
# MAIN DETECTION
# ============================================================================

def detect_cameras() -> List[CameraInfo]:
    """
    Detect all connected USB cameras and return their info.
    Combines multiple detection methods (lsusb, v4l2-ctl, OpenCV).
    """
    logger = logging.getLogger("ThunderBird2.CameraDetection")
    cameras_info = []
    
    logger.info("Starting camera detection...")
    
    # Step 1: Get USB devices
    usb_cameras = get_usb_camera_devices()
    
    if not usb_cameras:
        logger.warning("No USB camera devices found in /dev/video*")
        return cameras_info
    
    logger.info(f"Found {len(usb_cameras)} video device(s)")
    
    # Step 2: For each device, get capabilities
    for device, usb_info in usb_cameras.items():
        try:
            # Extract index from device name (e.g., "/dev/video0" -> 0)
            index = int(device.split("video")[1])
        except (ValueError, IndexError):
            index = -1
        
        # Get capabilities from both v4l2 and OpenCV
        v4l2_caps = get_camera_capabilities_v4l2(device)
        opencv_caps = get_camera_capabilities_opencv(index) if index >= 0 else []
        
        # Merge capabilities (prefer v4l2, supplement with OpenCV)
        capabilities = v4l2_caps if v4l2_caps else opencv_caps
        
        # Determine best resolution
        best_resolution = None
        if capabilities:
            best_cap = max(capabilities, key=lambda c: c.width * c.height)
            best_resolution = f"{best_cap.width}x{best_cap.height}"
        
        # Create camera info
        camera = CameraInfo(
            device=device,
            index=index,
            name=usb_info.get("name", "Unknown"),
            vendor_id=usb_info.get("vendor_id", "0000"),
            product_id=usb_info.get("product_id", "0000"),
            capabilities=capabilities,
            resolution=best_resolution,
        )
        
        cameras_info.append(camera)
        
        logger.info(
            f"  Device: {device} | "
            f"USB: {camera.vendor_id}:{camera.product_id} | "
            f"Best resolution: {camera.resolution}"
        )
    
    logger.info(f"Detection complete: {len(cameras_info)} camera(s) found")
    return cameras_info

# ============================================================================
# OUTPUT & REPORTING
# ============================================================================

def print_camera_report(cameras: List[CameraInfo]):
    """Print a human-readable report of detected cameras."""
    
    print("\n" + "=" * 80)
    print("ThunderBird2 — Camera Detection Report")
    print("=" * 80)
    
    if not cameras:
        print("⚠ No cameras detected!")
        print("\nTroubleshooting:")
        print("  1. Check USB connections: lsusb | grep -i camera")
        print("  2. Check v4l2 devices: ls /dev/video*")
        print("  3. Test with: v4l2-ctl -d /dev/video0 --info")
        return
    
    print(f"\nFound {len(cameras)} camera(s):\n")
    
    for i, cam in enumerate(cameras, 1):
        print(f"Camera {i}: {cam.device}")
        print(f"  Name:          {cam.name}")
        print(f"  USB ID:        {cam.vendor_id}:{cam.product_id}")
        print(f"  Best res:      {cam.resolution}")
        print(f"  Capabilities:  {len(cam.capabilities)} resolution(s)")
        
        if cam.capabilities:
            print(f"    {', '.join(f'{c.width}x{c.height}@{c.fps}fps' for c in cam.capabilities[:5])}")
            if len(cam.capabilities) > 5:
                print(f"    ... and {len(cam.capabilities) - 5} more")
        
        print()
    
    print("=" * 80)

def save_camera_report(cameras: List[CameraInfo], filepath: str):
    """Save camera detection results to JSON file."""
    report = {
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "total_cameras": len(cameras),
        "cameras": [
            {
                **asdict(cam),
                "capabilities": [asdict(c) for c in cam.capabilities]
            }
            for cam in cameras
        ]
    }
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✓ Report saved to: {filepath}")

# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="ThunderBird2 USB Camera Detection & Capabilities"
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save report to log file"
    )
    parser.add_argument(
        "--json",
        type=str,
        help="Save JSON report to specified file"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logger = setup_logging(save_to_file=args.save)
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Detect cameras
    cameras = detect_cameras()
    
    # Print report
    print_camera_report(cameras)
    
    # Save report if requested
    if args.json:
        save_camera_report(cameras, args.json)
    elif args.save:
        json_path = CAMERA_LOG_PATH.replace(".log", ".json")
        save_camera_report(cameras, json_path)

if __name__ == "__main__":
    main()
