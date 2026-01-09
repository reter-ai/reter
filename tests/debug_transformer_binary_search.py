#!/usr/bin/env python3
"""Binary search to find where transformer.py fails to parse."""
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

print(f"Total lines: {len(lines)}")
print(f"Total chars: {sum(len(l) for l in lines)}")

def try_parse(code, label):
    """Try to parse code and return (wme_count, errors)."""
    reasoner = Reter()
    try:
        wme_count, errors = reasoner.load_python_code(code, "test.py")
        return wme_count, errors
    except Exception as e:
        return -1, [str(e)]

# Binary search for problematic section
def find_failing_range(lines):
    """Binary search to find the first line range that fails."""
    total = len(lines)

    # Test in chunks of 100 lines
    print("\n--- Testing chunks of 100 lines ---")
    for start in range(0, total, 100):
        end = min(start + 100, total)
        code = ''.join(lines[start:end])
        wmes, errors = try_parse(code, f"lines {start+1}-{end}")
        status = "FAIL" if wmes == 0 or errors else "OK"
        if wmes == 0 or errors:
            err_msg = str(errors[0]) if errors else "no errors"
            print(f"  Lines {start+1:4d}-{end:4d}: {status} (wmes={wmes}, error={err_msg[:50]})")
        else:
            print(f"  Lines {start+1:4d}-{end:4d}: OK ({wmes} wmes)")

    # Now test cumulative
    print("\n--- Testing cumulative from start ---")
    for end in [100, 200, 300, 500, 1000, 1500, 2000, 2500, 3000, 3500, total]:
        if end > total:
            end = total
        code = ''.join(lines[:end])
        wmes, errors = try_parse(code, f"first {end} lines")
        status = "FAIL" if wmes == 0 or errors else "OK"
        if wmes == 0 or errors:
            err_msg = errors[0] if errors else "no errors"
            print(f"  First {end:4d} lines: {status} (wmes={wmes}, error={str(err_msg)[:60]})")
        else:
            print(f"  First {end:4d} lines: OK ({wmes} wmes)")
        if end == total:
            break

find_failing_range(lines)

# Also test the full file again
print("\n--- Full file test ---")
code = ''.join(lines)
wmes, errors = try_parse(code, "full file")
print(f"Full file: wmes={wmes}, errors={errors}")
