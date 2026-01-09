#!/usr/bin/env python3
"""Test nested f-string patterns that cause the parser exception."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from reter import Reter

def try_parse(code, label):
    """Try to parse code and return (wme_count, errors)."""
    reasoner = Reter()
    try:
        wme_count, errors = reasoner.load_python_code(code, "test.py")
        err_summary = "exception" if (errors and errors[0].get('message', '').startswith('Parse failed')) else (f"{len(errors)} errors" if errors else "ok")
        print(f"  {label}: wmes={wme_count}, {err_summary}")
        return wme_count, errors
    except Exception as e:
        print(f"  {label}: Python exception: {e}")
        return -1, [str(e)]

# Test progressively complex f-string patterns
print("Testing f-string patterns:")

# Simple f-string
try_parse('x = f"hello"', 'Simple f-string')

# F-string with variable
try_parse('x = f"hello {name}"', 'F-string with variable')

# F-string with expression
try_parse('x = f"hello {1+1}"', 'F-string with expression')

# F-string with method call
try_parse('x = f"hello {name.upper()}"', 'F-string with method call')

# F-string with list
try_parse('x = f"items: {items}"', 'F-string with list variable')

# F-string with list comprehension
try_parse('x = f"items: {[x for x in items]}"', 'F-string with list comp')

# F-string with join
try_parse('x = f"items: {\", \".join(items)}"', 'F-string with join')

# F-string with join and generator
try_parse('x = f"items: {\", \".join(str(x) for x in items)}"', 'F-string with join+generator')

# Nested f-string (inner f-string)
try_parse('x = f"outer {f\"inner\"}"', 'Nested f-string')

# The exact failing pattern
print("\nThe exact failing pattern:")
try_parse('''x = f'    x-axis [{", ".join(f"{c}" for c in categories)}]' ''', 'Exact failing pattern')

# Simplified versions
print("\nSimplified versions:")
try_parse('''x = f'{", ".join(f"{c}" for c in categories)}' ''', 'Simplified nested f-string')
try_parse('''x = f'{", ".join(c for c in categories)}' ''', 'Without nested f-string')
try_parse('''x = f'{", ".join(items)}' ''', 'Simple join')

# Further isolate
print("\nFurther isolation:")
try_parse('''x = f'{f"{c}" for c in cats}' ''', 'Generator with nested f-string')
try_parse('''x = f'{[f"{c}" for c in cats]}' ''', 'List comp with nested f-string')
