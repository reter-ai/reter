"""Test to replicate OPTIONAL query exponential blowup (segfault/OOM).

The issue: When entities have multiple values for attributes, OPTIONAL clauses
create Cartesian products that grow exponentially and crash around 30-35k rows.

Crash threshold discovered:
- 30,000 rows: Works (150 methods * 20 callers * 10 params)
- 35,000 rows: Crashes (175 methods * 20 callers * 10 params)

This test creates controlled scenarios to reproduce the issue.
"""
import pytest
import time
import tracemalloc
from reter import Reter


def create_high_cardinality_data(reasoner: Reter, num_methods: int,
                                  callers_per_method: int,
                                  params_per_method: int,
                                  locals_per_method: int = 0):
    """Create test data with high cardinality relationships.

    Note: "Function" is a reserved keyword in the AI parser, using "Caller" instead.
    """
    all_facts = []

    for i in range(num_methods):
        method_id = f"method{i}"
        all_facts.append(f'Method({method_id})')
        all_facts.append(f'methodName({method_id}, "{method_id}")')
        all_facts.append(f'atLine({method_id}, {i * 10})')

        for c in range(callers_per_method):
            caller_id = f"caller{i}x{c}"
            all_facts.append(f'Caller({caller_id})')
            all_facts.append(f'calledBy({method_id}, {caller_id})')

        for p in range(params_per_method):
            param_id = f"param{i}x{p}"
            all_facts.append(f'Param({param_id})')
            all_facts.append(f'hasParam({method_id}, {param_id})')

        for l in range(locals_per_method):
            local_id = f"local{i}x{l}"
            all_facts.append(f'LocalVar({local_id})')
            all_facts.append(f'hasLocal({method_id}, {local_id})')

    reasoner.load_ontology("\n".join(all_facts), "test.blowup")
    return num_methods


def test_optional_blowup_small():
    """Small test case - 60 rows, should complete quickly."""
    reasoner = Reter("ai")

    # 10 methods * 3 callers * 2 params = 60 rows
    create_high_cardinality_data(reasoner,
                                  num_methods=10,
                                  callers_per_method=3,
                                  params_per_method=2)

    query = """
    SELECT ?m ?name ?caller ?param
    WHERE {
        ?m type Method .
        ?m methodName ?name .
        OPTIONAL { ?m calledBy ?caller }
        OPTIONAL { ?m hasParam ?param }
    }
    """

    start = time.time()
    result = reasoner.reql(query)
    elapsed = time.time() - start

    print(f"\nSmall test: {result.num_rows} rows in {elapsed:.3f}s")
    assert result.num_rows == 60  # Exact Cartesian product
    assert elapsed < 5.0


def test_optional_blowup_medium():
    """Medium test case - 5,000 rows, should complete quickly."""
    reasoner = Reter("ai")

    # 100 methods * 10 callers * 5 params = 5,000 rows
    create_high_cardinality_data(reasoner,
                                  num_methods=100,
                                  callers_per_method=10,
                                  params_per_method=5)

    query = """
    SELECT ?m ?name ?caller ?param
    WHERE {
        ?m type Method .
        ?m methodName ?name .
        OPTIONAL { ?m calledBy ?caller }
        OPTIONAL { ?m hasParam ?param }
    }
    """

    start = time.time()
    tracemalloc.start()

    result = reasoner.reql(query, timeout_ms=30000)

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    elapsed = time.time() - start

    print(f"\nMedium test: {result.num_rows} rows in {elapsed:.3f}s")
    print(f"Memory: current={current/1024/1024:.1f}MB, peak={peak/1024/1024:.1f}MB")

    assert result.num_rows == 5000


def test_optional_blowup_at_threshold():
    """Test at the working threshold - 30,000 rows (should work)."""
    reasoner = Reter("ai")

    # 150 methods * 20 callers * 10 params = 30,000 rows (this works)
    create_high_cardinality_data(reasoner,
                                  num_methods=150,
                                  callers_per_method=20,
                                  params_per_method=10)

    query = """
    SELECT ?m ?name ?caller ?param
    WHERE {
        ?m type Method .
        ?m methodName ?name .
        OPTIONAL { ?m calledBy ?caller }
        OPTIONAL { ?m hasParam ?param }
    }
    """

    print("\nThreshold test: 30,000 rows (should work)...")
    start = time.time()
    result = reasoner.reql(query, timeout_ms=60000)
    elapsed = time.time() - start

    print(f"Result: {result.num_rows} rows in {elapsed:.3f}s")
    assert result.num_rows == 30000


def test_optional_blowup_crash():
    """Test above threshold - 35,000 rows (causes segfault).

    This test demonstrates the crash bug. Skip in CI to avoid killing the process.
    """
    reasoner = Reter("ai")

    # 175 methods * 20 callers * 10 params = 35,000 rows (crashes!)
    create_high_cardinality_data(reasoner,
                                  num_methods=175,
                                  callers_per_method=20,
                                  params_per_method=10)

    query = """
    SELECT ?m ?name ?caller ?param
    WHERE {
        ?m type Method .
        ?m methodName ?name .
        OPTIONAL { ?m calledBy ?caller }
        OPTIONAL { ?m hasParam ?param }
    }
    """

    print("\nCrash test: 35,000 rows (will likely segfault)...")
    print("If this test passes, the bug has been fixed!")

    start = time.time()
    try:
        result = reasoner.reql(query, timeout_ms=60000)
        elapsed = time.time() - start
        print(f"UNEXPECTED SUCCESS: {result.num_rows} rows in {elapsed:.3f}s")
        # If we get here, the bug is fixed!
        assert result.num_rows == 35000
    except RuntimeError as e:
        elapsed = time.time() - start
        print(f"Runtime error after {elapsed:.3f}s: {e}")
        pytest.fail("Query failed with RuntimeError (timeout or OOM)")


def test_optional_blowup_three_optionals():
    """Test with 3 OPTIONAL clauses - smaller data but higher explosion factor."""
    reasoner = Reter("ai")

    # 50 methods * 10 callers * 5 params * 3 locals = 7,500 rows
    create_high_cardinality_data(reasoner,
                                  num_methods=50,
                                  callers_per_method=10,
                                  params_per_method=5,
                                  locals_per_method=3)

    query = """
    SELECT ?m ?name ?caller ?param ?local
    WHERE {
        ?m type Method .
        ?m methodName ?name .
        OPTIONAL { ?m calledBy ?caller }
        OPTIONAL { ?m hasParam ?param }
        OPTIONAL { ?m hasLocal ?local }
    }
    """

    print("\n3-OPTIONAL test: Expected 50 * 10 * 5 * 3 = 7,500 rows...")
    start = time.time()
    result = reasoner.reql(query, timeout_ms=60000)
    elapsed = time.time() - start

    print(f"Result: {result.num_rows} rows in {elapsed:.3f}s")
    assert result.num_rows == 7500


def test_workaround_separate_queries():
    """Demonstrate the workaround: use separate queries instead of multiple OPTIONALs.

    This approach avoids the Cartesian product entirely by doing separate queries
    and joining in application code if needed.
    """
    reasoner = Reter("ai")

    # Same data that would produce 5000 rows with combined OPTIONAL
    create_high_cardinality_data(reasoner,
                                  num_methods=100,
                                  callers_per_method=10,
                                  params_per_method=5)

    start = time.time()

    # Query 1: Get methods (100 rows)
    methods_result = reasoner.reql("""
        SELECT ?m ?name
        WHERE {
            ?m type Method .
            ?m methodName ?name
        }
    """)

    # Query 2: Get callers (1000 rows)
    callers_result = reasoner.reql("""
        SELECT ?m ?caller
        WHERE {
            ?m type Method .
            ?m calledBy ?caller
        }
    """)

    # Query 3: Get params (500 rows)
    params_result = reasoner.reql("""
        SELECT ?m ?param
        WHERE {
            ?m type Method .
            ?m hasParam ?param
        }
    """)

    elapsed = time.time() - start

    total_rows = methods_result.num_rows + callers_result.num_rows + params_result.num_rows
    cartesian_rows = 100 * 10 * 5

    print(f"\nWorkaround test:")
    print(f"  Methods: {methods_result.num_rows} rows")
    print(f"  Callers: {callers_result.num_rows} rows")
    print(f"  Params: {params_result.num_rows} rows")
    print(f"  Total rows: {total_rows}")
    print(f"  vs Cartesian: {cartesian_rows} rows")
    print(f"  Reduction: {cartesian_rows / total_rows:.1f}x fewer rows")
    print(f"  Total time: {elapsed:.3f}s")

    assert total_rows == 1600  # 100 + 1000 + 500
    assert elapsed < 5.0


def test_get_architecture_pattern():
    """Test replicating get_architecture.cadsl query pattern.

    This query has 3 OPTIONAL clauses with GROUP BY and COUNT aggregations:
    - Module with file (base)
    - OPTIONAL: Class in same file
    - OPTIONAL: Function in same file
    - OPTIONAL: Module imports

    This is the exact pattern from get_architecture.cadsl that crashes Codeine.
    """
    reasoner = Reter("ai")

    # Create realistic codebase data:
    # - 100 modules (files)
    # - ~3 classes per module = 300 classes
    # - ~5 functions per module = 500 functions
    # - ~10 imports per module = 1000 imports
    # Cartesian: 100 * 3 * 5 * 10 = 15,000 rows before aggregation

    all_facts = []
    num_modules = 100
    classes_per_module = 3
    functions_per_module = 5
    imports_per_module = 10

    for i in range(num_modules):
        module_id = f"module{i}"
        file_path = f"src/file{i}.py"

        # Module with file
        all_facts.append(f'Module({module_id})')
        all_facts.append(f'inFile({module_id}, "{file_path}")')

        # Classes in module
        for c in range(classes_per_module):
            class_id = f"class{i}x{c}"
            all_facts.append(f'Class({class_id})')
            all_facts.append(f'inFile({class_id}, "{file_path}")')

        # Functions in module (use "Func" since "Function" is reserved keyword)
        for f in range(functions_per_module):
            func_id = f"func{i}x{f}"
            all_facts.append(f'Func({func_id})')
            all_facts.append(f'inFile({func_id}, "{file_path}")')

        # Imports
        for imp in range(imports_per_module):
            import_id = f"import{i}x{imp}"
            all_facts.append(f'imports({module_id}, {import_id})')

    reasoner.load_ontology("\n".join(all_facts), "test.architecture")

    # This is the exact query pattern from get_architecture.cadsl
    # (with {Module} etc resolved to just Module)
    query = """
    SELECT ?file (COUNT(?class) AS ?class_count) (COUNT(?func) AS ?function_count) (COUNT(?import) AS ?import_count)
    WHERE {
        ?m type Module .
        ?m inFile ?file .
        OPTIONAL { ?class type Class . ?class inFile ?file }
        OPTIONAL { ?func type Func . ?func inFile ?file }
        OPTIONAL { ?m imports ?import }
    }
    GROUP BY ?file
    ORDER BY ?file
    """

    print(f"\nget_architecture pattern test:")
    print(f"  {num_modules} modules, {classes_per_module} classes/module, "
          f"{functions_per_module} functions/module, {imports_per_module} imports/module")
    expected_cartesian = num_modules * classes_per_module * functions_per_module * imports_per_module
    print(f"  Expected Cartesian before aggregation: {expected_cartesian} rows")

    start = time.time()
    result = reasoner.reql(query, timeout_ms=60000)
    elapsed = time.time() - start

    print(f"  Result: {result.num_rows} rows in {elapsed:.3f}s")

    # Should have num_modules rows after GROUP BY
    assert result.num_rows == num_modules, f"Expected {num_modules} rows, got {result.num_rows}"
    print(f"  SUCCESS: Query returned {result.num_rows} grouped rows")


def test_get_architecture_pattern_large():
    """Larger test - closer to real codebase size.

    - 500 modules
    - 5 classes per module = 2500 classes
    - 10 functions per module = 5000 functions
    - 20 imports per module = 10000 imports
    Cartesian: 500 * 5 * 10 * 20 = 500,000 rows before aggregation
    """
    reasoner = Reter("ai")

    all_facts = []
    num_modules = 500
    classes_per_module = 5
    functions_per_module = 10
    imports_per_module = 20

    for i in range(num_modules):
        module_id = f"module{i}"
        file_path = f"src/file{i}.py"

        all_facts.append(f'Module({module_id})')
        all_facts.append(f'inFile({module_id}, "{file_path}")')

        for c in range(classes_per_module):
            class_id = f"class{i}x{c}"
            all_facts.append(f'Class({class_id})')
            all_facts.append(f'inFile({class_id}, "{file_path}")')

        for f in range(functions_per_module):
            func_id = f"func{i}x{f}"
            all_facts.append(f'Func({func_id})')
            all_facts.append(f'inFile({func_id}, "{file_path}")')

        for imp in range(imports_per_module):
            import_id = f"import{i}x{imp}"
            all_facts.append(f'imports({module_id}, {import_id})')

    reasoner.load_ontology("\n".join(all_facts), "test.architecture.large")

    query = """
    SELECT ?file (COUNT(?class) AS ?class_count) (COUNT(?func) AS ?function_count) (COUNT(?import) AS ?import_count)
    WHERE {
        ?m type Module .
        ?m inFile ?file .
        OPTIONAL { ?class type Class . ?class inFile ?file }
        OPTIONAL { ?func type Func . ?func inFile ?file }
        OPTIONAL { ?m imports ?import }
    }
    GROUP BY ?file
    ORDER BY ?file
    """

    print(f"\nget_architecture LARGE pattern test:")
    print(f"  {num_modules} modules, {classes_per_module} classes/module, "
          f"{functions_per_module} functions/module, {imports_per_module} imports/module")
    expected_cartesian = num_modules * classes_per_module * functions_per_module * imports_per_module
    print(f"  Expected Cartesian before aggregation: {expected_cartesian} rows")

    start = time.time()
    result = reasoner.reql(query, timeout_ms=120000)  # 2 minute timeout for large test
    elapsed = time.time() - start

    print(f"  Result: {result.num_rows} rows in {elapsed:.3f}s")
    assert result.num_rows == num_modules, f"Expected {num_modules} rows, got {result.num_rows}"
    print(f"  SUCCESS: Query returned {result.num_rows} grouped rows")


if __name__ == "__main__":
    print("=" * 60)
    print("OPTIONAL Query Blowup Tests")
    print("=" * 60)

    print("\n--- Small Test (60 rows) ---")
    test_optional_blowup_small()

    print("\n--- Medium Test (5,000 rows) ---")
    test_optional_blowup_medium()

    print("\n--- 3-OPTIONAL Test (7,500 rows) ---")
    test_optional_blowup_three_optionals()

    print("\n--- Workaround Test ---")
    test_workaround_separate_queries()

    print("\n--- Threshold Test (30,000 rows) ---")
    test_optional_blowup_at_threshold()

    print("\n--- Crash Test (35,000 rows) ---")
    print("WARNING: This test will likely cause a segfault!")
    try:
        test_optional_blowup_crash()
    except Exception as e:
        print(f"Test failed as expected: {e}")

    print("\n" + "=" * 60)
    print("Tests complete")
