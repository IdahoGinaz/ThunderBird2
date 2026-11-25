# RTSP Streaming - Implementation & Troubleshooting

## Quick Start
```bash
# On Pi, app starts automatically:
python3 src/main.py

# On Windows/Mac, connect with VLC:
# File → Open Network Stream → rtsp://thunderbird2.local:8554/camera
```

Expected: Live camera feed at ~7 fps (Logitech C270 may be laggy)

## Architecture

### GStreamer Pipeline
```
appsrc (Python frame injection)
  ↓ [JPEG frames from camera_manager]
jpegdec (decode JPEG to raw video)
  ↓
videoscale (resize 1920x1080 → 1280x720 for Android head unit)
  ↓
videoconvert (ensure correct color format)
  ↓
x264enc (H.264 video encoding)
  ↓
rtph264pay (RTP packetization for RTSP)
  ↓
RTSP clients (VLC, Android head unit, etc.)
```

### Thread Model
- **Main loop**: Captures frames from USB cameras, routes to outputs
- **GLib loop**: Background daemon thread processing RTSP client requests
- **Camera threads**: Each camera has its own capture thread (OpenCV)

**Critical**: The GLib.MainLoop runs in a separate thread. Without it, RTSPServer.attach() doesn't work - client handshakes time out.

## Configuration

### In `src/config.py`
```python
RTSP_HOST = "0.0.0.0"           # Listen on all interfaces
RTSP_PORT = 8554                # Standard RTSP port
RTSP_PATH = "/camera"           # Stream URL path
RTSP_SUSPEND_MODE = "NONE"      # Keep encoding even with no clients
```

### In `src/output_manager.py` (RTSPOutput class)
```python
# Pipeline video resolution (cameras capture at this)
width=1920, height=1080

# Output resolution (scaled down for Android head unit)
width=1280, height=720

# H.264 encoding bitrate
bitrate=2000  # 2 Mbps (adjust for bandwidth)
```

## Testing

### From Windows/Mac
```bash
# VLC: File → Open Network Stream
rtsp://thunderbird2.local:8554/camera

# Or command line:
ffplay rtsp://thunderbird2.local:8554/camera
vlc rtsp://thunderbird2.local:8554/camera
```

### From Pi Terminal (gst-launch)
```bash
gst-launch-1.0 rtsp://thunderbird2.local:8554/camera ! autovideosink
```

### Check RTSP Port
```bash
# On Pi
netstat -tuln | grep 8554
# Expected: tcp 0 0 0.0.0.0:8554 0.0.0.0:* LISTEN
```

### Monitor Frames
```bash
# On Pi, in another terminal
tail -f /tmp/tb2.log | grep -E "Frame|sent|fps"
# Expected: Frame 100 sent (7.1 fps) - active_camera=0
```

## Troubleshooting

### "Unable to open MRL" in VLC
**Symptom**: VLC says "unable to open MRL 'rtsp://...'"

**Diagnosis**:
1. Check Pi is reachable: `ping thunderbird2.local`
2. Check RTSP port open: `ssh thunderbird2@thunderbird2.local "netstat -tuln | grep 8554"`
3. Check app running: `ssh thunderbird2@thunderbird2.local "ps aux | grep python"`
4. Check logs: `ssh thunderbird2@thunderbird2.local "tail /tmp/tb2.log"`

**Common causes**:
- App not running (see step 3 above)
- Firewall blocking port 8554 (check Pi firewall rules)
- Incorrect hostname/IP address
- GLib.MainLoop not running (logs show error)

### "Output 'rtsp' failed to send frame" (SOLVED)
**Previous Issue** (Session 7-8): Frames weren't being injected into RTSP pipeline.

**Root Cause**: appsrc element caps were malformed:
```bash
# BROKEN:
"appsrc ! image/jpeg,width=1920,height=1080 ! jpegdec"
#        ^ Invalid syntax - caps not properly specified

# FIXED:
"appsrc caps=\"image/jpeg,width=1920,height=1080\" ! jpegdec"
#       ^ Caps now a property of appsrc element
```

**Solution**: Update `src/output_manager.py` line 215 (committed in 436bfbd)

### Video Laggy or Stuttering
**Likely causes**:
1. **Logitech C270 latency** (~200ms typical)
   - Solution: Use Arducam 1080P instead (much faster)
   
2. **H.264 encoding CPU load** (15-20% per encode)
   - Solution: Reduce bitrate (`bitrate=1000` in config)
   - Solution: Use VP8 codec instead (but weaker compression)
   
3. **Network bandwidth**
   - Current: ~2 Mbps at 7 fps (1280x720 H.264)
   - Acceptable on LAN; may need optimization over long distances

**Monitor CPU**:
```bash
ssh thunderbird2@thunderbird2.local "top -b -n 1 | grep python"
# Expected: 20-30% CPU (x264enc + frame capture)
```

### No Video, But RTSP Connects
**Symptom**: VLC connects, shows duration, but no video frames

**Diagnosis**:
1. Check appsrc element exists: `grep "Captured appsrc" /tmp/tb2.log`
2. Check frames being sent: `tail /tmp/tb2.log | grep "Frame.*sent"`
3. Run gst-launch to test pipeline manually:
```bash
gst-launch-1.0 -v \
  filesrc location=test.jpg ! jpegdec ! \
  videoscale ! video/x-raw,width=1280,height=720 ! \
  videoconvert ! x264enc ! rtph264pay ! \
  rtpsink host=127.0.0.1 port=5000
```

**Common fixes**:
- Check camera is capturing: `ls -la /dev/video*`
- Check config.py camera resolution matches pipeline
- Enable GST_DEBUG for detailed logs:
```bash
GST_DEBUG=3 python3 src/main.py 2>&1 | tee /tmp/gst-debug.log
```

### Multiple RTSP Clients (Untested)
**Current Design**: Single shared appsrc element for all clients.

**Risk**: Multiple clients pushing to same appsrc may cause buffer conflicts.

**Testing Required**:
1. Open 2-3 VLC instances to same RTSP stream
2. Watch for latency/freezing in secondary clients
3. Check for errors in logs

**If issues occur**:
- Implement per-client appsrc elements in factory
- Or use GStreamer tee element to split pipeline

## Performance Targets

| Metric | Current | Target | Notes |
|--------|---------|--------|-------|
| FPS | 7.1 | 10+ | Limited by Logitech C270 |
| Latency | ~200ms | <100ms | H.264 encoding adds 50-100ms |
| CPU (Pi) | 25% | <30% | x264enc + frame capture |
| Bandwidth | 2 Mbps | 1-3 Mbps | Varies with motion/bitrate |
| Clients | 1 | 2+ | Untested with multiple clients |

## Future Improvements

### Codec Options
- **Current**: H.264 (good quality/compression, moderate CPU)
- **Alternative**: VP8 (better compression, more CPU)
- **Alternative**: MJPEG (less CPU, more bandwidth)

### Scaling
- Implement per-client pipelines for better isolation
- Add adaptive bitrate (lower when network congested)
- Pipeline state management (pause when no clients)

### Integration
- Add RTSP authentication (username/password)
- Support multiple camera feeds on different paths
- Add video recording to USB drive
- Integrate with Android head unit codec negotiation

## References
- GStreamer docs: https://gstreamer.freedesktop.org/
- RTSP spec: RFC 7826
- H.264 video codec: https://en.wikipedia.org/wiki/Advanced_Video_Coding
- Raspberry Pi GStreamer: https://www.raspberrypi.org/documentation/usage/video/
