# Development Workflow Guide

## ✅ Deployment Now Uses Direct Git Pull

As of this session, **git is installed on the Pi** and the home directory is a full git repository tracking GitHub. This replaces manual SCP transfers.

### New Deployment Workflow (Recommended):

```powershell
# 1. Make changes locally
# 2. Run validation
.\scripts\validate.ps1 -Test

# 3. If validation passes, commit and push
git add .
git commit -m "..."
git push origin main

# 4. Deploy to Pi (SSH into Pi)
ssh thunderbird2@thunderbird2.local

# On Pi, pull latest changes
cd ~
git pull origin main
python3 src/main.py
```

Or as a one-liner from local PC:
```powershell
# After pushing, deploy directly
ssh thunderbird2@thunderbird2.local "cd ~ && git pull origin main && python3 src/main.py"
```

### Legacy SCP Workflow (Still Works):

If you need to quickly test without committing:
```powershell
# Copy single file without committing
scp src\view_logic.py thunderbird2@thunderbird2.local:~/src/view_logic.py
```

## Quick Commands

### Before every commit/push:
```powershell
# Validate all Python files locally
.\scripts\validate.ps1

# Or with self-tests
.\scripts\validate.ps1 -Test
```

### Local development workflow:
```powershell
# 1. Make changes locally
# 2. Run validation
.\scripts\validate.ps1 -Test

# 3. If validation passes, commit
git add .
git commit -m "..."

# 4. Push to GitHub
git push origin main

# 5. Deploy to Pi
ssh thunderbird2@thunderbird2.local "cd ~ && git pull origin main"
```

### Test on Pi:
```powershell
# Quick test with timeout
ssh thunderbird2@thunderbird2.local "cd ~ && timeout 10 python3 src/main.py"

# Check git status on Pi
ssh thunderbird2@thunderbird2.local "cd ~ && git status && git log --oneline -5"
```

## Safety Features Now In Place

✅ **Git on Pi** - Full repository sync, versioning, and rollback capability  
✅ **Git line endings** - Configured to `core.autocrlf=input` (prevents CRLF/LF mixing)  
✅ **Pre-commit hook** - Runs Python syntax check before each commit  
✅ **Validation script** - Full syntax check + self-tests  
✅ **Linting tools** - black, pylint, pytest installed  

## Why These Matter

| Issue | Prevention |
|-------|-----------|
| Lost work / no version history | Git on Pi tracks all versions |
| Wrong code deployed | `git pull` pulls exactly what was pushed |
| Encoding errors | Git config prevents line-ending issues |
| Silent breakage | Pre-commit hook catches syntax errors |
| Pushing broken code | Tests run locally first |

## Pi Repository Setup

The Pi home directory is now a full git repository:
- **Remote**: `https://github.com/IdahoGinaz/ThunderBird2.git`
- **Branch**: `main` (tracking `origin/main`)
- **Last commit**: Available via `git log --oneline`

To verify on Pi:
```bash
cd ~
git status
git log --oneline -5
git remote -v
```

## Rollback / Revert on Pi

If a deployment breaks:
```bash
# See what changed
git log --oneline -10

# Revert to previous commit
git reset --hard HEAD~1

# Or revert to specific commit
git reset --hard <commit-hash>

# Then restart
python3 src/main.py
```

## Future Improvements

**Recommended (not yet done):**
- Automated deployment via systemd service (auto-restart on boot)
- GitHub Actions CI/CD (auto-test on push, deploy on success)
- VS Code Remote-SSH for direct Pi editing (eliminates SCP/manual sync entirely)

## Troubleshooting

### Git pull fails with authentication errors:
```bash
# If HTTPS auth fails, use SSH keys instead
# Pi should already have SSH keys set up for GitHub
# See SSH_SETUP.md for details
```

### Pre-commit hook not triggering locally:
```powershell
# Make hook executable
git config core.hooksPath .git/hooks

# Or manually run validation
.\scripts\validate.ps1
```

### Need to sync Pi with GitHub without changing code:
```bash
# On Pi
git fetch origin
git diff main origin/main  # see what would change
git pull origin main       # apply changes
```

