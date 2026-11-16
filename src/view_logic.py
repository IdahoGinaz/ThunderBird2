"""
ThunderBird2 — View Logic & Control

Handles view switching based on:
  - Turn signals (GPIO from octocoupler + CAN from Nissan Atlas)
  - Manual input (Bluetooth keyboard)
  - Reverse/brake detection
  
Coordinates which camera(s) to display and in what layout.

Author: Copilot
Updated: 2026-11-17
"""

import os
import sys
import logging
import threading
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
    NORMAL = "NORMAL"           # Normal forward view
    LEFT_INDICATOR = "LEFT_INDICATOR"    # Left turn signal active
    RIGHT_INDICATOR = "RIGHT_INDICATOR"  # Right turn signal active
    REVERSE = "REVERSE"         # Reverse camera (backup)
    PARKED = "PARKED"           # Quad-view or carousel
    MANUAL = "MANUAL"           # Driver manually selected

@dataclass
class InputSignals:
    """Current state of all input signals."""
    left_indicator: bool = False
    right_indicator: bool = False
    reverse: bool = False
    brake: bool = False
    manual_camera: Optional[int] = None  # 0=front, 1=left, 2=right, 3=rear
    timestamp: float = 0.0

# ============================================================================
# INPUT READERS
# ============================================================================

class InputReader(ABC):
    """Base class for different input sources (GPIO, CAN, Bluetooth)."""
    
    @abstractmethod
    def read_signals(self) -> InputSignals:
        """
        Read current state of signals.
        
        Returns:
            InputSignals with current values
        """
        pass
    
    @abstractmethod
    def start(self):
        """Start reading inputs."""
        pass
    
    @abstractmethod
    def stop(self):
        """Stop reading inputs."""
        pass

class GPIOInputReader(InputReader):
    """
    Read turn signals and control signals from GPIO (octocoupler).
    
    Uses RPi.GPIO or gpiozero library to poll octocoupler pins.
    """
    
    def __init__(self):
        """Initialize GPIO reader."""
        self.is_running = False
        logger.info("GPIOInputReader created")
        # TODO: Import RPi.GPIO or gpiozero
        # TODO: Configure pins from config.OCTOCOUPLER_PINS
    
    def read_signals(self) -> InputSignals:
        """
        Read current state of GPIO pins.
        
        Returns:
            InputSignals with GPIO pin states
        """
        # TODO: Read GPIO pins
        # TODO: Apply debouncing (config.INDICATOR_DEBOUNCE_MS)
        # TODO: Return InputSignals
        
        return InputSignals()
    
    def start(self):
        """Start GPIO polling thread."""
        if self.is_running:
            return
        
        self.is_running = True
        # TODO: Start background polling thread
        logger.info("GPIOInputReader started")
    
    def stop(self):
        """Stop GPIO polling."""
        self.is_running = False
        logger.info("GPIOInputReader stopped")

class CANInputReader(InputReader):
    """
    Read turn signals and status from Nissan Atlas CAN bus.
    
    Uses python-can library to decode CAN messages.
    CAN IDs and message formats from config.CAN_MESSAGES.
    """
    
    def __init__(self):
        """Initialize CAN reader."""
        self.is_running = False
        self.can_bus = None  # python-can Bus object
        self.last_can_message_time = 0.0
        logger.info("CANInputReader created")
        # TODO: Import python-can
        # TODO: Initialize CAN interface (RS485 HAT)
    
    def read_signals(self) -> InputSignals:
        """
        Read current state from CAN bus.
        
        If CAN is silent, returns all-false (let GPIO fallback take over).
        
        Returns:
            InputSignals with CAN message states
        """
        # TODO: Read pending CAN messages
        # TODO: Decode using config.CAN_MESSAGES
        # TODO: Check timeout (config.CAN_FALLBACK_TIMEOUT)
        # TODO: Return InputSignals or fallback
        
        return InputSignals()
    
    def start(self):
        """Start CAN message reader."""
        if self.is_running:
            return
        
        self.is_running = True
        # TODO: Start background CAN reading thread
        logger.info("CANInputReader started")
    
    def stop(self):
        """Stop CAN reader."""
        self.is_running = False
        logger.info("CANInputReader stopped")

class BluetoothInputReader(InputReader):
    """
    Read manual input from Bluetooth keyboard.
    
    Maps keyboard keys to camera selection:
      1 = Front camera
      2 = Left camera
      3 = Right camera
      4 = Rear camera
      0 = Auto (use GPIO/CAN)
    """
    
    def __init__(self):
        """Initialize Bluetooth reader."""
        self.is_running = False
        self.selected_camera = None
        logger.info("BluetoothInputReader created")
        # TODO: Import bluetooth module
        # TODO: Connect to BT keyboard
    
    def read_signals(self) -> InputSignals:
        """
        Read manual input from Bluetooth keyboard.
        
        Returns:
            InputSignals with manual_camera set if key pressed
        """
        # TODO: Poll bluetooth keyboard events
        # TODO: Map keypresses to camera selection
        # TODO: Return InputSignals
        
        return InputSignals()
    
    def start(self):
        """Start Bluetooth input reader."""
        if self.is_running:
            return
        
        self.is_running = True
        # TODO: Start background BT event reader
        logger.info("BluetoothInputReader started")
    
    def stop(self):
        """Stop Bluetooth reader."""
        self.is_running = False
        logger.info("BluetoothInputReader stopped")

# ============================================================================
# VIEW CONTROLLER
# ============================================================================

class ViewLogic:
    """
    Main view switching logic.
    
    Combines signals from GPIO, CAN, and Bluetooth to decide which
    camera(s) to display. Implements debouncing and fallback logic.
    
    Responsibilities:
      - Read inputs from multiple sources
      - Apply debouncing
      - Determine current view mode
      - Signal output pipeline what to display
      - Handle setup menu if needed
    """
    
    def __init__(self):
        """Initialize view logic."""
        self.current_view: ViewMode = ViewMode(DEFAULT_VIEW)
        self.previous_view: Optional[ViewMode] = None
        self.is_running = False
        
        # Input readers
        self.gpio_reader: Optional[GPIOInputReader] = None
        self.can_reader: Optional[CANInputReader] = None
        self.bt_reader: Optional[BluetoothInputReader] = None
        
        # Callbacks when view changes
        self.on_view_change_callbacks: List[Callable[[ViewMode], None]] = []
        
        logger.info("ViewLogic initialized")
    
    def register_on_view_change(self, callback: Callable[[ViewMode], None]):
        """
        Register callback to be called when view mode changes.
        
        Args:
            callback: Function that takes ViewMode as argument
        """
        self.on_view_change_callbacks.append(callback)
    
    def _determine_view_mode(self, signals: InputSignals) -> ViewMode:
        """
        Determine which view mode should be active based on input signals.
        
        Priority (highest to lowest):
          1. Manual Bluetooth input (driver override)
          2. Reverse signal (backup camera)
          3. Turn signal + indicator (turn signal priority)
          4. Default normal view
        
        Args:
            signals: Current input signals from all sources
        
        Returns:
            ViewMode that should be displayed
        """
        # TODO: Implement priority-based view selection
        # TODO: Apply debouncing logic
        
        return ViewMode.NORMAL
    
    def process_signals(self, signals: InputSignals) -> bool:
        """
        Process input signals and update view if needed.
        
        Args:
            signals: Current input signals
        
        Returns:
            True if view changed, False if same
        """
        new_view = self._determine_view_mode(signals)
        
        if new_view != self.current_view:
            logger.info(f"View changed: {self.current_view.value} -> {new_view.value}")
            self.previous_view = self.current_view
            self.current_view = new_view
            
            # Call registered callbacks
            for callback in self.on_view_change_callbacks:
                try:
                    callback(self.current_view)
                except Exception as e:
                    logger.error(f"Error in view change callback: {e}")
            
            return True
        
        return False
    
    def start(self):
        """Start view logic and input readers."""
        if self.is_running:
            logger.warning("ViewLogic already running")
            return
        
        self.is_running = True
        
        # Start input readers
        if self.gpio_reader:
            self.gpio_reader.start()
        if self.can_reader:
            self.can_reader.start()
        if self.bt_reader:
            self.bt_reader.start()
        
        logger.info("ViewLogic started")
    
    def stop(self):
        """Stop view logic and input readers."""
        if not self.is_running:
            return
        
        self.is_running = False
        
        # Stop input readers
        if self.gpio_reader:
            self.gpio_reader.stop()
        if self.can_reader:
            self.can_reader.stop()
        if self.bt_reader:
            self.bt_reader.stop()
        
        logger.info("ViewLogic stopped")
    
    def get_current_view(self) -> ViewMode:
        """Get the current view mode."""
        return self.current_view
    
    def set_manual_view(self, camera_id: Optional[int]):
        """
        Manually override view mode (from Bluetooth keyboard).
        
        Args:
            camera_id: Camera to display (None = auto)
        """
        # TODO: Create InputSignals with manual_camera set
        # TODO: Process and update view
        
        pass

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def debounce_signal(signal_history: List[bool], window_size: int = 3) -> bool:
    """
    Apply debouncing to a signal to reduce false triggers.
    
    Args:
        signal_history: Recent signal values (True/False)
        window_size: Majority voting window
    
    Returns:
        Debounced signal value
    """
    if not signal_history:
        return False
    
    # Simple majority voting
    true_count = sum(1 for s in signal_history[-window_size:] if s)
    return true_count >= (window_size // 2 + 1)

if __name__ == "__main__":
    # Test view logic
    logging.basicConfig(level=logging.INFO)
    
    logic = ViewLogic()
    
    def on_view_change(view: ViewMode):
        print(f"View changed: {view.value}")
    
    logic.register_on_view_change(on_view_change)
    logic.start()
    
    # Simulate signals
    for i in range(5):
        signals = InputSignals(
            left_indicator=(i >= 2),
            right_indicator=False,
        )
        logic.process_signals(signals)
    
    logic.stop()
