# Project Name
ThunderBird2

## What it does
Project to replace the physical sidemirrors of a Nissan Atlas 2017 with USB cameras that change view based on indicator behaviour.

## Hardware
See [docs/hardware.md](docs/hardware.md) for parts list, pinout and wiring.

## Quick start
1. Copy `.env.example` to `.env` and fill in values.
2. Follow [docs/setup.md](docs/setup.md).

## Status
✅ **Phase 2 - Core Implementation (RTSP Complete)**
- Live camera to RTSP streaming working (rtsp://thunderbird2.local:8554/camera)
- Keyboard input ready (manual testing on Pi)
- Next: GPIO/CAN input readers, automatic view switching

See [TODO.md](TODO.md) for detailed task list.

## Layout
```
AGENTS.md   Rules and context for the AI assistant (read first by Copilot)
TODO.md     Goal and task list
src/        Python code for Pi / PC
firmware/   ESP32 / microcontroller code (ESPHome, PlatformIO, MicroPython)
tests/      Automated tests
docs/       Hardware, setup, decisions
scripts/    Deploy / install helpers
```
