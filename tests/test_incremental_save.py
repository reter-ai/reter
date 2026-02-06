"""
Tests for incremental save functionality using HybridReteNetwork.

These tests verify the delta journal system for incremental storage:
1. Delta files are created and used for modifications
2. Multiple save cycles with deltas persist correctly
3. Compaction merges deltas into base
4. Source-level tracking (add/remove sources)
5. Recovery after reopen
"""

import tempfile
import os
import pytest
from reter import Reter
from reter_core.owl_rete_cpp import ReteNetwork, HybridReteNetwork, Fact


class TestIncrementalSaveDeltaCreation:
    """Tests that verify delta files are created for modifications."""

    def test_delta_file_is_separate_and_smaller(self, tmp_path):
        """Test that delta is a separate file much smaller than base."""
        # Create base with many facts
        net = ReteNetwork()
        for i in range(100):
            net.add_fact(Fact({'subject': f'Base{i}', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)
        base_size = os.path.getsize(base_path)

        # Open hybrid and add a few facts
        hybrid = HybridReteNetwork()
        hybrid.open(base_path)

        for i in range(5):
            hybrid.add_fact(Fact({'subject': f'Delta{i}', 'predicate': 'type', 'object': 'NewThing'}))
        hybrid.save()

        # Verify delta file exists separately
        delta_path = hybrid.delta_path()
        assert os.path.exists(delta_path), "Delta file should exist"
        assert delta_path != base_path, "Delta should be separate file"
        assert delta_path.endswith('.delta'), "Delta file should have .delta extension"

        # Delta should be MUCH smaller than base (only contains 5 facts vs 100)
        delta_size = os.path.getsize(delta_path)
        assert delta_size < base_size / 5, f"Delta ({delta_size}) should be much smaller than base ({base_size})"

        # Verify two separate files on disk
        files = os.listdir(tmp_path)
        assert any('.delta' in f for f in files), f"Delta file should exist in {files}"

        hybrid.close()

    def test_delta_file_created_on_modification(self, tmp_path):
        """Test that delta file is created when facts are added."""
        # Create base network
        net = ReteNetwork()
        for i in range(5):
            net.add_fact(Fact({'subject': f'E{i}', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        # Open hybrid and add facts
        hybrid = HybridReteNetwork()
        hybrid.open(base_path)

        # Add new facts
        for i in range(5, 10):
            hybrid.add_fact(Fact({'subject': f'E{i}', 'predicate': 'type', 'object': 'NewThing'}))

        # Delta file should exist
        delta_path = hybrid.delta_path()
        assert os.path.exists(delta_path), "Delta file should be created"

        # Delta should have size > header
        assert hybrid.delta_file_size() > 16, "Delta should contain entries"
        assert hybrid.delta_fact_count() == 5, "Should have 5 delta facts"

        hybrid.close()

    def test_delta_grows_with_modifications(self, tmp_path):
        """Test that delta file grows as more facts are added."""
        net = ReteNetwork()
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        hybrid = HybridReteNetwork()
        hybrid.open(base_path)

        sizes = []
        for i in range(5):
            hybrid.add_fact(Fact({'subject': f'E{i}', 'predicate': 'type', 'object': 'Thing'}))
            hybrid.save()
            sizes.append(hybrid.delta_file_size())

        # Delta should grow with each addition
        for i in range(1, len(sizes)):
            assert sizes[i] >= sizes[i-1], f"Delta should grow: {sizes}"

        hybrid.close()


class TestIncrementalSaveMultipleCycles:
    """Tests for multiple save cycles with delta journals."""

    def test_five_cycles_delta_accumulation(self, tmp_path):
        """Test 5 cycles of modifications accumulate in delta."""
        # Create base
        net = ReteNetwork()
        for i in range(10):
            net.add_fact(Fact({'subject': f'Base{i}', 'predicate': 'type', 'object': 'BaseThing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        # 5 cycles: open, add, save, close
        for cycle in range(5):
            hybrid = HybridReteNetwork()
            hybrid.open(base_path)

            # Add facts for this cycle
            for i in range(3):
                hybrid.add_fact(Fact({
                    'subject': f'Cycle{cycle}_E{i}',
                    'predicate': 'type',
                    'object': f'Cycle{cycle}Thing'
                }))

            hybrid.save()
            hybrid.close()

        # Verify final state
        hybrid = HybridReteNetwork()
        hybrid.open(base_path)

        assert hybrid.fact_count() == 10 + (5 * 3), f"Expected {10 + 15} facts"
        assert hybrid.base_fact_count() == 10, "Base should be unchanged"
        assert hybrid.delta_fact_count() == 15, "Delta should have 15 facts"

        hybrid.close()

    def test_interleaved_add_remove_with_delta(self, tmp_path):
        """Test interleaved add/remove operations with delta tracking."""
        net = ReteNetwork()
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        # Cycle 1: Add source1
        hybrid = HybridReteNetwork()
        hybrid.open(base_path)
        facts1 = [Fact({'subject': f'S1_E{i}', 'predicate': 'type', 'object': 'Thing'}) for i in range(5)]
        hybrid.add_source('source1', facts1)
        hybrid.save()
        hybrid.close()

        # Cycle 2: Add source2
        hybrid = HybridReteNetwork()
        hybrid.open(base_path)
        facts2 = [Fact({'subject': f'S2_E{i}', 'predicate': 'type', 'object': 'Thing'}) for i in range(5)]
        hybrid.add_source('source2', facts2)
        hybrid.save()
        assert hybrid.fact_count() == 10
        hybrid.close()

        # Cycle 3: Remove source1, add source3
        hybrid = HybridReteNetwork()
        hybrid.open(base_path)
        hybrid.remove_source('source1')
        facts3 = [Fact({'subject': f'S3_E{i}', 'predicate': 'type', 'object': 'Thing'}) for i in range(3)]
        hybrid.add_source('source3', facts3)
        hybrid.save()
        hybrid.close()

        # Verify final state
        hybrid = HybridReteNetwork()
        hybrid.open(base_path)
        # source2 (5) + source3 (3) = 8
        assert hybrid.fact_count() == 8, f"Expected 8 facts, got {hybrid.fact_count()}"
        hybrid.close()


class TestIncrementalSaveCompaction:
    """Tests for compaction of delta into base."""

    def test_compact_resets_delta(self, tmp_path):
        """Test that compaction merges delta into base and resets delta."""
        net = ReteNetwork()
        for i in range(5):
            net.add_fact(Fact({'subject': f'Base{i}', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        # Add delta facts
        hybrid = HybridReteNetwork()
        hybrid.open(base_path)
        for i in range(5, 15):
            hybrid.add_fact(Fact({'subject': f'Delta{i}', 'predicate': 'type', 'object': 'DeltaThing'}))

        assert hybrid.base_fact_count() == 5
        assert hybrid.delta_fact_count() == 10

        # Compact
        hybrid.compact()

        # After compaction, all facts should be in base
        assert hybrid.fact_count() == 15, "Total should be unchanged"
        assert hybrid.base_fact_count() == 15, "All facts should be in base"
        assert hybrid.delta_fact_count() == 0, "Delta should be empty"

        hybrid.close()

    def test_compact_after_deletions(self, tmp_path):
        """Test compaction after deletions removes deleted facts from base."""
        net = ReteNetwork()
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        # Add source and then remove it
        hybrid = HybridReteNetwork()
        hybrid.open(base_path)

        facts = [Fact({'subject': f'E{i}', 'predicate': 'type', 'object': 'Thing'}) for i in range(10)]
        hybrid.add_source('test_source', facts)
        assert hybrid.fact_count() == 10

        # Remove half via a different source approach
        hybrid.remove_source('test_source')
        assert hybrid.fact_count() == 0
        assert hybrid.deleted_fact_count() == 10

        # Compact should result in empty base
        hybrid.compact()
        assert hybrid.base_fact_count() == 0, "Base should be empty after compaction"
        assert hybrid.delta_fact_count() == 0, "Delta should be empty"
        assert hybrid.deleted_fact_count() == 0, "No deleted facts tracked"

        hybrid.close()

    def test_compact_persists_correctly(self, tmp_path):
        """Test that compacted state persists correctly on reopen."""
        net = ReteNetwork()
        for i in range(5):
            net.add_fact(Fact({'subject': f'Base{i}', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        # Add delta and compact
        hybrid = HybridReteNetwork()
        hybrid.open(base_path)
        for i in range(5, 10):
            hybrid.add_fact(Fact({'subject': f'Delta{i}', 'predicate': 'type', 'object': 'DeltaThing'}))
        hybrid.compact()
        hybrid.close()

        # Reopen and verify
        hybrid2 = HybridReteNetwork()
        hybrid2.open(base_path)

        assert hybrid2.fact_count() == 10
        assert hybrid2.base_fact_count() == 10
        assert hybrid2.delta_fact_count() == 0

        # Add more facts to verify network still works
        hybrid2.add_fact(Fact({'subject': 'New', 'predicate': 'type', 'object': 'Thing'}))
        assert hybrid2.fact_count() == 11
        assert hybrid2.delta_fact_count() == 1

        hybrid2.close()


class TestIncrementalSaveSourceTracking:
    """Tests for source-level tracking in delta journal."""

    def test_add_source_batch_efficiency(self, tmp_path):
        """Test that add_source is more efficient than individual adds."""
        net = ReteNetwork()
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        hybrid = HybridReteNetwork()
        hybrid.open(base_path)

        # Add 100 facts via batch add_source
        facts = [Fact({'subject': f'E{i}', 'predicate': 'type', 'object': 'Thing'}) for i in range(100)]
        count = hybrid.add_source('batch_source', facts)

        assert count == 100
        assert hybrid.fact_count() == 100
        assert hybrid.delta_fact_count() == 100

        hybrid.close()

    def test_remove_source_efficient(self, tmp_path):
        """Test that remove_source efficiently marks all facts as deleted."""
        net = ReteNetwork()
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        hybrid = HybridReteNetwork()
        hybrid.open(base_path)

        # Add 50 facts
        facts = [Fact({'subject': f'E{i}', 'predicate': 'type', 'object': 'Thing'}) for i in range(50)]
        hybrid.add_source('my_source', facts)
        assert hybrid.fact_count() == 50

        # Remove all with one operation
        removed = hybrid.remove_source('my_source')

        assert removed == 50
        assert hybrid.fact_count() == 0
        assert hybrid.deleted_fact_count() == 50

        hybrid.close()

    def test_multiple_sources_tracked(self, tmp_path):
        """Test that multiple sources are tracked independently."""
        net = ReteNetwork()
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        hybrid = HybridReteNetwork()
        hybrid.open(base_path)

        # Add three sources
        for src_idx in range(3):
            facts = [
                Fact({'subject': f'S{src_idx}_E{i}', 'predicate': 'type', 'object': 'Thing'})
                for i in range(10)
            ]
            hybrid.add_source(f'source{src_idx}', facts)

        assert hybrid.fact_count() == 30

        # Remove middle source
        hybrid.remove_source('source1')
        assert hybrid.fact_count() == 20

        # Remove first source
        hybrid.remove_source('source0')
        assert hybrid.fact_count() == 10

        hybrid.close()


class TestIncrementalSaveRecovery:
    """Tests for recovery after reopening."""

    def test_delta_recovered_on_reopen(self, tmp_path):
        """Test that delta journal is replayed on reopen."""
        net = ReteNetwork()
        for i in range(5):
            net.add_fact(Fact({'subject': f'Base{i}', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        # Add delta facts and save
        hybrid = HybridReteNetwork()
        hybrid.open(base_path)
        for i in range(5, 12):
            hybrid.add_fact(Fact({'subject': f'Delta{i}', 'predicate': 'type', 'object': 'DeltaThing'}))
        hybrid.save()
        hybrid.close()

        # Reopen - delta should be recovered
        hybrid2 = HybridReteNetwork()
        hybrid2.open(base_path)

        assert hybrid2.fact_count() == 12
        assert hybrid2.base_fact_count() == 5
        assert hybrid2.delta_fact_count() == 7

        hybrid2.close()

    def test_deletions_recovered_on_reopen(self, tmp_path):
        """Test that deletions in delta are recovered on reopen."""
        net = ReteNetwork()
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        # Add source and remove it
        hybrid = HybridReteNetwork()
        hybrid.open(base_path)
        facts = [Fact({'subject': f'E{i}', 'predicate': 'type', 'object': 'Thing'}) for i in range(10)]
        hybrid.add_source('to_delete', facts)
        hybrid.save()
        hybrid.remove_source('to_delete')
        hybrid.save()
        hybrid.close()

        # Reopen - should see 0 facts
        hybrid2 = HybridReteNetwork()
        hybrid2.open(base_path)

        assert hybrid2.fact_count() == 0
        assert hybrid2.deleted_fact_count() == 10

        hybrid2.close()


class TestIncrementalSaveMaterialize:
    """Tests for materializing hybrid network into regular network."""

    def test_materialize_includes_base_and_delta(self, tmp_path):
        """Test that materialize_into includes both base and delta facts."""
        net = ReteNetwork()
        for i in range(5):
            net.add_fact(Fact({'subject': f'Base{i}', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        hybrid = HybridReteNetwork()
        hybrid.open(base_path)
        for i in range(5, 10):
            hybrid.add_fact(Fact({'subject': f'Delta{i}', 'predicate': 'type', 'object': 'DeltaThing'}))

        # Materialize into fresh network
        target = ReteNetwork()
        hybrid.materialize_into(target)

        assert target.fact_count() == 10

        hybrid.close()

    def test_materialize_excludes_deleted(self, tmp_path):
        """Test that materialize_into excludes deleted facts."""
        net = ReteNetwork()
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        hybrid = HybridReteNetwork()
        hybrid.open(base_path)

        # Add and then remove some
        facts1 = [Fact({'subject': f'Keep{i}', 'predicate': 'type', 'object': 'Thing'}) for i in range(5)]
        facts2 = [Fact({'subject': f'Delete{i}', 'predicate': 'type', 'object': 'Thing'}) for i in range(5)]
        hybrid.add_source('keep', facts1)
        hybrid.add_source('delete', facts2)
        hybrid.remove_source('delete')

        # Materialize
        target = ReteNetwork()
        hybrid.materialize_into(target)

        # Only kept facts should be there
        assert target.fact_count() == 5

        hybrid.close()


class TestIncrementalSaveLargeScale:
    """Large scale tests for incremental save."""

    def test_large_batch_delta(self, tmp_path):
        """Test large batch of facts added to delta."""
        net = ReteNetwork()
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        hybrid = HybridReteNetwork()
        hybrid.open(base_path)

        # Add 1000 facts
        facts = [
            Fact({'subject': f'E{i}', 'predicate': 'type', 'object': 'Thing'})
            for i in range(1000)
        ]
        count = hybrid.add_source('large_source', facts)

        assert count == 1000
        assert hybrid.fact_count() == 1000
        assert hybrid.delta_fact_count() == 1000

        # Save and reopen
        hybrid.save()
        hybrid.close()

        hybrid2 = HybridReteNetwork()
        hybrid2.open(base_path)
        assert hybrid2.fact_count() == 1000

        hybrid2.close()

    def test_multiple_compactions(self, tmp_path):
        """Test multiple compaction cycles."""
        net = ReteNetwork()
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        total_facts = 0
        for cycle in range(3):
            hybrid = HybridReteNetwork()
            hybrid.open(base_path)

            # Add facts
            facts = [
                Fact({'subject': f'Cycle{cycle}_E{i}', 'predicate': 'type', 'object': 'Thing'})
                for i in range(100)
            ]
            hybrid.add_source(f'cycle{cycle}', facts)
            total_facts += 100

            # Compact
            hybrid.compact()

            assert hybrid.base_fact_count() == total_facts
            assert hybrid.delta_fact_count() == 0

            hybrid.close()

        # Final verification
        hybrid = HybridReteNetwork()
        hybrid.open(base_path)
        assert hybrid.fact_count() == 300
        assert hybrid.base_fact_count() == 300
        hybrid.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
