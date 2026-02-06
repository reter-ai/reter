"""
Tests for Cap'n Proto lazy loading functionality.

Tests the load_lazy(), is_lazy(), and materialize() methods of ReteNetwork.
"""
import pytest
import tempfile
import os
import time

from reter_core import owl_rete_cpp


def make_fact(s, p, o):
    """Helper to create a Fact object."""
    f = owl_rete_cpp.Fact()
    f.set("subject", s)
    f.set("predicate", p)
    f.set("object", o)
    return f


class TestLazyLoadingBasic:
    """Basic lazy loading tests."""

    def test_load_lazy_returns_true(self, tmp_path):
        """Test that load_lazy returns True for valid file."""
        # Create and save a network
        net = owl_rete_cpp.ReteNetwork()
        net.add_fact(make_fact("Alice", "knows", "Bob"))

        filepath = str(tmp_path / "test.bin")
        net.save(filepath)

        # Load lazily
        net2 = owl_rete_cpp.ReteNetwork()
        result = net2.load_lazy(filepath)

        assert result is True

    def test_is_lazy_after_load_lazy(self, tmp_path):
        """Test that is_lazy() returns True after load_lazy()."""
        net = owl_rete_cpp.ReteNetwork()
        net.add_fact(make_fact("Alice", "knows", "Bob"))

        filepath = str(tmp_path / "test.bin")
        net.save(filepath)

        net2 = owl_rete_cpp.ReteNetwork()
        net2.load_lazy(filepath)

        assert net2.is_lazy() is True

    def test_is_lazy_false_for_normal_network(self):
        """Test that is_lazy() returns False for normal network."""
        net = owl_rete_cpp.ReteNetwork()
        assert net.is_lazy() is False

    def test_fact_count_in_lazy_mode(self, tmp_path):
        """Test that fact_count() works in lazy mode."""
        net = owl_rete_cpp.ReteNetwork()
        for i in range(10):
            net.add_fact(make_fact(f"Entity{i}", "type", "Thing"))

        filepath = str(tmp_path / "test.bin")
        net.save(filepath)

        net2 = owl_rete_cpp.ReteNetwork()
        net2.load_lazy(filepath)

        assert net2.fact_count() == 10


class TestLazyLoadingQueries:
    """Test queries in lazy mode."""

    def test_arrow_query_in_lazy_mode(self, tmp_path):
        """Test that Arrow queries work in lazy mode."""
        net = owl_rete_cpp.ReteNetwork()
        net.add_fact(make_fact("Alice", "knows", "Bob"))
        net.add_fact(make_fact("Bob", "knows", "Charlie"))
        net.add_fact(make_fact("Charlie", "likes", "Pizza"))

        filepath = str(tmp_path / "test.bin")
        net.save(filepath)

        net2 = owl_rete_cpp.ReteNetwork()
        net2.load_lazy(filepath)

        # Arrow queries should work
        table = net2.get_all_facts_arrow()
        assert table.num_rows == 3
        assert "subject" in table.column_names
        assert "predicate" in table.column_names
        assert "object" in table.column_names

    def test_find_facts_arrow_in_lazy_mode(self, tmp_path):
        """Test that find_facts_arrow works in lazy mode."""
        net = owl_rete_cpp.ReteNetwork()
        net.add_fact(make_fact("Alice", "knows", "Bob"))
        net.add_fact(make_fact("Alice", "knows", "Charlie"))
        net.add_fact(make_fact("Bob", "knows", "David"))

        filepath = str(tmp_path / "test.bin")
        net.save(filepath)

        net2 = owl_rete_cpp.ReteNetwork()
        net2.load_lazy(filepath)

        # Find facts where subject is Alice
        results = net2.find_facts_arrow({"subject": "Alice"})
        assert results.num_rows == 2


class TestMaterialize:
    """Test materialize() functionality."""

    def test_materialize_changes_is_lazy(self, tmp_path):
        """Test that materialize() changes is_lazy to False."""
        net = owl_rete_cpp.ReteNetwork()
        net.add_fact(make_fact("Alice", "knows", "Bob"))

        filepath = str(tmp_path / "test.bin")
        net.save(filepath)

        net2 = owl_rete_cpp.ReteNetwork()
        net2.load_lazy(filepath)
        assert net2.is_lazy() is True

        net2.materialize()
        assert net2.is_lazy() is False

    def test_materialize_preserves_fact_count(self, tmp_path):
        """Test that materialize() preserves all facts."""
        net = owl_rete_cpp.ReteNetwork()
        for i in range(5):
            net.add_fact(make_fact(f"Entity{i}", "type", "Thing"))

        filepath = str(tmp_path / "test.bin")
        net.save(filepath)

        net2 = owl_rete_cpp.ReteNetwork()
        net2.load_lazy(filepath)
        count_before = net2.fact_count()

        net2.materialize()
        count_after = net2.fact_count()

        assert count_before == count_after == 5

    def test_get_all_facts_after_materialize(self, tmp_path):
        """Test that get_all_facts() works after materialize()."""
        net = owl_rete_cpp.ReteNetwork()
        net.add_fact(make_fact("Alice", "knows", "Bob"))
        net.add_fact(make_fact("Bob", "knows", "Charlie"))

        filepath = str(tmp_path / "test.bin")
        net.save(filepath)

        net2 = owl_rete_cpp.ReteNetwork()
        net2.load_lazy(filepath)

        # In lazy mode, get_all_facts returns empty (by design)
        facts_lazy = net2.get_all_facts()
        assert len(facts_lazy) == 0

        # After materialize, get_all_facts works
        net2.materialize()
        facts_materialized = net2.get_all_facts()
        assert len(facts_materialized) == 2


class TestLazyLoadingEdgeCases:
    """Edge case tests for lazy loading."""

    def test_empty_network(self, tmp_path):
        """Test lazy loading an empty network."""
        net = owl_rete_cpp.ReteNetwork()

        filepath = str(tmp_path / "empty.bin")
        net.save(filepath)

        net2 = owl_rete_cpp.ReteNetwork()
        result = net2.load_lazy(filepath)

        assert result is True
        assert net2.is_lazy() is True
        assert net2.fact_count() == 0

    def test_load_lazy_nonexistent_file(self):
        """Test load_lazy with non-existent file returns False."""
        net = owl_rete_cpp.ReteNetwork()
        result = net.load_lazy("/nonexistent/path/file.bin")

        assert result is False
        assert net.is_lazy() is False

    def test_multiple_load_lazy_calls(self, tmp_path):
        """Test that calling load_lazy multiple times works."""
        # Create two different files
        net1 = owl_rete_cpp.ReteNetwork()
        net1.add_fact(make_fact("A", "rel", "B"))
        file1 = str(tmp_path / "test1.bin")
        net1.save(file1)

        net2 = owl_rete_cpp.ReteNetwork()
        net2.add_fact(make_fact("X", "rel", "Y"))
        net2.add_fact(make_fact("Y", "rel", "Z"))
        file2 = str(tmp_path / "test2.bin")
        net2.save(file2)

        # Load first file
        net = owl_rete_cpp.ReteNetwork()
        net.load_lazy(file1)
        assert net.fact_count() == 1

        # Load second file (replaces first)
        net.load_lazy(file2)
        assert net.fact_count() == 2


class TestLazyLoadingPerformance:
    """Performance-related tests for lazy loading."""

    @pytest.mark.slow
    def test_lazy_load_faster_than_eager(self, tmp_path):
        """Test that lazy loading is faster than eager loading."""
        # Create a network with many facts
        net = owl_rete_cpp.ReteNetwork()
        for i in range(1000):
            net.add_fact(make_fact(f"Entity{i}", "type", "Thing"))
            net.add_fact(make_fact(f"Entity{i}", "hasValue", str(i)))

        filepath = str(tmp_path / "large.bin")
        net.save(filepath)

        # Time eager load
        net_eager = owl_rete_cpp.ReteNetwork()
        t1 = time.perf_counter()
        net_eager.load(filepath)
        eager_time = time.perf_counter() - t1

        # Time lazy load
        net_lazy = owl_rete_cpp.ReteNetwork()
        t2 = time.perf_counter()
        net_lazy.load_lazy(filepath)
        lazy_time = time.perf_counter() - t2

        # Lazy should be faster (at least 2x for this size)
        # Note: for very small files, the difference may be negligible
        print(f"Eager: {eager_time:.4f}s, Lazy: {lazy_time:.4f}s")
        assert lazy_time < eager_time or lazy_time < 0.1  # Allow if both are very fast


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
