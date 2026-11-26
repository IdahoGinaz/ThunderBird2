"""
ThunderBird2 — View Logic & Control

Handles view switching based on:
  - Turn signals (GPIO from octocoupler + CAN from Nissan Atlas)
  - Manual input (Keyboard for POC, Bluetooth keyboard later)
  - Reverse/brake detection
  
Coordinates which camera(s) to display and in what layout.

Author: Copilot
Updated: 2026-11-17
"""

import os
import sys
import logging
import threading
import time
import select
from typing import Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from abc import ABC, abstractmethod

sys.path.insert(0, os.path.dirname(__file__))
from config import (
    VIEW_MODES,
    DEFAULT_VIEW,
    OCTOCOUPLER_PINS,
    CAN_MESSAGES,
    CAN_FALLBACK_TIMEOUT,
    INDICATOR_DEBOUNCE_MS,
)

logger = logging.getLogger("ThunderBird2.ViewLogic")

# ============================================================================
# ENUMS & DATA STRUCTURES
# ============================================================================

class ViewMode(Enum):
    """View modes that can be displayed to the driver."""
    NORMAL = "NORMAL"
    LEFT_INDICATOR = "LEFT_INDICATOR"
    RIGHT_INDICATOR = "RIGHT_INDICATOR"
    REVERSE = "REVERSE"
    PARKED = "PARKED"
    MANUAL = "MANUAL"

@dataclass
class InputSignals:
    """Current state of all input signals."""
    left_indicator: bool = False
    right_indicator: bool = False
    reverse: bool = False
    brake: bool = False
    manual_camera: Optional[int] = None
    timestamp: float = 0.0

# ============================================================================
# INPUT READERS
# ============================================================================

class InputReader(ABC):
    """Base class for different input sources (GPIO, CAN, Keyboard)."""
    
    @abstractmethod
    def read_signals(self) -> InputSignals:
        """Read current state of signals."""
        pass
    
    @abstractmethod
    def start(self):
        """Start reading inputs."""
        pass
    
    @abstractmethod
    def stop(self):
        """Stop reading inputs."""
        pass

class KeyboardInputReader(InputReader):
    """
    Read manual camera selection from keyboard (POC & permanent).
    
    Supports dynamic camera count. Keys:
      - '1' through '9': Select camera (up to num_cameras)
      - 'r'/'R': Toggle reverse mode
      - 'l'/'L': Left turn signal
      - 'k'/'K': Right turn signal (mnemonic: riGht = K)
      - 'n'/'N': Normal mode
      - 'q'/'Q': Quit
    """
    
    def __init__(self, num_cameras: int = 3):
        """Initialize keyboard reader.
        
        Args:
            num_cameras: Number of available cameras (dynamic support)
        """
        self.is_running = False
        self.num_cameras = num_cameras
        self.current_camera = 0
        self.reverse = False
        self.left_indicator = False
        self.right_indicator = False
        self.signals = InputSignals()
        self.original_settings = None
        logger.info(f"KeyboardInputReader created - supporting {num_cameras} camera(s)")
        self._print_help()
    
    def _print_help(self):
        """Print keyboard controls."""
        print("\n" + "="*60)
        print("ThunderBird2 Keyboard Controls")
        print("="*60)
        for cam_num in range(1, min(self.num_cameras + 1, 10)):
            print(f"  '{cam_num}' : Camera {cam_num}")
        print(f"  'r'  : Reverse (back camera)")
        print(f"  'l'  : Left turn signal")
        print(f"  'k'  : Right turn signal")
        print(f"  'n'  : Normal view")
        print(f"  'q'  : Quit")
        print("="*60 + "\n")
    
    def read_signals(self) -> InputSignals:
        """Check for keyboard input (truly non-blocking)."""
        if not self.is_running:
            return self.signals
        
        # Try to read single character without blocking
        try:
            # Using non-blocking read with select as fallback for compatibility
            if sys.stdin in select.select([sys.stdin], [], [], 0.001)[0]:
                try:
                    # Non-blocking read - will raise BlockingIOError if no data
                    key = sys.stdin.read(1).lower()
                    if not key:  # EOF
                        return self.signals
                except (BlockingIOError, IOError):
                    # No data available yet
                    return self.signals
                
                if key == 'q':
                    raise KeyboardInterrupt("User quit via keyboard")
                
                # Camera selection (1-9)
                elif key.isdigit():
                    cam_num = int(key)
                    if 1 <= cam_num <= self.num_cameras:
                        self.current_camera = cam_num - 1
                        self.signals.manual_camera = cam_num - 1
                        self.left_indicator = False
                        self.right_indicator = False
                        self.reverse = False
                        logger.info(f"Selected camera {cam_num}")
                    else:
                        logger.debug(f"Camera {cam_num} not available (have {self.num_cameras})")
                
                # Reverse mode
                elif key == 'r':
                    self.reverse = not self.reverse
                    self.signals.reverse = self.reverse
                    self.signals.manual_camera = None
                    self.left_indicator = False
                    self.right_indicator = False
                    logger.info(f"Reverse: {self.reverse}")
                
                # Turn signals
                elif key == 'l':
                    self.left_indicator = not self.left_indicator
                    self.right_indicator = False  # Can't turn both ways
                    self.signals.left_indicator = self.left_indicator
                    self.signals.right_indicator = False
                    self.reverse = False
                    self.signals.manual_camera = None
                    logger.info(f"Left indicator: {self.left_indicator}")
                
                elif key == 'k':  # k for riGht
                    self.right_indicator = not self.right_indicator
                    self.left_indicator = False  # Can't turn both ways
                    self.signals.left_indicator = False
                    self.signals.right_indicator = self.right_indicator
                    self.reverse = False
                    self.signals.manual_camera = None
                    logger.info(f"Right indicator: {self.right_indicator}")
                
                # Normal mode
                elif key == 'n':
                    self.reverse = False
                    self.left_indicator = False
                    self.right_indicator = False
                    self.signals.manual_camera = None
                    self.signals.reverse = False
                    self.signals.left_indicator = False
                    self.signals.right_indicator = False
                    logger.info("Normal mode")
        
        except (EOFError, KeyboardInterrupt):
            raise
        except Exception as e:
            logger.debug(f"Keyboard read error: {e}")
        
        self.signals.timestamp = time.time()
        return self.signals
    
    def start(self):
        """Start reading keyboard input."""
        self.is_running = True
        # Set stdin to non-blocking, raw mode on Unix-like systems if it's a real TTY
        try:
            import tty
            import termios
            import fcntl
            
            # Only apply raw mode if stdin is a TTY (real terminal, not piped/SSH)
            if sys.stdin.isatty():
                self.original_settings = termios.tcgetattr(sys.stdin)
                # Set raw mode (no line buffering, no echo)
                tty.setraw(sys.stdin.fileno())
                
                # Also set non-blocking at OS level
                flags = fcntl.fcntl(sys.stdin, fcntl.F_GETFL)
                fcntl.fcntl(sys.stdin, fcntl.F_SETFL, flags | os.O_NONBLOCK)
                
                logger.info("Terminal set to raw, non-blocking mode for instant key detection")
            else:
                logger.info("stdin is not a TTY (SSH/piped input) - using select-based input")
        except Exception as e:
            logger.warning(f"Could not set terminal to raw mode: {e} (using fallback)")
    
    def stop(self):
        """Stop reading keyboard input."""
        self.is_running = False
        # Restore terminal settings
        try:
            if self.original_settings:
                import termios
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.original_settings)
        except:
            pass
        logger.info("Keyboard reader stopped")

class GPIOInputReader(InputReader):
    """
    Read turn signals and control signals from GPIO (octocoupler).
    TODO: Implement in Phase 3 when hardware is wired.
    """
    
    def __init__(self):
        """Initialize GPIO reader."""
        self.is_running = False
        self.signals = InputSignals()
        logger.info("GPIOInputReader created (not yet implemented)")
    
    def read_signals(self) -> InputSignals:
        """Return dummy signals for now."""
        return self.signals
    
    def start(self):
        """Start reading GPIO."""
        self.is_running = True
    
    def stop(self):
        """Stop reading GPIO."""
        self.is_running = False

class CANInputReader(InputReader):
    """
    Read Nissan Atlas CAN messages (turn signals, reverse, brake).
    TODO: Implement in Phase 3 when CAN HAT is wired and IDs are known.
    """
    
    def __init__(self):
        """Initialize CAN reader."""
        self.is_running = False
        self.signals = InputSignals()
        logger.info("CANInputReader created (not yet implemented)")
    
    def read_signals(self) -> InputSignals:
        """Return dummy signals for now."""
        return self.signals
    
    def start(self):
        """Start reading CAN bus."""
        self.is_running = True
    
    def stop(self):
        """Stop reading CAN."""
        self.is_running = False

# ============================================================================
# VIEW LOGIC ENGINE
# ============================================================================

class ViewLogicEngine:
    """
    Main view switching logic.
    
    Reads input signals (GPIO, CAN, keyboard) and determines which camera(s)
    to display based on priority:
      1. Manual override (keyboard input)
      2. Reverse camera (when in reverse)
      3. Turn signals (left/right turn)
      4. Normal view (front camera)
    """
    
    def __init__(self, num_cameras: int = 3):
        """Initialize view logic."""
        self.num_cameras = num_cameras
        self.input_reader: Optional[InputReader] = None
        self.current_view = DEFAULT_VIEW
        self.last_signals = InputSignals()
        self.on_view_change_callback: Optional[Callable] = None
        logger.info(f"ViewLogicEngine initialized with {num_cameras} cameras")
    
    def set_input_reader(self, reader: InputReader):
        """Set the input reader (keyboard, GPIO, CAN, etc)."""
        self.input_reader = reader
        logger.info(f"Input reader set: {reader.__class__.__name__}")
    
    def register_on_view_change(self, callback: Callable):
        """Register a callback for when view mode changes."""
        self.on_view_change_callback = callback
        logger.info(f"View change callback registered")
    
    def get_active_camera(self) -> int:
        """
        Determine which camera should be active based on current inputs.
        
        Returns:
            Camera index (0-based)
        """
        if self.input_reader is None:
            logger.warning("No input reader set, using camera 0")
            return 0
        
        signals = self.input_reader.read_signals()
        self.last_signals = signals
        
        previous_view = self.current_view
        
        # Priority 1: Manual override (keyboard/Bluetooth)
        if signals.manual_camera is not None:
            self.current_view = ViewMode.MANUAL
            camera = signals.manual_camera
        # Priority 2: Reverse camera
        elif signals.reverse:
            self.current_view = ViewMode.REVERSE
            camera = 2  # Assuming camera 2 is rear-facing
        # Priority 3: Turn signals
        elif signals.left_indicator:
            self.current_view = ViewMode.LEFT_INDICATOR
            camera = 1  # Left camera
        elif signals.right_indicator:
            self.current_view = ViewMode.RIGHT_INDICATOR
            camera = 1  # Right camera (or 2, depending on layout)
        # Priority 4: Normal forward view
        else:
            self.current_view = ViewMode.NORMAL
            camera = 0
        
        # Trigger callback if view changed
        if previous_view != self.current_view and self.on_view_change_callback:
            self.on_view_change_callback(self.current_view)
        
        return camera
    
    def get_view_info(self) -> Dict:
        """Get current view mode and camera info."""
        active_camera = self.get_active_camera()
        return {
            "mode": self.current_view.value,
            "camera": active_camera,
            "left_indicator": self.last_signals.left_indicator,
            "right_indicator": self.last_signals.right_indicator,
            "reverse": self.last_signals.reverse,
        }
    
    def start(self):
        """Start view logic engine."""
        if self.input_reader:
            self.input_reader.start()
        logger.info("ViewLogicEngine started")
    
    def stop(self):
        """Stop view logic engine."""
        if self.input_reader:
            self.input_reader.stop()
        logger.info("ViewLogicEngine stopped")

if __name__ == "__main__":
    # Test keyboard input
    logging.basicConfig(level=logging.INFO)
    
    engine = ViewLogicEngine(num_cameras=3)
    reader = KeyboardInputReader()
    engine.set_input_reader(reader)
    engine.start()
    
    print("\n=== Keyboard Input Test ===")
    print("Press: 1/2/3 to select camera, r for reverse, q to quit")
    print()
    
    try:
        for i in range(100):
            view_info = engine.get_view_info()
            print(f"Camera: {view_info['camera']} | Mode: {view_info['mode']}", end='\r')
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nQuit")
    finally:
        engine.stop()
