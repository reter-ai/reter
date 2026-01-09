"""Test to isolate get_architecture.cadsl crash.

This test loads actual Python files (like Codeine does) and runs the
same query pattern that crashes Codeine's MCP server.
"""
import pytest
import time
import os
from pathlib import Path
from reter import Reter


def test_get_architecture_with_real_files():
    """Load real Python files and run get_architecture query pattern."""
    reasoner = Reter("ai")

    # Load some real Python files from the codeine codebase
    codeine_src = Path("D:/ROOT/codeine_root/codeine/src/codeine")

    files_loaded = 0
    for py_file in codeine_src.rglob("*.py"):
        if files_loaded >= 50:  # Start with 50 files
            break
        try:
            reasoner.load_python_file(str(py_file))
            files_loaded += 1
            print(f"Loaded: {py_file.name}")
        except Exception as e:
            print(f"Failed to load {py_file}: {e}")

    print(f"\nLoaded {files_loaded} Python files")

    # Run the exact query pattern from get_architecture.cadsl
    # Using py: prefix for Python files
    query = """
    SELECT ?file (COUNT(?class) AS ?class_count) (COUNT(?func) AS ?function_count) (COUNT(?import) AS ?import_count)
    WHERE {
        ?m type py:Module .
        ?m inFile ?file .
        OPTIONAL { ?class type py:Class . ?class inFile ?file }
        OPTIONAL { ?func type py:Function . ?func inFile ?file }
        OPTIONAL { ?m imports ?import }
    }
    GROUP BY ?file
    ORDER BY ?file
    """

    print("\nRunning get_architecture query pattern...")
    start = time.time()
    result = reasoner.reql(query, timeout_ms=60000)
    elapsed = time.time() - start

    print(f"Result: {result.num_rows} rows in {elapsed:.3f}s")
    assert result.num_rows > 0, "Expected some results"
    print("SUCCESS!")


def test_get_architecture_with_many_files():
    """Load many real Python files - closer to full Codeine scale."""
    reasoner = Reter("ai")

    # Load Python files from multiple directories
    paths = [
        Path("D:/ROOT/codeine_root/codeine/src/codeine"),
        Path("D:/ROOT/codeine_root/reter/src/reter"),
        Path("D:/ROOT/codeine_root/reter/tests"),
    ]

    files_loaded = 0
    for base_path in paths:
        if not base_path.exists():
            continue
        for py_file in base_path.rglob("*.py"):
            try:
                reasoner.load_python_file(str(py_file))
                files_loaded += 1
            except Exception as e:
                pass  # Skip files that fail to load

    print(f"\nLoaded {files_loaded} Python files")

    # Run the query
    query = """
    SELECT ?file (COUNT(?class) AS ?class_count) (COUNT(?func) AS ?function_count) (COUNT(?import) AS ?import_count)
    WHERE {
        ?m type py:Module .
        ?m inFile ?file .
        OPTIONAL { ?class type py:Class . ?class inFile ?file }
        OPTIONAL { ?func type py:Function . ?func inFile ?file }
        OPTIONAL { ?m imports ?import }
    }
    GROUP BY ?file
    ORDER BY ?file
    """

    print("\nRunning get_architecture query on large dataset...")
    start = time.time()
    result = reasoner.reql(query, timeout_ms=120000)
    elapsed = time.time() - start

    print(f"Result: {result.num_rows} rows in {elapsed:.3f}s")
    assert result.num_rows > 0
    print("SUCCESS!")


def test_get_architecture_oo_prefix():
    """Test with oo: prefix (language-agnostic) like Codeine uses."""
    reasoner = Reter("ai")

    # Load Python files
    codeine_src = Path("D:/ROOT/codeine_root/codeine/src/codeine")
    files_loaded = 0
    for py_file in codeine_src.rglob("*.py"):
        if files_loaded >= 30:
            break
        try:
            reasoner.load_python_file(str(py_file))
            files_loaded += 1
        except:
            pass

    print(f"\nLoaded {files_loaded} files")

    # Use oo: prefix like Codeine does after placeholder resolution
    query = """
    SELECT ?file (COUNT(?class) AS ?class_count) (COUNT(?func) AS ?function_count) (COUNT(?import) AS ?import_count)
    WHERE {
        ?m type oo:Module .
        ?m inFile ?file .
        OPTIONAL { ?class type oo:Class . ?class inFile ?file }
        OPTIONAL { ?func type oo:Function . ?func inFile ?file }
        OPTIONAL { ?m imports ?import }
    }
    GROUP BY ?file
    ORDER BY ?file
    """

    print("\nRunning with oo: prefix...")
    start = time.time()
    result = reasoner.reql(query, timeout_ms=60000)
    elapsed = time.time() - start

    print(f"Result: {result.num_rows} rows in {elapsed:.3f}s")
    # May be 0 if oo: types don't exist in Python-loaded data
    print(f"SUCCESS with {result.num_rows} rows")


def test_get_architecture_full_scale():
    """Full scale test - load ALL files like Codeine does."""
    reasoner = Reter("ai")

    # Load from all source directories
    base = Path("D:/ROOT/codeine_root")

    # Python files
    py_count = 0
    for py_file in base.rglob("*.py"):
        # Skip test files and __pycache__
        if "__pycache__" in str(py_file):
            continue
        if "site-packages" in str(py_file):
            continue
        try:
            reasoner.load_python_file(str(py_file))
            py_count += 1
        except:
            pass

    print(f"\nLoaded {py_count} Python files")

    # The query
    query = """
    SELECT ?file (COUNT(?class) AS ?class_count) (COUNT(?func) AS ?function_count) (COUNT(?import) AS ?import_count)
    WHERE {
        ?m type py:Module .
        ?m inFile ?file .
        OPTIONAL { ?class type py:Class . ?class inFile ?file }
        OPTIONAL { ?func type py:Function . ?func inFile ?file }
        OPTIONAL { ?m imports ?import }
    }
    GROUP BY ?file
    ORDER BY ?file
    """

    print("\nRunning FULL SCALE get_architecture query...")
    print("This may take a while or crash - that's what we're testing!")

    start = time.time()
    result = reasoner.reql(query, timeout_ms=180000)
    elapsed = time.time() - start

    print(f"Result: {result.num_rows} rows in {elapsed:.3f}s")
    print("SUCCESS - NO CRASH!")


@pytest.mark.skip(reason="C++ parser crashes with access violation on some files - needs native debugging")
def test_get_architecture_multi_language():
    """Test with Python AND C++ files - like real Codeine."""
    reasoner = Reter("ai")

    base = Path("D:/ROOT/codeine_root")

    # Python files
    py_count = 0
    for py_file in (base / "codeine" / "src").rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        try:
            reasoner.load_python_file(str(py_file))
            py_count += 1
        except:
            pass

    print(f"Loaded {py_count} Python files")

    # C++ files
    cpp_count = 0
    for cpp_file in (base / "reter_core" / "rete_cpp").rglob("*.cpp"):
        try:
            reasoner.load_cpp_file(str(cpp_file))
            cpp_count += 1
        except:
            pass

    for h_file in (base / "reter_core" / "rete_cpp").rglob("*.h"):
        try:
            reasoner.load_cpp_file(str(h_file))
            cpp_count += 1
        except:
            pass

    print(f"Loaded {cpp_count} C++ files")
    print(f"Total: {py_count + cpp_count} files")

    # Query with oo: prefix (language-agnostic like Codeine)
    query = """
    SELECT ?file (COUNT(?class) AS ?class_count) (COUNT(?func) AS ?function_count) (COUNT(?import) AS ?import_count)
    WHERE {
        ?m type oo:Module .
        ?m inFile ?file .
        OPTIONAL { ?class type oo:Class . ?class inFile ?file }
        OPTIONAL { ?func type oo:Function . ?func inFile ?file }
        OPTIONAL { ?m imports ?import }
    }
    GROUP BY ?file
    ORDER BY ?file
    """

    print("\nRunning MULTI-LANGUAGE get_architecture query...")
    start = time.time()
    result = reasoner.reql(query, timeout_ms=180000)
    elapsed = time.time() - start

    print(f"Result: {result.num_rows} rows in {elapsed:.3f}s")
    print("SUCCESS - NO CRASH!")


def test_get_architecture_from_codeine_snapshot():
    """Load the actual Codeine snapshot and run get_architecture query.

    This is the most accurate reproduction of the crash scenario.
    """
    snapshot_path = Path("D:/ROOT/codeine_root/.codeine/.default.reter")

    if not snapshot_path.exists():
        pytest.skip(f"Snapshot not found: {snapshot_path}")

    reasoner = Reter("ai")

    print(f"\nLoading Codeine snapshot from {snapshot_path}...")
    start = time.time()
    # Use the raw network's load method (exposed from C++ bindings)
    success = reasoner.network.load(str(snapshot_path))
    load_time = time.time() - start
    if not success:
        pytest.fail(f"Failed to load snapshot from {snapshot_path}")
    print(f"Snapshot loaded in {load_time:.2f}s")

    # The exact query from get_architecture.cadsl with oo: prefix
    query = """
    SELECT ?file (COUNT(?class) AS ?class_count) (COUNT(?func) AS ?function_count) (COUNT(?import) AS ?import_count)
    WHERE {
        ?m type oo:Module .
        ?m inFile ?file .
        OPTIONAL { ?class type oo:Class . ?class inFile ?file }
        OPTIONAL { ?func type oo:Function . ?func inFile ?file }
        OPTIONAL { ?m imports ?import }
    }
    GROUP BY ?file
    ORDER BY ?file
    """

    print("\nRunning get_architecture query on Codeine snapshot...")
    print("This should reproduce the crash if it's in RETER!")

    start = time.time()
    result = reasoner.reql(query, timeout_ms=180000)
    elapsed = time.time() - start

    print(f"Result: {result.num_rows} rows in {elapsed:.3f}s")
    print("SUCCESS - NO CRASH!")


def test_get_architecture_snapshot_with_timeout():
    """Same as above but with timeout_ms > 0 (uses different code path)."""
    snapshot_path = Path("D:/ROOT/codeine_root/.codeine/.default.reter")

    if not snapshot_path.exists():
        pytest.skip(f"Snapshot not found: {snapshot_path}")

    reasoner = Reter("ai")

    print(f"\nLoading Codeine snapshot...")
    success = reasoner.network.load(str(snapshot_path))
    if not success:
        pytest.fail(f"Failed to load snapshot from {snapshot_path}")
    print("Snapshot loaded successfully")

    query = """
    SELECT ?file (COUNT(?class) AS ?class_count) (COUNT(?func) AS ?function_count) (COUNT(?import) AS ?import_count)
    WHERE {
        ?m type oo:Module .
        ?m inFile ?file .
        OPTIONAL { ?class type oo:Class . ?class inFile ?file }
        OPTIONAL { ?func type oo:Function . ?func inFile ?file }
        OPTIONAL { ?m imports ?import }
    }
    GROUP BY ?file
    ORDER BY ?file
    """

    # Test with timeout_ms=0 (no timeout thread)
    print("\nTest 1: timeout_ms=0...")
    result = reasoner.reql(query, timeout_ms=0)
    print(f"  Result: {result.num_rows} rows - OK")

    # Test with timeout_ms>0 (uses TimeoutQueryExecutor)
    print("\nTest 2: timeout_ms=60000...")
    result = reasoner.reql(query, timeout_ms=60000)
    print(f"  Result: {result.num_rows} rows - OK")

    print("\nSUCCESS - Both code paths work!")


if __name__ == "__main__":
    print("=" * 60)
    print("get_architecture Crash Isolation Tests")
    print("=" * 60)

    print("\n--- Test 1: Small set (50 files) ---")
    test_get_architecture_with_real_files()

    print("\n--- Test 2: Medium set (multiple dirs) ---")
    test_get_architecture_with_many_files()

    print("\n--- Test 3: oo: prefix ---")
    test_get_architecture_oo_prefix()

    print("\n--- Test 4: FULL SCALE ---")
    test_get_architecture_full_scale()

    print("\n" + "=" * 60)
    print("All tests passed!")
