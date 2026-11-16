#!/usr/bin/env python3
"""
ThunderBird2 — Main Application Entry Point

Coordinates camera capture → view switching → multi-output encoding.

Usage:
    python src/main.py              # Run normally
    python src/main.py --config     # Print config summary
    python src/main.py --test       # Run self-tests
"""

import os
import sys
import logging
import argparse
import signal
from typing import Optional

sys.path.insert(0, os.path.dirname(__file__))

import config
from camera_manager import CameraManager
from view_logic import ViewLogic
from output_manager import OutputManager

# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging():
    """Configure logging for the application."""
    logger = logging.getLogger("ThunderBird2")
    logger.setLevel(config.LOG_LEVEL)
    
    formatter = logging.Formatter(
        "[%(asctime)s] %(name)s — %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    log_dir = config.LOG_DIR
    os.makedirs(log_dir, exist_ok=True)
    
    file_handler = logging.FileHandler(os.path.join(log_dir, "app.log"))
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

logger = setup_logging()

# ============================================================================
# APPLICATION STATE
# ============================================================================

class ThunderBird2:
    """Main application controller."""
    
    def __init__(self):
        """Initialize the application."""
        self.camera_manager = CameraManager()
        self.view_logic = ViewLogic()
        self.output_manager = OutputManager()
        
        self.is_running = False
        self.frame_count = 0
        
        logger.info("ThunderBird2 application initialized")
    
    def setup(self) -> bool:
        """
        Initialize all subsystems.
        
        Returns:
            True if setup successful, False otherwise
        """
        logger.info("Setting up subsystems...")
        
        # Detect cameras
        if not self.camera_manager.detect_cameras():
            logger.error("Failed to detect cameras")
            return False
        
        logger.info("Camera setup complete")
        
        # Setup view logic
        # Register callback for view changes
        self.view_logic.register_on_view_change(self._on_view_changed)
        logger.info("View logic setup complete")
        
        # Setup output manager (creates encoders, streams)
        logger.info("Output manager initialized")
        
        # Validate configuration
        is_valid, issues = config.validate_config()
        if not is_valid:
            for issue in issues:
                logger.warning(issue)
        
        logger.info("Setup complete")
        return True
    
    def start(self):
        """Start the application."""
        if self.is_running:
            logger.warning("Application already running")
            return
        
        logger.info("Starting ThunderBird2...")
        
        self.camera_manager.start()
        self.view_logic.start()
        self.output_manager.start()
        
        self.is_running = True
        logger.info("ThunderBird2 started successfully")
    
    def stop(self):
        """Stop the application gracefully."""
        if not self.is_running:
            return
        
        logger.info("Stopping ThunderBird2...")
        
        self.camera_manager.stop()
        self.view_logic.stop()
        self.output_manager.stop()
        
        self.is_running = False
        logger.info("ThunderBird2 stopped")
    
    def run(self):
        """Main event loop."""
        logger.info("Entering main event loop")
        
        try:
            frame_count = 0
            while self.is_running:
                # Capture frame from camera manager
                # frame = self.camera_manager.get_frame(timeout=0.033)  # ~30fps
                
                # TODO: Process signals and update view
                # signals = InputSignals(...)  # Collect from GPIO/CAN/BT
                # self.view_logic.process_signals(signals)
                
                # TODO: Encode and send to outputs
                # self.output_manager.send_frame(frame.data, frame.width, frame.height, frame.fps)
                
                frame_count += 1
                if frame_count % 300 == 0:  # Every 10 seconds at 30fps
                    self.output_manager.print_stats()
        
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
        finally:
            self.stop()
    
    def _on_view_changed(self, view):
        """Callback when view mode changes."""
        logger.info(f"View changed to: {view.value}")

# ============================================================================
# SIGNAL HANDLERS
# ============================================================================

def setup_signal_handlers(app: ThunderBird2):
    """Setup signal handlers for graceful shutdown."""
    
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        app.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

# ============================================================================
# CLI & TESTING
# ============================================================================

def print_config_summary():
    """Print configuration summary."""
    print()
    print("=" * 70)
    print("ThunderBird2 Configuration Summary")
    print("=" * 70)
    print()
    
    print("Camera Configuration:")
    for key, val in config.get_camera_info().items():
        print(f"  {key}: {val}")
    
    print()
    print("Video Output Pipeline (priority order):")
    for i, output in enumerate(config.get_output_pipeline(), 1):
        print(f"  {i}. {output}")
    
    print()
    print("GPIO Pins (Octocoupler):")
    for pin_name, pin_num in config.OCTOCOUPLER_PINS.items():
        status = "CONFIGURED" if pin_num != -1 else "NOT YET WIRED"
        print(f"  {pin_name}: GPIO {pin_num} [{status}]")
    
    print()
    print("Configuration Status:")
    is_valid, issues = config.validate_config()
    if is_valid:
        print("  ✓ Configuration is valid")
    else:
        for issue in issues:
            print(f"  ! {issue}")
    
    print()
    print("=" * 70)

def run_tests():
    """Run self-tests."""
    print()
    print("=" * 70)
    print("ThunderBird2 Self-Tests")
    print("=" * 70)
    print()
    
    # Test 1: Config validation
    print("Test 1: Configuration validation... ", end="")
    is_valid, issues = config.validate_config()
    if is_valid:
        print("PASS")
    else:
        print("WARNINGS")
        for issue in issues:
            print(f"  - {issue}")
    
    # Test 2: Camera detection (import test)
    print("Test 2: Camera detection module... ", end="")
    try:
        from camera_detection import detect_cameras
        print("PASS")
    except Exception as e:
        print(f"FAIL: {e}")
    
    # Test 3: Camera manager
    print("Test 3: Camera manager module... ", end="")
    try:
        mgr = CameraManager()
        print("PASS")
    except Exception as e:
        print(f"FAIL: {e}")
    
    # Test 4: View logic
    print("Test 4: View logic module... ", end="")
    try:
        logic = ViewLogic()
        print("PASS")
    except Exception as e:
        print(f"FAIL: {e}")
    
    # Test 5: Output manager
    print("Test 5: Output manager module... ", end="")
    try:
        output = OutputManager()
        print("PASS")
    except Exception as e:
        print(f"FAIL: {e}")
    
    print()
    print("=" * 70)

# ============================================================================
# ENTRY POINT
# ============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="ThunderBird2 — Camera Controller for Nissan Atlas"
    )
    parser.add_argument(
        "--config",
        action="store_true",
        help="Print configuration summary and exit"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run self-tests and exit"
    )
    
    args = parser.parse_args()
    
    if args.config:
        print_config_summary()
        return 0
    
    if args.test:
        run_tests()
        return 0
    
    # Run the application
    app = ThunderBird2()
    
    # Setup signal handlers
    setup_signal_handlers(app)
    
    # Initialize
    if not app.setup():
        logger.error("Setup failed")
        return 1
    
    # Start and run
    app.start()
    app.run()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
