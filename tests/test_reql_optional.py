"""
Python integration tests for REQL OPTIONAL pattern support

Tests the OPTIONAL graph pattern functionality using Acero LEFT_OUTER join.
OPTIONAL patterns should add columns without filtering out base results.
"""

import pytest
from reter import Reter


def test_optional_basic():
    """Test basic OPTIONAL pattern with left-join semantics"""
    reter = Reter("ai")

    # Load test data: some persons have email, some don't
    reter.load_ontology("""
Person(Alice)
Person(Bob)
Person(Charlie)
hasEmail(Alice, 'alice@example.com')
hasEmail(Charlie, 'charlie@example.com')
    """, "test.optional.basic")

    # Query with OPTIONAL - should return all persons, with email where available
    result = reter.reql("""
        SELECT ?person ?email WHERE {
            ?person type Person .
            OPTIONAL { ?person hasEmail ?email }
        }
    """)

    # Should return all 3 persons
    assert result.num_rows == 3

    df = result.to_pandas()
    persons = set(df['?person'])
    assert persons == {'Alice', 'Bob', 'Charlie'}

    # Check that Alice and Charlie have emails, Bob has NULL/None
    alice_row = df[df['?person'] == 'Alice']
    assert alice_row['?email'].iloc[0] == 'alice@example.com'

    charlie_row = df[df['?person'] == 'Charlie']
    assert charlie_row['?email'].iloc[0] == 'charlie@example.com'

    bob_row = df[df['?person'] == 'Bob']
    # NULL values from Arrow show as None in pandas
    assert bob_row['?email'].iloc[0] is None or str(bob_row['?email'].iloc[0]) == 'nan'


def test_optional_multiple_patterns():
    """Test multiple OPTIONAL patterns in same query"""
    reter = Reter("ai")

    # Load test data
    reter.load_ontology("""
Person(Alice)
Person(Bob)
Person(Charlie)
hasEmail(Alice, 'alice@example.com')
hasPhone(Bob, '555-1234')
hasEmail(Charlie, 'charlie@example.com')
hasPhone(Charlie, '555-5678')
    """, "test.optional.multiple")

    # Query with two OPTIONAL patterns
    result = reter.reql("""
        SELECT ?person ?email ?phone WHERE {
            ?person type Person .
            OPTIONAL { ?person hasEmail ?email }
            OPTIONAL { ?person hasPhone ?phone }
        }
    """)

    # Should return all 3 persons
    assert result.num_rows == 3

    df = result.to_pandas()

    # Alice: has email, no phone
    alice_row = df[df['?person'] == 'Alice']
    assert alice_row['?email'].iloc[0] == 'alice@example.com'
    assert alice_row['?phone'].iloc[0] is None or str(alice_row['?phone'].iloc[0]) == 'nan'

    # Bob: no email, has phone
    bob_row = df[df['?person'] == 'Bob']
    assert bob_row['?email'].iloc[0] is None or str(bob_row['?email'].iloc[0]) == 'nan'
    assert bob_row['?phone'].iloc[0] == '555-1234'

    # Charlie: has both
    charlie_row = df[df['?person'] == 'Charlie']
    assert charlie_row['?email'].iloc[0] == 'charlie@example.com'
    assert charlie_row['?phone'].iloc[0] == '555-5678'


def test_optional_with_filter():
    """Test OPTIONAL combined with FILTER"""
    reter = Reter("ai")

    # Load test data
    reter.load_ontology("""
Person(Alice)
Person(Bob)
Person(Charlie)
age(Alice, 25)
age(Bob, 30)
age(Charlie, 18)
hasEmail(Alice, 'alice@example.com')
hasEmail(Bob, 'bob@example.com')
    """, "test.optional.filter")

    # Query: adults (age > 21) with optional email
    result = reter.reql("""
        SELECT ?person ?age ?email WHERE {
            ?person age ?age .
            FILTER(?age > 21)
            OPTIONAL { ?person hasEmail ?email }
        }
    """)

    # Should return Alice and Bob only (adults)
    assert result.num_rows == 2

    df = result.to_pandas()
    persons = set(df['?person'])
    assert persons == {'Alice', 'Bob'}

    # Both should have their ages and emails
    alice_row = df[df['?person'] == 'Alice']
    assert int(alice_row['?age'].iloc[0]) == 25
    assert alice_row['?email'].iloc[0] == 'alice@example.com'

    bob_row = df[df['?person'] == 'Bob']
    assert int(bob_row['?age'].iloc[0]) == 30
    assert bob_row['?email'].iloc[0] == 'bob@example.com'


def test_optional_nested_pattern():
    """Test OPTIONAL with multiple triples in the optional pattern"""
    reter = Reter("ai")

    # Load test data
    reter.load_ontology("""
Person(Alice)
Person(Bob)
Organization(ACME)
Organization(TechCorp)
worksAt(Alice, ACME)
orgEmail(ACME, 'contact@acme.com')
worksAt(Bob, TechCorp)
    """, "test.optional.nested")

    # Query: persons with optional work info (both org and org email)
    result = reter.reql("""
        SELECT ?person ?org ?orgEmail WHERE {
            ?person type Person .
            OPTIONAL {
                ?person worksAt ?org .
                ?org orgEmail ?orgEmail
            }
        }
    """)

    df = result.to_pandas()

    # Alice: has org and org email
    alice_row = df[df['?person'] == 'Alice']
    assert len(alice_row) == 1
    assert alice_row['?org'].iloc[0] == 'ACME'
    assert alice_row['?orgEmail'].iloc[0] == 'contact@acme.com'

    # Bob: has org but no org email, so entire OPTIONAL doesn't match
    bob_row = df[df['?person'] == 'Bob']
    assert len(bob_row) == 1
    # Since the OPTIONAL pattern requires BOTH triples and one is missing,
    # the entire pattern fails and we get NULLs
    assert bob_row['?org'].iloc[0] is None or str(bob_row['?org'].iloc[0]) == 'nan'
    assert bob_row['?orgEmail'].iloc[0] is None or str(bob_row['?orgEmail'].iloc[0]) == 'nan'


def test_optional_with_union():
    """Test OPTIONAL combined with UNION"""
    reter = Reter("ai")

    # Load test data
    reter.load_ontology("""
Person(Alice)
Person(Bob)
Student(Charlie)
hasEmail(Alice, 'alice@example.com')
hasEmail(Charlie, 'charlie@example.com')
    """, "test.optional.union")

    # Query: Person OR Student, with optional email
    result = reter.reql("""
        SELECT ?entity ?email WHERE {
            {
                ?entity type Person
            } UNION {
                ?entity type Student
            }
            OPTIONAL { ?entity hasEmail ?email }
        }
    """)

    # Should return all 3: Alice, Bob, Charlie
    assert result.num_rows == 3

    df = result.to_pandas()
    entities = set(df['?entity'])
    assert entities == {'Alice', 'Bob', 'Charlie'}

    # Alice and Charlie have emails
    alice_row = df[df['?entity'] == 'Alice']
    assert alice_row['?email'].iloc[0] == 'alice@example.com'

    charlie_row = df[df['?entity'] == 'Charlie']
    assert charlie_row['?email'].iloc[0] == 'charlie@example.com'

    # Bob has NULL
    bob_row = df[df['?entity'] == 'Bob']
    assert bob_row['?email'].iloc[0] is None or str(bob_row['?email'].iloc[0]) == 'nan'


def test_optional_distinct():
    """Test OPTIONAL with DISTINCT modifier"""
    reter = Reter("ai")

    # Load test data (duplicate relationships)
    reter.load_ontology("""
Person(Alice)
hasEmail(Alice, 'alice@example.com')
hasEmail(Alice, 'alice@example.com')
    """, "test.optional.distinct")

    # Query with DISTINCT
    result = reter.reql("""
        SELECT DISTINCT ?person ?email WHERE {
            ?person type Person .
            OPTIONAL { ?person hasEmail ?email }
        }
    """)

    # Should have only 1 row (deduplication)
    assert result.num_rows == 1

    df = result.to_pandas()
    assert df['?person'].iloc[0] == 'Alice'
    assert df['?email'].iloc[0] == 'alice@example.com'


def test_optional_order_by():
    """Test OPTIONAL with ORDER BY"""
    reter = Reter("ai")

    # Load test data
    reter.load_ontology("""
Person(Alice)
Person(Bob)
Person(Charlie)
age(Alice, 30)
age(Bob, 25)
age(Charlie, 35)
hasEmail(Bob, 'bob@example.com')
    """, "test.optional.orderby")

    # Query ordered by age
    result = reter.reql("""
        SELECT ?person ?age ?email WHERE {
            ?person age ?age .
            OPTIONAL { ?person hasEmail ?email }
        }
        ORDER BY ?age
    """)

    assert result.num_rows == 3

    df = result.to_pandas()

    # Should be ordered: Bob (25), Alice (30), Charlie (35)
    ages = [int(age) for age in df['?age']]
    assert ages == [25, 30, 35]

    persons = list(df['?person'])
    assert persons == ['Bob', 'Alice', 'Charlie']

    # Only Bob has email
    assert df['?email'].iloc[0] == 'bob@example.com'
    assert df['?email'].iloc[1] is None or str(df['?email'].iloc[1]) == 'nan'
    assert df['?email'].iloc[2] is None or str(df['?email'].iloc[2]) == 'nan'


def test_optional_limit():
    """Test OPTIONAL with LIMIT"""
    reter = Reter("ai")

    # Load test data
    reter.load_ontology("""
Person(Alice)
Person(Bob)
Person(Charlie)
hasEmail(Alice, 'alice@example.com')
    """, "test.optional.limit")

    # Query with LIMIT
    result = reter.reql("""
        SELECT ?person ?email WHERE {
            ?person type Person .
            OPTIONAL { ?person hasEmail ?email }
        }
        LIMIT 2
    """)

    # Should return only 2 results
    assert result.num_rows == 2


def test_optional_empty_result():
    """Test OPTIONAL when optional pattern never matches"""
    reter = Reter("ai")

    # Load test data: persons exist but no emails at all
    reter.load_ontology("""
Person(Alice)
Person(Bob)
    """, "test.optional.empty")

    # Query with OPTIONAL that never matches
    result = reter.reql("""
        SELECT ?person ?email WHERE {
            ?person type Person .
            OPTIONAL { ?person hasEmail ?email }
        }
    """)

    # Should still return all persons with NULL emails
    assert result.num_rows == 2

    df = result.to_pandas()
    persons = set(df['?person'])
    assert persons == {'Alice', 'Bob'}

    # Both should have NULL emails
    for _, row in df.iterrows():
        assert row['?email'] is None or str(row['?email']) == 'nan'


def test_optional_large_string_concatenation():
    """Test OPTIONAL pattern with many rows and long strings.

    This test exercises the fix for Arrow string offset overflow (>2GB).
    When concatenating string columns with many rows/large data, Arrow's
    regular 'string' type can overflow. The fix casts to 'large_string'
    before concatenation.

    While this test can't trigger the actual 2GB limit without massive
    memory usage, it validates the code path with many rows and long
    strings to ensure the fix is working correctly.

    Regression test for: "offset overflow while concatenating arrays,
    consider casting input from `string` to `large_string` first"
    """
    reter = Reter("ai")

    # Generate many individuals with long string values
    # This helps create multi-chunk Arrow arrays internally
    ontology_parts = []
    num_entities = 500  # Use enough entities to potentially trigger multi-chunk behavior

    for i in range(num_entities):
        # Create entity with long name
        entity = f"Entity_{i:04d}"
        ontology_parts.append(f"Person({entity})")

        # Only half have email (to test OPTIONAL NULL handling)
        if i % 2 == 0:
            # Use a long string value to increase data size
            long_email = f"{'x' * 100}.email_{i:04d}@{'y' * 50}.example.com"
            ontology_parts.append(f"hasEmail({entity}, '{long_email}')")

    reter.load_ontology("\n".join(ontology_parts), "test.optional.large_strings")

    # Query with OPTIONAL - exercises the multi-chunk concatenation code path
    result = reter.reql("""
        SELECT ?person ?email WHERE {
            ?person type Person .
            OPTIONAL { ?person hasEmail ?email }
        }
    """)

    # Should return all entities
    assert result.num_rows == num_entities

    df = result.to_pandas()

    # Verify all entities are returned
    assert len(df) == num_entities

    # Verify entities with even index have email, odd index have NULL
    for i in range(min(10, num_entities)):  # Check a sample
        entity = f"Entity_{i:04d}"
        row = df[df['?person'] == entity]
        assert len(row) == 1

        if i % 2 == 0:
            # Should have email
            assert row['?email'].iloc[0] is not None
            assert 'email_' in str(row['?email'].iloc[0])
        else:
            # Should be NULL
            assert row['?email'].iloc[0] is None or str(row['?email'].iloc[0]) == 'nan'


def test_union_large_string_concatenation():
    """Test UNION with many rows to exercise safe_concatenate_tables.

    This test verifies the fix for string offset overflow when
    concatenating multiple UNION result tables.
    """
    reter = Reter("ai")

    # Create two sets of entities
    ontology_parts = []
    num_entities_per_type = 200

    for i in range(num_entities_per_type):
        # Type A entities
        entity_a = f"TypeA_{i:04d}"
        ontology_parts.append(f"TypeA({entity_a})")
        # Long description
        long_desc = f"Description_{'a' * 100}_{i:04d}"
        ontology_parts.append(f"hasDescription({entity_a}, '{long_desc}')")

        # Type B entities
        entity_b = f"TypeB_{i:04d}"
        ontology_parts.append(f"TypeB({entity_b})")
        long_desc = f"Description_{'b' * 100}_{i:04d}"
        ontology_parts.append(f"hasDescription({entity_b}, '{long_desc}')")

    reter.load_ontology("\n".join(ontology_parts), "test.union.large_strings")

    # UNION query - exercises the safe_concatenate_tables code path
    result = reter.reql("""
        SELECT ?entity ?desc WHERE {
            {
                ?entity type TypeA .
                ?entity hasDescription ?desc
            } UNION {
                ?entity type TypeB .
                ?entity hasDescription ?desc
            }
        }
    """)

    # Should return all entities from both types
    expected_total = num_entities_per_type * 2
    assert result.num_rows == expected_total

    df = result.to_pandas()

    # Verify we have entities from both types
    type_a_count = len([e for e in df['?entity'] if str(e).startswith('TypeA_')])
    type_b_count = len([e for e in df['?entity'] if str(e).startswith('TypeB_')])

    assert type_a_count == num_entities_per_type
    assert type_b_count == num_entities_per_type


def test_optional_multiple_with_group_by_count():
    """Test multiple OPTIONAL patterns with GROUP BY and COUNT.

    This is a regression test for a bug where multiple OPTIONAL clauses
    combined with GROUP BY and COUNT produce incorrect results due to
    cross-product behavior.

    Expected: Each COUNT should count its own OPTIONAL pattern independently.
    Bug behavior: Counts become identical (field_count × method_count).

    Example with the bug:
    - Class with 35 fields and 51 methods
    - Expected: attr_count=35, method_count=51
    - Bug result: attr_count=1785, method_count=1785 (35 × 51 cross-product)
    """
    reter = Reter("ai")

    # Load test data: a class with specific counts of fields and methods
    reter.load_ontology("""
Class(MyDataClass)
name(MyDataClass, 'MyDataClass')

# 3 fields
Field(field1)
Field(field2)
Field(field3)
definedIn(field1, MyDataClass)
definedIn(field2, MyDataClass)
definedIn(field3, MyDataClass)

# 5 methods
Method(method1)
Method(method2)
Method(method3)
Method(method4)
Method(method5)
definedIn(method1, MyDataClass)
definedIn(method2, MyDataClass)
definedIn(method3, MyDataClass)
definedIn(method4, MyDataClass)
definedIn(method5, MyDataClass)
    """, "test.optional.groupby.count")

    # Query with two OPTIONAL patterns and COUNT aggregation
    result = reter.reql("""
        SELECT ?c ?name (COUNT(?attr) AS ?attr_count) (COUNT(?method) AS ?method_count)
        WHERE {
            ?c type Class .
            ?c name ?name .
            OPTIONAL { ?attr type Field . ?attr definedIn ?c }
            OPTIONAL { ?method type Method . ?method definedIn ?c }
        }
        GROUP BY ?c ?name
    """)

    assert result.num_rows == 1, f"Expected 1 row, got {result.num_rows}"

    df = result.to_pandas()
    row = df.iloc[0]

    attr_count = int(row['?attr_count'])
    method_count = int(row['?method_count'])

    # The bug would show attr_count=15 and method_count=15 (3 × 5 cross-product)
    # Correct behavior: attr_count=3, method_count=5
    assert attr_count == 3, f"Expected attr_count=3, got {attr_count} (cross-product bug if 15)"
    assert method_count == 5, f"Expected method_count=5, got {method_count} (cross-product bug if 15)"


def test_optional_multiple_with_group_by_count_null_handling():
    """Test multiple OPTIONAL with GROUP BY/COUNT when some OPTIONALs are empty.

    Ensures that empty OPTIONAL patterns produce count=0, not incorrect values.
    """
    reter = Reter("ai")

    # Load test data: one class with fields but no methods, another with neither
    reter.load_ontology("""
Class(DataOnlyClass)
name(DataOnlyClass, 'DataOnlyClass')
Field(data_field1)
Field(data_field2)
definedIn(data_field1, DataOnlyClass)
definedIn(data_field2, DataOnlyClass)

Class(EmptyClass)
name(EmptyClass, 'EmptyClass')
    """, "test.optional.groupby.null")

    result = reter.reql("""
        SELECT ?c ?name (COUNT(?attr) AS ?attr_count) (COUNT(?method) AS ?method_count)
        WHERE {
            ?c type Class .
            ?c name ?name .
            OPTIONAL { ?attr type Field . ?attr definedIn ?c }
            OPTIONAL { ?method type Method . ?method definedIn ?c }
        }
        GROUP BY ?c ?name
        ORDER BY ?name
    """)

    assert result.num_rows == 2, f"Expected 2 rows, got {result.num_rows}"

    df = result.to_pandas()

    # DataOnlyClass: 2 fields, 0 methods
    data_only = df[df['?name'] == 'DataOnlyClass'].iloc[0]
    assert int(data_only['?attr_count']) == 2, f"DataOnlyClass attr_count should be 2"
    assert int(data_only['?method_count']) == 0, f"DataOnlyClass method_count should be 0"

    # EmptyClass: 0 fields, 0 methods
    empty = df[df['?name'] == 'EmptyClass'].iloc[0]
    assert int(empty['?attr_count']) == 0, f"EmptyClass attr_count should be 0"
    assert int(empty['?method_count']) == 0, f"EmptyClass method_count should be 0"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
