#!/usr/bin/env python3
"""Quick test for GStreamer availability."""

try:
    import gi
    gi.require_version("Gst", "1.0")
    gi.require_version("GstRtspServer", "1.0")
    from gi.repository import Gst, GstRtspServer
    
    if not Gst.is_initialized():
        Gst.init(None)
    
    print("SUCCESS: GStreamer and GStreamer RTSP Server available")
    print(f"GStreamer version: {'.'.join(map(str, Gst.version()))}")
    
except ImportError as e:
    print(f"ERROR: GStreamer not available: {e}")
    print("Install with: sudo apt-get install python3-gi gir1.2-gstreamer-1.0 gir1.2-gst-rtsp-server-1.0")
    exit(1)
except Exception as e:
    print(f"ERROR: {e}")
    exit(1)
