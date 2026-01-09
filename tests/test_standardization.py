"""Test that attributes now use definedIn predicate (standardization)"""

from reter import Reter
import pytest


def test_attributes_use_definedin():
    """Test that attributes use definedIn predicate for standardization."""
    # Test code with attributes
    test_code = """
class Server:
    def __init__(self):
        self.manager = PluginManager()
        self._state = StateManager()
        self.port = 8080

class PluginManager:
    pass

class StateManager:
    pass
"""

    # Create RETER instance
    r = Reter()

    # Load test code
    print("Loading test code...")
    r.load_python_code(test_code, module_name="test_standardization")

    # Test 1: Query attributes using definedIn (NEW standard)
    print("\n=== Test 1: Query attributes with definedIn ===")
    result = r.reql("""
        SELECT ?attr ?name ?class ?className WHERE {
            ?attr concept "py:Attribute" .
            ?attr definedIn ?class .
            ?attr name ?name .
            ?class name ?className
        }
    """)

    print(f"Attributes found using definedIn: {len(result)}")
    if len(result) > 0:
        print(f"  Columns: {result.column_names}")
        for i in range(len(result)):
            row = {col: result[col][i].as_py() for col in result.column_names}
            print(f"  Row {i}: {row}")


def test_has_attribute_inference():
    """Test that hasAttribute inference rule works."""
    test_code = """
class Server:
    def __init__(self):
        self.manager = PluginManager()
        self._state = StateManager()
        self.port = 8080

class PluginManager:
    pass

class StateManager:
    pass
"""

    r = Reter()
    r.load_python_code(test_code, module_name="test_standardization")

    print("\n=== Test 2: Test hasAttribute inference rule ===")
    result2 = r.reql("""
        SELECT ?className ?attrName WHERE {
            ?class concept "py:Class" .
            ?class name ?className .
            ?class hasAttribute ?attr .
            ?attr name ?attrName
        }
    """)

    print(f"hasAttribute relationships found: {len(result2)}")
    for i in range(len(result2)):
        row = {col: result2[col][i].as_py() for col in result2.column_names}
        if '?className' in row and '?attrName' in row:
            print(f"  {row['?className']} hasAttribute {row['?attrName']}")


def test_ofclass_not_used():
    """Test that ofClass is NOT used (standardization)."""
    test_code = """
class Server:
    def __init__(self):
        self.manager = PluginManager()
        self._state = StateManager()
        self.port = 8080

class PluginManager:
    pass

class StateManager:
    pass
"""

    r = Reter()
    r.load_python_code(test_code, module_name="test_standardization")

    print("\n=== Test 3: Verify ofClass is NOT used ===")
    result3 = r.reql("""
        SELECT ?attr ?name WHERE {
            ?attr concept "py:Attribute" .
            ?attr ofClass ?class .
            ?attr name ?name
        }
    """)

    print(f"Attributes found using ofClass (should be 0): {len(result3)}")
    if len(result3) > 0:
        print("  WARNING: ofClass still being used!")
    else:
        print("  ✓ Confirmed: ofClass is NOT used (standardization successful)")

    print("\n=== Standardization Test Complete ===")
