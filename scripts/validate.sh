#!/bin/bash
# Validation script - runs before commits/pushes

set -e  # Exit on first error

echo "=== Python Syntax Check ==="
for file in src/*.py; do
    printf "  %-30s " "$file"
    if python3 -m py_compile "$file" 2>/dev/null; then
        echo "✓"
    else
        echo "✗ FAILED"
        exit 1
    fi
done

echo ""
echo "=== Running Self-Tests ==="
cd "$(dirname "$0")/.."
python3 src/main.py --test

echo ""
echo "✓ All validations passed!"
