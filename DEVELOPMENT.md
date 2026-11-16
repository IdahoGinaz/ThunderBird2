# Development Workflow Guide

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

# 4. Push to Pi
git push origin main
```

### Test on Pi:
```powershell
# Quick test
ssh thunderbird2@thunderbird2.local "cd ~/src && python3 main.py --test"

# Run with timeout
ssh thunderbird2@thunderbird2.local "cd ~/src && timeout 10 python3 main.py"
```

## Safety Features Now In Place

✅ **Git line endings** - Configured to `core.autocrlf=input` (prevents CRLF/LF mixing)  
✅ **Pre-commit hook** - Runs Python syntax check before each commit  
✅ **Validation script** - Full syntax check + self-tests  
✅ **Linting tools** - black, pylint, pytest installed  

## Why These Matter

| Issue | Prevention |
|-------|-----------|
| File corruption on SCP | Validation catches before push |
| Encoding errors | Git config prevents line-ending issues |
| Silent breakage | Pre-commit hook catches syntax errors |
| Pushing broken code | Tests run locally first |

## Future Improvements

**Recommended (not yet done):**
- VS Code Remote-SSH for direct Pi editing (eliminates SCP entirely)
- GitHub Actions CI/CD (auto-test on push)
- Automated deployment to Pi systemd service

## Troubleshooting

If pre-commit hook isn't triggering:
```powershell
# Make hook executable
git config core.hooksPath .git/hooks

# Or manually run validation
.\scripts\validate.ps1
```

If encoding issues persist:
```powershell
# Normalize all Python files to UTF-8 LF
git add .
git commit --amend --no-edit
```
