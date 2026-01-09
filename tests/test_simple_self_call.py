"""
Test the simplest possible case: self.method() call within the same class.
"""

from reter import Reter
import tempfile
import os
import pytest


def test_simple_self_call():
    """Test that self.method() calls are properly extracted."""
    code = '''
class Server:
    def start(self):
        self.initialize()

    def initialize(self):
        pass
'''

    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(code)
        f.flush()
        temp_path = f.name

    try:
        r = Reter()
        print(f"Loading: {temp_path}")
        wmes = r.load_python_file(temp_path)
        print(f"✓ Added {wmes} WMEs\n")

        # Check what methods exist
        print("=== Methods ===")
        result = r.reql("""
            SELECT ?method ?name
            WHERE {
                ?method concept "py:Method" .
                ?method name ?name
            }
        """)
        print(f"Methods found: {result.num_rows}")
        for row in range(result.num_rows):
            if '?name' in result.column_names:
                name = result.column('?name')[row].as_py()
                method = result.column('?method')[row].as_py()
                print(f"  {method} (name: {name})")

        # Check for ANY calls relationships (not just to methods)
        print("\n=== ALL calls relationships ===")
        result = r.reql("""
            SELECT ?caller ?callee
            WHERE {
                ?caller calls ?callee
            }
        """)
        print(f"Calls found: {result.num_rows}")
        if result.num_rows > 0:
            for row in range(result.num_rows):
                caller = result.column('?caller')[row].as_py()
                callee = result.column('?callee')[row].as_py()
                print(f"  {caller} calls {callee}")
        else:
            print("  No calls relationships found!")

        # Check for calls where callee is also a method
        print("\n=== Calls where callee is a Method ===")
        result = r.reql("""
            SELECT ?caller ?callerName ?callee ?calleeName
            WHERE {
                ?caller concept "py:Method" .
                ?caller name ?callerName .
                ?caller calls ?callee .
                ?callee concept "py:Method" .
                ?callee name ?calleeName
            }
        """)
        print(f"Method-to-Method calls found: {result.num_rows}")
        if result.num_rows > 0:
            for row in range(result.num_rows):
                caller_name = result.column('?callerName')[row].as_py()
                callee_name = result.column('?calleeName')[row].as_py()
                print(f"  {caller_name} -> {callee_name}")
        else:
            print("  No method-to-method calls found!")
            print("\n  This means resolveMethodCall() is returning empty string")
            print("  OR calls relationship is not being created at all")

    finally:
        os.unlink(temp_path)
