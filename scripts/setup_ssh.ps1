# setup_ssh.ps1 - Set up SSH key access to Raspberry Pi
# PowerShell 5.1 compatible version

param(
    [string]$RPiIP = "192.168.178.103",
    [string]$RPiUser = "wolfpack"
)

$ErrorActionPreference = "Stop"

Write-Host "===== ThunderBird2 SSH Key Setup =====" -ForegroundColor Cyan
Write-Host ""

# Get public key
$pubKey = Get-Content "$env:USERPROFILE\.ssh\id_ed25519.pub"
Write-Host "Your public key:" -ForegroundColor Yellow
Write-Host $pubKey
Write-Host ""

# Build the connection string
$connection = $RPiUser + "@" + $RPiIP

Write-Host "Connecting to $connection..." -ForegroundColor Yellow
Write-Host ""

try {
    # Create .ssh directory and add key (using semicolon separators for PowerShell 5.1)
    $setupCmd = "mkdir -p ~/.ssh; chmod 700 ~/.ssh; echo '$pubKey' >> ~/.ssh/authorized_keys; chmod 600 ~/.ssh/authorized_keys; echo 'SSH key added!'"
    
    & ssh $connection $setupCmd
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "SUCCESS: Public key added to RPi!" -ForegroundColor Green
    } else {
        Write-Host "ERROR: Failed to add key (exit code: $LASTEXITCODE)" -ForegroundColor Red
        exit 1
    }
    
} catch {
    Write-Host "ERROR: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Manual step: SSH into the Pi and add this line to ~/.ssh/authorized_keys" -ForegroundColor Yellow
    Write-Host "  ssh $connection"
    Write-Host "  mkdir -p ~/.ssh"
    Write-Host "  nano ~/.ssh/authorized_keys"
    Write-Host ""
    Write-Host "Then paste: $pubKey" -ForegroundColor Cyan
    exit 1
}

Write-Host ""
Write-Host "Testing SSH connection..." -ForegroundColor Yellow

try {
    & ssh $connection "uname -a"
    Write-Host ""
    Write-Host "SUCCESS: SSH key authentication works!" -ForegroundColor Green
    
} catch {
    Write-Host "ERROR: SSH connection test failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Optional: Add to ~/.ssh/config for easier access:" -ForegroundColor Cyan
Write-Host ""
Write-Host "Host thunderbird2"
Write-Host "  HostName $RPiIP"
Write-Host "  User $RPiUser"
Write-Host "  IdentityFile ~/.ssh/id_ed25519"
Write-Host ""
Write-Host "Then use: ssh thunderbird2" -ForegroundColor Green
