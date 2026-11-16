# Project Name

One-line description.

> **Starting a new project from this template? Read "Using this template" below, then delete that section.**

## What it does
-

## Hardware
See [docs/hardware.md](docs/hardware.md) for parts list, pinout and wiring.

## Quick start
1. Copy `.env.example` to `.env` and fill in values.
2. Follow [docs/setup.md](docs/setup.md).

## Status
See [TODO.md](TODO.md).

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

---

## Using this template

### 1. Create the new project
**Option A: GitHub template repository (recommended).** One-time: on GitHub open this repo, Settings, tick **Template repository**. Then for each project click **Use this template**, Create a new repository (name it, e.g. `esp32-garden-sensor`; private is fine), then:
```
cd C:\Users\GGPC\OneDrive\Github
git clone https://github.com/<you>/<new-project>.git
```
A template gives you a fresh repo with clean history, nothing linked back to the template. Cloning the template directly would carry its history and remote.

**Option B: plain copy (no GitHub needed).**
```
cd C:\Users\GGPC\OneDrive\Github
Copy-Item project-template new-project -Recurse
cd new-project
Remove-Item .git -Recurse -Force   # only if a .git folder was copied
git init
```

### 2. Fill in before the first chat (10 minutes, worth it)
| File | What to fill in |
|------|-----------------|
| `README.md` | Name, one-liner; delete this "Using this template" section |
| `AGENTS.md` | The **Project** paragraph, the Hardware/Stack lines, and the Commands block |
| `docs/hardware.md` | Parts, voltages, pinout, devices/IPs. The more exact, the fewer wiring mistakes |
| `TODO.md` | The **Goal** (what "done" looks like) and the first few items under Now |
| `.env.example` | Add any new settings. Copy to `.env` for real values (gitignored) |

Delete what doesn't apply (e.g. `firmware/` for a Pi-only project, or `src/` for pure ESPHome).

### 3. Start the chat
Open the project folder in VS Code and say something like:
> Read AGENTS.md, TODO.md and docs/hardware.md. Today's goal is the first item in TODO "Now". Propose a short plan before coding.

### 4. While working
- Tell me when wiring or parts change, or paste serial/journal/ESPHome logs when something fails.
- I update `TODO.md`, `docs/hardware.md` and `docs/decisions.md` as we go; commit regularly.
- Never put WiFi passwords, MQTT credentials, HA tokens or LoRa keys in tracked files. Use `.env` or `secrets.yaml`.

### SSH keys (quick reminder)
```
ssh-keygen -t ed25519      # once per PC, accept defaults
# copy the public key to the target (Windows has no ssh-copy-id):
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh user@host "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys"
```
Then add a host alias in `~\.ssh\config` so you can just run `ssh mypi`. Ask me and I'll walk through it.
