#!/usr/bin/env python3
"""
Minimal test case to reproduce the multi-class nesting bug.
"""

import unittest
import tempfile
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reter import Reter


# Simplest case that fails
SIMPLE_CASE = '''class First:
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def method(self):
        return self.a


class Second:
    def __init__(self, x, y):
        self.x = x
        self.y = y
'''


# Case with multiple methods - does this trigger the bug?
MULTI_METHOD_CASE = '''class First:
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def method_one(self):
        return self.a

    def method_two(self):
        return self.b

    def method_three(self):
        return self.a + self.b


class Second:
    def __init__(self, x, y):
        self.x = x
        self.y = y
'''


# Case with f-strings - does this trigger the bug?
FSTRING_CASE = '''class First:
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def method(self, data):
        lines = []
        for h in data:
            lines.append(f' {h} ')
        return lines


class Second:
    def __init__(self, x, y):
        self.x = x
        self.y = y
'''


# Case with complex comprehension - does this trigger the bug?
COMPREHENSION_CASE = '''class First:
    def __init__(self, a, b):
        self.a = a
        self.b = b

    def method(self, headers, widths):
        lines = []
        sep = '+' + '+'.join('-' * (w + 2) for w in widths) + '+'
        lines.append(sep)
        lines.append('|' + '|'.join(f' {h:<{w}} ' for h, w in zip(headers, widths)) + '|')
        lines.append(sep)
        return "\\n".join(lines)


class Second:
    def __init__(self, x, y):
        self.x = x
        self.y = y
'''


class TestMinimalBug(unittest.TestCase):
    """Find minimal reproduction case."""

    def _check_classes_not_nested(self, code, expected_classes):
        """Helper to check that classes are not nested."""
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
            self.assertEqual(class_names, expected_classes, f"Got classes: {class_names}")

            # Check none are nested - the entity ID (?x) is the qualified name
            for c in classes:
                qname = c["?x"]
                parts = qname.split(".")
                self.assertEqual(
                    len(parts), 2,
                    f"{c['?name']} should not be nested, got: {qname}"
                )
        finally:
            os.unlink(temp_path)

    def test_simple_case(self):
        """Test simplest case."""
        self._check_classes_not_nested(SIMPLE_CASE, {"First", "Second"})

    def test_multi_method_case(self):
        """Test multiple methods."""
        self._check_classes_not_nested(MULTI_METHOD_CASE, {"First", "Second"})

    def test_fstring_case(self):
        """Test f-string usage."""
        self._check_classes_not_nested(FSTRING_CASE, {"First", "Second"})

    def test_comprehension_case(self):
        """Test complex comprehension."""
        self._check_classes_not_nested(COMPREHENSION_CASE, {"First", "Second"})


# Isolate the exact problematic construct
FSTRING_FORMAT_SPEC_BUG = '''class First:
    def method(self, h, w):
        return f' {h:<{w}} '


class Second:
    def __init__(self, x):
        self.x = x
'''


FSTRING_IN_JOIN_BUG = '''class First:
    def method(self, items, widths):
        return '|'.join(f' {h:<{w}} ' for h, w in zip(items, widths))


class Second:
    def __init__(self, x):
        self.x = x
'''


GENERATOR_ONLY = '''class First:
    def method(self, items, widths):
        return list(w + 2 for w in widths)


class Second:
    def __init__(self, x):
        self.x = x
'''


class TestIsolatedBug(unittest.TestCase):
    """Isolate the exact problematic construct."""

    def _check_classes_not_nested(self, code, expected_classes):
        """Helper to check that classes are not nested."""
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
            self.assertEqual(class_names, expected_classes, f"Got classes: {class_names}")

            # Check none are nested - the entity ID (?x) is the qualified name
            for c in classes:
                qname = c["?x"]
                parts = qname.split(".")
                self.assertEqual(
                    len(parts), 2,
                    f"{c['?name']} should not be nested, got: {qname}"
                )
        finally:
            os.unlink(temp_path)

    def test_fstring_format_spec(self):
        """Test f-string with dynamic format spec {h:<{w}}."""
        self._check_classes_not_nested(FSTRING_FORMAT_SPEC_BUG, {"First", "Second"})

    def test_fstring_in_join(self):
        """Test f-string in join with generator."""
        self._check_classes_not_nested(FSTRING_IN_JOIN_BUG, {"First", "Second"})

    def test_generator_only(self):
        """Test plain generator expression."""
        self._check_classes_not_nested(GENERATOR_ONLY, {"First", "Second"})


if __name__ == "__main__":
    unittest.main()
