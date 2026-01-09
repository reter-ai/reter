#!/usr/bin/env python3
"""Narrow down what in 2500-2600 triggers the exception."""
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
    reasoner = Reter()
    try:
        wme_count, errors = reasoner.load_python_code(code, "test.py")
        return wme_count, errors
    except Exception as e:
        return -1, [str(e)]

def is_exception(errors):
    if not errors:
        return False
    err = errors[0]
    if isinstance(err, dict):
        return err.get('message', '').startswith('Parse failed: ')
    return 'Parse failed' in str(err)

# Add the problematic line to different contexts
pattern_line = 'x = f\'test {", ".join(f"{c}" for c in cats)}\'\n'

print("Binary search to find minimum context that causes exception with pattern...")

low = 2500
high = 2600

while low < high:
    mid = (low + high) // 2
    code = ''.join(lines[:mid]) + pattern_line
    wmes, errors = try_parse(code)
    exception = is_exception(errors)

    if exception:
        high = mid
        print(f"  Lines 1-{mid} + pattern: EXCEPTION")
    else:
        low = mid + 1
        print(f"  Lines 1-{mid} + pattern: OK/ERRORS (wmes={wmes})")

print(f"\nMinimum context for exception: {low} lines")

# Check what's special about lines around this point
print(f"\n--- Content around line {low} ---")
for i in range(max(0, low-10), min(len(lines), low+5)):
    line = lines[i].rstrip()
    # Highlight f-strings
    marker = " <<< f-string" if "f'" in line or 'f"' in line else ""
    print(f"{i+1:4d}: {line[:75]}{marker}")
