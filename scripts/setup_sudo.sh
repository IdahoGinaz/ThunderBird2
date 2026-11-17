#!/bin/bash
# Configure passwordless sudo for thunderbird2 user
echo "thunderbird2 ALL=(ALL) NOPASSWD: ALL" | sudo -S tee /etc/sudoers.d/thunderbird2
chmod 0440 /etc/sudoers.d/thunderbird2
echo "✓ Passwordless sudo configured for thunderbird2 user"
