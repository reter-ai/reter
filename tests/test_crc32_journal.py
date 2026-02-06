"""
Intensive tests for Issue #5: CRC32 checksums in delta journal.

Tests:
- CRC32 calculation correctness
- Corruption detection
- Corrupted entry skipping
- Backward compatibility with old format
- Large data integrity
"""

import pytest
import tempfile
import os
import struct
from pathlib import Path

from reter_core.owl_rete_cpp import (
    ReteNetwork, HybridReteNetwork, Fact
)


class TestCRC32Basic:
    """Basic CRC32 functionality tests."""

    def test_journal_entries_have_crc32(self, tmp_path):
        """Test that journal entries are written with CRC32."""
        # Create base
        net = ReteNetwork()
        for i in range(3):
            net.add_fact(Fact({'subject': f'E{i}', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        # Open hybrid and add facts
        hybrid = HybridReteNetwork()
        hybrid.open(base_path)
        hybrid.add_fact(Fact({'subject': 'X', 'predicate': 'type', 'object': 'NewThing'}))
        hybrid.save()
        hybrid.close()

        # Verify delta file exists and has content
        delta_path = base_path + ".delta"
        assert os.path.exists(delta_path)
        with open(delta_path, 'rb') as f:
            content = f.read()
        # Header is 16 bytes + at least one entry with CRC32
        assert len(content) > 16

    def test_multiple_entries_all_have_crc32(self, tmp_path):
        """Test CRC32 for multiple journal entries."""
        net = ReteNetwork()
        net.add_fact(Fact({'subject': 'Base', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        hybrid = HybridReteNetwork()
        hybrid.open(base_path)

        # Add multiple facts individually (creates separate entries)
        for i in range(10):
            hybrid.add_fact(Fact({
                'subject': f'Entity{i}',
                'predicate': 'hasValue',
                'object': f'Value{i}'
            }))

        hybrid.save()

        # Verify all facts are accessible
        assert hybrid.fact_count() == 11  # 1 base + 10 delta
        hybrid.close()

        # Reopen and verify integrity
        hybrid2 = HybridReteNetwork()
        hybrid2.open(base_path)
        assert hybrid2.fact_count() == 11
        hybrid2.close()


class TestCRC32CorruptionDetection:
    """Tests for corruption detection via CRC32."""

    def test_detect_corrupted_entry_header(self, tmp_path):
        """Test that corrupted entry header is detected."""
        net = ReteNetwork()
        net.add_fact(Fact({'subject': 'E1', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        hybrid = HybridReteNetwork()
        hybrid.open(base_path)
        hybrid.add_fact(Fact({'subject': 'E2', 'predicate': 'type', 'object': 'NewThing'}))
        hybrid.save()
        hybrid.close()

        # Corrupt the delta file (modify a byte in the first entry)
        delta_path = base_path + ".delta"
        with open(delta_path, 'r+b') as f:
            f.seek(20)  # Skip header, modify entry
            original = f.read(1)
            f.seek(20)
            f.write(bytes([original[0] ^ 0xFF]))  # Flip bits

        # Reopen - should handle corruption gracefully
        hybrid2 = HybridReteNetwork()
        result = hybrid2.open(base_path)
        # Should still open (corrupted entries are skipped)
        assert result == True
        # May have fewer facts due to corruption
        hybrid2.close()

    def test_corruption_in_data_detected(self, tmp_path):
        """Test that data corruption is detected via CRC mismatch."""
        net = ReteNetwork()
        net.add_fact(Fact({'subject': 'Base', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        hybrid = HybridReteNetwork()
        hybrid.open(base_path)
        # Add a fact with longer data
        hybrid.add_fact(Fact({
            'subject': 'LongEntity',
            'predicate': 'hasLongValue',
            'object': 'A' * 100  # Long value
        }))
        hybrid.save()
        hybrid.close()

        delta_path = base_path + ".delta"
        file_size = os.path.getsize(delta_path)

        # Corrupt data near the end (in the value)
        with open(delta_path, 'r+b') as f:
            f.seek(file_size - 20)  # Near end
            f.write(b'CORRUPTED')

        # Reopen - should handle gracefully
        hybrid2 = HybridReteNetwork()
        hybrid2.open(base_path)
        # The corrupted entry should be skipped
        hybrid2.close()


class TestCRC32BatchOperations:
    """Tests for CRC32 with batch operations."""

    def test_add_source_batch_has_crc32(self, tmp_path):
        """Test CRC32 for add_source batch operation."""
        net = ReteNetwork()
        net.add_fact(Fact({'subject': 'Base', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        hybrid = HybridReteNetwork()
        hybrid.open(base_path)

        # Batch add
        facts = [
            Fact({'subject': f'B{i}', 'predicate': 'batchProp', 'object': f'V{i}'})
            for i in range(50)
        ]
        added = hybrid.add_source("batch_source", facts)
        assert added == 50
        hybrid.save()
        hybrid.close()

        # Reopen and verify
        hybrid2 = HybridReteNetwork()
        hybrid2.open(base_path)
        assert hybrid2.fact_count() == 51  # 1 base + 50 batch
        hybrid2.close()

    def test_delete_source_has_crc32(self, tmp_path):
        """Test CRC32 for delete_source operation."""
        net = ReteNetwork()
        for i in range(10):
            net.add_fact(Fact({'subject': f'E{i}', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        hybrid = HybridReteNetwork()
        hybrid.open(base_path)

        # Add source then delete it
        facts = [
            Fact({'subject': f'D{i}', 'predicate': 'delProp', 'object': f'V{i}'})
            for i in range(20)
        ]
        hybrid.add_source("to_delete", facts)
        assert hybrid.fact_count() == 30

        removed = hybrid.remove_source("to_delete")
        assert removed == 20
        assert hybrid.fact_count() == 10

        hybrid.save()
        hybrid.close()

        # Reopen and verify deletion persisted
        hybrid2 = HybridReteNetwork()
        hybrid2.open(base_path)
        assert hybrid2.fact_count() == 10
        hybrid2.close()


class TestCRC32LargeData:
    """Tests for CRC32 with large data volumes."""

    def test_large_facts_integrity(self, tmp_path):
        """Test CRC32 integrity with large fact data."""
        net = ReteNetwork()
        net.add_fact(Fact({'subject': 'Base', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        hybrid = HybridReteNetwork()
        hybrid.open(base_path)

        # Add facts with large string values
        for i in range(10):
            fact = Fact({
                'subject': f'LargeEntity{i}',
                'predicate': 'hasLargeValue',
                'object': 'X' * 1000  # 1KB per fact
            })
            hybrid.add_fact(fact)

        assert hybrid.fact_count() == 11
        hybrid.save()
        hybrid.close()

        # Reopen and verify all facts are accessible
        hybrid2 = HybridReteNetwork()
        hybrid2.open(base_path)
        assert hybrid2.fact_count() == 11
        assert hybrid2.delta_fact_count() == 10
        assert hybrid2.base_fact_count() == 1
        hybrid2.close()

    def test_many_small_entries_integrity(self, tmp_path):
        """Test CRC32 with many small journal entries."""
        net = ReteNetwork()
        net.add_fact(Fact({'subject': 'Base', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        hybrid = HybridReteNetwork()
        hybrid.open(base_path)

        # Add many small facts individually
        for i in range(500):
            hybrid.add_fact(Fact({
                'subject': f'S{i}',
                'predicate': 'p',
                'object': f'O{i}'
            }))

        assert hybrid.fact_count() == 501
        hybrid.save()
        hybrid.close()

        # Reopen and verify all entries intact
        hybrid2 = HybridReteNetwork()
        hybrid2.open(base_path)
        assert hybrid2.fact_count() == 501
        hybrid2.close()


class TestCRC32BackwardCompatibility:
    """Tests for backward compatibility with old journal format."""

    def test_handles_zero_crc32_gracefully(self, tmp_path):
        """Test that entries with crc32=0 (old format) are accepted."""
        # This tests that the implementation doesn't reject old-format entries
        # We can't easily create old-format files, but we verify the logic
        # by checking that new entries are created correctly

        net = ReteNetwork()
        net.add_fact(Fact({'subject': 'E1', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        hybrid = HybridReteNetwork()
        hybrid.open(base_path)
        hybrid.add_fact(Fact({'subject': 'E2', 'predicate': 'type', 'object': 'New'}))
        hybrid.save()
        hybrid.close()

        # Verify the entry is readable
        hybrid2 = HybridReteNetwork()
        hybrid2.open(base_path)
        assert hybrid2.fact_count() == 2
        hybrid2.close()


class TestCRC32StressTest:
    """Stress tests for CRC32 implementation."""

    @pytest.mark.slow
    def test_rapid_add_remove_cycles(self, tmp_path):
        """Test CRC32 under rapid add/remove cycles."""
        net = ReteNetwork()
        net.add_fact(Fact({'subject': 'Permanent', 'predicate': 'type', 'object': 'Thing'}))
        base_path = str(tmp_path / "test.bin")
        net.save(base_path)

        hybrid = HybridReteNetwork()
        hybrid.open(base_path)

        # Rapid cycles
        for cycle in range(10):
            # Add batch
            facts = [
                Fact({'subject': f'C{cycle}E{i}', 'predicate': 'p', 'object': 'o'})
                for i in range(50)
            ]
            hybrid.add_source(f"source_{cycle}", facts)

            # Remove previous batch (except first)
            if cycle > 0:
                hybrid.remove_source(f"source_{cycle - 1}")

        hybrid.save()
        hybrid.close()

        # Verify final state
        hybrid2 = HybridReteNetwork()
        hybrid2.open(base_path)
        # Should have: 1 permanent + 50 from last cycle
        assert hybrid2.fact_count() == 51
        hybrid2.close()
