#!/usr/bin/env python3
"""Test if context triggers the exception with nested f-strings."""
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
    if not errors:
        return False
    err = errors[0]
    if isinstance(err, dict):
        return err.get('message', '').startswith('Parse failed: ')
    return 'Parse failed' in str(err)

# The pattern that might be problematic - line 2652
# lines.append(f'    x-axis [{", ".join(f"{c}" for c in categories)}]')

print("Testing with context before line 2652...")

# Try adding context gradually
for context_lines in [100, 500, 1000, 2000, 2500, 2600, 2640, 2645, 2650, 2651]:
    code = ''.join(lines[:context_lines])
    # Add the problematic line
    code += '\n# Added line\nx = f\'test {", ".join(f"{c}" for c in cats)}\'\n'

    wmes, errors = try_parse(code)
    exception = is_exception(errors)
    status = "EXCEPTION" if exception else ("ERRORS" if errors else "OK")
    print(f"  {context_lines} lines + pattern: {status} (wmes={wmes})")

print("\n\nTest: Does removing the pattern at line 2652 fix the file?")
# Remove line 2652 and see if file parses
modified_lines = lines[:2651] + lines[2653:]
code = ''.join(modified_lines)
wmes, errors = try_parse(code)
exception = is_exception(errors)
status = "EXCEPTION" if exception else ("ERRORS" if errors else "OK")
print(f"  File without line 2652: {status} (wmes={wmes})")

print("\n\nTest: Simplify line 2652 to avoid nested f-string")
# Replace line 2652 with simpler version
simplified = lines[:2651] + ["        lines.append('    x-axis [' + ', '.join(str(c) for c in categories) + ']')\n"] + lines[2653:]
code = ''.join(simplified)
wmes, errors = try_parse(code)
exception = is_exception(errors)
status = "EXCEPTION" if exception else ("ERRORS" if errors else "OK")
print(f"  File with simplified line 2652: {status} (wmes={wmes})")
