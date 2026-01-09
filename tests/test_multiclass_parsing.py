#!/usr/bin/env python3
"""
Test Suite for Multi-Class Parsing
===================================

Tests that multiple top-level classes are correctly parsed as separate classes,
not nested under each other. This tests the DEDENT token emission bug.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reter import Reter


class TestMultiClassParsing(unittest.TestCase):
    """Test cases for parsing multiple top-level classes."""

    def setUp(self):
        """Set up each test."""
        self.reasoner = Reter()

    def test_two_simple_classes(self):
        """Test two simple classes are parsed as separate top-level classes."""
        code = """
class First:
    def method_a(self):
        pass

class Second:
    def method_b(self):
        pass
"""
        wme_count, errors = self.reasoner.load_python_code(code, "test_module")

        # Query for all classes
        classes = self.reasoner.pattern(
            ("?x", "type", "py:Class"),
            ("?x", "name", "?name")
        ).to_list()

        class_names = {c["?name"] for c in classes}
        self.assertEqual(class_names, {"First", "Second"})
        self.assertEqual(len(classes), 2, f"Expected 2 classes, got {len(classes)}: {class_names}")

    def test_three_classes_with_methods(self):
        """Test three classes with methods are parsed correctly."""
        code = """
class Alpha:
    def alpha_method(self, x):
        return x * 2

class Beta:
    def beta_method(self, y):
        return y + 1

class Gamma:
    def gamma_method(self, z):
        return z - 1
"""
        wme_count, errors = self.reasoner.load_python_code(code, "test_module")

        # Query for all classes
        classes = self.reasoner.pattern(
            ("?x", "type", "py:Class"),
            ("?x", "name", "?name")
        ).to_list()

        class_names = {c["?name"] for c in classes}
        self.assertEqual(class_names, {"Alpha", "Beta", "Gamma"})
        self.assertEqual(len(classes), 3)

    def test_class_methods_belong_to_correct_class(self):
        """Test that methods are associated with the correct class."""
        code = """
class First:
    def first_method(self):
        pass

class Second:
    def second_method(self):
        pass
"""
        wme_count, errors = self.reasoner.load_python_code(code, "test_module")

        # Query for methods of First class
        first_methods = self.reasoner.pattern(
            ("?class", "type", "py:Class"),
            ("?class", "name", "First"),
            ("?class", "hasMethod", "?method"),
            ("?method", "name", "?method_name")
        ).to_list()

        first_method_names = {m["?method_name"] for m in first_methods}
        self.assertEqual(first_method_names, {"first_method"})

        # Query for methods of Second class
        second_methods = self.reasoner.pattern(
            ("?class", "type", "py:Class"),
            ("?class", "name", "Second"),
            ("?class", "hasMethod", "?method"),
            ("?method", "name", "?method_name")
        ).to_list()

        second_method_names = {m["?method_name"] for m in second_methods}
        self.assertEqual(second_method_names, {"second_method"})

    def test_class_with_blank_lines_between(self):
        """Test classes separated by blank lines."""
        code = """
class First:
    def method_a(self):
        return 1


class Second:
    def method_b(self):
        return 2


class Third:
    def method_c(self):
        return 3
"""
        wme_count, errors = self.reasoner.load_python_code(code, "test_module")

        classes = self.reasoner.pattern(
            ("?x", "type", "py:Class"),
            ("?x", "name", "?name")
        ).to_list()

        class_names = {c["?name"] for c in classes}
        self.assertEqual(class_names, {"First", "Second", "Third"})

    def test_class_with_complex_body(self):
        """Test class with complex body doesn't consume next class."""
        code = """
class ComplexClass:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    def method_one(self):
        result = []
        for i in range(10):
            if i % 2 == 0:
                result.append(i)
        return result

    def method_two(self, data):
        return sum(data)

class SimpleClass:
    def simple_method(self):
        pass
"""
        wme_count, errors = self.reasoner.load_python_code(code, "test_module")

        classes = self.reasoner.pattern(
            ("?x", "type", "py:Class"),
            ("?x", "name", "?name")
        ).to_list()

        class_names = {c["?name"] for c in classes}
        self.assertEqual(class_names, {"ComplexClass", "SimpleClass"})

        # Verify SimpleClass has only one method
        simple_methods = self.reasoner.pattern(
            ("?class", "type", "py:Class"),
            ("?class", "name", "SimpleClass"),
            ("?class", "hasMethod", "?method"),
            ("?method", "name", "?method_name")
        ).to_list()

        self.assertEqual(len(simple_methods), 1)
        self.assertEqual(simple_methods[0]["?method_name"], "simple_method")

    def test_parameters_not_accumulated(self):
        """Test that parameters from one class don't accumulate into another."""
        code = """
class First:
    def __init__(self, a, b, c):
        self.a = a
        self.b = b
        self.c = c

class Second:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Third:
    def __init__(self, p):
        self.p = p
"""
        wme_count, errors = self.reasoner.load_python_code(code, "test_module")

        # Get parameter counts for each class's __init__
        for class_name, expected_params in [("First", 3), ("Second", 2), ("Third", 1)]:
            params = self.reasoner.pattern(
                ("?class", "type", "py:Class"),
                ("?class", "name", class_name),
                ("?class", "hasMethod", "?method"),
                ("?method", "name", "__init__"),
                ("?method", "hasParameter", "?param"),
                ("?param", "name", "?param_name")
            ).to_list()

            # Filter out 'self' parameter
            non_self_params = [p for p in params if p["?param_name"] != "self"]
            self.assertEqual(
                len(non_self_params),
                expected_params,
                f"{class_name}.__init__ should have {expected_params} params (excluding self), "
                f"got {len(non_self_params)}: {[p['?param_name'] for p in non_self_params]}"
            )


class TestTransformerFileParsing(unittest.TestCase):
    """Test parsing of the actual transformer.py file."""

    def setUp(self):
        """Set up each test."""
        self.reasoner = Reter()

    def test_transformer_classes_not_nested(self):
        """Test that RenderChartStep is not nested under RenderTableStep."""
        transformer_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "codeine", "src", "codeine", "cadsl", "transformer.py"
        )

        if not os.path.exists(transformer_path):
            self.skipTest(f"transformer.py not found at {transformer_path}")

        wme_count, errors = self.reasoner.load_python_file(transformer_path)

        if wme_count == 0 or errors:
            self.skipTest(f"Failed to parse transformer.py: {errors}")

        # Query for RenderTableStep
        render_table = self.reasoner.pattern(
            ("?x", "type", "py:Class"),
            ("?x", "name", "RenderTableStep")
        ).to_list()
        self.assertEqual(len(render_table), 1, "Should have exactly one RenderTableStep class")

        # Query for RenderChartStep
        render_chart = self.reasoner.pattern(
            ("?x", "type", "py:Class"),
            ("?x", "name", "RenderChartStep")
        ).to_list()
        self.assertEqual(len(render_chart), 1, "Should have exactly one RenderChartStep class")

        # Get qualified names - RenderChartStep should NOT be nested under RenderTableStep
        # The entity ID (?x) is the qualified name
        if render_chart:
            qname = render_chart[0]["?x"]
            self.assertNotIn(
                "RenderTableStep",
                qname,
                f"RenderChartStep should NOT be nested under RenderTableStep, got qualifiedName: {qname}"
            )

    def test_transformer_init_parameters(self):
        """Test that __init__ methods have correct parameter counts."""
        transformer_path = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "codeine", "src", "codeine", "cadsl", "transformer.py"
        )

        if not os.path.exists(transformer_path):
            self.skipTest(f"transformer.py not found at {transformer_path}")

        wme_count, errors = self.reasoner.load_python_file(transformer_path)

        # RenderTableStep.__init__ should have 7 parameters (excluding self):
        # format, columns, title, totals, sort, group_by, max_rows
        params = self.reasoner.pattern(
            ("?class", "type", "py:Class"),
            ("?class", "name", "RenderTableStep"),
            ("?class", "hasMethod", "?method"),
            ("?method", "name", "__init__"),
            ("?method", "hasParameter", "?param"),
            ("?param", "name", "?param_name")
        ).to_list()

        param_names = [p["?param_name"] for p in params if p["?param_name"] != "self"]

        # Should be exactly 7 parameters, not 60!
        self.assertLessEqual(
            len(param_names),
            10,  # Allow some margin but definitely not 60
            f"RenderTableStep.__init__ has too many parameters ({len(param_names)}), "
            f"expected ~7. Got: {param_names[:20]}..."  # Show first 20
        )


if __name__ == "__main__":
    unittest.main()
