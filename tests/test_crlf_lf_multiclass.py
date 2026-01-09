#!/usr/bin/env python3
"""
Test that CRLF vs LF line endings work correctly for multi-class parsing.
"""

import unittest
import tempfile
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reter import Reter


# Same code structure as transformer.py around line 2380
MULTICLASS_CODE = '''class First:
    """First class with methods."""

    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

    def method_one(self):
        result = []
        for i in range(10):
            if i % 2 == 0:
                result.append(i)
        return result

    def method_two(self, data):
        return sum(data)


class Second:
    """Second class."""

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def other_method(self):
        return self.x + self.y
'''


class TestLineEndingMultiClass(unittest.TestCase):
    """Test multi-class parsing with different line endings."""

    def test_lf_line_endings(self):
        """Test with Unix LF line endings."""
        code = MULTICLASS_CODE.replace('\r\n', '\n')  # Ensure LF only

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, newline='\n') as f:
            f.write(code)
            temp_path = f.name

        try:
            reasoner = Reter()
            wme_count, errors = reasoner.load_python_file(temp_path)

            classes = reasoner.pattern(
                ("?x", "type", "py:Class"),
                ("?x", "name", "?name")
            ).to_list()

            class_names = {c["?name"] for c in classes}
            self.assertEqual(class_names, {"First", "Second"})

            # Check Second is not nested (entity ID should not contain First)
            for c in classes:
                if c["?name"] == "Second":
                    # The entity ID (?x) is the qualified name
                    self.assertNotIn(".First.", c["?x"],
                        f"Second should not be nested under First: {c['?x']}")
        finally:
            os.unlink(temp_path)

    def test_crlf_line_endings(self):
        """Test with Windows CRLF line endings."""
        code = MULTICLASS_CODE.replace('\r\n', '\n').replace('\n', '\r\n')  # Convert to CRLF

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, newline='') as f:
            f.write(code)
            temp_path = f.name

        try:
            reasoner = Reter()
            wme_count, errors = reasoner.load_python_file(temp_path)

            classes = reasoner.pattern(
                ("?x", "type", "py:Class"),
                ("?x", "name", "?name")
            ).to_list()

            class_names = {c["?name"] for c in classes}
            self.assertEqual(class_names, {"First", "Second"},
                f"Expected 2 classes, got: {class_names}")

            # Check Second is not nested (entity ID should not contain First)
            for c in classes:
                if c["?name"] == "Second":
                    # The entity ID (?x) is the qualified name
                    self.assertNotIn(".First.", c["?x"],
                        f"Second should not be nested under First: {c['?x']}")
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    unittest.main()
