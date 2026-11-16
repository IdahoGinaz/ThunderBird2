# Decisions & lessons learned

Newest first. One or two lines each: what, why, date.

- 2026-11-17 — **Multi-output architecture**: RTSP (primary remote), RCA composite (fallback USB adapter), USB DVR (direct Android integration). Provides flexibility for different head unit firmware and fallback options.
- 2026-11-17 — **Auto-detect cameras with setup menu**: 2x Arducam 1080P + 1x Logitech 720p; menu activates if camera count/IDs change. Keeps system adaptable as cameras may be swapped.
- 2026-11-17 — **Dual input redundancy**: CAN bus (Nissan Atlas native) + GPIO (truck lights via octocoupler). CAN is primary; GPIO fallback if CAN unavailable. Improves reliability in real-world conditions.
- 2026-11-17 — **Config module pattern**: Centralize all hardware pinouts, vendor IDs, CAN settings in src/config.py (never scattered magic numbers). Makes maintenance easier and reduces wiring mistakes.
- 2026-11-17 — **Systemd service for auto-start**: Ensures Pi restarts services on crash and boots to live camera feed without manual intervention. Critical for automotive use.

