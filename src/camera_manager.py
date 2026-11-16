"""
ThunderBird2 — Camera Manager

Handles detection, initialization, and frame capture from connected USB cameras.
Adapts to different camera configurations (auto-detect).

Author: Copilot
Updated: 2026-11-17
"""

import os
import sys
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod

sys.path.insert(0, os.path.dirname(__file__))
from config import (
    CAMERA_FORMATS,
    DEFAULT_RESOLUTION,
    DEFAULT_FPS,
    CAMERA_INIT_TIMEOUT,
)

logger = logging.getLogger("ThunderBird2.CameraManager")

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class Frame:
    """A single video frame."""
    data: bytes          # Raw or encoded frame data
    width: int
    height: int
    fps: int
    timestamp: float     # Time when frame was captured
    camera_id: int       # Which camera this came from
    format: str          # "RGB", "YUV", "JPEG", etc.

# ============================================================================
# CAMERA MANAGER
# ============================================================================

class CameraManager:
    """
    Manages multiple USB cameras, their initialization, and frame capture.
    
    Responsibilities:
      - Auto-detect connected cameras and their capabilities
      - Initialize cameras with appropriate resolution/format
      - Capture frames from one or multiple cameras
      - Handle camera disconnects/reconnects
      - Trigger setup menu if camera configuration changes
    """
    
    def __init__(self):
        """Initialize the camera manager."""
        self.cameras: Dict[int, 'CameraDevice'] = {}
        self.is_running = False
        self.setup_menu_needed = False
        logger.info("CameraManager initialized")
    
    def detect_cameras(self) -> bool:
        """
        Enumerate connected USB cameras and initialize them.
        
        Returns:
            True if cameras initialized successfully, False otherwise
        """
        logger.info("Detecting cameras...")
        # TODO: Implement camera detection using camera_detection.py
        # TODO: Check against known camera configuration
        # TODO: If count/vendor IDs changed, set setup_menu_needed = True
        
        return True
    
    def get_frame(self, timeout: float = 1.0) -> Optional[Frame]:
        """
        Capture a single frame from active camera(s).
        
        In compositing mode, blends multiple cameras into one output.
        In single-camera mode, just returns that camera's frame.
        
        Args:
            timeout: Maximum time to wait for a frame (seconds)
        
        Returns:
            Frame object or None if timeout/error
        """
        # TODO: Implement frame capture logic
        # TODO: Handle frame compositing (multiple cameras -> one output)
        # TODO: Fallback if primary camera fails
        
        pass
    
    def set_camera_resolution(self, resolution: str):
        """
        Set all cameras to a specific resolution.
        
        Args:
            resolution: Key from config.CAMERA_FORMATS (e.g., "1080P")
        """
        # TODO: Validate resolution
        # TODO: Apply to all cameras
        # TODO: Handle cameras with limited format support
        
        pass
    
    def handle_camera_change(self):
        """
        Called when camera configuration changes (plugged in/removed).
        Triggers setup menu and reinitializes.
        """
        # TODO: Pause frame capture
        # TODO: Signal setup menu needed
        # TODO: Reinitialize cameras
        
        pass
    
    def start(self):
        """Start capturing frames."""
        if self.is_running:
            logger.warning("CameraManager already running")
            return
        
        self.is_running = True
        logger.info("CameraManager started")
    
    def stop(self):
        """Stop capturing frames and release cameras."""
        if not self.is_running:
            return
        
        self.is_running = False
        # TODO: Release camera resources
        logger.info("CameraManager stopped")

# ============================================================================
# CAMERA DEVICE (internal)
# ============================================================================

class CameraDevice:
    """
    Wrapper for a single USB camera device.
    Handles V4L2 or OpenCV-based capture.
    """
    
    def __init__(self, device_path: str, camera_id: int, vendor_id: str, product_id: str):
        """
        Initialize a camera device.
        
        Args:
            device_path: e.g., "/dev/video0"
            camera_id: 0-based index for multi-camera setup
            vendor_id: USB vendor ID (hex string)
            product_id: USB product ID (hex string)
        """
        self.device_path = device_path
        self.camera_id = camera_id
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.is_open = False
        
        logger.info(f"CameraDevice created: {device_path} (USB {vendor_id}:{product_id})")
    
    def open(self, resolution: str = DEFAULT_RESOLUTION, fps: int = DEFAULT_FPS) -> bool:
        """
        Open and initialize the camera.
        
        Returns:
            True if successful, False otherwise
        """
        # TODO: Use V4L2 or OpenCV to open device
        # TODO: Set resolution and frame rate
        # TODO: Verify camera is working
        
        pass
    
    def capture_frame(self, timeout: float = 1.0) -> Optional[Frame]:
        """
        Capture a single frame from this camera.
        
        Returns:
            Frame object or None if error
        """
        # TODO: Read one frame from device
        # TODO: Return Frame with metadata
        
        pass
    
    def close(self):
        """Release camera resources."""
        # TODO: Close V4L2/OpenCV capture
        
        pass

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def compare_camera_configs(previous: List[Tuple[str, str]], current: List[Tuple[str, str]]) -> bool:
    """
    Check if camera configuration changed (count or USB IDs).
    
    Args:
        previous: List of (vendor_id, product_id) from last known config
        current: List of (vendor_id, product_id) from current detection
    
    Returns:
        True if configuration changed, False if same
    """
    # TODO: Implement comparison
    
    return previous != current

if __name__ == "__main__":
    # Test camera detection
    logging.basicConfig(level=logging.INFO)
    
    mgr = CameraManager()
    mgr.detect_cameras()
    mgr.start()
    
    for i in range(10):
        frame = mgr.get_frame()
        if frame:
            print(f"Frame {i}: {frame.width}x{frame.height} from camera {frame.camera_id}")
    
    mgr.stop()
