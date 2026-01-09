"""Test to isolate OOM crash with OPTIONAL queries on methods."""
from reter import Reter


def test_cpp_duplicates_detail():
    """Show detailed info about C++ duplicates."""
    snapshot_path = r"D:\ROOT\codeine_root\.codeine\.default.reter"

    reasoner = Reter()
    success = reasoner.network.load(snapshot_path)
    if not success:
        print(f"Failed to load snapshot")
        return

    print("Checking C++ method duplicates in detail...\n")

    # Get all C++ methods with their files
    query = """
    SELECT ?m ?name ?file ?line
    WHERE {
        ?m concept "cpp:Method" .
        ?m name ?name .
        ?m inFile ?file .
        ?m atLine ?line
    }
    """

    result = reasoner.reql(query)
    print(f"Total cpp:Method entities: {result.num_rows}")

    if result.num_rows > 0:
        methods = result.column('?m').to_pylist()
        names = result.column('?name').to_pylist()
        files = result.column('?file').to_pylist()
        lines = result.column('?line').to_pylist()

        from collections import Counter
        counts = Counter(methods)
        duplicates = [(k, v) for k, v in counts.items() if v > 1]

        print(f"\nFound {len(duplicates)} duplicate method IDs:")
        for entity_id, count in duplicates[:10]:
            print(f"\n  {entity_id}: {count}x")
            # Find all occurrences
            for i, m in enumerate(methods):
                if m == entity_id:
                    print(f"    - File: {files[i]}, Line: {lines[i]}, Name: {names[i]}")


if __name__ == "__main__":
    test_cpp_duplicates_detail()
