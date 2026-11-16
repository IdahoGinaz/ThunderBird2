# AGENTS.md — instructions for AI coding assistants

Read this file, `README.md`, `TODO.md`, and `docs/hardware.md` before writing code.

## Project
We're building a robust, automotive‑grade dual‑camera controller on a Raspberry Pi that can switch, composite, and display camera feeds based on GPIO, CAN, or manual input — all running continuously under systemd.

Project to replace the physical sidemirrors of a Nissan Atlas 2017 with USB cameras that change view based on indicator behaviour.
Project must be able to detect the type and number of cameras connected and adapt the view as these may change.
This may mean a setup menu is required if there are changes to the default setup to select which camera is which and what view setup is required.
Start up must be quick and auto-restart on failure.
Output will be to an android based head unit that takes a video feed either by USB (it's DVR function) or RCA input. We should be able
to use a converter if needed to get the best resolution.
Once operating well will consider object detection in certain cameras.
Will need to consider how safe power down works.

Open to considering other options/platforms/approach to what I've already started with.


## Hardware & platform (source of truth: docs/hardware.md)
- Boards: Raspberry Pi 4.  Currently running BookWorm.
- RS485 CAN Hat
- Octocoupler (8 Channel)
- Sabrent 10 port USB HUb. Model HB-BU10
- Android Head Unit.   Android 13 "B200 - Core 8 - Rom 64GB - LPDDR4 - Ram 4GB - 1280X720 - ID7"
- 2007 Nissan Atlas (Truck)
- Sensors/radios: <!-- e.g. BME280 on I2C 0x76, SX1262 LoRa 915 MHz -->
- Dev machine: Windows + VS Code. Targets are deployed over SSH (key auth; I'm new to SSH keys, so explain key/config steps) or USB serial.  Raspberry Pi has a wifi connection to my home network that we can connect too.
- Bluetooth Mini Keyboard.
- 2 * USB Cameras (Arducam 1080P Low Light USB camera - "ID 0c45:0261 Microdia Arducam 1080P Low Light").  Keep in mind these may change.
- 1 * logitech 720p USB camera.
- 1 Bluetooth OBDII engine code reader.


## Stack & conventions
- Preferred tooling by purpose:
  - **ESP32 default: ESPHome** (YAML) when it covers the need and the device talks to Home Assistant/MQTT.
  - **PlatformIO (Arduino)** when ESPHome can't do it (custom protocols, LoRa firmware, tight timing). Say why you chose it.
  - **Python** on Pi/PC for glue, services and scripts. Other options welcome if justified.
- OS on the Pi varies per project; confirm it in `docs/hardware.md` before giving OS-specific commands.
- Pi code lives in `src/`, microcontroller code in `firmware/`, tests in `tests/`.
- Keep it simple and readable; hobby project, not enterprise. Prefer few dependencies.
- Pin and config values go in one config module/file, never scattered as magic numbers.
- Add short docstrings/comments only where non-obvious.

## Hard rules
1. **Never invent pin numbers, I2C addresses, or wiring.** Use `docs/hardware.md`; if missing, ask me.
2. **Voltage safety:** flag any 3.3V vs 5V mismatch, missing level shifters, or pin conflicts (boot-strapping pins, ADC2 + WiFi on ESP32, I2C/SPI overlays on Pi).
3. **Never commit secrets** (WiFi, MQTT, API tokens, HA long-lived tokens, LoRa keys). Use `.env` / `secrets.yaml` / `secrets.h` (all gitignored) and update the `*.example` file.
4. **Radio legality:** LoRa frequency, power and duty cycle must match my region (see below). Don't raise TX power without asking.
5. **Ask before** destructive actions: flashing firmware, changing `/boot/firmware/config.txt`, `rm -rf`, force-push, editing systemd units on a live device.
6. Don't add dependencies or restructure folders without saying why first.

## Region / radio
- Country: New Zealand. LoRa band: **NZ915 (915 MHz)**. Timezone: Pacific/Auckland.
- **If LoRa/radio links misbehave, check the region/frequency setting first** (wrong region preset on module, Meshtastic, ChirpStack or firmware) before debugging anything else.

## Workflow
- Small steps: plan briefly, implement, then tell me exactly how to test it (command, expected output).
- Run tests/linters yourself where possible (`pytest`, `ruff`, `pio test`, `esphome config`).
- Hardware can't be tested by you: give me a checklist for what to observe (LED, serial log, MQTT topic).
- After finishing a task: tick it in `TODO.md`, log non-obvious choices in `docs/decisions.md`, and update `docs/hardware.md` if wiring changed.

## Session start and end checks
**At the start of a session**, before coding, briefly tell me about:
- Unfilled `<!-- -->` placeholders or blank tables in `AGENTS.md`, `docs/hardware.md`, `TODO.md` and `README.md` that matter for the current task (ask me to fill them, or offer to).
- Open questions listed in `TODO.md`.
- Whether the "Using this template" section is still in `README.md`.

**At the end of a task or session**, remind me to:
- Review `TODO.md` (ticked items, new items, open questions).
- Check `docs/hardware.md` and `docs/setup.md` match what we actually built (wiring, pins, IPs, commands).
- Confirm `.env.example` lists any new settings, and that no secrets were added to tracked files.
- Note decisions worth keeping in `docs/decisions.md`.
- Commit the changes.

Keep these checks short: a few bullets, not a lecture.

## Commands
```
# setup:   <!-- python -m venv .venv ; .venv\Scripts\activate ; pip install -e . -->
# test:    <!-- pytest -->
# lint:    <!-- ruff check . -->
# deploy:  <!-- scripts/deploy.ps1 <host> -->
# monitor: <!-- pio device monitor / esphome logs x.yaml / ssh pi@host journalctl -fu <service> -->
```
