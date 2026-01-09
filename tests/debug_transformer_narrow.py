#!/usr/bin/env python3
"""Narrow down exact line where exception occurs (2500-3000)."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from reter import Reter

transformer_path = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "codeine", "src", "codeine", "cadsl", "transformer.py"
)

with open(transformer_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

def try_parse(code):
    """Try to parse code and return (wme_count, errors)."""
    reasoner = Reter()
    try:
        wme_count, errors = reasoner.load_python_code(code, "test.py")
        return wme_count, errors
    except Exception as e:
        return -1, [str(e)]

def is_exception(errors):
    """Check if the error is a C++ exception (not just syntax errors)."""
    if not errors:
        return False
    err = errors[0]
    if isinstance(err, dict):
        return err.get('message', '').startswith('Parse failed: ')
    return 'Parse failed' in str(err)

# Binary search between 2500 and 3000
print("Binary search between 2500-3000 lines...")

low = 2500
high = 3000

while low < high:
    mid = (low + high) // 2
    code = ''.join(lines[:mid])
    wmes, errors = try_parse(code)
    exception = is_exception(errors)

    print(f"  Lines 1-{mid}: wmes={wmes}, exception={exception}")

    if exception:
        high = mid
    else:
        low = mid + 1

print(f"\nFirst exception at line: {low}")

# Now test the exact line range
print(f"\nTesting individual lines around {low}...")
for end in range(low - 10, low + 10):
    if end < 2500 or end > 3100:
        continue
    code = ''.join(lines[:end])
    wmes, errors = try_parse(code)
    exception = is_exception(errors)
    status = "EXCEPTION" if exception else ("SYNTAX ERR" if errors else "OK")
    print(f"  Lines 1-{end}: {status} (wmes={wmes})")

# Print the content around the problem area
print(f"\n--- Content around line {low} ---")
for i in range(max(0, low-15), min(len(lines), low+5)):
    print(f"{i+1:4d}: {lines[i].rstrip()[:80]}")
