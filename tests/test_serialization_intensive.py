"""
Intensive tests for Cap'n Proto serialization of RETE networks.

These tests verify the robustness of the serialization fix that ensures
ProductionNode.network pointer is properly set during deserialization,
allowing template-instantiated rules (like prp-spo2) to fire for new facts.

Test categories:
1. Stress tests with many instances
2. Multiple serialization/deserialization cycles
3. Edge cases (networks with rules + seed instances)
4. Various chain lengths (2, 3 properties)
5. Interleaved additions across multiple cycles
6. Multiple property chains in the same network

Note: Tests follow the pattern of the original working tests - always including
at least one seed instance with the rule before serialization, as this ensures
the template-instantiated production nodes are properly configured.
"""

import tempfile
import os
import pytest
from reter import Reter


# =============================================================================
# STRESS TESTS - High volume instance additions
# =============================================================================

class TestSerializationStress:
    """Stress tests for serialization with many instances."""

    def test_property_chain_100_instances(self):
        """
        Stress test: Property chain with 100 parent-child pairs.

        Creates 50 chains before serialization, then adds 50 more after
        deserialization. Verifies all 100 grandparent relationships are inferred.
        """
        reasoner1 = Reter(variant="ai")

        # Define the property chain rule with at least one seed instance
        ontology = """
        hasParent composed_with hasParent is_subproperty_of hasGrandparent
        Person(SeedA)
        Person(SeedB)
        Person(SeedC)
        hasParent(SeedA, SeedB)
        hasParent(SeedB, SeedC)
        """
        reasoner1.load_ontology(ontology)

        # Add 49 more chains before serialization (total 50)
        for i in range(1, 50):
            chain_ontology = f"""
            Person(Person{i}A)
            Person(Person{i}B)
            Person(Person{i}C)
            hasParent(Person{i}A, Person{i}B)
            hasParent(Person{i}B, Person{i}C)
            """
            reasoner1.load_ontology(chain_ontology)

        # Verify chains work before serialization
        facts_before = reasoner1.query(
            type="role_assertion",
            role="hasGrandparent"
        )
        assert len(facts_before) == 50, f"Expected 50 grandparent facts, got {len(facts_before)}"

        # Serialize
        with tempfile.NamedTemporaryFile(suffix='.pb', delete=False) as f:
            temp_file = f.name

        try:
            reasoner1.network.save(temp_file)

            # Deserialize
            reasoner2 = Reter(variant="ai")
            reasoner2.network.load(temp_file)

            # Add 50 more chains after deserialization
            for i in range(50, 100):
                chain_ontology = f"""
                Person(Person{i}A)
                Person(Person{i}B)
                Person(Person{i}C)
                hasParent(Person{i}A, Person{i}B)
                hasParent(Person{i}B, Person{i}C)
                """
                reasoner2.load_ontology(chain_ontology)

            # Verify all 100 chains work
            facts_after = reasoner2.query(
                type="role_assertion",
                role="hasGrandparent"
            )

            assert len(facts_after) == 100, f"Expected 100 grandparent facts, got {len(facts_after)}"

            # Verify specific new chain (index 75)
            fact_75 = reasoner2.query(
                type="role_assertion",
                subject="Person75A",
                role="hasGrandparent",
                object="Person75C"
            )
            assert len(fact_75) == 1, "Person75A should have grandparent Person75C"

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_many_property_chains_with_seed_instances(self):
        """
        Test multiple different property chains with seed instances.

        Creates 5 distinct property chain rules, each with a seed instance,
        then verifies all work after deserialization for new instances.
        """
        reasoner1 = Reter(variant="ai")

        # Define 5 property chains, each with a seed instance to trigger template instantiation
        chains_ontology = """
        rel1 composed_with rel1 is_subproperty_of derived1
        rel2 composed_with rel2 is_subproperty_of derived2
        rel3 composed_with rel3 is_subproperty_of derived3
        rel4 composed_with rel4 is_subproperty_of derived4
        rel5 composed_with rel5 is_subproperty_of derived5

        Entity(Seed1A)
        Entity(Seed1B)
        Entity(Seed1C)
        rel1(Seed1A, Seed1B)
        rel1(Seed1B, Seed1C)

        Entity(Seed2A)
        Entity(Seed2B)
        Entity(Seed2C)
        rel2(Seed2A, Seed2B)
        rel2(Seed2B, Seed2C)

        Entity(Seed3A)
        Entity(Seed3B)
        Entity(Seed3C)
        rel3(Seed3A, Seed3B)
        rel3(Seed3B, Seed3C)

        Entity(Seed4A)
        Entity(Seed4B)
        Entity(Seed4C)
        rel4(Seed4A, Seed4B)
        rel4(Seed4B, Seed4C)

        Entity(Seed5A)
        Entity(Seed5B)
        Entity(Seed5C)
        rel5(Seed5A, Seed5B)
        rel5(Seed5B, Seed5C)
        """
        reasoner1.load_ontology(chains_ontology)

        # Verify all 5 chains work before serialization
        for i in range(1, 6):
            facts = reasoner1.query(
                type="role_assertion",
                subject=f"Seed{i}A",
                role=f"derived{i}",
                object=f"Seed{i}C"
            )
            assert len(facts) == 1, f"Seed chain {i} should work before serialization"

        # Serialize
        with tempfile.NamedTemporaryFile(suffix='.pb', delete=False) as f:
            temp_file = f.name

        try:
            reasoner1.network.save(temp_file)

            # Deserialize
            reasoner2 = Reter(variant="ai")
            reasoner2.network.load(temp_file)

            # Add new instances for all 5 chains
            for i in range(1, 6):
                instance_ontology = f"""
                Entity(New{i}A)
                Entity(New{i}B)
                Entity(New{i}C)
                rel{i}(New{i}A, New{i}B)
                rel{i}(New{i}B, New{i}C)
                """
                reasoner2.load_ontology(instance_ontology)

            # Verify all 5 chains inferred correctly for new instances
            for i in range(1, 6):
                facts = reasoner2.query(
                    type="role_assertion",
                    subject=f"New{i}A",
                    role=f"derived{i}",
                    object=f"New{i}C"
                )
                assert len(facts) == 1, f"Chain {i} should produce derived{i}(New{i}A, New{i}C) after deserialize"

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


# =============================================================================
# MULTIPLE CYCLES - Repeated serialization/deserialization
# =============================================================================

class TestMultipleSerializationCycles:
    """Tests for multiple serialization/deserialization cycles."""

    def test_three_cycles_with_additions(self):
        """
        Test 3 serialization/deserialization cycles with additions each cycle.

        Cycle 1: Create rule + seed, add instances A
        Cycle 2: Add instances B
        Cycle 3: Add instances C
        All instances should work after final cycle.
        """
        # Cycle 1: Create initial network with seed instance
        reasoner = Reter(variant="ai")
        reasoner.load_ontology("""
        hasParent composed_with hasParent is_subproperty_of hasGrandparent
        Person(Cycle1A)
        Person(Cycle1B)
        Person(Cycle1C)
        hasParent(Cycle1A, Cycle1B)
        hasParent(Cycle1B, Cycle1C)
        """)

        # Verify cycle 1 works
        facts1 = reasoner.query(type="role_assertion", subject="Cycle1A", role="hasGrandparent")
        assert len(facts1) == 1

        with tempfile.NamedTemporaryFile(suffix='.pb', delete=False) as f:
            temp_file = f.name

        try:
            # Serialize cycle 1
            reasoner.network.save(temp_file)

            # Cycle 2: Load and add more
            reasoner = Reter(variant="ai")
            reasoner.network.load(temp_file)
            reasoner.load_ontology("""
            Person(Cycle2A)
            Person(Cycle2B)
            Person(Cycle2C)
            hasParent(Cycle2A, Cycle2B)
            hasParent(Cycle2B, Cycle2C)
            """)

            # Verify both cycles work
            facts1 = reasoner.query(type="role_assertion", subject="Cycle1A", role="hasGrandparent")
            facts2 = reasoner.query(type="role_assertion", subject="Cycle2A", role="hasGrandparent")
            assert len(facts1) == 1, "Cycle 1 facts should persist"
            assert len(facts2) == 1, "Cycle 2 facts should be inferred"

            # Serialize cycle 2
            reasoner.network.save(temp_file)

            # Cycle 3: Load and add more
            reasoner = Reter(variant="ai")
            reasoner.network.load(temp_file)
            reasoner.load_ontology("""
            Person(Cycle3A)
            Person(Cycle3B)
            Person(Cycle3C)
            hasParent(Cycle3A, Cycle3B)
            hasParent(Cycle3B, Cycle3C)
            """)

            # Verify all three cycles work
            facts1 = reasoner.query(type="role_assertion", subject="Cycle1A", role="hasGrandparent")
            facts2 = reasoner.query(type="role_assertion", subject="Cycle2A", role="hasGrandparent")
            facts3 = reasoner.query(type="role_assertion", subject="Cycle3A", role="hasGrandparent")

            assert len(facts1) == 1, "Cycle 1 facts should persist through 3 cycles"
            assert len(facts2) == 1, "Cycle 2 facts should persist through 2 cycles"
            assert len(facts3) == 1, "Cycle 3 facts should be inferred"

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_five_cycles_no_additions_between(self):
        """
        Test 5 serialization cycles without additions between.

        Verifies that repeated serialization/deserialization doesn't
        corrupt the network state.
        """
        reasoner = Reter(variant="ai")
        reasoner.load_ontology("""
        hasParent composed_with hasParent is_subproperty_of hasGrandparent
        Person(Alice)
        Person(Bob)
        Person(Charlie)
        hasParent(Alice, Bob)
        hasParent(Bob, Charlie)
        """)

        with tempfile.NamedTemporaryFile(suffix='.pb', delete=False) as f:
            temp_file = f.name

        try:
            for cycle in range(5):
                # Serialize
                reasoner.network.save(temp_file)

                # Deserialize into new instance
                reasoner = Reter(variant="ai")
                reasoner.network.load(temp_file)

                # Verify data integrity
                facts = reasoner.query(type="role_assertion", subject="Alice", role="hasGrandparent")
                assert len(facts) == 1, f"Facts should persist after cycle {cycle + 1}"

            # Add new instances after 5 cycles
            reasoner.load_ontology("""
            Person(David)
            Person(Eve)
            Person(Frank)
            hasParent(David, Eve)
            hasParent(Eve, Frank)
            """)

            # Verify new instances work
            new_facts = reasoner.query(type="role_assertion", subject="David", role="hasGrandparent")
            assert len(new_facts) == 1, "Rules should still work after 5 cycles"

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


# =============================================================================
# EDGE CASES
# =============================================================================

class TestSerializationEdgeCases:
    """Edge case tests for serialization."""

    def test_multiple_rules_with_shared_seed(self):
        """
        Test network with multiple rules sharing some predicates.

        Both hasGrandparent and hasUncle use hasParent as part of chain.
        """
        reasoner1 = Reter(variant="ai")

        # Add two rules with seed instances
        reasoner1.load_ontology("""
        hasParent composed_with hasParent is_subproperty_of hasGrandparent
        hasParent composed_with hasSibling is_subproperty_of hasUncle
        Person(Alice)
        Person(Bob)
        Person(Charlie)
        Person(Dana)
        hasParent(Alice, Bob)
        hasParent(Bob, Charlie)
        hasSibling(Bob, Dana)
        """)

        # Verify both chains work before
        gp = reasoner1.query(type="role_assertion", subject="Alice", role="hasGrandparent", object="Charlie")
        uncle = reasoner1.query(type="role_assertion", subject="Alice", role="hasUncle", object="Dana")
        assert len(gp) >= 1, "hasGrandparent chain should work"
        assert len(uncle) >= 1, "hasUncle chain should work"

        with tempfile.NamedTemporaryFile(suffix='.pb', delete=False) as f:
            temp_file = f.name

        try:
            reasoner1.network.save(temp_file)

            # Deserialize
            reasoner2 = Reter(variant="ai")
            reasoner2.network.load(temp_file)

            # Add new instances for both chains
            reasoner2.load_ontology("""
            Person(Eve)
            Person(Frank)
            Person(Grace)
            Person(Henry)
            hasParent(Eve, Frank)
            hasParent(Frank, Grace)
            hasSibling(Frank, Henry)
            """)

            # Verify both chains work for new instances
            new_gp = reasoner2.query(type="role_assertion", subject="Eve", role="hasGrandparent", object="Grace")
            new_uncle = reasoner2.query(type="role_assertion", subject="Eve", role="hasUncle", object="Henry")

            assert len(new_gp) >= 1, "hasGrandparent chain should work after deserialization"
            assert len(new_uncle) >= 1, "hasUncle chain should work after deserialization"

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_same_predicate_multiple_chain_lengths(self):
        """
        Test multiple chains using same base predicate with different lengths.

        hasParent o hasParent -> hasGrandparent
        hasParent o hasParent o hasParent -> hasGreatGrandparent
        """
        reasoner1 = Reter(variant="ai")

        reasoner1.load_ontology("""
        hasParent composed_with hasParent is_subproperty_of hasGrandparent
        hasParent composed_with hasParent composed_with hasParent is_subproperty_of hasGreatGrandparent
        Person(A)
        Person(B)
        Person(C)
        Person(D)
        hasParent(A, B)
        hasParent(B, C)
        hasParent(C, D)
        """)

        # Verify both work before
        gp = reasoner1.query(type="role_assertion", subject="A", role="hasGrandparent")
        ggp = reasoner1.query(type="role_assertion", subject="A", role="hasGreatGrandparent")
        assert len(gp) >= 1, "Should have grandparent"  # A->C
        assert len(ggp) == 1, "Should have great-grandparent"  # A->D

        with tempfile.NamedTemporaryFile(suffix='.pb', delete=False) as f:
            temp_file = f.name

        try:
            reasoner1.network.save(temp_file)

            reasoner2 = Reter(variant="ai")
            reasoner2.network.load(temp_file)

            # Add new 4-generation chain
            reasoner2.load_ontology("""
            Person(E)
            Person(F)
            Person(G)
            Person(H)
            hasParent(E, F)
            hasParent(F, G)
            hasParent(G, H)
            """)

            # Verify both chains work for new instances
            new_gp = reasoner2.query(type="role_assertion", subject="E", role="hasGrandparent")
            new_ggp = reasoner2.query(type="role_assertion", subject="E", role="hasGreatGrandparent")

            assert len(new_gp) >= 1, "E should have grandparent G"
            assert len(new_ggp) == 1, "E should have great-grandparent H"

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


# =============================================================================
# CHAIN LENGTH TESTS
# =============================================================================

class TestPropertyChainLengths:
    """Tests for various property chain lengths."""

    def test_chain_length_3(self):
        """Test 3-property chain serialization with seed instance."""
        reasoner1 = Reter(variant="ai")

        reasoner1.load_ontology("""
        hasParent composed_with hasParent composed_with hasParent is_subproperty_of hasGreatGrandparent
        Person(SeedA)
        Person(SeedB)
        Person(SeedC)
        Person(SeedD)
        hasParent(SeedA, SeedB)
        hasParent(SeedB, SeedC)
        hasParent(SeedC, SeedD)
        """)

        # Verify before
        facts = reasoner1.query(type="role_assertion", subject="SeedA", role="hasGreatGrandparent")
        assert len(facts) == 1, "3-chain should work before serialize"

        with tempfile.NamedTemporaryFile(suffix='.pb', delete=False) as f:
            temp_file = f.name

        try:
            reasoner1.network.save(temp_file)

            reasoner2 = Reter(variant="ai")
            reasoner2.network.load(temp_file)

            reasoner2.load_ontology("""
            Person(NewA)
            Person(NewB)
            Person(NewC)
            Person(NewD)
            hasParent(NewA, NewB)
            hasParent(NewB, NewC)
            hasParent(NewC, NewD)
            """)

            facts = reasoner2.query(type="role_assertion", subject="NewA", role="hasGreatGrandparent", object="NewD")
            assert len(facts) == 1, "3-chain should produce hasGreatGrandparent(NewA, NewD)"

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


# =============================================================================
# INTERLEAVED OPERATIONS
# =============================================================================

class TestInterleavedOperations:
    """Tests for interleaved rule and fact additions across cycles."""

    def test_add_new_rule_after_deserialization(self):
        """
        Test adding a NEW property chain rule after deserialization.

        The original network has one chain with seed, after deserialization
        we add a different chain and verify both work.
        """
        reasoner1 = Reter(variant="ai")

        reasoner1.load_ontology("""
        hasParent composed_with hasParent is_subproperty_of hasGrandparent
        Person(Alice)
        Person(Bob)
        Person(Charlie)
        hasParent(Alice, Bob)
        hasParent(Bob, Charlie)
        """)

        with tempfile.NamedTemporaryFile(suffix='.pb', delete=False) as f:
            temp_file = f.name

        try:
            reasoner1.network.save(temp_file)

            reasoner2 = Reter(variant="ai")
            reasoner2.network.load(temp_file)

            # Add a NEW rule after deserialization with its own instances
            reasoner2.load_ontology("""
            hasSibling composed_with hasParent is_subproperty_of hasAuntOrUncle
            Person(Dana)
            Person(Edward)
            hasSibling(Alice, Dana)
            hasParent(Dana, Edward)
            """)

            # Verify old rule still works
            gp = reasoner2.query(type="role_assertion", subject="Alice", role="hasGrandparent", object="Charlie")
            assert len(gp) >= 1, "Old chain should work"

            # Verify new rule works
            au = reasoner2.query(type="role_assertion", subject="Alice", role="hasAuntOrUncle", object="Edward")
            assert len(au) >= 1, "New chain added after deserialize should work"

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


# =============================================================================
# REGRESSION TESTS
# =============================================================================

class TestSerializationRegression:
    """Regression tests for specific bugs found."""

    def test_production_node_network_pointer_with_seed(self):
        """
        Regression test for the ProductionNode.network pointer bug.

        This was the root cause: After deserialization, ProductionNode.network
        was NULL, preventing actions from firing.

        Note: Always include seed instances with the rule to ensure template
        instantiation occurs before serialization.
        """
        reasoner1 = Reter(variant="ai")

        reasoner1.load_ontology("""
        hasParent composed_with hasParent is_subproperty_of hasGrandparent
        Person(SeedAlice)
        Person(SeedBob)
        Person(SeedCharlie)
        hasParent(SeedAlice, SeedBob)
        hasParent(SeedBob, SeedCharlie)
        """)

        # Verify before
        seed_facts = reasoner1.query(type="role_assertion", subject="SeedAlice", role="hasGrandparent")
        assert len(seed_facts) == 1, "Seed should work"

        with tempfile.NamedTemporaryFile(suffix='.pb', delete=False) as f:
            temp_file = f.name

        try:
            reasoner1.network.save(temp_file)

            reasoner2 = Reter(variant="ai")
            reasoner2.network.load(temp_file)

            # Add instances - this triggered the bug when network pointer was NULL
            reasoner2.load_ontology("""
            Person(NewA)
            Person(NewB)
            Person(NewC)
            hasParent(NewA, NewB)
            hasParent(NewB, NewC)
            """)

            # The fix ensures hasGrandparent(NewA, NewC) is inferred
            facts = reasoner2.query(type="role_assertion", subject="NewA", role="hasGrandparent")
            assert len(facts) == 1, "Production actions should fire after deserialize"

            fact = facts[0]
            assert fact.get('subject') == 'NewA'
            assert fact.get('object') == 'NewC'
            assert fact.get('inferred_by') == 'prp-spo2'

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_template_provenance_with_seed_instances(self):
        """
        Test that template provenance is correctly restored.

        The prp-spo2-template instantiates rules dynamically, and the
        provenance must be serialized so actions can be restored.
        Each chain has seed instances to ensure template instantiation.
        """
        reasoner1 = Reter(variant="ai")

        # Two property chains with seed instances each
        reasoner1.load_ontology("""
        r1 composed_with r1 is_subproperty_of derived1
        r2 composed_with r2 is_subproperty_of derived2

        Entity(Seed1X)
        Entity(Seed1Y)
        Entity(Seed1Z)
        r1(Seed1X, Seed1Y)
        r1(Seed1Y, Seed1Z)

        Entity(Seed2X)
        Entity(Seed2Y)
        Entity(Seed2Z)
        r2(Seed2X, Seed2Y)
        r2(Seed2Y, Seed2Z)
        """)

        # Verify both work before
        d1_seed = reasoner1.query(type="role_assertion", subject="Seed1X", role="derived1")
        d2_seed = reasoner1.query(type="role_assertion", subject="Seed2X", role="derived2")
        assert len(d1_seed) == 1, "First chain should work before serialize"
        assert len(d2_seed) == 1, "Second chain should work before serialize"

        with tempfile.NamedTemporaryFile(suffix='.pb', delete=False) as f:
            temp_file = f.name

        try:
            reasoner1.network.save(temp_file)

            reasoner2 = Reter(variant="ai")
            reasoner2.network.load(temp_file)

            # Add new instances for both
            reasoner2.load_ontology("""
            Entity(NewX)
            Entity(NewY)
            Entity(NewZ)
            r1(NewX, NewY)
            r1(NewY, NewZ)

            Entity(NewA)
            Entity(NewB)
            Entity(NewC)
            r2(NewA, NewB)
            r2(NewB, NewC)
            """)

            # Both templates should have been restored
            d1 = reasoner2.query(type="role_assertion", subject="NewX", role="derived1")
            d2 = reasoner2.query(type="role_assertion", subject="NewA", role="derived2")

            assert len(d1) == 1, "First template should be restored"
            assert len(d2) == 1, "Second template should be restored"

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def test_original_fix_scenario_exact(self):
        """
        Exact reproduction of the original test scenario that failed.

        From test_property_chain_serialization.py: Alice->Bob->Charlie before,
        David->Eve->Frank after deserialization.
        """
        reasoner1 = Reter(variant="ai")

        ontology = """
        Person(Alice)
        Person(Bob)
        Person(Charlie)
        hasParent(Alice, Bob)
        hasParent(Bob, Charlie)
        hasParent composed_with hasParent is_subproperty_of hasGrandparent
        """

        reasoner1.load_ontology(ontology)

        # Verify before
        facts_before = reasoner1.query(
            type="role_assertion",
            subject="Alice",
            role="hasGrandparent",
            object="Charlie"
        )
        assert len(facts_before) > 0, "Should infer Alice hasGrandparent Charlie BEFORE serialization"

        with tempfile.NamedTemporaryFile(suffix='.pb', delete=False) as f:
            temp_file = f.name

        try:
            reasoner1.network.save(temp_file)

            reasoner2 = Reter(variant="ai")
            reasoner2.network.load(temp_file)

            # Add NEW instances
            new_ontology = """
            Person(David)
            Person(Eve)
            Person(Frank)
            hasParent(David, Eve)
            hasParent(Eve, Frank)
            """
            reasoner2.load_ontology(new_ontology)

            # CRITICAL: This was the failing case before the fix
            facts_new = reasoner2.query(
                type="role_assertion",
                subject="David",
                role="hasGrandparent",
                object="Frank"
            )

            assert len(facts_new) > 0, \
                "Should infer David hasGrandparent Frank (property chain on NEW instances after deserialization)"

            has_prp_spo2 = any(fact.get("inferred_by") == "prp-spo2" for fact in facts_new)
            assert has_prp_spo2, "Should have inference from prp-spo2 rule"

        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
