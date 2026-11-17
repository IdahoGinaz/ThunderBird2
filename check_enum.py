#!/usr/bin/env python3
"""Check RTSPSuspendMode enum values."""

import gi
gi.require_version("GstRtspServer", "1.0")
from gi.repository import GstRtspServer

print("RTSPSuspendMode values:")
print([x for x in dir(GstRtspServer.RTSPSuspendMode) if not x.startswith('_')])
