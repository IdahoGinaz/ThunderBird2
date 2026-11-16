# AGENTS.md — instructions for AI coding assistants

Read this file, `README.md`, `TODO.md`, and `docs/hardware.md` before writing code.

## Project
<!-- One paragraph: what it does, what problem it solves. -->

## Hardware & platform (source of truth: docs/hardware.md)
- Boards: <!-- e.g. Raspberry Pi Zero 2 W (OS varies per project), ESP32-S3 -->
- Sensors/radios: <!-- e.g. BME280 on I2C 0x76, SX1262 LoRa 915 MHz -->
- Integrations: <!-- which of the PeterLab services below this touches -->
- Dev machine: Windows + VS Code. Targets are deployed over SSH (key auth; I'm new to SSH keys, so explain key/config steps) or USB serial.

## Bigger picture: PeterLab
This project may be a node in my homelab (repo: `..\PeterLab`; see its `docs/architecture.md`, `docs/principles.md`). Defaults unless the project says otherwise:
- **MQTT is the telemetry backbone.** Publish sensor data to MQTT; use Home Assistant MQTT discovery where sensible.
- **Home Assistant owns automation. OpenTAK (local server) owns situational awareness.** Don't duplicate those roles in device code.
- Other planned services: Node-RED, Meshtastic, ChirpStack, InfluxDB/Grafana. Remote access via Tailscale only; no public port forwarding.
- Principles: simplicity over cleverness, open standards, low power, document decisions, one new major service at a time.
- TAK data format (CoT) is undecided; keep options open and ask before committing to one.

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
- Update `PeterLab` docs if this project adds a service, device, MQTT topic or network change there.

Keep these checks short: a few bullets, not a lecture.

## Commands
```
# setup:   <!-- python -m venv .venv ; .venv\Scripts\activate ; pip install -e . -->
# test:    <!-- pytest -->
# lint:    <!-- ruff check . -->
# deploy:  <!-- scripts/deploy.ps1 <host> -->
# monitor: <!-- pio device monitor / esphome logs x.yaml / ssh pi@host journalctl -fu <service> -->
```
