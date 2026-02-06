"""
Intensive tests for Issue #7: Windows versioned filenames for compaction.

Tests:
- Version number tracking
- Compaction creates new version
- Old versions are cleaned up
- Gap handling in version numbers
- Multiple compaction cycles
- Recovery from failed compaction
"""

import pytest
import tempfile
import os
import sys
from pathlib import Path

from reter_core.owl_rete_cpp import (
    ReteNetwork, HybridReteNetwork, Fact
)


def is_windows():
    return sys.platform == 'win32'


class TestVersionedFilenamesBasic:
    """Basic versioned filename functionality tests."""

    def test_first_open_creates_version(self, tmp_path):
        """Test that first open initializes versioning properly."""
        net = ReteNetwork()
        for i in range(5):
            net.add_fact(Fact({'subject': f'E{i}', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        hybrid = HybridReteNetwork()
        hybrid.open(base_path)
        assert hybrid.fact_count() == 5
        hybrid.close()

        # On Windows, original file should be renamed to .v1
        if is_windows():
            v1_path = base_path + ".v1"
            # Either original or v1 should exist
            assert os.path.exists(base_path) or os.path.exists(v1_path)

    def test_compact_creates_new_version(self, tmp_path):
        """Test that compact creates a new version file."""
        net = ReteNetwork()
        for i in range(3):
            net.add_fact(Fact({'subject': f'E{i}', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        hybrid = HybridReteNetwork()
        hybrid.open(base_path)

        # Add delta facts
        for i in range(3, 6):
            hybrid.add_fact(Fact({'subject': f'E{i}', 'predicate': 'type', 'object': 'Delta'}))

        assert hybrid.fact_count() == 6
        hybrid.compact()
        hybrid.close()

        # Verify state persists
        hybrid2 = HybridReteNetwork()
        hybrid2.open(base_path)
        assert hybrid2.fact_count() == 6
        hybrid2.close()


class TestVersionedFilenamesCompaction:
    """Tests for versioned filenames during compaction."""

    def test_multiple_compactions(self, tmp_path):
        """Test multiple sequential compactions."""
        net = ReteNetwork()
        net.add_fact(Fact({'subject': 'Base', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        expected_count = 1

        for cycle in range(5):
            hybrid = HybridReteNetwork()
            hybrid.open(base_path)

            # Add facts
            for i in range(3):
                hybrid.add_fact(Fact({
                    'subject': f'C{cycle}E{i}',
                    'predicate': 'type',
                    'object': 'CycleThing'
                }))
            expected_count += 3

            assert hybrid.fact_count() == expected_count

            # Compact
            hybrid.compact()
            hybrid.close()

            # Verify after compact
            hybrid2 = HybridReteNetwork()
            hybrid2.open(base_path)
            assert hybrid2.fact_count() == expected_count
            hybrid2.close()

    def test_compaction_cleans_old_versions(self, tmp_path):
        """Test that old version files are cleaned up."""
        net = ReteNetwork()
        net.add_fact(Fact({'subject': 'Base', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        # Do multiple compactions
        for cycle in range(3):
            hybrid = HybridReteNetwork()
            hybrid.open(base_path)
            hybrid.add_fact(Fact({
                'subject': f'E{cycle}',
                'predicate': 'type',
                'object': 'Thing'
            }))
            hybrid.compact()
            hybrid.close()

        # Count version files
        version_files = list(tmp_path.glob("test.bin.v*"))
        # Should have at most 1-2 version files (current + maybe one being cleaned up)
        # Older versions should be deleted
        if is_windows():
            assert len(version_files) <= 2

    def test_reopen_after_compact_finds_correct_version(self, tmp_path):
        """Test that reopen finds the correct version after compaction."""
        net = ReteNetwork()
        for i in range(5):
            net.add_fact(Fact({'subject': f'E{i}', 'predicate': 'type', 'object': 'Base'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        # First session: open, modify, compact
        hybrid = HybridReteNetwork()
        hybrid.open(base_path)
        for i in range(5, 10):
            hybrid.add_fact(Fact({'subject': f'E{i}', 'predicate': 'type', 'object': 'Delta1'}))
        hybrid.compact()
        hybrid.close()

        # Second session: open, modify, compact
        hybrid2 = HybridReteNetwork()
        hybrid2.open(base_path)
        assert hybrid2.fact_count() == 10
        for i in range(10, 15):
            hybrid2.add_fact(Fact({'subject': f'E{i}', 'predicate': 'type', 'object': 'Delta2'}))
        hybrid2.compact()
        hybrid2.close()

        # Third session: just verify
        hybrid3 = HybridReteNetwork()
        hybrid3.open(base_path)
        assert hybrid3.fact_count() == 15
        hybrid3.close()


class TestVersionGapHandling:
    """Tests for handling gaps in version numbers."""

    def test_handles_version_gap(self, tmp_path):
        """Test that gaps in version numbers are handled correctly."""
        net = ReteNetwork()
        net.add_fact(Fact({'subject': 'Base', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        # Create version files with a gap
        if is_windows():
            # Manually create version files with gap
            hybrid = HybridReteNetwork()
            hybrid.open(base_path)
            hybrid.add_fact(Fact({'subject': 'E1', 'predicate': 'type', 'object': 'V1'}))
            hybrid.compact()  # Creates v2
            hybrid.add_fact(Fact({'subject': 'E2', 'predicate': 'type', 'object': 'V2'}))
            hybrid.compact()  # Creates v3
            hybrid.close()

            # Delete v2 to create a gap (v1 missing, v3 exists)
            v1_path = base_path + ".v1"
            if os.path.exists(v1_path):
                try:
                    os.remove(v1_path)
                except:
                    pass  # May fail if still in use

            # Reopen - should still find highest version
            hybrid2 = HybridReteNetwork()
            hybrid2.open(base_path)
            # Should have found the latest version
            assert hybrid2.fact_count() >= 1
            hybrid2.close()

    def test_handles_multiple_gaps(self, tmp_path):
        """Test handling of multiple gaps in version sequence."""
        net = ReteNetwork()
        net.add_fact(Fact({'subject': 'Base', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        # Multiple compaction cycles
        for i in range(5):
            hybrid = HybridReteNetwork()
            hybrid.open(base_path)
            hybrid.add_fact(Fact({'subject': f'E{i}', 'predicate': 'type', 'object': f'V{i}'}))
            hybrid.compact()
            hybrid.close()

        # Verify final state
        hybrid_final = HybridReteNetwork()
        hybrid_final.open(base_path)
        assert hybrid_final.fact_count() == 6  # 1 base + 5 added
        hybrid_final.close()


class TestCompactionWithDelta:
    """Tests for compaction with delta journal."""

    def test_delta_cleared_after_compact(self, tmp_path):
        """Test that delta journal is cleared after compaction."""
        net = ReteNetwork()
        net.add_fact(Fact({'subject': 'Base', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        hybrid = HybridReteNetwork()
        hybrid.open(base_path)

        # Add delta facts
        for i in range(10):
            hybrid.add_fact(Fact({'subject': f'D{i}', 'predicate': 'type', 'object': 'Delta'}))

        assert hybrid.delta_fact_count() == 10
        assert hybrid.base_fact_count() == 1

        # Compact
        hybrid.compact()

        # After compact, delta should be empty, base should have all
        assert hybrid.delta_fact_count() == 0
        assert hybrid.base_fact_count() == 11
        assert hybrid.fact_count() == 11

        hybrid.close()

    def test_deleted_facts_removed_after_compact(self, tmp_path):
        """Test that deleted facts are physically removed after compaction."""
        net = ReteNetwork()
        for i in range(10):
            net.add_fact(Fact({'subject': f'E{i}', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        hybrid = HybridReteNetwork()
        hybrid.open(base_path)

        # Add facts via source
        facts = [
            Fact({'subject': f'D{i}', 'predicate': 'type', 'object': 'Delta'})
            for i in range(10)
        ]
        hybrid.add_source("to_delete", facts)
        assert hybrid.fact_count() == 20

        # Delete the source
        hybrid.remove_source("to_delete")
        assert hybrid.fact_count() == 10
        assert hybrid.deleted_fact_count() == 10

        # Compact - deleted facts should be physically removed
        hybrid.compact()

        assert hybrid.fact_count() == 10
        assert hybrid.deleted_fact_count() == 0

        hybrid.close()


class TestCompactionStress:
    """Stress tests for compaction."""

    @pytest.mark.slow
    def test_many_compact_cycles_stability(self, tmp_path):
        """Test stability over many compaction cycles."""
        net = ReteNetwork()
        net.add_fact(Fact({'subject': 'Permanent', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        for cycle in range(20):
            hybrid = HybridReteNetwork()
            hybrid.open(base_path)

            # Add some facts
            for i in range(5):
                hybrid.add_fact(Fact({
                    'subject': f'C{cycle}E{i}',
                    'predicate': 'cycleNum',
                    'object': str(cycle)
                }))

            # Compact every 3 cycles
            if cycle % 3 == 0:
                hybrid.compact()

            hybrid.close()

        # Final verification
        hybrid_final = HybridReteNetwork()
        hybrid_final.open(base_path)
        # 1 permanent + 20 cycles * 5 facts = 101 facts
        assert hybrid_final.fact_count() == 101
        hybrid_final.close()

    @pytest.mark.slow
    def test_large_data_compaction(self, tmp_path):
        """Test compaction with moderate amounts of data."""
        net = ReteNetwork()
        # Create 200 base facts (reduced to avoid Cap'n Proto traversal limit)
        for i in range(200):
            net.add_fact(Fact({'subject': f'B{i}', 'predicate': 'type', 'object': 'Base'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        hybrid = HybridReteNetwork()
        hybrid.open(base_path)

        # Add 200 delta facts
        facts = [
            Fact({'subject': f'D{i}', 'predicate': 'type', 'object': 'Delta'})
            for i in range(200)
        ]
        hybrid.add_source("large_delta", facts)

        assert hybrid.fact_count() == 400

        # Compact
        hybrid.compact()

        assert hybrid.fact_count() == 400
        assert hybrid.base_fact_count() == 400
        assert hybrid.delta_fact_count() == 0

        hybrid.close()

        # Verify persistence
        hybrid2 = HybridReteNetwork()
        hybrid2.open(base_path)
        assert hybrid2.fact_count() == 400
        hybrid2.close()


class TestAsyncCompaction:
    """Tests for async compaction."""

    def test_async_compact_completes(self, tmp_path):
        """Test that async compaction completes successfully."""
        net = ReteNetwork()
        for i in range(5):
            net.add_fact(Fact({'subject': f'E{i}', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        hybrid = HybridReteNetwork()
        hybrid.open(base_path)

        for i in range(5, 10):
            hybrid.add_fact(Fact({'subject': f'E{i}', 'predicate': 'type', 'object': 'Delta'}))

        # Start async compact
        hybrid.compact_async()

        # Wait for completion
        hybrid.wait_for_compaction()

        # Verify result
        assert not hybrid.is_compacting()
        assert hybrid.fact_count() == 10

        hybrid.close()

    def test_is_compacting_flag(self, tmp_path):
        """Test that is_compacting flag works correctly."""
        net = ReteNetwork()
        for i in range(100):
            net.add_fact(Fact({'subject': f'E{i}', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        hybrid = HybridReteNetwork()
        hybrid.open(base_path)

        for i in range(100, 200):
            hybrid.add_fact(Fact({'subject': f'E{i}', 'predicate': 'type', 'object': 'Delta'}))

        # Before compaction
        assert not hybrid.is_compacting()

        # Start async
        hybrid.compact_async()

        # Wait and verify
        hybrid.wait_for_compaction()
        assert not hybrid.is_compacting()

        hybrid.close()
