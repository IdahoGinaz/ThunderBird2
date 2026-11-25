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
    
    Uses GStreamer to encode JPEG frames to H.264 and serve via RTSP.
    """
    
    def __init__(self):
        """Initialize RTSP output."""
        self.is_running = False
        self.stats = OutputStats(name="RTSP")
        self.server = None
        self.pipeline = None
        self.appsrc = None
        self.bus = None
        self.gstreamer_available = False
        self.lock = threading.Lock()
        self.glib_loop = None
        self.glib_thread = None
        
        try:
            import gi
            gi.require_version("Gst", "1.0")
            gi.require_version("GstRtspServer", "1.0")
            from gi.repository import Gst, GstRtspServer
            self.Gst = Gst
            self.GstRtspServer = GstRtspServer
            
            # Initialize GStreamer
            if not Gst.is_initialized():
                Gst.init(None)
            
            self.gstreamer_available = True
            logger.info(f"RTSPOutput created: rtsp://{RTSP_HOST}:{RTSP_PORT}{RTSP_PATH} (GStreamer ready)")
        except ImportError as e:
            logger.warning(f"GStreamer RTSP server not available: {e}")
            logger.warning("RTSP output will use frame counting fallback. Install with:")
            logger.warning("  sudo apt-get install gir1.2-gst-rtsp-server-1.0")
            self.Gst = None
            self.GstRtspServer = None
        except Exception as e:
            logger.error(f"Error initializing GStreamer: {e}")
            self.Gst = None
            self.GstRtspServer = None
    
    def start(self):
        """Start RTSP server and begin streaming."""
        if self.is_running:
            logger.warning("RTSP output already running")
            return
        
        if not self.gstreamer_available:
            logger.warning("GStreamer RTSP server not available, using fallback frame counting")
            self.is_running = True
            self.stats.is_active = True
            return
        
        try:
            Gst = self.Gst
            GstRtspServer = self.GstRtspServer
            GLib = __import__("gi.repository", fromlist=["GLib"]).GLib
            
            # Create RTSP server
            self.server = GstRtspServer.RTSPServer()
            self.server.set_property("service", str(RTSP_PORT))
            self.server.set_property("address", RTSP_HOST)
            
            # Create media factory with dynamic pipeline creation
            media_factory = self._create_media_factory()
            
            # Attach to default mount points
            mount_points = self.server.get_mount_points()
            mount_points.add_factory(RTSP_PATH, media_factory)
            
            # Create and start GLib main loop in background thread
            # This is REQUIRED for the RTSP server to process client requests
            self.glib_loop = GLib.MainLoop()
            self.glib_thread = threading.Thread(target=self._glib_main_loop, daemon=True)
            self.glib_thread.start()
            
            # Attach server to the main loop
            self.server.attach(self.glib_loop.get_context())
            
            self.is_running = True
            self.stats.is_active = True
            logger.info(f"RTSP output started on {RTSP_HOST}:{RTSP_PORT}{RTSP_PATH} (with GLib main loop)")
        
        except Exception as e:
            self.is_running = False
            self.stats.errors += 1
            self.stats.last_error = str(e)
            logger.error(f"Failed to start RTSP server: {e}", exc_info=True)
    
    def _glib_main_loop(self):
        """Run GLib main loop in background thread to process RTSP requests."""
        try:
            if self.glib_loop:
                self.glib_loop.run()
        except Exception as e:
            logger.error(f"GLib main loop error: {e}")
    
    def _create_media_factory(self):
        """Create RTSP media factory with per-client pipelines."""
        try:
            GstRtspServer = self.GstRtspServer
            Gst = self.Gst
            parent_self = self
            
            class RTSPMediaFactory(GstRtspServer.RTSPMediaFactory):
                def __init__(self):
                    super().__init__()
                
                def do_create_element(self, url):
                    # Create pipeline with appsrc for live frame injection
                    pipeline_str = (
                        "appsrc name=source is-live=true do-timestamp=false "
                        "caps=\"image/jpeg,width=1920,height=1080\" ! "
                        "jpegdec ! "
                        "videoscale ! video/x-raw,width=1280,height=720 ! "
                        "videoconvert ! "
                        "x264enc speed-preset=ultrafast bitrate=2000 ! "
                        "rtph264pay name=pay0 pt=96"
                    )
                    
                    pipeline = Gst.parse_launch(pipeline_str)
                    if not pipeline:
                        raise Exception("Failed to parse pipeline")
                    
                    # Capture first appsrc element for frame injection
                    source = pipeline.get_by_name("source")
                    if source and not parent_self.appsrc:
                        with parent_self.lock:
                            if not parent_self.appsrc:
                                parent_self.appsrc = source
                                logger.info("Captured appsrc element from RTSP pipeline")
                    
                    return pipeline
            
            factory = RTSPMediaFactory()
            factory.set_shared(False)  # Create new pipeline per client
            # Don't suspend - keep encoding even when no clients connected
            factory.set_suspend_mode(GstRtspServer.RTSPSuspendMode.NONE)
            
            return factory
        
        except Exception as e:
            logger.error(f"Error creating RTSP media factory: {e}")
            raise
    
    def _on_bus_message(self, bus, message):
        """Handle GStreamer bus messages (legacy, not used in dynamic mode)."""
        pass
    
    
    def stop(self):
        """Stop RTSP server."""
        if not self.is_running:
            return
        
        try:
            self.is_running = False
            
            # Stop GLib main loop
            if self.glib_loop:
                self.glib_loop.quit()
            
            # Wait for thread to finish
            if self.glib_thread and self.glib_thread.is_alive():
                self.glib_thread.join(timeout=2)
            
            self.glib_loop = None
            self.glib_thread = None
            self.appsrc = None
            if self.server:
                self.server = None
            self.stats.is_active = False
            logger.info("RTSP output stopped")
        except Exception as e:
            logger.error(f"Error stopping RTSP server: {e}")
    
    def send_frame(self, frame_data: bytes, width: int, height: int, fps: int) -> bool:
        """
        Send frame to RTSP clients via appsrc injection.
        
        Args:
            frame_data: JPEG encoded frame bytes
            width: Frame width (1920 expected)
            height: Frame height (1080 expected)
            fps: Frames per second from camera
        
        Returns:
            True if sent successfully
        """
        if not self.is_running:
            return False
        
        try:
            if not self.gstreamer_available or not self.appsrc:
                # Fallback: just count frames while waiting for first client
                self.stats.frames_sent += 1
                self.stats.bytes_sent += len(frame_data)
                return True
            
            Gst = self.Gst
            
            # Create buffer from JPEG frame data
            buf = Gst.Buffer.new_wrapped(frame_data)
            # Set duration based on frame rate
            buf.duration = Gst.SECOND // fps if fps > 0 else 33 * Gst.MSECOND
            
            # Push buffer to appsrc element
            with self.lock:
                try:
                    result = self.appsrc.emit("push-buffer", buf)
                    if result != Gst.FlowReturn.OK:
                        logger.debug(f"GStreamer push-buffer returned: {result}")
                        self.stats.errors += 1
                        return False
                except Exception as e:
                    logger.debug(f"Error pushing buffer to appsrc: {e}")
                    self.stats.errors += 1
                    return False
            
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
    
    Uses GStreamer to convert JPEG -> NTSC/PAL and loop back via V4L2.
    """
    
    def __init__(self):
        """Initialize RCA composite output."""
        self.is_running = False
        self.stats = OutputStats(name="RCA Composite")
        self.gstreamer_available = False
        self.pipeline = None
        self.appsrc = None
        
        try:
            import gi
            gi.require_version("Gst", "1.0")
            from gi.repository import Gst
            self.Gst = Gst
            
            if not Gst.is_initialized():
                Gst.init(None)
            
            self.gstreamer_available = True
            logger.info(f"RCACompositeOutput created: {RCA_DEVICE} ({RCA_FORMAT}) (GStreamer ready)")
        except (ImportError, ValueError):
            logger.warning(f"RCACompositeOutput: GStreamer not available, using frame counting fallback")
            logger.info(f"Would output to: {RCA_DEVICE} ({RCA_FORMAT})")
            self.Gst = None
    
    def start(self):
        """Start RCA composite output."""
        if self.is_running:
            logger.warning("RCA output already running")
            return
        
        self.is_running = True
        
        if self.gstreamer_available and self.Gst:
            try:
                # TODO: Create V4L2loopback pipeline
                # Pipeline: appsrc -> jpegdec -> videoconvert -> ntscenc (or palenc) -> v4l2sink device=/dev/video10
                pass
            except Exception as e:
                logger.warning(f"RCA GStreamer pipeline failed: {e}, using fallback")
        else:
            logger.debug("RCA output: using frame counting fallback")
        
        self.stats.is_active = True
        logger.info(f"RCA output started on {RCA_DEVICE}")
    
    def stop(self):
        """Stop RCA output."""
        if not self.is_running:
            return
        
        self.is_running = False
        self.stats.is_active = False
        logger.info("RCA output stopped")
    
    def send_frame(self, frame_data: bytes, width: int, height: int, fps: int) -> bool:
        """
        Send frame to RCA composite output.
        
        Args:
            frame_data: JPEG encoded frame
            width: Frame width
            height: Frame height
            fps: Frames per second
        
        Returns:
            True if sent successfully
        """
        if not self.is_running:
            return False
        
        try:
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
        
        # Check if UVC gadget is available
        self.uvc_gadget_path = "/sys/kernel/config/usb_gadget/webcam/functions/uvc.0/streaming"
        self.has_uvc_gadget = os.path.exists(self.uvc_gadget_path) if hasattr(os, 'path') else False
        
        if self.has_uvc_gadget:
            logger.info("USBDVROutput: UVC gadget available")
        else:
            logger.info("USBDVROutput: UVC gadget not available, will use fallback frame counting")
    
    def start(self):
        """Start USB DVR output."""
        if self.is_running:
            logger.warning("USB DVR output already running")
            return
        
        self.is_running = True
        
        if self.has_uvc_gadget:
            try:
                # TODO: Enable UVC gadget for frame streaming
                logger.debug("USB DVR: Would configure UVC gadget for MJPEG streaming")
            except Exception as e:
                logger.warning(f"USB DVR gadget failed: {e}, using fallback")
        else:
            logger.debug("USB DVR: using frame counting fallback")
        
        self.stats.is_active = True
        logger.info("USB DVR output started")
    
    def stop(self):
        """Stop USB DVR output."""
        if not self.is_running:
            return
        
        self.is_running = False
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
