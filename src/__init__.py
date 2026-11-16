"""
ThunderBird2 - Camera Controller for Nissan Atlas

Raspberry Pi-based dual-camera controller that switches between side-mirror
camera views based on turn signals, with video output to Android head unit
via USB DVR, RCA composite, and RTSP.
"""

__version__ = "0.1.0"
__author__ = "Copilot"

from . import config

__all__ = ["config"]
