"""
Test for GROUP BY + ORDER BY + LIMIT bug.

The issue: When using GROUP BY with COUNT and ORDER BY DESC + LIMIT,
the results are incomplete/incorrect compared to using HAVING.

Working query (with HAVING):
    SELECT ?class ?name (COUNT(?method) AS ?method_count) WHERE {
        ?class type oo:Class .
        ?class name ?name .
        ?class hasMethod ?method
    }
    GROUP BY ?class ?name
    HAVING (?method_count > 5)
    ORDER BY DESC(?method_count)

Broken query (with just LIMIT):
    SELECT ?class ?name (COUNT(?method) AS ?method_count) WHERE {
        ?class type oo:Class .
        ?class name ?name .
        ?class hasMethod ?method
    }
    GROUP BY ?class ?name
    ORDER BY DESC(?method_count)
    LIMIT 10
"""

import pytest
from reter_core import ReteNetwork, Fact


def create_fact(fact_type: str, **attrs) -> Fact:
    """Helper to create a Fact with attributes."""
    f = Fact()
    f.set("type", fact_type)
    for key, value in attrs.items():
        f.set(key, str(value))
    return f


def setup_test_data(reter: ReteNetwork):
    """Create test data with classes having different method counts."""
    # Class A: 10 methods
    reter.add_fact(create_fact("instance_of", individual="ClassA", concept="oo:Class"))
    reter.add_fact(create_fact("role_assertion", subject="ClassA", role="name", object="ClassA"))
    for i in range(10):
        method_id = f"ClassA.method{i}"
        reter.add_fact(create_fact("instance_of", individual=method_id, concept="oo:Method"))
        reter.add_fact(create_fact("role_assertion", subject="ClassA", role="hasMethod", object=method_id))

    # Class B: 5 methods
    reter.add_fact(create_fact("instance_of", individual="ClassB", concept="oo:Class"))
    reter.add_fact(create_fact("role_assertion", subject="ClassB", role="name", object="ClassB"))
    for i in range(5):
        method_id = f"ClassB.method{i}"
        reter.add_fact(create_fact("instance_of", individual=method_id, concept="oo:Method"))
        reter.add_fact(create_fact("role_assertion", subject="ClassB", role="hasMethod", object=method_id))

    # Class C: 15 methods
    reter.add_fact(create_fact("instance_of", individual="ClassC", concept="oo:Class"))
    reter.add_fact(create_fact("role_assertion", subject="ClassC", role="name", object="ClassC"))
    for i in range(15):
        method_id = f"ClassC.method{i}"
        reter.add_fact(create_fact("instance_of", individual=method_id, concept="oo:Method"))
        reter.add_fact(create_fact("role_assertion", subject="ClassC", role="hasMethod", object=method_id))

    # Class D: 3 methods
    reter.add_fact(create_fact("instance_of", individual="ClassD", concept="oo:Class"))
    reter.add_fact(create_fact("role_assertion", subject="ClassD", role="name", object="ClassD"))
    for i in range(3):
        method_id = f"ClassD.method{i}"
        reter.add_fact(create_fact("instance_of", individual=method_id, concept="oo:Method"))
        reter.add_fact(create_fact("role_assertion", subject="ClassD", role="hasMethod", object=method_id))

    # Class E: 20 methods (should be first in DESC order)
    reter.add_fact(create_fact("instance_of", individual="ClassE", concept="oo:Class"))
    reter.add_fact(create_fact("role_assertion", subject="ClassE", role="name", object="ClassE"))
    for i in range(20):
        method_id = f"ClassE.method{i}"
        reter.add_fact(create_fact("instance_of", individual=method_id, concept="oo:Method"))
        reter.add_fact(create_fact("role_assertion", subject="ClassE", role="hasMethod", object=method_id))


def test_groupby_count_without_limit():
    """Test GROUP BY with COUNT - no LIMIT (baseline)."""
    reter = ReteNetwork()
    setup_test_data(reter)

    result = reter.reql_query("""
        SELECT ?class ?name (COUNT(?method) AS ?method_count) WHERE {
            ?class type oo:Class .
            ?class name ?name .
            ?class hasMethod ?method
        }
        GROUP BY ?class ?name
        ORDER BY DESC(?method_count)
    """, 30000)

    print(f"\n=== Without LIMIT ===")
    print(f"Rows: {result.num_rows}")
    df = result.to_pandas()
    print(df)

    # Should have 5 classes
    assert result.num_rows == 5, f"Expected 5 rows, got {result.num_rows}"

    # Check order: E(20), C(15), A(10), B(5), D(3)
    counts = df['?method_count'].tolist()
    assert counts == [20, 15, 10, 5, 3], f"Expected [20, 15, 10, 5, 3], got {counts}"


def test_groupby_count_with_limit():
    """Test GROUP BY with COUNT and LIMIT - THIS IS THE BUG."""
    reter = ReteNetwork()
    setup_test_data(reter)

    result = reter.reql_query("""
        SELECT ?class ?name (COUNT(?method) AS ?method_count) WHERE {
            ?class type oo:Class .
            ?class name ?name .
            ?class hasMethod ?method
        }
        GROUP BY ?class ?name
        ORDER BY DESC(?method_count)
        LIMIT 3
    """, 30000)

    print(f"\n=== With LIMIT 3 ===")
    print(f"Rows: {result.num_rows}")
    df = result.to_pandas()
    print(df)

    # Should have top 3: E(20), C(15), A(10)
    assert result.num_rows == 3, f"Expected 3 rows, got {result.num_rows}"

    counts = df['?method_count'].tolist()
    names = df['?name'].tolist()

    # The bug: LIMIT is applied BEFORE aggregation completes
    # So we might get wrong results
    print(f"Names: {names}")
    print(f"Counts: {counts}")

    # Expected: ClassE=20, ClassC=15, ClassA=10
    assert counts[0] == 20, f"First should be 20 (ClassE), got {counts[0]}"
    assert counts[1] == 15, f"Second should be 15 (ClassC), got {counts[1]}"
    assert counts[2] == 10, f"Third should be 10 (ClassA), got {counts[2]}"


def test_groupby_count_with_having():
    """Test GROUP BY with COUNT and HAVING - this works."""
    reter = ReteNetwork()
    setup_test_data(reter)

    result = reter.reql_query("""
        SELECT ?class ?name (COUNT(?method) AS ?method_count) WHERE {
            ?class type oo:Class .
            ?class name ?name .
            ?class hasMethod ?method
        }
        GROUP BY ?class ?name
        HAVING (?method_count > 5)
        ORDER BY DESC(?method_count)
    """, 30000)

    print(f"\n=== With HAVING > 5 ===")
    print(f"Rows: {result.num_rows}")
    df = result.to_pandas()
    print(df)

    # Should have 3 classes with > 5 methods: E(20), C(15), A(10)
    assert result.num_rows == 3, f"Expected 3 rows, got {result.num_rows}"

    counts = df['?method_count'].tolist()
    assert counts == [20, 15, 10], f"Expected [20, 15, 10], got {counts}"


def test_groupby_count_with_having_and_limit():
    """Test GROUP BY with COUNT, HAVING, and LIMIT."""
    reter = ReteNetwork()
    setup_test_data(reter)

    result = reter.reql_query("""
        SELECT ?class ?name (COUNT(?method) AS ?method_count) WHERE {
            ?class type oo:Class .
            ?class name ?name .
            ?class hasMethod ?method
        }
        GROUP BY ?class ?name
        HAVING (?method_count >= 0)
        ORDER BY DESC(?method_count)
        LIMIT 3
    """, 30000)

    print(f"\n=== With HAVING >= 0 and LIMIT 3 ===")
    print(f"Rows: {result.num_rows}")
    df = result.to_pandas()
    print(df)

    # Should have top 3: E(20), C(15), A(10)
    assert result.num_rows == 3, f"Expected 3 rows, got {result.num_rows}"

    counts = df['?method_count'].tolist()
    assert counts[0] == 20, f"First should be 20, got {counts[0]}"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
