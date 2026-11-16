"""
ThunderBird2 — Output Manager

Encodes video frames and outputs to multiple targets simultaneously:
  1. RTSP stream (network camera feed)
  2. RCA composite video (via USB adapter)
  3. USB DVR mode (Android head unit)

Handles fallback between outputs if one fails.

Author: Copilot
Updated: 2026-11-17
"""

import os
import sys
import logging
import threading
from typing import Dict, List, Optional, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(__file__))
from config import (
    RTSP_ENABLED,
    RTSP_HOST,
    RTSP_PORT,
    RTSP_PATH,
    RTSP_BITRATE,
    RTSP_CODEC,
    RCA_ENABLED,
    RCA_DEVICE,
    RCA_FORMAT,
    USB_DVR_ENABLED,
    USB_DVR_BITRATE,
    VIDEO_ENCODER,
)

logger = logging.getLogger("ThunderBird2.OutputManager")

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class OutputStats:
    """Statistics for a single output."""
    name: str
    frames_sent: int = 0
    bytes_sent: int = 0
    errors: int = 0
    is_active: bool = False
    last_error: Optional[str] = None

# ============================================================================
# OUTPUT TARGETS
# ============================================================================

class OutputTarget(ABC):
    """Base class for video output targets."""
    
    @abstractmethod
    def start(self):
        """Start the output."""
        pass
    
    @abstractmethod
    def stop(self):
        """Stop the output."""
        pass
    
    @abstractmethod
    def send_frame(self, frame_data: bytes, width: int, height: int, fps: int) -> bool:
        """
        Send encoded frame to output.
        
        Args:
            frame_data: Encoded frame (H.264, JPEG, etc.)
            width: Frame width in pixels
            height: Frame height in pixels
            fps: Frames per second
        
        Returns:
            True if successful, False on error
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> OutputStats:
        """Get statistics for this output."""
        pass

class RTSPOutput(OutputTarget):
    """
    RTSP (Real Time Streaming Protocol) output.
    
    Makes the camera available as a network stream that the Android head unit
    or other clients can connect to and view.
    
    URL: rtsp://<pi-ip>:8554/camera
    
    Uses GStreamer or python-rtsp library.
    """
    
    def __init__(self):
        """Initialize RTSP output."""
        self.is_running = False
        self.stats = OutputStats(name="RTSP")
        logger.info(f"RTSPOutput created: rtsp://{RTSP_HOST}:{RTSP_PORT}{RTSP_PATH}")
        # TODO: Import GStreamer or rtsp library
        # TODO: Create RTSP server
    
    def start(self):
        """Start RTSP server and begin streaming."""
        if self.is_running:
            logger.warning("RTSP output already running")
            return
        
        self.is_running = True
        # TODO: Start RTSP server
        # TODO: Bind to RTSP_HOST:RTSP_PORT
        # TODO: Create sink for incoming frames
        
        self.stats.is_active = True
        logger.info(f"RTSP output started on {RTSP_HOST}:{RTSP_PORT}")
    
    def stop(self):
        """Stop RTSP server."""
        if not self.is_running:
            return
        
        self.is_running = False
        # TODO: Shut down RTSP server
        
        self.stats.is_active = False
        logger.info("RTSP output stopped")
    
    def send_frame(self, frame_data: bytes, width: int, height: int, fps: int) -> bool:
        """
        Send frame to RTSP clients.
        
        Args:
            frame_data: H.264 encoded frame
            width: Frame width
            height: Frame height
            fps: Frames per second
        
        Returns:
            True if sent successfully
        """
        if not self.is_running:
            return False
        
        try:
            # TODO: Push frame to RTSP sink
            self.stats.frames_sent += 1
            self.stats.bytes_sent += len(frame_data)
            return True
        
        except Exception as e:
            self.stats.errors += 1
            self.stats.last_error = str(e)
            logger.error(f"RTSP send error: {e}")
            return False
    
    def get_stats(self) -> OutputStats:
        """Get RTSP output statistics."""
        return self.stats

class RCACompositeOutput(OutputTarget):
    """
    RCA composite video output via USB adapter.
    
    Encodes to NTSC or PAL and sends to USB video device.
    Android head unit receives via RCA connector.
    
    Uses GStreamer to convert RGB -> NTSC/PAL and loop back via V4L2.
    """
    
    def __init__(self):
        """Initialize RCA composite output."""
        self.is_running = False
        self.stats = OutputStats(name="RCA Composite")
        logger.info(f"RCACompositeOutput created: {RCA_DEVICE} ({RCA_FORMAT})")
        # TODO: Import GStreamer
        # TODO: Create V4L2 loopback device (if needed)
    
    def start(self):
        """Start RCA composite output."""
        if self.is_running:
            logger.warning("RCA output already running")
            return
        
        self.is_running = True
        # TODO: Start GStreamer pipeline
        # TODO: Create V4L2 loopback sink
        
        self.stats.is_active = True
        logger.info(f"RCA output started on {RCA_DEVICE}")
    
    def stop(self):
        """Stop RCA output."""
        if not self.is_running:
            return
        
        self.is_running = False
        # TODO: Shut down GStreamer pipeline
        
        self.stats.is_active = False
        logger.info("RCA output stopped")
    
    def send_frame(self, frame_data: bytes, width: int, height: int, fps: int) -> bool:
        """
        Send frame to RCA composite output.
        
        Args:
            frame_data: RGB frame (or other format)
            width: Frame width
            height: Frame height
            fps: Frames per second
        
        Returns:
            True if sent successfully
        """
        if not self.is_running:
            return False
        
        try:
            # TODO: Send frame through GStreamer pipeline
            # TODO: Encode to NTSC/PAL
            # TODO: Push to V4L2 loopback device
            
            self.stats.frames_sent += 1
            self.stats.bytes_sent += len(frame_data)
            return True
        
        except Exception as e:
            self.stats.errors += 1
            self.stats.last_error = str(e)
            logger.error(f"RCA send error: {e}")
            return False
    
    def get_stats(self) -> OutputStats:
        """Get RCA output statistics."""
        return self.stats

class USBDVROutput(OutputTarget):
    """
    USB DVR mode — Pi acts as a USB video device.
    
    Android head unit sees the Pi as a USB camera in its DVR app.
    
    Uses USB gadget mode (UVC - USB Video Class) if available,
    or GStreamer V4L2loopback.
    """
    
    def __init__(self):
        """Initialize USB DVR output."""
        self.is_running = False
        self.stats = OutputStats(name="USB DVR")
        logger.info("USBDVROutput created")
        # TODO: Check if UVC gadget available (Raspberry Pi OS)
        # TODO: Fallback to V4L2loopback
    
    def start(self):
        """Start USB DVR output."""
        if self.is_running:
            logger.warning("USB DVR output already running")
            return
        
        self.is_running = True
        # TODO: Enable UVC gadget or V4L2loopback
        # TODO: Create sink for incoming frames
        
        self.stats.is_active = True
        logger.info("USB DVR output started")
    
    def stop(self):
        """Stop USB DVR output."""
        if not self.is_running:
            return
        
        self.is_running = False
        # TODO: Disable UVC gadget
        
        self.stats.is_active = False
        logger.info("USB DVR output stopped")
    
    def send_frame(self, frame_data: bytes, width: int, height: int, fps: int) -> bool:
        """
        Send frame to USB DVR output.
        
        Args:
            frame_data: H.264 or MJPEG encoded frame
            width: Frame width
            height: Frame height
            fps: Frames per second
        
        Returns:
            True if sent successfully
        """
        if not self.is_running:
            return False
        
        try:
            # TODO: Send frame to UVC gadget or V4L2loopback
            self.stats.frames_sent += 1
            self.stats.bytes_sent += len(frame_data)
            return True
        
        except Exception as e:
            self.stats.errors += 1
            self.stats.last_error = str(e)
            logger.error(f"USB DVR send error: {e}")
            return False
    
    def get_stats(self) -> OutputStats:
        """Get USB DVR output statistics."""
        return self.stats

# ============================================================================
# OUTPUT MANAGER
# ============================================================================

class OutputManager:
    """
    Manages multiple video outputs simultaneously.
    
    Responsibilities:
      - Encode video frame to appropriate codec/format
      - Send encoded frame to all active outputs
      - Handle fallback if output fails
      - Track statistics for each output
      - Restart outputs on error
    
    Priority order (for fallback):
      1. RTSP (network, most flexible)
      2. RCA composite (USB adapter, reliable)
      3. USB DVR (direct Android integration, simplest)
    """
    
    def __init__(self):
        """Initialize output manager."""
        self.outputs: Dict[str, OutputTarget] = {}
        self.is_running = False
        self.frame_buffer = None
        
        # Initialize enabled outputs
        if RTSP_ENABLED:
            self.outputs["rtsp"] = RTSPOutput()
        if RCA_ENABLED:
            self.outputs["rca"] = RCACompositeOutput()
        if USB_DVR_ENABLED:
            self.outputs["usb_dvr"] = USBDVROutput()
        
        logger.info(f"OutputManager initialized with {len(self.outputs)} output(s)")
    
    def start(self):
        """Start all output targets."""
        if self.is_running:
            logger.warning("OutputManager already running")
            return
        
        self.is_running = True
        
        for name, output in self.outputs.items():
            try:
                output.start()
            except Exception as e:
                logger.error(f"Error starting output '{name}': {e}")
        
        logger.info("OutputManager started")
    
    def stop(self):
        """Stop all output targets."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        for name, output in self.outputs.items():
            try:
                output.stop()
            except Exception as e:
                logger.error(f"Error stopping output '{name}': {e}")
        
        logger.info("OutputManager stopped")
    
    def send_frame(self, frame_data: bytes, width: int, height: int, fps: int) -> bool:
        """
        Send frame to all active outputs.
        
        Args:
            frame_data: Raw or encoded frame data
            width: Frame width in pixels
            height: Frame height in pixels
            fps: Frames per second
        
        Returns:
            True if at least one output succeeded
        """
        if not self.is_running:
            return False
        
        any_success = False
        
        for name, output in self.outputs.items():
            try:
                if output.send_frame(frame_data, width, height, fps):
                    any_success = True
                else:
                    logger.warning(f"Output '{name}' failed to send frame")
            
            except Exception as e:
                logger.error(f"Exception in output '{name}': {e}")
        
        return any_success
    
    def get_stats(self) -> Dict[str, OutputStats]:
        """
        Get statistics for all outputs.
        
        Returns:
            Dict mapping output name to OutputStats
        """
        return {name: output.get_stats() for name, output in self.outputs.items()}
    
    def print_stats(self):
        """Print human-readable statistics."""
        print("\n" + "=" * 70)
        print("Video Output Statistics")
        print("=" * 70)
        
        for name, stats in self.get_stats().items():
            status = "ACTIVE" if stats.is_active else "INACTIVE"
            print(f"\n{name.upper()} — [{status}]")
            print(f"  Frames sent:   {stats.frames_sent}")
            print(f"  Bytes sent:    {stats.bytes_sent:,}")
            print(f"  Errors:        {stats.errors}")
            if stats.last_error:
                print(f"  Last error:    {stats.last_error}")
        
        print("\n" + "=" * 70)

if __name__ == "__main__":
    # Test output manager
    logging.basicConfig(level=logging.INFO)
    
    mgr = OutputManager()
    mgr.start()
    
    # Simulate frames
    test_frame = b'\x00' * (1920 * 1080)
    for i in range(10):
        success = mgr.send_frame(test_frame, 1920, 1080, 30)
        print(f"Frame {i}: {'OK' if success else 'FAILED'}")
    
    mgr.print_stats()
    mgr.stop()
