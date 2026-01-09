"""
Test entity deduplication feature with EntityAccumulator.

This test verifies that entities appearing in multiple files
are merged into a single entity with combined attributes.
"""

import pytest
from reter_core import owl_rete_cpp as owl


def test_entity_accumulation_basic():
    """Test basic entity accumulation API."""
    network = owl.ReteNetwork()

    # Start accumulation mode
    network.begin_entity_accumulation()
    assert network.is_entity_accumulation_active() == True

    # End accumulation mode
    network.end_entity_accumulation()
    assert network.is_entity_accumulation_active() == False


def test_cpp_deduplication_same_entities():
    """Test that entities defined in multiple files are merged."""
    # Test with two header files that both declare the same class
    header1 = '''
class MyClass {
public:
    int add(int a, int b);
};
'''

    header2 = '''
class MyClass {
public:
    int add(int a, int b);
};
'''

    # WITH accumulation
    network_with = owl.ReteNetwork()
    network_with.begin_entity_accumulation()
    owl.load_cpp_from_string(network_with, header1, 'header1.h', 'header1.h')
    owl.load_cpp_from_string(network_with, header2, 'header2.h', 'header2.h')
    print(f"Accumulated: {network_with.accumulated_entity_count()} entities")
    network_with.end_entity_accumulation()

    table_with = network_with.query({'type': 'instance_of', 'concept': 'cpp:Method'})
    print(f"Methods WITH accumulation: {table_with.num_rows}")

    # WITHOUT accumulation
    network_without = owl.ReteNetwork()
    owl.load_cpp_from_string(network_without, header1, 'header1.h', 'header1.h')
    owl.load_cpp_from_string(network_without, header2, 'header2.h', 'header2.h')

    table_without = network_without.query({'type': 'instance_of', 'concept': 'cpp:Method'})
    print(f"Methods WITHOUT accumulation: {table_without.num_rows}")

    # WITH accumulation should have merged entities (1)
    # WITHOUT accumulation should have duplicates (2)
    assert table_with.num_rows == 1, f"Expected 1 merged method, got {table_with.num_rows}"
    assert table_without.num_rows == 2, f"Expected 2 duplicate methods, got {table_without.num_rows}"


def test_infile_merge_collect_all():
    """Test that inFile attribute uses COLLECT_ALL strategy."""
    header1 = '''
class MyClass {
    void method();
};
'''
    header2 = '''
class MyClass {
    void method();
};
'''

    network = owl.ReteNetwork()
    network.begin_entity_accumulation()
    owl.load_cpp_from_string(network, header1, 'file1.h', 'file1.h')
    owl.load_cpp_from_string(network, header2, 'file2.h', 'file2.h')
    network.end_entity_accumulation()

    table = network.query({'type': 'instance_of', 'concept': 'cpp:Method'})
    assert table.num_rows == 1, "Should have 1 merged method"

    # Check that inFile contains both files (comma-separated)
    in_file = table.column('inFile')[0].as_py()
    print(f"Merged inFile: {in_file}")
    assert 'file1.h' in in_file, "Should contain file1.h"
    assert 'file2.h' in in_file, "Should contain file2.h"


def test_boolean_flags_merge_or():
    """Test that boolean flags use BOOLEAN_OR strategy."""
    # First file has isVirtual = false
    code1 = '''
class MyClass {
public:
    void method();
};
'''
    # Second file has isVirtual = true
    code2 = '''
class MyClass {
public:
    virtual void method();
};
'''

    network = owl.ReteNetwork()
    network.begin_entity_accumulation()
    owl.load_cpp_from_string(network, code1, 'file1.h', 'file1.h')
    owl.load_cpp_from_string(network, code2, 'file2.h', 'file2.h')
    network.end_entity_accumulation()

    table = network.query({'type': 'instance_of', 'concept': 'cpp:Method'})
    assert table.num_rows == 1, "Should have 1 merged method"

    # isVirtual should be true (BOOLEAN_OR)
    is_virtual = table.column('isVirtual')[0].as_py()
    print(f"Merged isVirtual: {is_virtual}")
    assert is_virtual == 'true', "isVirtual should be true after BOOLEAN_OR merge"


def test_class_deduplication():
    """Test that classes are also deduplicated."""
    header1 = '''
class MyClass {
public:
    int x;
};
'''
    header2 = '''
class MyClass {
public:
    int x;
};
'''

    network = owl.ReteNetwork()
    network.begin_entity_accumulation()
    owl.load_cpp_from_string(network, header1, 'header1.h', 'header1.h')
    owl.load_cpp_from_string(network, header2, 'header2.h', 'header2.h')
    network.end_entity_accumulation()

    table = network.query({'type': 'instance_of', 'concept': 'cpp:Class'})
    print(f"Classes with accumulation: {table.num_rows}")
    assert table.num_rows == 1, "Should have 1 merged class"

    # Check inFile
    in_file = table.column('inFile')[0].as_py()
    print(f"Merged class inFile: {in_file}")
    assert 'header1.h' in in_file and 'header2.h' in in_file


def test_accumulated_entity_count():
    """Test the accumulated_entity_count method."""
    header1 = '''
class Class1 { void m1(); };
class Class2 { void m2(); };
'''
    header2 = '''
class Class1 { void m1(); };
'''

    network = owl.ReteNetwork()
    network.begin_entity_accumulation()
    owl.load_cpp_from_string(network, header1, 'h1.h', 'h1.h')

    # After first file, should have some accumulated entities
    count1 = network.accumulated_entity_count()
    print(f"After first file: {count1} entities")
    assert count1 > 0, "Should have accumulated some entities"

    owl.load_cpp_from_string(network, header2, 'h2.h', 'h2.h')

    # After second file, count should stay same or increase (not decrease)
    count2 = network.accumulated_entity_count()
    print(f"After second file: {count2} entities")
    assert count2 >= count1, "Entity count should not decrease"

    network.end_entity_accumulation()


if __name__ == "__main__":
    print("=" * 60)
    print("Test 1: Basic entity accumulation API")
    print("=" * 60)
    test_entity_accumulation_basic()
    print("PASSED\n")

    print("=" * 60)
    print("Test 2: C++ deduplication of same entities")
    print("=" * 60)
    test_cpp_deduplication_same_entities()
    print("PASSED\n")

    print("=" * 60)
    print("Test 3: inFile merge (COLLECT_ALL strategy)")
    print("=" * 60)
    test_infile_merge_collect_all()
    print("PASSED\n")

    print("=" * 60)
    print("Test 4: Boolean flags merge (BOOLEAN_OR strategy)")
    print("=" * 60)
    test_boolean_flags_merge_or()
    print("PASSED\n")

    print("=" * 60)
    print("Test 5: Class deduplication")
    print("=" * 60)
    test_class_deduplication()
    print("PASSED\n")

    print("=" * 60)
    print("Test 6: Accumulated entity count")
    print("=" * 60)
    test_accumulated_entity_count()
    print("PASSED\n")

    print("=" * 60)
    print("All tests passed!")
    print("=" * 60)
