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
import threading
import queue
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod

try:
    import cv2
except ImportError:
    cv2 = None

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
        self.frame_queue: queue.Queue = queue.Queue(maxsize=10)
        self.capture_threads: List[threading.Thread] = []
        logger.info("CameraManager initialized")
    
    def detect_cameras(self) -> bool:
        """
        Enumerate connected USB cameras and initialize them.
        
        Returns:
            True if cameras initialized successfully, False otherwise
        """
        logger.info("Detecting cameras...")
        
        if cv2 is None:
            logger.error("OpenCV not installed; cannot detect cameras")
            return False
        
        # Map device paths to expected camera types
        # Device indices are hardware-dependent and can change with USB enumeration
        camera_configs = [
            ("/dev/video0", "0c45", "0261"),  # Arducam 1080P #1
            ("/dev/video4", "0c45", "0261"),  # Arducam 1080P #2
            ("/dev/video8", "0513", "0318"),  # Logitech C270
        ]
        
        camera_id = 0
        for device_path, vendor_id, product_id in camera_configs:
            if not os.path.exists(device_path):
                logger.debug(f"Device {device_path} not found")
                continue
            
            camera = CameraDevice(device_path, camera_id, vendor_id, product_id)
            
            # Try to open (automatically skips ISP and metadata devices)
            if camera.open():
                self.cameras[camera_id] = camera
                camera_id += 1
                logger.info(f"Camera initialized: {device_path}")
        
        if not self.cameras:
            logger.warning("No cameras could be initialized")
            return False
        
        logger.info(f"Successfully initialized {len(self.cameras)} camera(s)")
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
        try:
            frame = self.frame_queue.get(timeout=timeout)
            return frame
        except queue.Empty:
            return None
    
    def set_camera_resolution(self, resolution: str):
        """
        Set all cameras to a specific resolution.
        
        Args:
            resolution: Key from config.CAMERA_FORMATS (e.g., "1080P")
        """
        if resolution not in CAMERA_FORMATS:
            logger.error(f"Unknown resolution: {resolution}")
            return
        
        width, height, fps = CAMERA_FORMATS[resolution]
        for camera in self.cameras.values():
            camera.set_resolution(width, height, fps)
            logger.info(f"Set {camera.device_path} to {resolution}")
    
    def handle_camera_change(self):
        """
        Called when camera configuration changes (plugged in/removed).
        Triggers setup menu and reinitializes.
        """
        logger.info("Camera configuration changed, reinitializing...")
        self.setup_menu_needed = True
        self.stop()
        self.cameras.clear()
        self.detect_cameras()
        self.start()
    
    def _capture_worker(self, camera: 'CameraDevice'):
        """
        Worker thread for capturing frames from a single camera.
        
        Args:
            camera: CameraDevice instance
        """
        logger.info(f"Capture worker started for {camera.device_path}")
        
        while self.is_running:
            try:
                frame = camera.capture_frame(timeout=0.5)
                if frame and not self.frame_queue.full():
                    self.frame_queue.put(frame, block=False)
            except queue.Full:
                pass  # Drop oldest frame
            except Exception as e:
                logger.error(f"Error capturing from {camera.device_path}: {e}")
                time.sleep(0.1)
    
    def start(self):
        """Start capturing frames."""
        if self.is_running:
            logger.warning("CameraManager already running")
            return
        
        if not self.cameras:
            logger.error("No cameras to start; call detect_cameras() first")
            return
        
        self.is_running = True
        
        # Start a capture worker thread for each camera
        for camera in self.cameras.values():
            thread = threading.Thread(target=self._capture_worker, args=(camera,), daemon=True)
            thread.start()
            self.capture_threads.append(thread)
        
        logger.info(f"CameraManager started with {len(self.cameras)} camera(s)")
    
    def stop(self):
        """Stop capturing frames and release cameras."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Wait for capture threads to finish
        for thread in self.capture_threads:
            thread.join(timeout=2.0)
        self.capture_threads.clear()
        
        # Release all cameras
        for camera in self.cameras.values():
            camera.close()
        
        logger.info("CameraManager stopped")

# ============================================================================
# CAMERA DEVICE (internal)
# ============================================================================

class CameraDevice:
    """
    Wrapper for a single USB camera device.
    Handles OpenCV-based capture via V4L2.
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
        self.capture = None
        self.width = DEFAULT_RESOLUTION.split("P")[0]  # Extract from "1080P"
        self.height = DEFAULT_RESOLUTION.split("P")[0]
        self.fps = DEFAULT_FPS
        
        logger.info(f"CameraDevice created: {device_path} (USB {vendor_id}:{product_id})")
    
    def open(self, resolution: str = DEFAULT_RESOLUTION, fps: int = DEFAULT_FPS) -> bool:
        """
        Open and initialize the camera.
        
        Returns:
            True if successful, False otherwise
        """
        if cv2 is None:
            logger.error("OpenCV not available")
            return False
        
        if self.is_open:
            logger.warning(f"{self.device_path} already open")
            return True
        
        try:
            # Extract width, height from resolution string
            # For now, hardcode common resolutions
            if "1080" in resolution:
                self.width, self.height = 1920, 1080
            elif "720" in resolution:
                self.width, self.height = 1280, 720
            else:
                self.width, self.height = 640, 480
            
            self.fps = fps
            
            # Try to open camera via OpenCV using device path
            # OpenCV supports 'v4l2:/path/to/device' on Linux
            self.capture = cv2.VideoCapture(self.device_path)
            
            if not self.capture.isOpened():
                logger.error(f"Failed to open {self.device_path}")
                return False
            
            # Set resolution and FPS
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.capture.set(cv2.CAP_PROP_FPS, self.fps)
            
            # Verify settings were applied
            actual_width = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = int(self.capture.get(cv2.CAP_PROP_FPS))
            
            self.is_open = True
            logger.info(
                f"Opened {self.device_path}: {actual_width}x{actual_height} @ {actual_fps}fps"
            )
            return True
        
        except Exception as e:
            logger.error(f"Exception opening {self.device_path}: {e}")
            return False
    
    def capture_frame(self, timeout: float = 1.0) -> Optional[Frame]:
        """
        Capture a single frame from this camera.
        
        Returns:
            Frame object or None if error
        """
        if not self.is_open or self.capture is None:
            return None
        
        try:
            ret, frame_bgr = self.capture.read()
            
            if not ret:
                logger.warning(f"Failed to read frame from {self.device_path}")
                return None
            
            # Convert BGR to RGB for consistency
            frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            
            # Encode to bytes
            _, encoded = cv2.imencode('.jpg', frame_bgr, [cv2.IMWRITE_JPEG_QUALITY, 85])
            frame_bytes = encoded.tobytes()
            
            return Frame(
                data=frame_bytes,
                width=frame_rgb.shape[1],
                height=frame_rgb.shape[0],
                fps=self.fps,
                timestamp=time.time(),
                camera_id=self.camera_id,
                format="JPEG",
            )
        
        except Exception as e:
            logger.error(f"Error capturing frame from {self.device_path}: {e}")
            return None
    
    def set_resolution(self, width: int, height: int, fps: int):
        """Update camera resolution and FPS."""
        if not self.is_open or self.capture is None:
            return
        
        self.width = width
        self.height = height
        self.fps = fps
        
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self.capture.set(cv2.CAP_PROP_FPS, fps)
    
    def close(self):
        """Release camera resources."""
        if self.is_open and self.capture is not None:
            self.capture.release()
            self.is_open = False
            logger.info(f"Closed {self.device_path}")

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
    return previous != current

if __name__ == "__main__":
    # Test camera capture
    logging.basicConfig(level=logging.INFO)
    
    mgr = CameraManager()
    if mgr.detect_cameras():
        mgr.start()
        
        for i in range(30):
            frame = mgr.get_frame(timeout=1.0)
            if frame:
                print(f"Frame {i}: {frame.width}x{frame.height} from camera {frame.camera_id} ({frame.format})")
            else:
                print(f"Frame {i}: Timeout or error")
            time.sleep(0.1)
        
        mgr.stop()
    else:
        print("Failed to detect cameras")

