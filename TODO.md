# TODO

## Goal (definition of done)
Raspberry Pi continuously captures from 3 USB cameras, switches views based on truck turn signals (GPIO + CAN), outputs video to Android head unit via USB DVR + RCA composite + RTSP. Auto-detects camera changes and prompts setup menu. Auto-starts and restart-on-failure via systemd.

## Now — Phase 1: Foundation
- [x] SSH key setup and Pi connectivity (manual method documented)
- [x] Fill hardware documentation (pinout, power, network devices)
- [x] Create config.py with centralized constants
- [x] Camera detection script (enumerate /dev/video*, capabilities)
- [x] Architecture stubs (camera_manager, view_logic, output_manager)

**Status**: Phase 1 complete! All foundation modules created and tested.

## Development Setup ✓
- [x] Git line ending normalization (core.autocrlf=input)
- [x] Pre-commit hook for syntax validation
- [x] Validation script with self-tests
- [x] Development workflow guide (DEVELOPMENT.md)
- [x] Linting tools installed (black, pylint, pytest)

**Before each session:** Run `.\scripts\validate.ps1 -Test` to catch errors early

## Now — Phase 2: Core implementation (continued)
- [x] Install OpenCV and camera dependencies on Pi
- [x] Fix camera_detection.py glob issue (was using shell=True)
- [x] Implement camera_manager.py with real OpenCV capture loop
  - [x] Multi-threaded frame capture from USB cameras
  - [x] Frame queue with JPEG encoding
  - [x] Resolution and FPS configuration
  - [x] Graceful startup/shutdown
  - [x] All 3 cameras tested and capturing (2x Arducam 1080P + 1x Logitech C270)
- [x] Fix syntax errors and import mismatches in core modules
  - [x] Fixed output_manager.py file corruption
  - [x] Updated main.py to use ViewLogicEngine (was importing ViewLogic)
  - [x] Added callback support to ViewLogicEngine (register_on_view_change)
  - [x] Application now starts successfully and runs event loop
- [ ] **Implement keyboard input reader (POC)**
  - [ ] Non-blocking keyboard input using `select` module
  - [ ] Keys: 1/2/3 for cameras, R for reverse, L/R for indicators, Q to quit
  - [ ] Test view switching with real camera output
- [ ] **Implement actual frame capture-to-output pipeline**
  - [ ] Pull frames from camera_manager queue in main loop
  - [ ] Route frames to selected output via output_manager
  - [ ] Test video appears on RTSP stream and RCA output
- [ ] Implement GPIO input reader (RPi.GPIO or gpiozero)
- [ ] Implement CAN input reader (python-can for Nissan Atlas)
- [ ] Implement view switching logic (priority: manual > reverse > turn > normal)
- [ ] Implement three-output encoding pipeline (RTSP + RCA + USB DVR)
- [ ] Implement actual frame capture-to-output pipeline
- [ ] Setup menu for camera configuration changes

## Phase 3: Polish
- [ ] Systemd service template (auto-start, restart on failure)
- [ ] Safe shutdown handler (graceful cleanup)
- [ ] Performance optimization (frame buffering, CPU pinning)
- [ ] Logging and diagnostics dashboard
- [ ] Object detection (future)

## Ideas / maybe
- [ ] Dashboard options for other information from OBDII sensor.
- [ ] Web UI for settings / camera test
- [ ] Home Assistant / MQTT integration

## Done
- [x] Project created from template
- [x] Architecture planned and documented
- [x] Config module created
- [x] Camera detection script created
- [x] Camera manager stub created
- [x] View logic stub created
- [x] Output manager stub created
- [x] Main application entry point created
- [x] All self-tests passing

## Known issues / open questions
- **Octocoupler GPIO mapping**: Not yet wired — waiting for pinout diagram (8 channels: left indicator, right indicator, reverse, brake, 4 spares)
- **CAN bus configuration**: Nissan Atlas 2007 CAN IDs TBD — need service manual or forum post
- **Android head unit video codec**: Need to confirm supported codecs (H.264, MJPEG, etc.) and USB DVR mode behavior
- **V4L2loopback or UVC gadget**: Check if Pi supports USB video device mode without additional software
- **Bluetooth keyboard pairing**: Need to test BT keyboard discovery and key mapping
