# ThunderBird2 Deployment Guide

## Quick Start

### Deploying from Local PC to Pi

```powershell
# 1. Make changes locally
# 2. Test locally with validation
.\scripts\validate.ps1 -Test

# 3. Commit and push
git add .
git commit -m "Your message"
git push origin main

# 4. Deploy to Pi (single command)
ssh thunderbird2@thunderbird2.local "cd ~ && git pull origin main && python3 src/main.py"
```

## SSH Connection Details

| Setting | Value |
|---------|-------|
| **Hostname** | `thunderbird2.local` or `192.168.178.103` |
| **Username** | `thunderbird2` |
| **Port** | 22 (default SSH) |
| **Auth** | SSH key-based (configured locally) |

## Common Deployment Tasks

### Deploy New Version
```bash
ssh thunderbird2@thunderbird2.local "cd ~ && git pull origin main"
```

### Start Application
```bash
ssh thunderbird2@thunderbird2.local "cd ~ && python3 src/main.py"
```

### Deploy + Start (One Command)
```bash
ssh thunderbird2@thunderbird2.local "cd ~ && git pull origin main && python3 src/main.py"
```

### Check What Version is Running
```bash
ssh thunderbird2@thunderbird2.local "cd ~ && git log --oneline -1"
```

### Check Git Status on Pi
```bash
ssh thunderbird2@thunderbird2.local "cd ~ && git status"
```

## Emergency / Rollback Procedures

### Stop Running Application
```bash
ssh thunderbird2@thunderbird2.local "pkill -f 'python3.*main.py'"
```

### Revert to Previous Version
```bash
ssh thunderbird2@thunderbird2.local "cd ~ && git reset --hard HEAD~1 && python3 src/main.py"
```

### Revert to Specific Commit
```bash
# First, see recent commits
ssh thunderbird2@thunderbird2.local "cd ~ && git log --oneline -10"

# Then revert to specific commit (replace <commit-hash>)
ssh thunderbird2@thunderbird2.local "cd ~ && git reset --hard <commit-hash> && python3 src/main.py"
```

### View Changes Between Versions
```bash
ssh thunderbird2@thunderbird2.local "cd ~ && git diff HEAD~1 HEAD"
```

## Troubleshooting

### "Could not resolve host: thunderbird2.local"
- Ensure Pi is on the same network
- Use IP instead: `192.168.178.103`
- Check if mDNS is working

### SSH Key Issues
- Verify key is in `~/.ssh/authorized_keys` on Pi
- Check permissions: `ssh thunderbird2@thunderbird2.local "ls -la ~/.ssh/"`

### Git Pull Fails
- Check network connection: `ssh thunderbird2@thunderbird2.local "ping -c 1 github.com"`
- Check git config: `ssh thunderbird2@thunderbird2.local "cd ~ && git remote -v"`
- Verify branch: `ssh thunderbird2@thunderbird2.local "cd ~ && git branch"`

### Application Crashes
- Check logs: `ssh thunderbird2@thunderbird2.local "tail -50 ~/logs/tb2.log"`
- Verify cameras connected: `ssh thunderbird2@thunderbird2.local "ls -la /dev/video*"`
- Check dependencies: `ssh thunderbird2@thunderbird2.local "python3 -c 'import gi'"`

## Repository Structure on Pi

```
/home/thunderbird2/
├── .git/                    # Git repository
├── src/
│   ├── main.py             # Main application
│   ├── view_logic.py       # Keyboard/input handling
│   ├── output_manager.py   # RTSP/RCA/USB output
│   ├── camera_manager.py   # USB camera capture
│   └── config.py           # Configuration
├── docs/                    # Documentation
├── logs/                    # Application logs
└── DEVELOPMENT.md           # Development guide
```

## Automation Ideas (Not Yet Implemented)

### Systemd Service (Auto-Start on Boot)
```ini
[Unit]
Description=ThunderBird2 Camera Application
After=network.target

[Service]
Type=simple
User=thunderbird2
WorkingDirectory=/home/thunderbird2
ExecStart=/usr/bin/python3 /home/thunderbird2/src/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### GitHub Actions Auto-Deployment
Example workflow to auto-deploy on main branch push (requires setup):
```yaml
name: Deploy to Pi
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy to Pi
        run: |
          ssh -i ${{secrets.PI_SSH_KEY}} thunderbird2@thunderbird2.local \
            "cd ~ && git pull origin main && python3 src/main.py"
```

## Keyboard Controls (Local Terminal)

When running on the Pi locally (with keyboard):

```
1       : Switch to Camera 1
2       : Switch to Camera 2  
3       : Switch to Camera 3
r       : Reverse mode (back camera)
l       : Left turn signal
k       : Right turn signal (k = riGht)
n       : Normal view
q       : Quit application
```

**Note**: Keys register immediately without pressing Enter (thanks to raw mode + fcntl O_NONBLOCK)

## Performance Monitoring

### Check Frame Rate
```bash
ssh thunderbird2@thunderbird2.local "tail -20 ~/logs/tb2.log | grep 'fps'"
```

### Monitor Resource Usage
```bash
ssh thunderbird2@thunderbird2.local "top -b -n 1 -p \$(pgrep -f 'python3.*main.py')"
```

### Check CPU/Memory
```bash
ssh thunderbird2@thunderbird2.local "free -h && df -h"
```

## Network Details

### RTSP Stream URL
```
rtsp://thunderbird2.local:8554/camera
or
rtsp://192.168.178.103:8554/camera
```

### Connect with VLC
1. Open VLC
2. Go to Media → Open Network Stream
3. Enter URL: `rtsp://thunderbird2.local:8554/camera`
4. Click Play

## Development Workflow

1. **Local Development** → Make changes on PC
2. **Local Testing** → Run `.\scripts\validate.ps1 -Test`
3. **Commit** → `git add .` → `git commit -m "..."`
4. **Push** → `git push origin main`
5. **Deploy** → `ssh ... "git pull && python3 src/main.py"`
6. **Verify** → Test camera feed in VLC, check frame rate

## Git Basics for This Project

```bash
# Check current version on Pi
git log --oneline -1

# See what changed in last deployment
git diff HEAD~1 HEAD

# List all commits available
git log --oneline -20

# See all branches
git branch -a

# See remote status
git remote -v
```

## Support / Documentation

- **Hardware Setup**: See `docs/hardware.md`
- **Development Guide**: See `DEVELOPMENT.md`
- **Configuration**: See `src/config.py`
- **Git on Pi**: Run `git help <command>` on Pi
