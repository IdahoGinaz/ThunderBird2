#!/usr/bin/env python3
"""
ThunderBird2 — POC (Proof of Concept) Demo

Runs a complete end-to-end demo:
  1. Captures from 3 USB cameras
  2. Accepts keyboard input (1/2/3 to select camera, r for reverse)
  3. Outputs to display + RTSP stream
  4. Shows FPS and stats

Usage:
    python src/run_poc.py
    
Keyboard controls:
    1 / 2 / 3  - Select camera
    r          - Toggle reverse mode
    q          - Quit
    
To view the RTSP stream from Windows:
    ffplay rtsp://thunderbird2.local:8554/camera
    or use VLC: File > Open Network Stream > rtsp://thunderbird2.local:8554/camera

Author: Copilot
Updated: 2026-11-17
"""

import sys
import os
import time
import logging
import signal

sys.path.insert(0, os.path.dirname(__file__))

from camera_manager import CameraManager
from view_logic import ViewLogicEngine, KeyboardInputReader
from output_manager import OutputManager, DisplayOutput, RTSPOutput

# ============================================================================
# CONFIGURATION
# ============================================================================

LOG_LEVEL = logging.INFO
SHOW_STATS_INTERVAL = 5.0  # Print stats every N seconds

# ============================================================================
# LOGGING
# ============================================================================

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger("ThunderBird2.POC")

# ============================================================================
# MAIN APPLICATION
# ============================================================================

class ThunderBird2POC:
    """Main POC application."""
    
    def __init__(self):
        """Initialize the application."""
        self.camera_manager = None
        self.view_logic = None
        self.output_manager = None
        self.is_running = False
        self.frame_count = 0
        self.last_stats_print = time.time()
    
    def setup(self) -> bool:
        """
        Initialize all components.
        
        Returns:
            True if successful, False otherwise
        """
        logger.info("=" * 80)
        logger.info("ThunderBird2 POC - Starting")
        logger.info("=" * 80)
        
        # Initialize camera manager
        logger.info("Initializing camera manager...")
        self.camera_manager = CameraManager()
        if not self.camera_manager.detect_cameras():
            logger.error("Failed to detect cameras")
            return False
        
        self.camera_manager.start()
        logger.info(f"✓ Camera manager started with {len(self.camera_manager.cameras)} camera(s)")
        
        # Initialize view logic with keyboard input
        logger.info("Initializing view logic...")
        self.view_logic = ViewLogicEngine(num_cameras=len(self.camera_manager.cameras))
        keyboard_reader = KeyboardInputReader()
        self.view_logic.set_input_reader(keyboard_reader)
        self.view_logic.start()
        logger.info("✓ View logic started (keyboard control)")
        
        # Initialize output manager
        logger.info("Initializing output manager...")
        self.output_manager = OutputManager()
        self.output_manager.add_output("display", DisplayOutput())
        self.output_manager.add_output("rtsp", RTSPOutput())
        self.output_manager.start()
        logger.info("✓ Output manager started")
        
        logger.info("=" * 80)
        logger.info("PRESS: 1/2/3 to select camera, r for reverse, q to quit")
        logger.info("=" * 80)
        
        return True
    
    def run(self):
        """Main event loop."""
        self.is_running = True
        
        try:
            while self.is_running:
                # Determine which camera to display
                view_info = self.view_logic.get_view_info()
                active_camera_id = view_info["camera"]
                
                # Get a frame from the active camera
                frame = self.camera_manager.get_frame(timeout=0.5)
                
                if frame and frame.camera_id == active_camera_id:
                    # Send frame to outputs
                    self.output_manager.send_frame(
                        frame.data,
                        frame.width,
                        frame.height,
                        frame.fps,
                    )
                    
                    self.frame_count += 1
                
                # Print stats periodically
                now = time.time()
                if now - self.last_stats_print > SHOW_STATS_INTERVAL:
                    self._print_stats()
                    self.last_stats_print = now
        
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
        finally:
            self.is_running = False
    
    def shutdown(self):
        """Clean up and shutdown."""
        logger.info("Shutting down...")
        
        if self.camera_manager:
            self.camera_manager.stop()
            logger.info("✓ Camera manager stopped")
        
        if self.view_logic:
            self.view_logic.stop()
            logger.info("✓ View logic stopped")
        
        if self.output_manager:
            self.output_manager.stop()
            logger.info("✓ Output manager stopped")
        
        self._print_stats()
        logger.info("=" * 80)
        logger.info("ThunderBird2 POC - Shutdown complete")
        logger.info("=" * 80)
    
    def _print_stats(self):
        """Print application statistics."""
        if not self.output_manager:
            return
        
        output_stats = self.output_manager.get_stats()
        avg_frame_size = 0
        
        print("\n" + "=" * 80)
        print("STATS:")
        print("=" * 80)
        
        for name, stats in output_stats.items():
            if stats.frames_sent > 0:
                avg_frame_size = stats.bytes_sent // stats.frames_sent
            
            status = "✓ ACTIVE" if stats.is_active else "• IDLE"
            print(
                f"  {name:12} | {status:8} | "
                f"Frames: {stats.frames_sent:6} | "
                f"Size: {avg_frame_size:6} bytes | "
                f"Errors: {stats.errors:3}"
            )
        
        print("=" * 80 + "\n")

# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    """Main entry point."""
    app = ThunderBird2POC()
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        app.is_running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run application
    try:
        if not app.setup():
            logger.error("Setup failed")
            return 1
        
        app.run()
        return 0
    
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1
    
    finally:
        app.shutdown()

if __name__ == "__main__":
    sys.exit(main())
