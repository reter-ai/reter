#!/usr/bin/env python3
"""Debug script to understand why transformer.py fails to parse."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from reter import Reter

transformer_path = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "codeine", "src", "codeine", "cadsl", "transformer.py"
)

print(f"Parsing: {transformer_path}")
print(f"File exists: {os.path.exists(transformer_path)}")

# Get file size and line count
with open(transformer_path, 'r', encoding='utf-8') as f:
    content = f.read()
print(f"File size: {len(content)} bytes")
print(f"Line count: {len(content.splitlines())}")

# Try parsing
reasoner = Reter()
wme_count, errors = reasoner.load_python_file(transformer_path)

print(f"\nResult:")
print(f"  WME count: {wme_count}")
print(f"  Errors: {len(errors)}")

if errors:
    print("\nFirst 20 errors:")
    for i, err in enumerate(errors[:20]):
        print(f"  Error {i}: {err}")

# Try parsing simple code to verify the parser works
print("\n\nTesting simple code:")
simple_code = '''
class First:
    def method_a(self):
        pass

class Second:
    def method_b(self):
        pass
'''

reasoner2 = Reter()
wme_count2, errors2 = reasoner2.load_python_code(simple_code, "simple.py")
print(f"  Simple code WMEs: {wme_count2}")
print(f"  Simple code errors: {len(errors2)}")
