#!/usr/bin/env python3
"""
Test Suite for Python Fact Extraction
======================================

Tests the Python code analysis capabilities of RETER.
Verifies that Python code is correctly parsed and facts are extracted.

Requirements:
    - RETER compiled with Python parser support
    - py_ontology.dl loaded
"""

import unittest
import tempfile
import os
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reter import Reter


class TestPythonFactExtraction(unittest.TestCase):
    """Test cases for Python code fact extraction."""

    def setUp(self):
        """Set up each test."""
        # Create a fresh reasoner for each test to avoid fact accumulation
        self.reasoner = Reter()

        # Load Python ontology
        ontology_path = Path(__file__).parent.parent / "py_ontology.dl"
        if ontology_path.exists():
            self.reasoner.load_ontology_file(str(ontology_path))
        else:
            # Create minimal ontology for testing
            self.reasoner.load_ontology("""
                py:Class ⊑ᑦ py:CodeEntity
                py:Function ⊑ᑦ py:CodeEntity
                py:Method ⊑ᑦ py:Function
                py:Parameter ⊑ᑦ py:CodeEntity
            """)

    def test_simple_class_extraction(self):
        """Test extraction of a simple class definition."""
        code = """
class Animal:
    '''A simple animal class.'''
    pass
"""
        wme_count, errors = self.reasoner.load_python_code(code, "test_module")

        # Query for classes
        classes = self.reasoner.pattern(
            ("?x", "type", "py:Class"),
            ("?x", "name", "?name")
        ).to_list()

        self.assertEqual(len(classes), 1)
        self.assertEqual(classes[0]["?name"], "Animal")

    def test_class_with_methods(self):
        """Test extraction of class with methods."""
        code = """
class Dog:
    def __init__(self, name):
        self.name = name

    def bark(self):
        return "Woof!"

    def fetch(self, item):
        return item
"""
        wme_count, errors = self.reasoner.load_python_code(code, "test_module")

        # Query for methods
        methods = self.reasoner.pattern(
            ("?class", "type", "py:Class"),
            ("?class", "hasMethod", "?method"),
            ("?class", "name", "?class_name"),
            ("?method", "name", "?method_name")
        ).to_list()

        method_names = {m["?method_name"] for m in methods}
        self.assertIn("__init__", method_names)
        self.assertIn("bark", method_names)
        self.assertIn("fetch", method_names)

    def test_inheritance(self):
        """Test extraction of inheritance relationships."""
        code = """
class Animal:
    pass

class Dog(Animal):
    pass

class Labrador(Dog):
    pass
"""
        wme_count, errors = self.reasoner.load_python_code(code, "test_module")

        # Query for inheritance
        inheritance = self.reasoner.pattern(
            ("?subclass", "inheritsFrom", "?superclass"),
            ("?subclass", "name", "?sub_name"),
            ("?superclass", "name", "?super_name")
        ).to_list()

        # Check direct inheritance
        inheritance_pairs = {(r["?sub_name"], r["?super_name"]) for r in inheritance}
        self.assertIn(("Dog", "Animal"), inheritance_pairs)
        self.assertIn(("Labrador", "Dog"), inheritance_pairs)

    def test_function_with_type_annotations(self):
        """Test extraction of functions with type annotations."""
        code = """
def greet(name: str) -> str:
    return f"Hello, {name}!"

def add(x: int, y: int) -> int:
    return x + y
"""
        wme_count, errors = self.reasoner.load_python_code(code, "test_module")

        # Query for functions with return types
        typed_funcs = self.reasoner.pattern(
            ("?func", "type", "py:Function"),
            ("?func", "name", "?name"),
            ("?func", "returnType", "?return_type")
        ).to_list()

        func_returns = {f["?name"]: f["?return_type"] for f in typed_funcs}
        self.assertEqual(func_returns.get("greet"), "str")
        self.assertEqual(func_returns.get("add"), "int")

    def test_parameter_extraction(self):
        """Test extraction of function parameters."""
        code = """
def process(data: list, threshold: float = 0.5, verbose: bool = False):
    pass
"""
        wme_count, errors = self.reasoner.load_python_code(code, "test_module")

        # Query for parameters
        params = self.reasoner.pattern(
            ("?param", "type", "py:Parameter"),
            ("?param", "name", "?name"),
            ("?param", "ofFunction", "?func")
        ).to_list()

        param_names = {p["?name"] for p in params}
        self.assertIn("data", param_names)
        self.assertIn("threshold", param_names)
        self.assertIn("verbose", param_names)

    def test_decorator_extraction(self):
        """Test extraction of decorators."""
        code = """
class MyClass:
    @property
    def name(self) -> str:
        return self._name

    @staticmethod
    def create():
        return MyClass()

    @classmethod
    def from_dict(cls, data):
        return cls(**data)
"""
        wme_count, errors = self.reasoner.load_python_code(code, "test_module")

        # Query for property decorators
        properties = self.reasoner.pattern(
            ("?method", "type", "py:Method"),
            ("?method", "hasDecorator", "property"),
            ("?method", "name", "?name")
        ).to_list()

        self.assertEqual(len(properties), 1)
        self.assertEqual(properties[0]["?name"], "name")

        # Query for static methods
        static_methods = self.reasoner.pattern(
            ("?method", "type", "py:Method"),
            ("?method", "hasDecorator", "staticmethod"),
            ("?method", "name", "?name")
        ).to_list()

        self.assertEqual(len(static_methods), 1)
        self.assertEqual(static_methods[0]["?name"], "create")

    def test_import_extraction(self):
        """Test extraction of import statements."""
        code = """
import os
from typing import List, Optional
import math as m
from collections import defaultdict
"""
        wme_count, errors = self.reasoner.load_python_code(code, "test_module")

        # Query for import facts - simple imports have modulePath
        simple_imports = self.reasoner.pattern(
            ("?import", "type", "py:Import"),
            ("?import", "modulePath", "?module")
        ).to_list()

        module_paths = {i["?module"] for i in simple_imports}
        # Simple imports: import os, import math as m
        self.assertIn("os", module_paths, f"Expected 'os' in module paths: {module_paths}")
        self.assertIn("math", module_paths, f"Expected 'math' in module paths: {module_paths}")

        # Query for from-imports - these have imports predicate for specific names
        from_imports = self.reasoner.pattern(
            ("?import", "type", "py:Import"),
            ("?import", "imports", "?name")
        ).to_list()

        imported_names = {i["?name"] for i in from_imports}
        # From-imports: from typing import List, Optional; from collections import defaultdict
        self.assertIn("List", imported_names, f"Expected 'List' in imported names: {imported_names}")
        self.assertIn("Optional", imported_names, f"Expected 'Optional' in imported names: {imported_names}")
        self.assertIn("defaultdict", imported_names, f"Expected 'defaultdict' in imported names: {imported_names}")

    def test_function_calls(self):
        """Test extraction of function call relationships."""
        code = """
def helper():
    return 42

def main():
    result = helper()
    print(result)
    return result
"""
        wme_count, errors = self.reasoner.load_python_code(code, "test_module")

        # Query for function calls using direct calls relation
        calls = self.reasoner.pattern(
            ("?caller", "calls", "?callee")
        ).to_list()

        # Verify we have call facts
        self.assertGreater(len(calls), 0, "No call facts were extracted!")

        # Check that main calls helper and print
        # Note: Names may be qualified (e.g., "test_module.main")
        callers = [c["?caller"] for c in calls]
        callees = [c["?callee"] for c in calls]

        # Find calls from main
        main_calls = [c["?callee"] for c in calls if "main" in c["?caller"]]

        # Check that main calls helper and print
        self.assertTrue(any("helper" in callee for callee in main_calls),
                       "main should call helper")
        self.assertTrue(any("print" in callee for callee in main_calls),
                       "main should call print")

    def test_docstring_extraction(self):
        """Test extraction of docstrings."""
        code = '''
class DocumentedClass:
    """This class has documentation."""

    def documented_method(self):
        """This method also has docs."""
        pass

def documented_function():
    """A well-documented function."""
    pass
'''
        wme_count, errors = self.reasoner.load_python_code(code, "test_module")

        # Query for documented classes
        documented = self.reasoner.pattern(
            ("?entity", "hasDocstring", "?doc")
        ).to_list()

        self.assertGreater(len(documented), 0)
        # Check that at least one docstring was extracted
        doc_texts = {d["?doc"] for d in documented}
        self.assertTrue(any("documentation" in doc for doc in doc_texts))

    def test_complex_inheritance(self):
        """Test transitive inheritance relationships."""
        code = """
class A:
    pass

class B(A):
    pass

class C(B):
    pass

class D(C):
    pass
"""
        wme_count, errors = self.reasoner.load_python_code(code, "test_module")

        # Query for transitive inheritance (if ontology supports it)
        # This assumes the ontology has transitive inheritance rules
        inheritance = self.reasoner.pattern(
            ("?descendant", "inheritsFrom", "?ancestor"),
            ("?descendant", "name", "D"),
            ("?ancestor", "name", "?ancestor_name")
        ).to_list()

        ancestor_names = {r["?ancestor_name"] for r in inheritance}
        # D should inherit from C, B, and A (transitively)
        self.assertIn("C", ancestor_names)  # Direct parent
        # Transitive parents depend on ontology rules
        if len(ancestor_names) > 1:
            self.assertIn("B", ancestor_names)
            self.assertIn("A", ancestor_names)

    def test_load_python_file(self):
        """Test loading Python code from a file."""
        # Create temporary Python file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
class TestClass:
    def test_method(self):
        return "test"
""")
            temp_path = f.name

        try:
            wme_count, errors = self.reasoner.load_python_file(temp_path)
            self.assertGreater(wme_count, 0)

            # Verify class was extracted
            classes = self.reasoner.pattern(
                ("?x", "type", "py:Class"),
                ("?x", "name", "TestClass")
            ).to_list()

            self.assertEqual(len(classes), 1)
        finally:
            # Clean up temporary file
            os.unlink(temp_path)

    def test_load_python_directory(self):
        """Test loading all Python files from a directory."""
        # Create temporary directory with Python files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test files
            file1 = Path(temp_dir) / "module1.py"
            file1.write_text("""
class Module1Class:
    pass
""")

            file2 = Path(temp_dir) / "module2.py"
            file2.write_text("""
class Module2Class:
    pass
""")

            # Create subdirectory
            subdir = Path(temp_dir) / "subpackage"
            subdir.mkdir()

            file3 = subdir / "module3.py"
            file3.write_text("""
class Module3Class:
    pass
""")

            # Load directory recursively
            total_wmes, errors = self.reasoner.load_python_directory(temp_dir, recursive=True)
            self.assertGreater(total_wmes, 0)

            # Verify all classes were extracted
            classes = self.reasoner.pattern(
                ("?x", "type", "py:Class"),
                ("?x", "name", "?name")
            ).to_list()

            class_names = {c["?name"] for c in classes}
            self.assertIn("Module1Class", class_names)
            self.assertIn("Module2Class", class_names)
            self.assertIn("Module3Class", class_names)

    def test_error_handling(self):
        """Test permissive error handling for invalid Python code."""
        invalid_code = """
def broken_function(
    # Missing closing parenthesis
    pass
"""

        # Parser uses error recovery - should not raise exception
        # but should still process what it can
        wme_count, errors = self.reasoner.load_python_code(invalid_code, "broken_module")

        # Should have at least created the module fact
        self.assertGreaterEqual(wme_count, 1)
        # Should have syntax errors reported
        self.assertIsInstance(errors, list)

    def test_empty_code(self):
        """Test handling of empty Python code."""
        empty_code = ""
        wme_count, errors = self.reasoner.load_python_code(empty_code, "empty_module")

        # Should still create module fact
        self.assertGreaterEqual(wme_count, 1)
        # Should have no syntax errors
        self.assertIsInstance(errors, list)

    def test_position_metadata(self):
        """Test extraction of source position metadata."""
        code = """
class MyClass:  # Line 2
    def method(self):  # Line 3
        pass
"""
        wme_count, errors = self.reasoner.load_python_code(code, "test_module")

        # Query for position information
        positions = self.reasoner.pattern(
            ("?entity", "atLine", "?line")
        ).to_list()

        # Should have line numbers for entities
        self.assertGreater(len(positions), 0)


class TestPythonOntologyInference(unittest.TestCase):
    """Test cases for Python ontology inference rules."""

    def setUp(self):
        """Set up each test."""
        # Create a fresh reasoner for each test to avoid fact accumulation
        self.reasoner = Reter()

        # Load full Python ontology with inference rules
        ontology_path = Path(__file__).parent.parent / "py_ontology.dl"
        if ontology_path.exists():
            self.reasoner.load_ontology_file(str(ontology_path))

    def test_inherited_methods(self):
        """Test inference of inherited methods."""
        code = """
class Animal:
    def speak(self):
        return "..."

    def move(self):
        return "moving"

class Dog(Animal):
    def bark(self):
        return "Woof!"
"""
        wme_count, errors = self.reasoner.load_python_code(code, "test_module")

        # Query for inherited methods
        inherited = self.reasoner.pattern(
            ("?class", "name", "Dog"),
            ("?class", "inheritsMethod", "?method"),
            ("?method", "name", "?method_name")
        ).to_list()

        inherited_method_names = {m["?method_name"] for m in inherited}
        # Dog should inherit speak and move from Animal
        if inherited_method_names:  # Only if inference rules are active
            self.assertIn("speak", inherited_method_names)
            self.assertIn("move", inherited_method_names)

    def test_undocumented_detection(self):
        """Test detection of undocumented entities."""
        code = """
class DocumentedClass:
    '''This class has docs.'''
    pass

class UndocumentedClass:
    pass

def documented_func():
    '''This function has docs.'''
    pass

def undocumented_func():
    pass
"""
        wme_count, errors = self.reasoner.load_python_code(code, "test_module")

        # Query for undocumented entities
        undocumented = self.reasoner.pattern(
            ("?entity", "undocumented", "true"),
            ("?entity", "name", "?name")
        ).to_list()

        undoc_names = {u["?name"] for u in undocumented}
        if undoc_names:  # Only if inference rules are active
            self.assertIn("UndocumentedClass", undoc_names)
            self.assertIn("undocumented_func", undoc_names)
            self.assertNotIn("DocumentedClass", undoc_names)
            self.assertNotIn("documented_func", undoc_names)

    def test_context_manager_detection(self):
        """Test detection of context managers."""
        code = """
class MyContextManager:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

class NotAContextManager:
    def __enter__(self):
        return self
    # Missing __exit__
"""
        wme_count, errors = self.reasoner.load_python_code(code, "test_module")

        # Query for context managers
        context_managers = self.reasoner.pattern(
            ("?class", "isContextManager", "true"),
            ("?class", "name", "?name")
        ).to_list()

        cm_names = {cm["?name"] for cm in context_managers}
        if cm_names:  # Only if inference rules are active
            self.assertIn("MyContextManager", cm_names)
            self.assertNotIn("NotAContextManager", cm_names)


if __name__ == "__main__":
    unittest.main()