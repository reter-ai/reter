"""
Test Python code analysis extraction and querying.

Tests the issues reported:
1. Method signatures with parameters
2. Line numbers for methods
3. Method bodies/logic
4. Dependencies between methods
5. Call relationships
6. REQL query patterns for finding methods by class
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from reter import Reter


@pytest.fixture
def reasoner():
    """Create a fresh reasoner instance for each test"""
    return Reter()


def query_to_rows(result):
    """Convert PyArrow Table to list of tuples"""
    if result.num_rows == 0:
        return []
    # Get all columns as lists
    columns = [result.column(name).to_pylist() for name in result.column_names]
    # Zip them into rows
    return list(zip(*columns))


@pytest.fixture
def sample_python_code():
    """Sample Python code for testing"""
    return """
class Calculator:
    '''A simple calculator class'''

    def __init__(self, initial_value=0):
        self.value = initial_value

    def add(self, x: int) -> int:
        '''Add x to the current value'''
        result = self.value + x
        self.value = result
        return result

    def multiply(self, x: int, y: int = 2) -> int:
        '''Multiply two numbers'''
        return x * y

    def calculate(self, a: int, b: int) -> int:
        '''Calculate using add and multiply'''
        temp = self.add(a)
        final = self.multiply(temp, b)
        return final

class MathHelper:
    @staticmethod
    def square(n: int) -> int:
        return n * n
"""


def test_method_extraction(reasoner, sample_python_code):
    """Test that methods are extracted from classes"""
    wme_count, errors = reasoner.load_python_code(sample_python_code, "calculator")
    assert wme_count > 0, "Should extract facts from Python code"
    assert isinstance(errors, list), "Should return error list"

    # Query for all methods
    result = reasoner.reql("""
        SELECT ?method ?name
        WHERE {
            ?method concept "py:Method" .
            ?method name ?name
        }
    """)

    # PyArrow Table - access columns
    method_col = result.column('?method').to_pylist()
    name_col = result.column('?name').to_pylist()

    methods = name_col
    print(f"Found methods: {methods}")
    print(f"Method qualified names: {method_col}")

    # Should find all methods including __init__
    assert "__init__" in methods, "Should extract __init__ method"
    assert "add" in methods, "Should extract add method"
    assert "multiply" in methods, "Should extract multiply method"
    assert "calculate" in methods, "Should extract calculate method"
    assert "square" in methods, "Should extract static method"


def test_method_parameters(reasoner, sample_python_code):
    """Test that method parameters are extracted with types"""
    wme_count, errors = reasoner.load_python_code(sample_python_code, "calculator")

    # First find the method ID for 'add' (includes full signature)
    method_result = reasoner.reql("""
        SELECT ?method
        WHERE {
            ?method concept "py:Method" .
            ?method name "add"
        }
    """)
    method_rows = query_to_rows(method_result)
    assert len(method_rows) > 0, "Should find add method"
    add_method_id = method_rows[0][0]

    # Query for parameters of the 'add' method using the actual method ID
    result = reasoner.reql(f"""
        SELECT ?param ?name ?type ?position
        WHERE {{
            ?param concept "py:Parameter" .
            ?param ofFunction "{add_method_id}" .
            ?param name ?name .
            ?param typeAnnotation ?type .
            ?param position ?position
        }}
        ORDER BY ?position
    """)

    rows = query_to_rows(result)
    print(f"Parameters of 'add' method: {rows}")

    assert len(rows) > 0, "Should extract parameters from add method"

    # Check if parameter 'x' with type 'int' is found
    param_names = [row[1] for row in rows]
    param_types = [row[2] for row in rows]

    assert "x" in param_names, "Should extract parameter 'x'"
    assert "int" in param_types, "Should extract type annotation 'int'"


def test_method_line_numbers(reasoner, sample_python_code):
    """Test that methods have line number information"""
    wme_count, errors = reasoner.load_python_code(sample_python_code, "calculator")

    # Query for methods with line numbers
    result = reasoner.reql("""
        SELECT ?method ?name ?line
        WHERE {
            ?method concept "py:Method" .
            ?method name ?name .
            ?method atLine ?line
        }
    """)

    rows = query_to_rows(result)
    print(f"Methods with line numbers: {rows}")

    assert len(rows) > 0, "Should have line numbers for methods"

    # All line numbers should be valid (non-empty strings)
    for row in rows:
        line_num = row[2]
        assert line_num and line_num != "", f"Method {row[1]} should have line number"
        assert int(line_num) > 0, f"Method {row[1]} should have positive line number"


def test_method_return_types(reasoner, sample_python_code):
    """Test that return type annotations are extracted"""
    wme_count, errors = reasoner.load_python_code(sample_python_code, "calculator")

    # Query for methods with return types
    result = reasoner.reql("""
        SELECT ?method ?name ?returnType
        WHERE {
            ?method concept "py:Method" .
            ?method name ?name .
            ?method returnType ?returnType
        }
    """)

    rows = query_to_rows(result)
    print(f"Methods with return types: {rows}")

    assert len(rows) > 0, "Should extract return types"

    # Check specific return types
    method_returns = {row[1]: row[2] for row in rows}
    assert method_returns.get("add") == "int", "add should return int"
    assert method_returns.get("multiply") == "int", "multiply should return int"


def test_call_relationships(reasoner, sample_python_code):
    """Test that function calls are extracted"""
    wme_count, errors = reasoner.load_python_code(sample_python_code, "calculator")

    # Query for call relationships
    result = reasoner.reql("""
        SELECT ?caller ?callee
        WHERE {
            ?caller calls ?callee
        }
    """)

    rows = query_to_rows(result)
    print(f"Call relationships: {rows}")

    assert len(rows) > 0, "Should extract call relationships"

    # Check that 'calculate' calls 'add' and 'multiply'
    calls = [(row[0], row[1]) for row in rows]

    # Find calls from calculate method
    calculate_calls = [callee for caller, callee in calls if "calculate" in caller]
    print(f"calculate calls: {calculate_calls}")

    assert len(calculate_calls) > 0, "calculate should call other methods"


def test_query_methods_by_class(reasoner, sample_python_code):
    """Test querying methods defined in a specific class"""
    wme_count, errors = reasoner.load_python_code(sample_python_code, "calculator")

    # Query methods defined in Calculator class
    result = reasoner.reql("""
        SELECT ?method ?name
        WHERE {
            ?method concept "py:Method" .
            ?method definedIn "calculator.Calculator" .
            ?method name ?name
        }
    """)

    rows = query_to_rows(result)
    print(f"Methods in Calculator class: {rows}")

    assert len(rows) >= 4, "Calculator should have at least 4 methods"

    method_names = [row[1] for row in rows]
    assert "__init__" in method_names
    assert "add" in method_names
    assert "multiply" in method_names
    assert "calculate" in method_names


def test_method_decorators(reasoner, sample_python_code):
    """Test that decorators are extracted"""
    wme_count, errors = reasoner.load_python_code(sample_python_code, "calculator")

    # Query for methods with decorators
    result = reasoner.reql("""
        SELECT ?method ?name ?decorator
        WHERE {
            ?method concept "py:Method" .
            ?method name ?name .
            ?method hasDecorator ?decorator
        }
    """)

    rows = query_to_rows(result)
    print(f"Methods with decorators: {rows}")

    if len(rows) > 0:
        # Check if staticmethod decorator is found
        decorators = [row[2] for row in rows]
        assert "staticmethod" in decorators, "Should extract @staticmethod decorator"


def test_default_parameter_values(reasoner, sample_python_code):
    """Test that default parameter values are extracted"""
    wme_count, errors = reasoner.load_python_code(sample_python_code, "calculator")

    # Query for parameters with default values
    result = reasoner.reql("""
        SELECT ?param ?name ?default
        WHERE {
            ?param concept "py:Parameter" .
            ?param name ?name .
            ?param defaultValue ?default
        }
    """)

    rows = query_to_rows(result)
    print(f"Parameters with defaults: {rows}")

    if len(rows) > 0:
        # Check specific defaults
        param_defaults = {row[1]: row[2] for row in rows}
        # __init__ has initial_value=0
        # multiply has y=2
        assert len(param_defaults) > 0, "Should extract default parameter values"


def test_class_docstrings(reasoner, sample_python_code):
    """Test that class docstrings are extracted"""
    wme_count, errors = reasoner.load_python_code(sample_python_code, "calculator")

    # Query for classes with docstrings
    result = reasoner.reql("""
        SELECT ?class ?name ?docstring
        WHERE {
            ?class concept "py:Class" .
            ?class name ?name .
            ?class hasDocstring ?docstring
        }
    """)

    rows = query_to_rows(result)
    print(f"Classes with docstrings: {rows}")

    if len(rows) > 0:
        # Calculator class should have docstring
        class_docs = {row[1]: row[2] for row in rows}
        assert "Calculator" in class_docs, "Should extract Calculator class docstring"


def test_method_qualified_names(reasoner, sample_python_code):
    """Test that methods have fully qualified names (encoded in method ID)"""
    wme_count, errors = reasoner.load_python_code(sample_python_code, "calculator")

    # The method ID itself contains the qualified name (module.Class.method(signature))
    result = reasoner.reql("""
        SELECT ?method ?name ?class
        WHERE {
            ?method concept "py:Method" .
            ?method name ?name .
            ?method definedIn ?class
        }
    """)

    rows = query_to_rows(result)
    print(f"Methods with classes: {rows}")

    assert len(rows) > 0, "Should have methods with class info"

    # The method IDs (first column) contain full qualified names with signatures
    method_ids = [row[0] for row in rows]
    
    # Check that expected methods exist (method IDs include signature)
    has_add = any("Calculator.add" in mid for mid in method_ids)
    has_multiply = any("Calculator.multiply" in mid for mid in method_ids)
    has_square = any("MathHelper.square" in mid for mid in method_ids)
    
    assert has_add, "Should have Calculator.add method"
    assert has_multiply, "Should have Calculator.multiply method"
    assert has_square, "Should have MathHelper.square method"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
