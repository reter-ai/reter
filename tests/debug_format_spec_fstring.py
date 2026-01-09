#!/usr/bin/env python3
"""Test format specification f-strings and their interaction with nested f-strings."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from reter import Reter

def try_parse(code, label):
    reasoner = Reter()
    try:
        wme_count, errors = reasoner.load_python_code(code, "test.py")
        is_exc = errors and errors[0].get('message', '').startswith('Parse failed')
        status = "EXCEPTION" if is_exc else ("ERRORS" if errors else "OK")
        print(f"  {label}: {status} (wmes={wme_count})")
        return wme_count, errors
    except Exception as e:
        print(f"  {label}: Python exception: {e}")
        return -1, [str(e)]

print("Test 1: Format specification f-strings alone")
# Format spec with variable width
try_parse("x = f'{value:<{width}}'", 'Variable width format')
try_parse("x = f' {h:<{w}} '", 'Padded variable width')
try_parse("x = '|'.join(f' {h:<{w}} ' for h, w in items)", 'In generator')

print("\nTest 2: Nested f-strings alone")
try_parse('x = f"{f\\"{c}\\"}"', 'Nested f-string')
try_parse('x = f\'test {", ".join(f"{c}" for c in cats)}\'', 'Nested in join')

print("\nTest 3: Format spec first, then nested f-string")
code = """
# Format spec f-string
x = f'{value:<{width}}'
# Nested f-string
y = f'{", ".join(f"{c}" for c in cats)}'
"""
try_parse(code, 'Format spec then nested')

print("\nTest 4: Larger context with format spec, then nested")
code = """
class Test:
    def method(self):
        # Format spec f-string
        x = f'{value:<{width}}'
        y = f' {h:<{w}} '
        z = '|'.join(f' {h:<{w}} ' for h, w in items)
        # Now nested f-string
        result = f'{", ".join(f"{c}" for c in cats)}'
"""
try_parse(code, 'Class with format spec and nested')

print("\nTest 5: Simulate transformer.py pattern")
code = """
class RenderTable:
    def _render_ascii(self):
        headers = ['a', 'b']
        widths = [10, 20]
        lines = []
        # Line 2566 pattern
        lines.append('|' + '|'.join(f' {h:<{w}} ' for h, w in zip(headers, widths)) + '|')
        # Line 2652 pattern
        categories = ['x', 'y']
        lines.append(f'    x-axis [{", ".join(f"{c}" for c in categories)}]')
"""
try_parse(code, 'Simulated transformer pattern')

print("\nTest 6: Just the critical lines")
code = """
lines.append('|' + '|'.join(f' {h:<{w}} ' for h, w in zip(headers, widths)) + '|')
lines.append(f'    x-axis [{", ".join(f"{c}" for c in categories)}]')
"""
try_parse(code, 'Just critical lines')

print("\nTest 7: Format spec f-string in loop, then nested")
code = """
for i in range(100):
    x = f'{v:<{w}}'
y = f'{", ".join(f"{c}" for c in cats)}'
"""
try_parse(code, 'Loop with format spec then nested')
