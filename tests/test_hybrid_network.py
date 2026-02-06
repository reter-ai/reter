"""Tests for HybridReteNetwork (Phase 6 - Incremental Storage)."""
import pytest
import tempfile
import os
import time

from reter_core.owl_rete_cpp import ReteNetwork, HybridReteNetwork, Fact


class TestHybridNetworkBasic:
    """Basic functionality tests."""

    def test_open_returns_true(self, tmp_path):
        """Test that open() returns True for valid file."""
        # Create base network
        net = ReteNetwork()
        net.add_fact(Fact({'subject': 'A', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        # Open hybrid network
        hybrid = HybridReteNetwork()
        result = hybrid.open(base_path)

        assert result is True
        assert hybrid.is_open() is True
        hybrid.close()

    def test_is_open_after_close(self, tmp_path):
        """Test that is_open() returns False after close()."""
        net = ReteNetwork()
        net.add_fact(Fact({'subject': 'A', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        hybrid = HybridReteNetwork()
        hybrid.open(base_path)
        hybrid.close()

        assert hybrid.is_open() is False

    def test_fact_count_matches_base(self, tmp_path):
        """Test that fact_count matches base after open."""
        net = ReteNetwork()
        for i in range(10):
            net.add_fact(Fact({'subject': f'E{i}', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        hybrid = HybridReteNetwork()
        hybrid.open(base_path)

        assert hybrid.fact_count() == 10
        assert hybrid.base_fact_count() == 10
        assert hybrid.delta_fact_count() == 0
        assert hybrid.deleted_fact_count() == 0
        hybrid.close()

    def test_delta_file_created(self, tmp_path):
        """Test that delta file is created on open."""
        net = ReteNetwork()
        net.add_fact(Fact({'subject': 'A', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        hybrid = HybridReteNetwork()
        hybrid.open(base_path)

        delta_path = hybrid.delta_path()
        assert os.path.exists(delta_path)
        assert hybrid.delta_file_size() >= 16  # At least header size
        hybrid.close()


class TestHybridNetworkAddFact:
    """Tests for adding facts to hybrid network."""

    def test_add_fact_increments_delta_count(self, tmp_path):
        """Test that add_fact increments delta_fact_count."""
        net = ReteNetwork()
        net.add_fact(Fact({'subject': 'A', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        hybrid = HybridReteNetwork()
        hybrid.open(base_path)

        result = hybrid.add_fact(Fact({'subject': 'B', 'predicate': 'type', 'object': 'Thing'}))

        assert result is True
        assert hybrid.fact_count() == 2
        assert hybrid.delta_fact_count() == 1
        hybrid.close()

    def test_add_fact_duplicate_returns_false(self, tmp_path):
        """Test that adding duplicate fact returns False."""
        net = ReteNetwork()
        net.add_fact(Fact({'subject': 'A', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        hybrid = HybridReteNetwork()
        hybrid.open(base_path)

        # Try to add same fact again
        result = hybrid.add_fact(Fact({'subject': 'A', 'predicate': 'type', 'object': 'Thing'}))

        assert result is False
        assert hybrid.fact_count() == 1  # No change
        hybrid.close()

    def test_add_source_batch(self, tmp_path):
        """Test adding multiple facts via add_source."""
        net = ReteNetwork()
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        hybrid = HybridReteNetwork()
        hybrid.open(base_path)

        facts = [
            Fact({'subject': f'E{i}', 'predicate': 'type', 'object': 'Thing'})
            for i in range(5)
        ]
        count = hybrid.add_source('test_source', facts)

        assert count == 5
        assert hybrid.fact_count() == 5
        assert hybrid.delta_fact_count() == 5
        hybrid.close()


class TestHybridNetworkRemoveFact:
    """Tests for removing facts from hybrid network."""

    def test_remove_source_marks_deleted(self, tmp_path):
        """Test that remove_source marks facts as deleted."""
        net = ReteNetwork()
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        hybrid = HybridReteNetwork()
        hybrid.open(base_path)

        # Add facts with source
        facts = [
            Fact({'subject': f'E{i}', 'predicate': 'type', 'object': 'Thing'})
            for i in range(3)
        ]
        hybrid.add_source('test_source', facts)
        assert hybrid.fact_count() == 3

        # Remove source
        removed = hybrid.remove_source('test_source')

        assert removed == 3
        assert hybrid.fact_count() == 0  # All gone
        assert hybrid.deleted_fact_count() == 3
        hybrid.close()


class TestHybridNetworkCompaction:
    """Tests for compaction."""

    def test_compact_merges_delta_to_base(self, tmp_path):
        """Test that compact merges delta into base."""
        net = ReteNetwork()
        for i in range(5):
            net.add_fact(Fact({'subject': f'E{i}', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        hybrid = HybridReteNetwork()
        hybrid.open(base_path)

        # Add delta facts
        for i in range(5, 10):
            hybrid.add_fact(Fact({'subject': f'E{i}', 'predicate': 'type', 'object': 'DeltaThing'}))

        assert hybrid.base_fact_count() == 5
        assert hybrid.delta_fact_count() == 5

        # Compact
        hybrid.compact()

        assert hybrid.fact_count() == 10
        assert hybrid.base_fact_count() == 10
        assert hybrid.delta_fact_count() == 0
        hybrid.close()

    def test_compact_persists_after_reopen(self, tmp_path):
        """Test that compacted state persists after close/reopen."""
        net = ReteNetwork()
        for i in range(5):
            net.add_fact(Fact({'subject': f'E{i}', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        # Open, add delta, compact, close
        hybrid = HybridReteNetwork()
        hybrid.open(base_path)
        for i in range(5, 10):
            hybrid.add_fact(Fact({'subject': f'E{i}', 'predicate': 'type', 'object': 'DeltaThing'}))
        hybrid.compact()
        hybrid.close()

        # Reopen and verify
        hybrid2 = HybridReteNetwork()
        hybrid2.open(base_path)

        assert hybrid2.fact_count() == 10
        assert hybrid2.base_fact_count() == 10
        assert hybrid2.delta_fact_count() == 0
        hybrid2.close()


class TestHybridNetworkPersistence:
    """Tests for delta persistence."""

    def test_delta_persists_after_reopen(self, tmp_path):
        """Test that delta facts persist after close/reopen."""
        net = ReteNetwork()
        for i in range(5):
            net.add_fact(Fact({'subject': f'E{i}', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        # Open, add delta, save, close
        hybrid = HybridReteNetwork()
        hybrid.open(base_path)
        for i in range(5, 8):
            hybrid.add_fact(Fact({'subject': f'E{i}', 'predicate': 'type', 'object': 'DeltaThing'}))
        hybrid.save()
        hybrid.close()

        # Reopen and verify
        hybrid2 = HybridReteNetwork()
        hybrid2.open(base_path)

        assert hybrid2.fact_count() == 8
        assert hybrid2.base_fact_count() == 5
        assert hybrid2.delta_fact_count() == 3
        hybrid2.close()


class TestHybridNetworkMaterialize:
    """Tests for materialize_into."""

    def test_materialize_into_populates_network(self, tmp_path):
        """Test that materialize_into populates a ReteNetwork."""
        net = ReteNetwork()
        for i in range(5):
            net.add_fact(Fact({'subject': f'E{i}', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        # Open and add delta
        hybrid = HybridReteNetwork()
        hybrid.open(base_path)
        for i in range(5, 8):
            hybrid.add_fact(Fact({'subject': f'E{i}', 'predicate': 'type', 'object': 'DeltaThing'}))

        # Materialize into new network
        target = ReteNetwork()
        hybrid.materialize_into(target)

        assert target.fact_count() == 8
        hybrid.close()
